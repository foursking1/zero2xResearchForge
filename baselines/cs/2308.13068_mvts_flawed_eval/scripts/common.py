"""Shared utilities for the SWaT/PSM anomaly-detection pipeline.

Handles data loading, NaN imputation, z-score standardization, windowing,
and threshold selection (oracle vs. training-based fixed).
"""
from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd

DATA_ROOT = Path("/mnt/f/dataset/cs/2308.13068_mvts_flawed_eval")


# --------------------------------------------------------------------------
# Data loading
# --------------------------------------------------------------------------
def load_swat():
    tr = np.load(DATA_ROOT / "SWaT_SWaT_train.npy", mmap_mode="r")
    te = np.load(DATA_ROOT / "SWaT_SWaT_test.npy", mmap_mode="r")
    lbl = np.load(DATA_ROOT / "SWaT_SWaT_test_label.npy", mmap_mode="r")
    return dict(
        name="SWaT",
        train=np.asarray(tr, dtype=np.float64),
        test=np.asarray(te, dtype=np.float64),
        label=(np.asarray(lbl, dtype=int) > 0).astype(int),
    )


def load_psm():
    tr = pd.read_csv(DATA_ROOT / "PSM_train.csv")
    te = pd.read_csv(DATA_ROOT / "PSM_test.csv")
    lb = pd.read_csv(DATA_ROOT / "PSM_test_label.csv")
    num = lambda df: df.drop(columns=["timestamp_(min)"], errors="ignore").to_numpy(np.float64)
    return dict(
        name="PSM",
        train=np.ascontiguousarray(num(tr)),
        test=np.ascontiguousarray(num(te)),
        label=(lb.iloc[:, 1].to_numpy(int) > 0).astype(int),
    )


def load_dataset(name: str) -> dict:
    name = name.upper()
    if name == "SWAT":
        return load_swat()
    if name == "PSM":
        return load_psm()
    raise ValueError(name)


# --------------------------------------------------------------------------
# Preprocessing
# --------------------------------------------------------------------------
def impute_nan_mean(train: np.ndarray) -> np.ndarray:
    """Fill NaN with the per-channel mean of the non-NaN values (in-place safe)."""
    if not np.isfinite(train).all():
        fill = np.nanmean(train, axis=0)
        out = np.where(np.isfinite(train), train, fill)
        return out.astype(train.dtype, copy=False)
    return train


def zscore_fit(train: np.ndarray):
    mean = train.mean(axis=0)
    std = train.std(axis=0)
    std[std == 0] = 1e-12
    return mean, std


def zscore_transform(x: np.ndarray, mean: np.ndarray, std: np.ndarray) -> np.ndarray:
    return (x - mean) / std


# --------------------------------------------------------------------------
# Windowing (for sequence models)
# --------------------------------------------------------------------------
def make_windows(x: np.ndarray, length: int, stride: int):
    n = x.shape[0]
    starts = np.arange(0, n - length + 1, stride)
    idx = starts[:, None] + np.arange(length)[None, :]
    return x[idx]


def window_aggregate(scores: np.ndarray, n_points: int, length: int, stride: int):
    """Aggregate per-window scores to per-point scores (mean over covering windows)."""
    n_windows = scores.shape[0]
    starts = np.arange(0, n_points - length + 1, stride)
    acc = np.zeros(n_points)
    cnt = np.zeros(n_points)
    for i, s in enumerate(starts):
        acc[s : s + length] += scores[i]
        cnt[s : s + length] += 1
    cnt[cnt == 0] = 1
    return acc / cnt


def smooth_ma(x: np.ndarray, w: int = 5) -> np.ndarray:
    """Centred moving-average smoothing (edge-padded with reflection)."""
    if w <= 1:
        return x.copy()
    pad = w // 2
    xp = np.pad(x, (pad, pad), mode="edge")
    kernel = np.ones(w) / w
    return np.convolve(xp, kernel, mode="valid")


# --------------------------------------------------------------------------
# Threshold selection
# --------------------------------------------------------------------------
def pointwise_metrics_from_scores(scores: np.ndarray, label: np.ndarray, thresh: float):
    pred = (scores >= thresh).astype(int)
    tp = int(((pred == 1) & (label == 1)).sum())
    fp = int(((pred == 1) & (label == 0)).sum())
    fn = int(((pred == 0) & (label == 1)).sum())
    prec = tp / (tp + fp) if (tp + fp) else 0.0
    rec = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
    return dict(tp=tp, fp=fp, fn=fn, precision=prec, recall=rec, f1=f1, n_pred=int(pred.sum()))


def best_threshold_oracle(scores: np.ndarray, label: np.ndarray):
    """Best pointwise-F1 threshold on the TEST segment (oracle; declared explicitly).

    Sweeps every unique score value via prefix sums -> exact argmax of pointwise F1.
    """
    order = np.argsort(scores)
    s_sorted = scores[order]
    lab_sorted = label[order]
    n = len(s_sorted)

    # pred = (score >= t). Sweep t over unique score values.
    # For a unique value v, threshold = v means points with score >= v are positive.
    cum_anom = np.concatenate([[0], np.cumsum(lab_sorted)])
    cum_all = np.arange(n + 1)
    idx = np.unique(s_sorted, return_index=True)[1]
    best_f1, best_t = -1.0, s_sorted[-1] + 1.0
    for i in idx:
        # points with score >= s_sorted[i] are positive
        tp = cum_anom[n] - cum_anom[i]
        fp = (cum_all[n] - cum_all[i]) - tp
        fn = cum_anom[i]
        prec = tp / (tp + fp) if (tp + fp) else 0.0
        rec = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
        if f1 > best_f1:
            best_f1, best_t = f1, s_sorted[i]
    if best_t == s_sorted[-1] + 1.0:  # degenerate: everything positive
        best_t = s_sorted[0] - 1.0
    return best_t, best_f1


def threshold_train_fixed(scores_train: np.ndarray, mode: str = "mean3std"):
    if mode == "mean3std":
        return float(scores_train.mean() + 3.0 * scores_train.std())
    if mode == "quantile99":
        return float(np.quantile(scores_train, 0.99))
    raise ValueError(mode)