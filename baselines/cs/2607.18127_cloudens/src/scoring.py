"""Anomaly scoring strategies on forecast reconstruction errors.

MD (Mahalanobis) strategy
-------------------------
Per-timestamp Mahalanobis distance of the reconstruction-error vector
(T x node*feat), mean/covariance estimated over the test period (as in
src/utils.py#calculate_mahalanobis_distance of the reproduction package),
min-max scaled (monotonic -- percentile thresholding is invariant), then
binary alarm iff distance > percentile(epsilon).  epsilon = 99.8 (paper).

LF (anomaly Likelihood Function) strategy
-----------------------------------------
Per-node error normalisation by median/IQR (get_err_scores), per-timestamp
max over nodes (top-1), min-max scale, squared, then the Numenta-style
anomaly likelihood over a rolling long window W=30 / short window W'=2.
Alarm iff likelihood > Lt = 0.99975.
"""
import numpy as np
from scipy.linalg import pinv
from scipy.stats import iqr

from anomaly_likelihood import compute_anomaly_likelihood


def get_err_scores(reconstruction_errors):
    """Per-timestamp score = (err - median) / (|IQR| + 1e-2), where median/IQR are
    computed over the WHOLE error tensor (all timestamps & nodes pooled), matching
    the reproduction package's utils.get_full_err_scores -> get_err_scores
    (called on the full [T, N] slice per feature; here num_features == 1)."""
    err = reconstruction_errors.astype(np.float64).reshape(-1)
    med = float(np.median(err))
    iqr_ = float(iqr(err))
    eps = 1e-2
    scores = (reconstruction_errors.astype(np.float64).reshape(len(reconstruction_errors), -1)
              - med) / (np.abs(iqr_) + eps)
    return scores


def calculate_mahalanobis_distance(reconstruction_errors):
    """MD per timestamp over the flattened reconstruction-error matrix [T, D].

    Two-step BLAS form (w = delta @ inv_cov; D2 = (w*delta).sum) -- the direct
    numpy einsum 'ij,jk,ik->i' materialises a huge [T,D,D] intermediate.
    """
    import time
    t0 = time.time()
    T = reconstruction_errors.shape[0]
    flat = np.ascontiguousarray(reconstruction_errors, dtype=np.float64).reshape(T, -1)
    mean_vec = np.mean(flat, axis=0)
    cov = np.cov(flat, rowvar=False)
    inv_cov = pinv(cov)
    delta = flat - mean_vec[None, :]
    w = delta @ inv_cov
    d2 = (w * delta).sum(axis=-1)
    print(f"[md] mahalanobis computed in {time.time()-t0:.1f}s (T={T})", flush=True)
    return np.sqrt(d2)


def score_mahalanobis(reconstruction_errors, percentile=99.8, topk=1):
    """Binary alarms from MD distances at the given percentile threshold."""
    md = calculate_mahalanobis_distance(reconstruction_errors)
    s = np.sort(md.reshape(-1, 1), axis=1)[:, -topk:].mean(axis=-1)
    threshold = np.percentile(s, percentile)
    alarms = (s > threshold).astype(int)
    return alarms, md


def mahalanobis_scores(reconstruction_errors, topk=1):
    """Per-timestamp MD score vector (threshold applied downstream)."""
    md = calculate_mahalanobis_distance(reconstruction_errors)
    s = np.sort(md.reshape(-1, 1), axis=1)[:, -topk:].mean(axis=-1)
    return s


def likelihood_scores(reconstruction_errors, long_window=30, short_window=2, topk=1):
    """Per-timestamp anomaly-likelihood vector (threshold applied downstream)."""
    err_full = get_err_scores(reconstruction_errors)     # [T, D]
    agg = np.sort(err_full, axis=1)[:, -topk:].mean(axis=-1)
    agg = (agg - agg.min()) / (agg.max() - agg.min() + 1e-12)
    agg = np.power(agg, 2)
    likelihoods = np.array([
        compute_anomaly_likelihood(agg[:i + 1], long_window, short_window)
        for i in range(len(agg))
    ])
    return likelihoods


def score_likelihood(reconstruction_errors, long_window=30, short_window=2,
                     lt=0.99975, topk=1):
    """Binary alarms from the anomaly likelihood function."""
    likelihoods = likelihood_scores(reconstruction_errors, long_window, short_window, topk)
    alarms = (likelihoods > lt).astype(int)
    return alarms, likelihoods


def threshold_mask(scores, percentile):
    th = np.percentile(scores, percentile)
    return (scores > th).astype(int)