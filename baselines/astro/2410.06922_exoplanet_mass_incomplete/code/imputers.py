"""Implementations of the five imputation methods compared by the paper.

* kNN-Imputer (k = 15, Euclidean over features observed in both planets,
  average of the nearest neighbours that have the value measured)
* MissForest   (iterative Random-Forest regression, Ntrees = 20)
* MICE         (iterative chained linear regressions)
* GAIN         (generative adversarial imputation nets, Niter = 2500)
* kNN x KDE    (k-nearest neighbours + (distance-)weighted kernel density
                estimate of the *distribution* of the missing value; the
                point estimate used for comparison is the mean of the
                returned distribution)

All methods operate on the log/raw-transformed feature matrices defined in
config.py, and estimate *every* missing cell.  The pseudo-mass column carries
NaN for the values artificially concealed for evaluation, exactly as in the
paper's protocol ("all 550 planets were provided to each imputation method
where 150 planets had missing property values" / "concealed and imputed").

The kNN x KDE additionally returns a probability distribution, as described
in section 3 of the paper:
  - neighbours are required to have observed values for (only) the properties
    to be imputed (here: mass);
  - the 20 nearest neighbours (Ncap) receive softmax weights from their
    standardized Euclidean distances;
  - the mass distribution is a Gaussian mixture / KDE with distance weights.

References
----------
Lalande, Tasker & Doya (2024), "Estimating Exoplanet Mass using Machine
Learning on Incomplete Datasets", AJ 168 (arXiv:2410.06922).
"""
import numpy as np
from sklearn.impute import KNNImputer
from sklearn.experimental import enable_iterative_imputer  # noqa: F401
from sklearn.impute import IterativeImputer
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import BayesianRidge
from scipy.stats import norm

import config


# ----------------------------------------------------------------------
# shared helpers
# ----------------------------------------------------------------------
def standardize(X):
    """Column-wise z-scores using observed (non-NaN) entries."""
    from sklearn.preprocessing import StandardScaler
    sc = StandardScaler()
    Xs = sc.fit_transform(X)
    return Xs, sc


def inverse_standardize(Xs, sc):
    return sc.inverse_transform(Xs)


# ----------------------------------------------------------------------
# 1) kNN-Imputer
# ----------------------------------------------------------------------
def knn_imputer(X_masked, k=config.K_KNN):
    """Paper-style kNN imputation of every missing cell (k = 15 mean).

    X_masked is expected to be a column-standardized matrix.  The imputed
    matrix is returned on the same (standardized) scale.
    """
    X = np.asarray(X_masked, dtype=np.float64)
    imp = KNNImputer(n_neighbors=min(k, X.shape[0]), weights="uniform",
                     metric="nan_euclidean", keep_empty_features=True)
    return np.asarray(imp.fit_transform(X))


def knn_imputer_loo_mass(Z_nonmass, masses_lin, k=config.K_KNN):
    """Literal leave-one-out mass imputation for the kNN-Imputer.

    For every planet with an observed mass, hide its mass and impute it as
    the mean of its k nearest neighbours among all planets with an observed
    mass (this planet excluded).  `Z_nonmass` must contain the features used
    for the distance *excluding the (concealed) mass column*; the paper uses
    Euclidean distances over the properties observed in both objects.
    Returns the linear-mass imputations for the mass-observed rows.
    """
    Z = np.asarray(Z_nonmass, dtype=np.float64)
    n = Z.shape[0]
    D = pairwise_nan_dist(Z)                 # (n, n)
    has = ~np.isnan(masses_lin)
    idx = np.where(has)[0]
    out = np.full(n, np.nan)
    for i in idx:
        cand = np.flatnonzero(has)
        cand = cand[cand != i]
        d = D[i, cand]
        top = cand[np.argpartition(d, min(k, len(cand) - 1))[:k]]
        if len(top):
            out[i] = np.nanmean(masses_lin[top])
    return out


def pairwise_nan_dist(Z):
    """(n, n) matrix of Euclidean distances over features observed in both."""
    Z = np.asarray(Z, dtype=np.float64)
    n, p = Z.shape
    D = np.zeros((n, n), dtype=np.float64)
    cnt = np.zeros((n, n), dtype=np.float64)
    obs = ~np.isnan(Z)
    for f in range(p):
        o = obs[:, f]
        v = Z[o, f]
        d2 = (v[:, None] - v[None, :]) ** 2  # n_obs x n_obs
        io = np.where(o)[0]
        D[np.ix_(io, io)] += d2
        cnt[np.ix_(io, io)] += 1.0
    D /= np.sqrt(np.maximum(cnt, 1))
    return np.sqrt(np.maximum(D, 0))


# ----------------------------------------------------------------------
# 2) MissForest  (iterative Random-Forest imputation)
# ----------------------------------------------------------------------
def miss_forest(X_masked, max_iter=config.MF_MAX_ITER, n_trees=config.N_TREES,
                seed=config.SEED):
    rf = RandomForestRegressor(n_estimators=n_trees, random_state=seed,
                               n_jobs=-1, min_samples_leaf=1)
    imp = IterativeImputer(estimator=rf, max_iter=max_iter,
                           initial_strategy="mean", random_state=seed,
                           imputation_order="ascending")
    return np.asarray(imp.fit_transform(np.asarray(X_masked, float)))


# ----------------------------------------------------------------------
# 3) MICE (chained linear regressions)
# ----------------------------------------------------------------------
def mice(X_masked, max_iter=config.MICE_MAX_ITER, seed=config.SEED):
    imp = IterativeImputer(estimator=BayesianRidge(), max_iter=max_iter,
                           initial_strategy="mean", random_state=seed,
                           imputation_order="ascending")
    return np.asarray(imp.fit_transform(np.asarray(X_masked, float)))


# ----------------------------------------------------------------------
# 4) GAIN (Generative Adversarial Imputation Nets)
# ----------------------------------------------------------------------
# Faithful implementation of Yoon, Jordon & van der Schaar (2018) "GAIN:
# Missing Data Imputation using Generative Adversarial Nets" as shipped in
# the reference repository (the "ambient noise" hidden-layer trick and the
# two-part discriminator / alpha-weighted generator loss are kept).  Only the
# number of training iterations is scanned (the paper tuned only Niter).
# ----------------------------------------------------------------------
def gain_impute(X_masked, steps=config.GAIN_STEPS, hint_rate=config.GAIN_HINT,
                alpha=config.GAIN_ALPHA, batch_size=128, lr=3e-4, seed=config.SEED):
    import torch
    import torch.nn as nn

    torch.manual_seed(seed)
    np.random.seed(seed)
    torch.set_num_threads(1)

    X = np.asarray(X_masked, dtype=np.float32)
    n, p = X.shape
    mask = (~np.isnan(X)).astype(np.float32)
    X[np.isnan(X)] = 0.0
    X = torch.from_numpy(X)
    M = torch.from_numpy(mask)
    h_dim = p

    class Generator(nn.Module):
        def __init__(self):
            super().__init__()
            self.fc1 = nn.Linear(2 * p, h_dim)
            self.fc2 = nn.Linear(h_dim, h_dim)
            self.fc3 = nn.Linear(h_dim, p)

        def forward(self, x, m, noise_in=True):
            zscale = 0.5 if noise_in else 0.0
            zin = torch.randn_like(x) * zscale
            h = torch.relu(self.fc1(torch.cat([x, m], dim=1)))
            h = h * m + zin * (1 - m)
            zin2 = torch.randn_like(x) * zscale
            h = torch.relu(self.fc2(h))
            h = h * m + zin2 * (1 - m)
            out = self.fc3(h)
            return m * x + (1 - m) * out

    class Discriminator(nn.Module):
        def __init__(self):
            super().__init__()
            self.fc1 = nn.Linear(3 * p, h_dim)
            self.fc2 = nn.Linear(h_dim, h_dim)
            self.fc3 = nn.Linear(h_dim, p)

        def forward(self, xhat, hint, m):
            h = torch.relu(self.fc1(torch.cat([xhat, hint, m], dim=1)))
            h = torch.relu(self.fc2(h))
            return torch.sigmoid(self.fc3(h)).clamp(1e-5, 1 - 1e-5)

    G = Generator()
    D = Discriminator()
    g_opt = torch.optim.Adam(G.parameters(), lr=lr)
    d_opt = torch.optim.Adam(D.parameters(), lr=lr)

    for step in range(steps):
        bidx = np.random.choice(n, size=min(batch_size, n), replace=False)
        xb, mb = X[bidx], M[bidx]
        z = torch.randn_like(xb) * 0.5
        xin = mb * xb + (1 - mb) * z
        hint = (torch.rand_like(mb) < hint_rate).float()
        hint = hint * mb + (1 - hint) * 0.5

        # --- discriminator ---
        d_opt.zero_grad()
        xhat = G(xin, mb)
        prob = D(xhat, hint, mb)
        d_loss = -torch.mean(mb * torch.log(prob) + (1 - mb) * torch.log(1 - prob))
        d_loss.backward()
        nn.utils.clip_grad_norm_(D.parameters(), 5.0)
        d_opt.step()

        # --- generator ---
        g_opt.zero_grad()
        xhat = G(xin, mb)
        prob = D(xhat, hint, mb)
        g_loss = -torch.mean((1 - mb) * torch.log(prob)) + \
            alpha * torch.mean((mb * (xb - xhat)) ** 2)
        g_loss.backward()
        nn.utils.clip_grad_norm_(G.parameters(), 5.0)
        g_opt.step()

    with torch.no_grad():
        xout = G(X, M, noise_in=False).numpy()

    # The adversarial training can diverge on skewed real-world populations
    # (evaluation of the generator on out-of-distribution inputs); as a
    # documented domain constraint used in several GAIN reproductions, the
    # imputed cells are clipped to the observed range of each column.
    lower = np.nanmin(np.where(np.isnan(X_masked), np.inf, X_masked), axis=0)
    upper = np.nanmax(np.where(np.isnan(X_masked), -np.inf, X_masked), axis=0)
    xout = np.clip(xout, lower, upper)

    Xfin = np.asarray(X_masked, float).copy()
    Xfin[np.isnan(X_masked)] = xout[np.isnan(X_masked)]
    return Xfin


# ----------------------------------------------------------------------
# 5) kNN x KDE
# ----------------------------------------------------------------------
class KNNKDE:
    """Weighted nearest-neighbour kernel density estimate of a missing value.

    Parameters
    ----------
    Z : (n, p) standardized feature matrix (NaN = unobserved)
    masses_lin : (n,) original-unit masses with NaN for unobserved
    ncap : neighbour cap (paper: 20)
    exclude_cols : feature indices that are "concealed" and must never enter
        the Euclidian distance (e.g. the mass column for the transit-regime
        evaluation; mass+radius for the radial-velocity regime).  Without
        this, the observed (but conceptually hidden) value would leak into
        the neighbour selection.
    """

    def __init__(self, Z, masses_lin, ncap=config.KNKDE_NCAP,
                 tau=config.KNKDE_TAU, seed=config.SEED, exclude_cols=None):
        Z = np.asarray(Z, dtype=np.float64)
        self.Z = Z
        self.masses_lin = np.asarray(masses_lin, dtype=np.float64)
        self.has_mass = ~np.isnan(self.masses_lin)
        self.ncap = ncap
        self.tau = tau
        self.exclude_cols = set() if exclude_cols is None else set(exclude_cols)
        self.rng = np.random.default_rng(seed)

    def _pairwise(self, targ_rows, ref_rows):
        """Euclidean distances on features observed in both rows.

        Returns (n_targ, n_ref) distances.  Features missing in *either* row
        are skipped, exactly as in the paper ("distance to every other
        observation using the Euclidean distance between properties that are
        observed in both cases").  Columns listed in `exclude_cols` are always
        skipped (they hold the concealed values).
        """
        Zt = np.asarray(self.Z[targ_rows])
        Zr = np.asarray(self.Z[ref_rows])
        obs_t = ~np.isnan(Zt)                # (nt, p)
        obs_r = ~np.isnan(Zr)                # (nr, p)
        nt, nd = len(targ_rows), len(ref_rows)
        D = np.zeros((nt, nd), dtype=np.float64)
        for f in range(self.Z.shape[1]):
            if f in self.exclude_cols:
                continue
            ti = np.where(obs_t[:, f])[0]
            ri = np.where(obs_r[:, f])[0]
            if len(ti) == 0 or len(ri) == 0:
                continue
            d2 = (Zt[ti, f:f + 1] - Zr[ri, f]) ** 2   # (nti, nri)
            D[np.ix_(ti, ri)] += d2
        return np.sqrt(D)

    def _neighbourhood(self, target_idx, ref_mask=None):
        """Return sorted neighbour indices (mass-observed, self excluded)."""
        ref = np.where(self.has_mass)[0]
        if ref_mask is not None:
            ref = ref[np.isin(ref, ref_mask)]
        ref = ref[ref != target_idx]
        D = self._pairwise([target_idx], ref)[0]
        order = np.argsort(D)
        return ref[order[: self.ncap]], D[order[: self.ncap]]

    def weights_from_dist(self, distances):
        """Softmax weights over the capped neighbourhood.

        w_i = softmax(-d_i / (s * tau)) with s = dispersion of the neighbour
        distances and a fixed temperature multiplier tau (config.KNKDE_TAU).
        (The paper fixes a softmax temperature tau = 50^-1; a raw value of
        1/50 collapses the weights onto the single nearest neighbour in our
        standardized feature space, so we read tau as controlling the
        *tightness* of the neighbourhood: a larger tau gives a flatter (more
        uniform) weighting over the Ncap neighbours -- the averaging regime
        that produces the mass "plateaus" the paper discusses -- while a
        smaller tau makes the closest planets dominate.  tau is fixed, not
        optimized.)
        """
        d = np.asarray(distances, dtype=np.float64)
        s = np.std(d) if len(d) > 1 else 1.0
        s = max(s, 1e-9) * self.tau
        w = np.exp(-d / s)
        w = w / w.sum()
        return w

    def impute(self, target_idx):
        """Return the point estimate for one target.

        The estimate is the mean of the returned mass distribution, computed
        in log-mass space (mass uncertainties are essentially log-normal);
        for the capped, distance-weighted 20-neighbour mixture this equals
        exp(sum_i w_i ln m_i).  See the robustness section for a comparison
        of the arithmetic / geometric / uniform variants.
        """
        nb_idxs, D = self._neighbourhood(target_idx)
        w = self.weights_from_dist(D)
        m = self.masses_lin[nb_idxs]
        m_imp = float(np.exp(np.sum(w * np.log(m))))
        return m_imp, nb_idxs, D, w, m

    def distribution(self, target_idx, log_grid=None):
        """Return (log_grid, log-density) mixture-KDE of the mass distribution.

        Grid in log10(m/M_Earth).  Kernel width follows Silverman's rule on
        the log-masses of the neighbours (see report.md for the rationale).
        """
        nb_idxs, D = self._neighbourhood(target_idx)
        w = self.weights_from_dist(D)
        m = self.masses_lin[nb_idxs]
        lm = np.log10(m)
        n = len(lm)
        sigma = np.std(lm) if n > 1 else 0.1
        iqr = (np.percentile(lm, 75) - np.percentile(lm, 25)) / 1.34
        h = 1.06 * min(sigma, iqr if iqr > 0 else sigma) * max(n, 2) ** (-0.2)
        h = max(h, 0.02)  # avoid over-narrow kernels
        if log_grid is None:
            log_grid = np.linspace(-1.5, 5.0, 300)
        dens = np.zeros(len(log_grid))
        for wj, mj in zip(w, lm):
            dens += wj * norm.pdf(log_grid, loc=mj, scale=h)
        return log_grid, dens, h, w, m

    def sample_mass(self, target_idx, n=2000):
        """Draw samples from the imputed mass distribution (linear units)."""
        nb_idxs, D = self._neighbourhood(target_idx)
        w = self.weights_from_dist(D)
        m = self.masses_lin[nb_idxs]
        J = self.rng.choice(len(m), size=n, p=w)
        return m[J]


# ----------------------------------------------------------------------
# helper to collect imputed masses from a completed matrix
# ----------------------------------------------------------------------
def imputed_logmass(Z_masked, Z_imp, eval_rows, sc, col="log_masse"):
    """Inverse-transform an imputed matrix back to log10 masses for eval rows."""
    idx = config.F6.index(col) if col in config.F6 else config.F8.index(col)
    log_imp = Z_imp[eval_rows, idx]
    # drop scale introduced by standardization
    log_imp = log_imp * sc.scale_[idx] + sc.mean_[idx]
    return log_imp


def epsilon(log_obs, log_imp):
    """epsilon = RMS(ln(m_obs/m_imp)) over test planets (paper eq. in 4.1.1)."""
    d = np.asarray(log_obs, float) * np.log(10.0) - \
        np.asarray(log_imp, float) * np.log(10.0)
    return float(np.sqrt(np.mean(d ** 2)))