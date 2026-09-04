"""Evaluation protocols for multivariate time-series anomaly detection.

Three protocols, all computed from a binary prediction vector and the label:

1. point-wise F1    -- the "honest" protocol: every point compared independently.
2. point-adjust F1  -- flaw-prone protocol: a true anomaly segment counts as fully
                       detected if ANY of its points is predicted anomalous
                       (prediction is 'adjusted' so every point of the segment
                       becomes a true positive).
3. event-level F1E  -- optional protocol with a false-alarm-rate penalty
                       (following the spirit of arXiv:2308.13068 Table 1).

All inputs are 1-d numpy arrays of 0/1 ints of equal length.
"""
from __future__ import annotations

import numpy as np


def _binary(x) -> np.ndarray:
    x = np.asarray(x)
    return (x > 0).astype(int)


def pointwise_prf(pred, true):
    """Precision / recall / F1 on a per-point basis."""
    pred, true = _binary(pred), _binary(true)
    tp = int(((pred == 1) & (true == 1)).sum())
    fp = int(((pred == 1) & (true == 0)).sum())
    fn = int(((pred == 0) & (true == 1)).sum())
    prec = tp / (tp + fp) if (tp + fp) else 0.0
    rec = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
    return dict(precision=prec, recall=rec, f1=f1, tp=tp, fp=fp, fn=fn,
                n_true_pos=int(true.sum()), n_pred_pos=int(pred.sum()))


def true_event_spans(true) -> np.ndarray:
    """Return (n_events, 2) array of [start, end) spans of contiguous 1s."""
    true = _binary(true)
    d = np.diff(np.concatenate([[0], true, [0]]))
    starts = np.where(d == 1)[0]
    ends = np.where(d == -1)[0]
    return np.stack([starts, ends], axis=1)


def point_adjust(pred, true) -> np.ndarray:
    """Adjust predictions: any true anomaly segment intersected by >=1 predicted
    point becomes fully predicted (the standard 'point-adjust' operation)."""
    pred, true = _binary(pred), _binary(true)
    adj = pred.copy()
    for s, e in true_event_spans(true):
        if pred[s:e].sum() > 0:
            adj[s:e] = 1
    return adj


def point_adjust_f1(pred, true):
    pred, true = _binary(pred), _binary(true)
    adj = point_adjust(pred, true)
    return pointwise_prf(adj, true)


def event_f1e(pred, true):
    """Event-level F1 with FAR penalty (paper-style).

    R    = fraction of true events overlapped by >=1 predicted event.
    FAR  = (# predicted events that overlap NO true event) / (# true events).
    F1E  = 2*R*(1-FAR)/(R + (1-FAR))   (harmonic mean of R and 1-FAR).
    """
    pred, true = _binary(pred), _binary(true)
    t_spans = true_event_spans(true)
    p_spans = true_event_spans(pred)
    n_t = len(t_spans)
    n_p = len(p_spans)
    if n_t == 0:
        return dict(f1e=0.0, recall_e=0.0, far=0.0, n_true_events=0, n_pred_events=int(n_p))
    hit = np.zeros(n_p, dtype=bool)
    for i, (ps, pe) in enumerate(p_spans):
        hit[i] = np.any((t_spans[:, 0] < pe) & (t_spans[:, 1] > ps))
    # event recall: fraction of true events hit by >=1 predicted event
    true_hit = np.zeros(n_t, dtype=bool)
    for j, (ts, te_) in enumerate(t_spans):
        true_hit[j] = np.any((p_spans[:, 0] < te_) & (p_spans[:, 1] > ts))
    recall_e = float(true_hit.mean()) if n_t else 0.0
    false_pred = int((~hit).sum())
    far = false_pred / n_t
    one_minus_far = max(1.0 - far, 0.0)
    if one_minus_far <= 0.0:
        f1e = 0.0
    else:
        f1e = 2 * recall_e * one_minus_far / (recall_e + one_minus_far)
    return dict(f1e=float(f1e), recall_e=float(recall_e), far=float(far),
                n_true_events=int(n_t), n_pred_events=int(n_p),
                n_false_pred_events=int(false_pred))


def evaluate_all(pred, true) -> dict:
    """Run all three protocols on a single prediction vector."""
    out = {}
    pw = pointwise_prf(pred, true)
    out["pointwise"] = pw
    pa = point_adjust_f1(pred, true)
    out["point_adjust"] = pa
    ev = event_f1e(pred, true)
    out["event_F1E"] = dict(f1e=ev["f1e"], recall_e=ev["recall_e"], far=ev["far"])
    return out