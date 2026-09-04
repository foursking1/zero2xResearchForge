"""Training, per-point anomaly-score computation and train-only likelihood
calibration.

Workflow for one (series, model):

1.  normalize values with z-score statistics computed from the *training*
    period only;
2.  time-split per common.time_split: [0,70%) train, last 10% of it =
    validation, [70%,100%) test;
3.  train the reconstruction likelihood model on the training window set with
    early stopping on the validation NLL (both train-only periods);
4.  compute a causal per-point Gaussian-NLL score stream over the whole
    series with the frozen model;
5.  calibrate detection (long window W, short window W', threshold theta) by a
    small grid/random search evaluated *only on the validation NLL scores and
    validation ground-truth windows* (both derived from the training period) —
    the test period is never touched;
6.  apply the calibrated detector to the test-period score stream and return
    the detections (point indices in test space) for the NAB scorer.
"""

from __future__ import annotations

import os

import numpy as np
import torch

from common import sliding_windows, zscore_fit, zscore_apply, time_split
from models import build_model
import nab_scorer as ns

torch.set_num_threads(1)


# ---------------------------------------------------------------------------
# training
# ---------------------------------------------------------------------------

def fit_early_stopping_window_sizes(n_train, val_len):
    """Window length is sized relative to the training period but kept in a
    modest band so every series can be trained quickly on CPU."""
    wlen = int(round(n_train / 10.0))
    wlen = int(np.clip(wlen, 16, 64))
    return wlen


def _subsample(x, limit):
    if len(x) <= limit:
        return x
    idx = np.linspace(0, len(x) - 1, limit).astype(int)
    return x[idx]


def train_ae(model, x_train, x_val, epochs=25, batch=128, lr=1e-3,
             patience=4, seed=0, max_samples_train=1500):
    """Train an AE reconstruction model with early stopping.

    x_train / x_val: 1-D z-scored arrays (train period, val period).
    Returns (model, best_val_nll).
    """
    torch.manual_seed(seed + 1)
    np.random.seed(seed + 1)
    wlen = model.wlen
    t_total = len(x_train) + len(x_val)
    if t_total - wlen + 1 < 2:
        raise ValueError("series too short for given wlen")

    win_train = sliding_windows(x_train, wlen)
    win_val = sliding_windows(x_val, wlen) if len(x_val) >= wlen \
        else sliding_windows(np.concatenate([x_val[:len(x_val) // 1],
                                             np.pad(x_val, (0, wlen - len(x_val)), mode="edge")]),
                             wlen)

    if win_train.shape[0] < 2:
        win_train = np.repeat(win_train, 2, axis=0)

    x_train_t = torch.tensor(win_train).float()
    x_val_t = torch.tensor(np.asarray(win_val)).float()
    limit = max(2, min(len(x_val_t), 128))
    x_val_t = x_val_t[np.linspace(0, len(x_val_t) - 1, limit).astype(int)]

    opt = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-5)
    def loss_fn(xb):
        mu, logvar, _ = model(xb)
        var = (2.0 * logvar).exp() + 1e-6
        return (((xb - mu) ** 2) / var + 2.0 * logvar).mean()

    best_nll = float("inf")
    best_state = None
    patience_count = 0
    for ep in range(epochs):
        model.train()
        # subsample the training set each epoch to bound CPU time
        n_train = win_train.shape[0]
        if n_train > max_samples_train:
            idx = np.random.RandomState(seed + ep).choice(n_train, max_samples_train, replace=False)
        else:
            idx = np.arange(n_train)
        perm = np.random.RandomState(seed + 1000 + ep).permutation(idx)
        tr_e = 0.0; cnt = 0
        for i in range(0, len(perm), batch):
            idx_b = torch.tensor(perm[i:i + batch])
            xb = x_train_t[idx_b]
            opt.zero_grad()
            loss = loss_fn(xb)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            tr_e += loss.item(); cnt += 1
        model.eval()
        with torch.no_grad():
            vl = 0.0; vc = 0
            for i in range(0, len(x_val_t), batch):
                xb = x_val_t[i:i + batch]
                vl += loss_fn(xb).item(); vc += 1
            val_nll = vl / max(vc, 1)
        if val_nll < best_nll - 1e-4:
            best_nll = val_nll
            best_state = {k: p.detach().clone() for k, p in model.state_dict().items()}
            patience_count = 0
        else:
            patience_count += 1
            if patience_count >= patience:
                break
    if best_state is not None:
        model.load_state_dict(best_state)
    return model, best_nll


def compute_per_point_nll(model, x_norm, batch=512):
    """Causal per-point Gaussian NLL: for point t (>= wlen-1), score is the
    reconstruction NLL of the window ending at t, evaluated at position t."""
    wlen = model.wlen
    n = len(x_norm)
    if n < wlen:
        wlen = n
    model.eval()
    with torch.no_grad():
        y = np.full(n, np.nan, dtype=np.float64)
        w = sliding_windows(x_norm, wlen)
        X = torch.tensor(np.asarray(w)).float()
        for i in range(0, len(X), batch):
            xb = X[i:i + batch]
            s = model.score(xb)[:, -1, 0].cpu().numpy()
            lo = i + wlen - 1
            hi = min(lo + len(s), n)
            y[lo:hi] = s[: hi - lo]
        # fill head with the first available value (no lookahead)
        first = y[wlen - 1]
        y[: wlen - 1] = first
    return y


# ---------------------------------------------------------------------------
# likelihood calibration (train/val only)
# ---------------------------------------------------------------------------

def calibrate(scores_full, val_start, val_end, test_start, n_test,
              test_windows, model_tag="", w_grid=None, wp_grid=None,
              th_grid=None):
    """Grid search of detection hyper-parameters (W long window, W' short
    window, theta threshold) on the *validation* slice only (train-derived).

    ``test_windows`` are full-series ground-truth index windows.  Only the
    part overlapping the validation slice can influence calibration; the
    chosen rule is then used to detect on the test slice (unseen here).

    Selection metric: a mini NAB-style normalized score computed on the
    validation slice (windows restricted to it).  When the validation slice
    contains no labelled window we fall back to a parsimony rule (fewest
    detections).
    """
    if w_grid is None or wp_grid is None or th_grid is None:
        wl = max(n_test, 40)
        w_grid = sorted({max(10, int(wl * 0.01)), max(20, int(wl * 0.02)),
                         max(30, int(wl * 0.04)), 80})
        w_grid = [w for w in w_grid if w <= max(10, int(wl * 0.5))] or [20]
        wp_grid = [1, 3]
        th_grid = [2.5, 3.0, 3.5, 4.0]

    val_scores = scores_full[val_start:val_end]

    # ground-truth windows restricted to the validation slice (offset space)
    val_len = val_end - val_start
    val_windows = [(max(s - val_start, 0), min(e - val_start, val_len - 1))
                   for (s, e) in test_windows
                   if e >= val_start and s < val_end]
    val_windows = [(s, e) for (s, e) in val_windows if e >= s]

    best = None
    best_res = None
    n_val_win = len(val_windows)
    for W in w_grid:
        for Wp in wp_grid:
            if Wp > W:
                continue
            for theta in th_grid:
                z, _ = detector_stream(val_scores, W, Wp)
                dets = np.nonzero(z > theta)[0]
                if n_val_win:
                    r = ns.score_series(dets, val_windows, val_len)
                    nul = ns.null_score(val_windows, val_len)
                    ide = ns.ideal_score(val_windows, val_len)
                    metric = ns.aggregate_and_normalize([r], [nul], [ide])
                    # guard against degenerate decisions
                    if len(dets) == 0:
                        metric -= 1.0
                    if len(dets) > 0.5 * val_len:
                        metric -= 2.0 * (len(dets) / val_len)
                else:
                    # no validation windows -> favour parsimony but retain
                    # enough capabbility (larger W -> higher possible z).
                    metric = -float(len(dets)) - (0.5 if W < 20 else 0.0) \
                        - (0.25 if W < 40 else 0.0)
                if best is None or metric > best:
                    best = metric
                    best_res = (W, Wp, theta, metric)
    if best_res is None:
        best_res = (w_grid[0], wp_grid[0], th_grid[0], -99.0)

    W, Wp, theta, metric = best_res
    return {
        "W": int(W), "Wp": int(Wp), "theta": float(theta),
        "val_metric": float(metric),
        "val_windows": val_windows,
        "rule": {"W": int(W), "Wp": int(Wp), "theta": float(theta)},
        "model_tag": model_tag,
    }


def detector_stream(scores, W, Wp):
    """Causal smoothing of a per-point NLL/anomaly score stream with a long
    baseline window W and short smoothing window Wp, returning a z-score.

    smoothed_t = mean(scores[t-Wp+1:t+1])
    baseline_t = mean(smoothed[t-W+1:t+1])   (rolling, causal)
    std_t      = std(smoothed[t-W+1:t+1])
    z_t = (smoothed_t - baseline_t) / max(std_t, eps)
    """
    s = np.asarray(scores, dtype=np.float64)
    n = len(s)
    eps = 1e-9
    idx = np.arange(n)

    def roll_mean_std(x, W):
        c = np.concatenate([[0.0], np.cumsum(x)])
        c2 = np.concatenate([[0.0], np.cumsum(x * x)])
        lo = np.maximum(0, idx - W + 1)
        cnt = idx - lo + 1
        mu = (c[idx + 1] - c[lo]) / cnt
        var = (c2[idx + 1] - c2[lo]) / cnt - mu * mu
        sd = np.sqrt(np.maximum(var, 0.0))
        return mu, sd

    # short smoothing
    sm_c = np.concatenate([[0.0], np.cumsum(s)])
    lo_s = np.maximum(0, idx - Wp + 1)
    smoothed = (sm_c[idx + 1] - sm_c[lo_s]) / (idx - lo_s + 1)
    # long-window baseline
    mu, sd = roll_mean_std(smoothed, W)
    z = (smoothed - mu) / np.maximum(sd, eps)
    return z, smoothed


def val_concordance(det_mask, windows, n):
    """Legacy helper (kept for reference); superseded by mini-NAB on val."""
    det_idx = np.nonzero(det_mask)[0]
    if windows:
        if len(det_idx) == 0:
            return -1.0
        covered = 0
        free_det = 0
        for (s, e) in windows:
            if ((det_idx >= s) & (det_idx <= e)).any():
                covered += 1
        covered_zone = set()
        for (s, e) in windows:
            covered_zone.update(range(max(0, s - 2), min(n, e + 3)))
        free_det = sum(1 for t in det_idx if t not in covered_zone)
        return covered - 0.15 * free_det
    return -0.5 * int(det_mask.sum())


def apply_detector(rule, test_scores):
    """Apply a calibrated detection rule to the test-period score stream and
    return test-space point indices of detections (clusters collapsed by the
    scorer)."""
    W, Wp, theta = rule["W"], rule["Wp"], rule["theta"]
    z, _ = detector_stream(test_scores, W, Wp)
    return np.nonzero(z > theta)[0]