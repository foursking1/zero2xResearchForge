# -*- coding: utf-8 -*-
"""Hellinger distance on the 2-dim SGWB marginal between two posterior sample sets.

Defined as  H^2 = 1 - int sqrt(f g) dx  (0 <= H <= 1), Appendix H of the paper.

We marginalise over the 20 red-noise nuisance parameters and compare only the
2-dim SGWB spectral parameters (e.g. [log10 A, gamma] for PowerLaw).  Densities
are estimated with a weighted Gaussian KDE on a common 2-D grid (Scott bandwidth
from the effective sample size).  Unweighted (direct-NF / MCMC) sample sets use
w_i = 1.
"""
import numpy as np
from scipy.stats import gaussian_kde


def _effective_n(w):
    """Effective sample size of a normalised/un-normalised weight set."""
    s = w.sum()
    if s <= 0:
        return 1.0
    return float(s * s / np.sum(w * w))


def weighted_kde_grid(x, w, grid, bw_scale=None):
    """Evaluate a weighted Gaussian KDE of x (N,2) at grid points (G,2).

    Bandwidth: Scott's rule using the weighted covariance and effective N.
    Returns density values f (G,) normalised so that the 2-D integral = 1
    (integrated by the caller with the grid cell area).
    """
    w = np.asarray(w, dtype=float)
    w = w / w.sum()
    n_eff = _effective_n(w)
    # weighted mean and covariance
    mu = np.average(x, axis=0, weights=w)
    d = x - mu
    cov = (d * w[:, None]).T @ d / (1.0 - np.sum(w * w))  # weighted cov (unbiased-ish)
    cov = np.atleast_2d(cov)
    # Scott rule bandwidth factor: n_eff^{-1/(d+4)} with d=2 -> n_eff^{-1/6}
    bw = n_eff ** (-1.0 / 6.0)
    # incorporate per-dim std from cov into a diagonal bandwidth for stability
    var = np.clip(np.diag(cov), 1e-12, None)
    sig = np.sqrt(var)
    if bw_scale is not None:
        sig = sig * bw_scale
    # evaluate: f(g) = sum_i w_i * prod_j N(g_j | x_ij, (bw*sig_j)^2)
    # vectorized over grid points
    f = np.zeros(len(grid))
    # chunk the grid to bound memory
    chunk = 4096
    for g0 in range(0, len(grid), chunk):
        gc = grid[g0:g0 + chunk]                      # (Gc,2)
        dg = gc[:, None, :] - x[None, :, :]           # (Gc,N,2)
        dg2 = (dg / (bw * sig)[None, None, :]) ** 2
        k = np.exp(-0.5 * dg2.sum(axis=-1))           # (Gc,N)
        f[g0:g0 + chunk] = k @ w
    # unnormalised KDE; the caller renormalises so the grid integral equals 1,
    # so the kernel normalisation constant 1/(2 pi bw^2 sig_x sig_y) cancels.
    return f, bw, sig


def hellinger_2d(x1, x2, w1=None, w2=None, grid=None, pad=1.5):
    """Hellinger distance between two 2-D sample sets x1, x2 (each N,2).

    w1, w2: optional weights (default uniform).  grid: optional (G,2) points;
    if None, a 72x72 grid spanning the union of the two samples padded by the
    KDE bandwidth is built.
    """
    x1 = np.asarray(x1, dtype=float)
    x2 = np.asarray(x2, dtype=float)
    n1, n2 = len(x1), len(x2)
    w1 = np.ones(n1) if w1 is None else np.asarray(w1, dtype=float)
    w2 = np.ones(n2) if w2 is None else np.asarray(w2, dtype=float)

    if grid is None:
        lo = np.minimum(x1.min(axis=0), x2.min(axis=0))
        hi = np.maximum(x1.max(axis=0), x2.max(axis=0))
        # rough bandwidth from combined std
        sig1 = np.sqrt(np.clip(np.var(x1, axis=0), 1e-12, None))
        sig2 = np.sqrt(np.clip(np.var(x2, axis=0), 1e-12, None))
        bw = (np.mean(sig1 + sig2) / 2.0) * 0.5
        lo = lo - pad * bw
        hi = hi + pad * bw
        gx = np.linspace(lo[0], hi[0], 72)
        gy = np.linspace(lo[1], hi[1], 72)
        gx, gy = np.meshgrid(gx, gy)
        grid = np.column_stack([gx.ravel(), gy.ravel()])

    f1, bw1, sig1 = weighted_kde_grid(x1, w1, grid)
    f2, bw2, sig2 = weighted_kde_grid(x2, w2, grid)

    # normalise densities so the grid integral equals 1
    # grid spacing
    gx = np.unique(grid[:, 0]); gy = np.unique(grid[:, 1])
    dx = gx[1] - gx[0] if len(gx) > 1 else 1.0
    dy = gy[1] - gy[0] if len(gy) > 1 else 1.0
    cell = dx * dy
    f1 = f1 / (f1.sum() * cell)
    f2 = f2 / (f2.sum() * cell)

    bc = np.sum(np.sqrt(f1 * f2)) * cell
    bc = np.clip(bc, 0.0, 1.0)
    H = np.sqrt(max(0.0, 1.0 - bc))
    return float(H), (grid, f1, f2)


def hellinger_1d(x1, x2, w1=None, w2=None, nbins=100):
    """Hellinger distance between two 1-D sample sets (grid-histogram based)."""
    x1 = np.asarray(x1, dtype=float)
    x2 = np.asarray(x2, dtype=float)
    w1 = np.ones(len(x1)) if w1 is None else np.asarray(w1, dtype=float)
    w2 = np.ones(len(x2)) if w2 is None else np.asarray(w2, dtype=float)
    lo = min(x1.min(), x2.min())
    hi = max(x1.max(), x2.max())
    if hi - lo < 1e-12:
        return 0.0
    bins = np.linspace(lo, hi, nbins + 1)
    h1, _ = np.histogram(x1, bins=bins, weights=w1, density=True)
    h2, _ = np.histogram(x2, bins=bins, weights=w2, density=True)
    # density=True already normalises to unit integral
    bc = np.sum(np.sqrt(h1 * h2)) * (bins[1] - bins[0])
    bc = np.clip(bc, 0.0, 1.0)
    return float(np.sqrt(max(0.0, 1.0 - bc)))
