"""Random-guess baseline (arXiv:2308.13068 Sec. 3.1 'fraction-F1' / Sec. 5).

Picks alpha time points uniformly at random from the test segment and labels
them anomalous; everything else normal. Computed under both the point-wise and
the point-adjust protocol. Repeated with independent RNG draws -> mean/std.

Repeated many times (>=10) with a fixed seed schedule, as required.
"""
from __future__ import annotations

import numpy as np

from protocols.eval_protocols import pointwise_prf, point_adjust_f1, event_f1e


def random_guess(alpha: int, n_points: int, rng: np.random.Generator) -> np.ndarray:
    """Binary prediction marking `alpha` random points as anomalous (no replacement)."""
    alpha = min(int(alpha), n_points)
    idx = rng.choice(n_points, size=alpha, replace=False)
    pred = np.zeros(n_points, dtype=int)
    pred[idx] = 1
    return pred


def random_guess_eval(alpha, label, n_repeats=50, seed0=0):
    """Run n_repeats random-guess trials; return dict of mean/std per protocol."""
    n = len(label)
    label = (np.asarray(label) > 0).astype(int)
    pw_f1, pa_f1, pw_prec, pw_rec, ev_f1e = [], [], [], [], []
    for r in range(n_repeats):
        rng = np.random.default_rng(seed0 + r)
        pred = random_guess(int(alpha), n, rng)
        r_pw = pointwise_prf(pred, label)
        r_pa = point_adjust_f1(pred, label)
        r_ev = event_f1e(pred, label)
        pw_f1.append(r_pw["f1"]); pa_f1.append(r_pa["f1"])
        pw_prec.append(r_pw["precision"]); pw_rec.append(r_pw["recall"])
        ev_f1e.append(r_ev["f1e"])
    pw_f1 = np.array(pw_f1); pa_f1 = np.array(pa_f1)
    return {
        "alpha": int(alpha),
        "n_repeats": n_repeats,
        "pointwise_f1_mean": float(pw_f1.mean()),
        "pointwise_f1_std": float(pw_f1.std()),
        "pointwise_precision_mean": float(np.mean(pw_prec)),
        "pointwise_recall_mean": float(np.mean(pw_rec)),
        "point_adjust_f1_mean": float(pa_f1.mean()),
        "point_adjust_f1_std": float(pa_f1.std()),
        "event_f1e_mean": float(np.mean(ev_f1e)),
        "gap_f1pa_minus_f1pw": float(pa_f1.mean() - pw_f1.mean()),
    }