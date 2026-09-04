# -*- coding: utf-8 -*-
"""22-dimensional PTA likelihood (per-pulsar power-law red noise + HD-correlated SGWB).

Built on the real NG15 ToA grid and white-noise levels extracted from the frozen
.tim files (ptadata.load_toas). The likelihood is the Gaussian marginal over the
Fourier coefficients of red noise and the SGWB common process:

    r ~ N(0, C),   C = N + F (Phi_red + Gamma_kron_phiGW) F^T

with Nf = 14 Fourier frequencies (paper Sec.II), Hellings-Downs matrix Gamma (Eq.7).

This is the likelihood used for BOTH the MCMC reference and the NF (paper's
forward-simulation protocol). It is a well-defined joint model for the 22 dims
(20 red-noise params + 2 SGWB params).

SGWB spectral models implemented (paper Appendix C):
  - PowerLaw : S(f) = A^2/(12 pi^2) (f/fyr)^(-gamma) fyr^-3          (Eq.5/red-noise form)
  - SMBHB    : S(f) = A^2/(12 pi^2) (f/fyr)^(-13/3) fyr^-3 /(1+(fbend/f)^(10/3))
  - DW       : broken power law S(f) = A^2/(12 pi^2) fyr^-3 (f/fyr)^(-3) x shape(f/fpeak),
               shape = (x)^3 for x<1 and x^-1 for x>=1   (Omega shape of Eq.C5-C7,
               converted to residual PSD S ~ Omega/f^6)
"""
import numpy as np
from scipy.linalg import cholesky, solve_triangular, inv

F_YR = 1.0 / 31557600.0  # 1/yr in Hz

# ---------- Hellings-Downs ----------
def hellings_downs(ra, dec):
    """Gamma_IJ from pulsar sky positions (ra, dec in radians)."""
    # angular separation
    cosang = np.cos(dec[:, None]) * np.cos(dec[None, :]) * np.cos(ra[:, None] - ra[None, :]) \
        + np.sin(dec[:, None]) * np.sin(dec[None, :])
    cosang = np.clip(cosang, -1, 1)
    ang = np.arccos(cosang)
    x = (1 - cosang) / 2.0
    gamma = 1.5 * x * np.log(x) - x / 4.0 + 0.5
    # diagonal should be 1
    np.fill_diagonal(gamma, 1.0)
    return gamma


# ---------- SGWB spectral shapes ----------
def sgwb_spectral(model_name, f, params, fyr=F_YR):
    """Return S_GW(f) [s^3] for the given model and 2 SGWB params.

    params: [log10 A, second-param] with second-param depending on model.
    """
    f = np.atleast_1d(np.asarray(f, dtype=float))
    if model_name == "PowerLaw":
        logA, gam = params
        A = 10 ** logA
        return (A ** 2) / (12 * np.pi ** 2) * (f / fyr) ** (-gam) * fyr ** (-3)
    elif model_name == "SMBHB":
        logA, logfb = params
        A = 10 ** logA
        fb = 10 ** logfb
        pl = (A ** 2) / (12 * np.pi ** 2) * (f / fyr) ** (-13.0 / 3.0) * fyr ** (-3)
        bend = 1.0 / (1.0 + (fb / f) ** (10.0 / 3.0))
        return pl * bend
    elif model_name == "DW":
        logA, logfp = params
        A = 10 ** logA
        fp = 10 ** logfp
        base = (A ** 2) / (12 * np.pi ** 2) * (f / fyr) ** (-3.0) * fyr ** (-3)
        x = f / fp
        shape = np.where(x < 1.0, x ** 3, x ** (-1.0))
        return base * shape
    else:
        raise ValueError(model_name)


class PTAJointLikelihood:
    """Gaussian likelihood p(r | theta) with marginalised Fourier coefficients.

    Precomputes A = F^T N^-1 F (280x280, block-diagonal per pulsar), b = F^T N^-1 r,
    c = r^T N^-1 r. Per-eval work: build Lambda = Phi_red + Gamma (x) phi_GW (280x280),
    invert, Woodbury for the quadratic form and log-det.
    """

    def __init__(self, times, sigma, ra, dec, nfreq=14, model_name="PowerLaw"):
        """times: list of per-pulsar ToA time arrays (s). sigma: list of white-noise stds (s).
        ra, dec: pulsar sky positions (radians)."""
        self.model_name = model_name
        self.npul = len(times)
        self.times = times
        self.sigma = sigma
        T_obs = max(t.max() for t in times)
        self.T_obs = T_obs
        freqs = np.arange(1, nfreq + 1) / T_obs
        self.freqs = freqs
        self.nfreq = nfreq
        self.dim_coef = 2 * nfreq  # 28 per pulsar
        self.dim = 2 * self.npul + 2  # 22

        # Hellings-Downs
        self.Gamma = hellings_downs(ra, dec)
        # Cholesky of Gamma for fast common-process simulation
        self.Gamma_chol = np.linalg.cholesky(self.Gamma)

        # per-pulsar Fourier design matrices and precomputed stats
        self.F = []
        self.A_blocks = []  # F_I^T N_I^-1 F_I
        self.FtNinvF = np.zeros((self.npul * self.dim_coef, self.npul * self.dim_coef))
        self.logdetN = 0.0
        for i, (t, s) in enumerate(zip(times, sigma)):
            F_i = self._fourier_basis(t, freqs)  # N_i x 28
            self.F.append(F_i)
            Ninv = 1.0 / s ** 2
            A_i = (F_i * Ninv[:, None]).T @ F_i  # 28x28
            self.A_blocks.append(A_i)
            sl = slice(i * self.dim_coef, (i + 1) * self.dim_coef)
            self.FtNinvF[sl, sl] = A_i
            self.logdetN += np.sum(np.log(s ** 2))

        self.N_inv_sqrt_F = []  # store N^-1/2 F for simulation
        for i, (t, s) in enumerate(zip(times, sigma)):
            self.N_inv_sqrt_F.append(self.F[i] / s[:, None])

    def _fourier_basis(self, t, freqs):
        cols = []
        for f in freqs:
            cols.append(np.cos(2 * np.pi * f * t))
            cols.append(np.sin(2 * np.pi * f * t))
        return np.column_stack(cols)

    # ----- parameter helpers -----
    def rednoise_phi(self, logA_red, gamma_red):
        """Diagonal 28-dim per-pulsar red-noise coefficient variance."""
        phis = []
        for logA, gam in zip(logA_red, gamma_red):
            A = 10 ** logA
            phi = (A ** 2) / (12 * np.pi ** 2) * (self.freqs / F_YR) ** (-gam) * F_YR ** (-3) / self.T_obs
            phis.append(np.repeat(phi, 2))
        return np.concatenate(phis)  # 280-dim

    def common_phi(self, sgwb_params):
        phi = sgwb_spectral(self.model_name, self.freqs, sgwb_params) / self.T_obs
        return np.repeat(phi, 2)  # 28-dim (sin & cos)

    def build_Lambda(self, theta):
        """theta: 22-dim [logA_red_1..10, gamma_red_1..10, sgwb1, sgwb2]."""
        logA_red = theta[0:self.npul]
        gamma_red = theta[self.npul:2 * self.npul]
        sgwb = theta[2 * self.npul:2 * self.npul + 2]
        phi_red = self.rednoise_phi(logA_red, gamma_red)  # 280
        phi_gw = self.common_phi(sgwb)  # 28
        # Lambda = Phi_red + Gamma (x) diag(phi_gw)  [pulsar-index outer]
        # ordering of 280-vector: [pulsar I, (freq,sin/cos)]  -> block index = pulsar
        Lam = np.diag(phi_red)
        Phi_gw_diag = np.diag(phi_gw)
        kron = np.kron(self.Gamma, Phi_gw_diag)
        Lam = Lam + kron
        return Lam

    def loglike(self, theta, r=None, b=None, c=None, precomputed=None):
        """Full log-likelihood. Precompute b,c once per dataset via prepare_data()."""
        if precomputed is not None:
            b, c = precomputed["b"], precomputed["c"]
        Lam = self.build_Lambda(theta)
        # check Lambda is PSD first (also yields logdetLam); if not -> -inf
        try:
            LL = cholesky(Lam, lower=True)
            logdetLam = 2.0 * np.sum(np.log(np.diag(LL)))
        except np.linalg.LinAlgError:
            return -np.inf
        Lam_inv = inv(Lam)
        M = Lam_inv + self.FtNinvF
        try:
            L = cholesky(M, lower=True)
        except np.linalg.LinAlgError:
            return -np.inf
        logdetM = 2.0 * np.sum(np.log(np.diag(L)))
        # solve M y = b
        y = solve_triangular(L, b, lower=True)
        y = solve_triangular(L.T, y, lower=False)
        quad = c - np.dot(b, y)
        logdetC = self.logdetN + logdetLam + logdetM
        N_total = sum(len(t) for t in self.times)
        logL = -0.5 * (quad + logdetC + N_total * np.log(2 * np.pi))
        if not np.isfinite(logL):
            return -np.inf
        return float(logL)

    def prepare_data(self, r):
        """b = F^T N^-1 r (280), c = r^T N^-1 r."""
        b_list = []
        c = 0.0
        idx = 0
        for i, (t, s) in enumerate(zip(self.times, self.sigma)):
            ri = r[idx:idx + len(t)]
            idx += len(t)
            Ninv = 1.0 / s ** 2
            b_i = (self.F[i] * Ninv[:, None]).T @ ri
            b_list.append(b_i)
            c += np.sum(ri ** 2 * Ninv)
        b = np.concatenate(b_list)
        return {"b": b, "c": float(c), "r": r}

    # ----- simulation (paper protocol: forward-simulate residuals) -----
    def simulate(self, theta, rng=None):
        """Draw a residual vector from the model at theta (full N_total-dim).

        Fast simulation: red-noise coefficients are drawn per pulsar from the diagonal
        covariance; common-process coefficients are drawn as
            C (10x28) = chol(Gamma) @ (z * sqrt(phi_gw)[None, :])
        which has covariance Gamma (x) diag(phi_gw).
        """
        if rng is None:
            rng = np.random.default_rng(0)
        logA_red = theta[0:self.npul]
        gamma_red = theta[self.npul:2 * self.npul]
        sgwb = theta[2 * self.npul:2 * self.npul + 2]
        phi_gw = self.common_phi(sgwb)  # 28 (sin/cos repeated)
        # common-process coefficients: 10 x 28
        z = rng.standard_normal((self.npul, self.dim_coef))
        coef_common = self.Gamma_chol @ (z * np.sqrt(phi_gw)[None, :])  # (10,28)

        resid = []
        for i, (t, s) in enumerate(zip(self.times, self.sigma)):
            ni = len(t)
            F_i = self.F[i]
            # red noise coefficients for this pulsar (28-dim, independent)
            A_red = 10 ** logA_red[i]
            phi_red_i = (A_red ** 2) / (12 * np.pi ** 2) * \
                (self.freqs / F_YR) ** (-gamma_red[i]) * F_YR ** (-3) / self.T_obs
            phi_red_i = np.repeat(phi_red_i, 2)
            coef_red = rng.standard_normal(self.dim_coef) * np.sqrt(phi_red_i)
            seg = F_i @ (coef_red + coef_common[i])
            seg += s * rng.standard_normal(ni)
            resid.append(seg)
        return np.concatenate(resid)

    # ----- priors -----
    @staticmethod
    def prior_ranges(model_name):
        """(lo, hi) for each of the 22 dims (log-uniform for amplitudes, uniform for indices)."""
        lo = [-19.0] * 10 + [1.0] * 10
        hi = [-13.0] * 10 + [7.0] * 10
        if model_name == "PowerLaw":
            lo += [-18.0, 1.0]
            hi += [-13.0, 7.0]
        elif model_name == "SMBHB":
            lo += [-18.0, -10.0]
            hi += [-12.0, -7.0]
        elif model_name == "DW":
            lo += [-18.0, -9.0]
            hi += [-12.0, -6.0]
        return np.array(lo), np.array(hi)

    def prior_logp(self, theta, lo, hi):
        if np.any(theta < lo) or np.any(theta > hi):
            return -np.inf
        # log-uniform for amplitude dims (0..9, 20), uniform for index dims (10..19, 21)
        lp = 0.0
        for d in range(22):
            if d < 10 or d == 20:
                lp += -np.log(hi[d] - lo[d]) * np.log(10.0)  # density in log10 space
            else:
                lp += -np.log(hi[d] - lo[d])
        return lp
