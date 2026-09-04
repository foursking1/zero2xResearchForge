"""Isolation Forest baseline anomaly detector.

Protocol identical to the deep models:

  * fit on sliding windows drawn from the *training* period (z-scored);
  * every point of the full series gets a causal anomaly score = mean of
    -decision_function over all windows that end at that point;
  * the same likelihood calibration (long/short window smoothing + threshold,
    train/validation only) is applied before detection on the test period.
"""

from __future__ import annotations

import numpy as np
from sklearn.ensemble import IsolationForest

from common import sliding_windows


def fit_if(x_train, wlen, seed=0, n_estimators=200, contamination="auto"):
    X = np.asarray(sliding_windows(x_train, wlen))
    if X.ndim == 3:
        X = X.reshape(X.shape[0], -1)
    limit = 20000
    if X.shape[0] > limit:
        idx = np.linspace(0, X.shape[0] - 1, limit).astype(int)
        X = X[idx]
    m = IsolationForest(n_estimators=n_estimators, contamination=contamination,
                        random_state=seed, n_jobs=1)
    m.fit(X)
    return m


def compute_per_point_if_score(m, x_norm, wlen, batch=5000):
    """Causal per-point anomaly score: the mean of -decision_function over the
    sliding windows ending at each point; the head of the series is padded
    with the first available score."""
    n = len(x_norm)
    if n < wlen:
        wlen = n
    y = np.full(n, np.nan)
    w = np.asarray(sliding_windows(x_norm, wlen))
    if w.ndim == 3:
        w = w.reshape(w.shape[0], -1)
    scores = np.empty(w.shape[0])
    for i in range(0, w.shape[0], batch):
        scores[i:i + batch] = -m.decision_function(w[i:i + batch])
    y[wlen - 1:] = scores
    y[:wlen - 1] = scores[0]
    sd = y.std()
    if sd > 0:
        y = (y - y.mean()) / sd
    return y