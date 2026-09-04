"""Correct implementation of the Volume Growth Transform (VGT) and VGT-dot.

The frozen reference implementation (`stratification_analysis.py` in the
reproduction workspace) contains a bug in its radius selection
(`_compute_radii`): `cKDTree.query(x, k=1)` returns the *index* of the nearest
neighbour (the point itself), so the "diameter" it computes is a neighbour
index, not a distance.  The resulting radii are orders of magnitude larger than
the data extent, all balls contain every point and every local-dimension
estimate collapses to ~0 (this is exactly what we observe when running the
frozen code; see C01 run).  We therefore implement the VGT faithfully from the
paper definition (Definition II.8) with a correct radius grid, and use the
frozen code only for comparison.

    VGT_x(s) = log mu(B_x(r = e^s))
    local dim n_x = d(log volume)/d(log r) over a small-radius window.
"""
import numpy as np
from scipy.spatial import cKDTree
from scipy.spatial.distance import cdist


def estimate_diameter(data, n_sample=400, seed=0):
    """Robust diameter estimate = max distance from a sample to any point."""
    rng = np.random.default_rng(seed)
    n = len(data)
    if n_sample >= n:
        idx = np.arange(n)
    else:
        idx = rng.choice(n, n_sample, replace=False)
    d = cdist(data[idx], data)          # (n_sample, n)
    return float(d.max())


def compute_radii(data, n_radii=28, r_min_frac=1e-4, r_max_frac=1.0,
                  seed=0):
    """Log-spaced radius grid spanning the data scale."""
    dia = estimate_diameter(data, seed=seed)
    r_min = max(dia * r_min_frac, 1e-9)
    r_max = dia * r_max_frac
    return np.logspace(np.log10(r_min), np.log10(r_max), n_radii), dia


def compute_vgt(data, center_indices=None, radii=None, n_radii=28,
                include_self=True):
    """Return dict with radii, log_radii, vgt_curves (n_pts x n_radii).

    mu(B_x(r)) is the counting measure (number of data points in the ball).
    """
    tree = cKDTree(data)
    if center_indices is None:
        center_indices = np.arange(len(data))
    center_indices = np.asarray(center_indices)
    if radii is None:
        radii, _ = compute_radii(data, n_radii=n_radii)

    curves = np.zeros((len(center_indices), len(radii)))
    for i, ci in enumerate(center_indices):
        for j, r in enumerate(radii):
            idxs = tree.query_ball_point(data[ci], r)
            n_in = len(idxs)
            if not include_self:
                n_in = max(0, n_in - 1)
            curves[i, j] = np.log(n_in + 1e-8)
    return {
        "radii": radii,
        "log_radii": np.log(radii),
        "vgt_curves": curves,
        "log_volumes": curves,
    }


def local_dim_from_vgt(log_r, log_v, r_min, r_max):
    """OLS slope of log VGT over radii in [r_min, r_max]."""
    mask = (np.exp(log_r) >= r_min) & (np.exp(log_r) <= r_max)
    if mask.sum() < 3:
        return float("nan")
    m, b = np.polyfit(log_r[mask], log_v[mask], 1)
    return float(m)


def vgt_dot_features(data, center_indices=None, n_radii=32,
                     smoothing_window=5, seed=0):
    """Mean of the (smoothed) derivative of the VGT curve across scales.

    This mirrors the paper's VGT-dot used as a clustering feature.
    Returns dict with features (n_pts,), derivative curves, smoothed curves.
    """
    radii, dia = compute_radii(data, n_radii=n_radii, seed=seed)
    res = compute_vgt(data, center_indices=center_indices, radii=radii)
    log_r = res["log_radii"]
    curves = res["vgt_curves"]

    n_pts = curves.shape[0]
    features = np.zeros(n_pts)
    derivs = np.zeros_like(curves)
    smoothed = np.zeros_like(curves)
    for i in range(n_pts):
        kernel = np.ones(smoothing_window) / smoothing_window
        s = np.convolve(curves[i], kernel, mode="same")
        smoothed[i] = s
        derivs[i] = np.gradient(s, log_r)
    features = derivs.mean(axis=1)
    return {
        "features": features,
        "derivatives": derivs,
        "smoothed": smoothed,
        "radii": radii,
        "log_radii": log_r,
        "diameter": dia,
    }


def local_dim_all(data, radii=None, r_lo=None, r_hi=None, n_radii=28,
                  center_indices=None, seed=0):
    """VGT local dimension at every (selected) point."""
    if radii is None:
        radii, dia = compute_radii(data, n_radii=n_radii, seed=seed)
    if r_lo is None:
        r_lo = radii[1]
    if r_hi is None:
        r_hi = radii[len(radii) // 2]
    res = compute_vgt(data, center_indices=center_indices, radii=radii)
    lds = np.zeros(len(res["vgt_curves"]))
    for i in range(len(res["vgt_curves"])):
        lds[i] = local_dim_from_vgt(res["log_radii"], res["vgt_curves"][i],
                                    r_lo, r_hi)
    return lds, res
