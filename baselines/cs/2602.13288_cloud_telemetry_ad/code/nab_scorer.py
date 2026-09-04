"""NAB-style anomaly-detection scoring (normalized NAB score).

Implements a faithful, documented version of the Numenta Anomaly Benchmark
(NAB) scoring semantics used by the reference paper:

  * ground-truth "anomaly windows" are given as [start, end] index ranges on a
    per-series timeline (test period only);
  * detections are *clustered*: successive detection timestamps that are within
    ``k = max(1, n//50)`` steps of each other form a single "detection event"
    and only the earliest timestamp of a cluster is used;
  * a window counts at most ONE true positive: the earliest detection cluster
    inside the window.  Later detections inside the same window are not scored
    as additional detections (merged into the TP).
  * the TP is weighted by *earliness* (detecting earlier inside a window gives
    more credit; a detection slightly before the window also gets credit,
    scaled down by binding-distance);
  * every other detection is a false positive, penalised by a distance-aware
    weight: FPs that are closer to a real anomaly window are weighted *less*
    (they are compatible with early detection), exactly the NAB motivation;
  * a window with no detection is a false negative;
  * all remaining points count toward true negatives;
  * per-(sub)group score = 100 * (S_model - S_null) / (S_ideal - S_null),
    where S_null / S_ideal are the raw scores of the NAB null detector
    (never fires) and ideal detector (fires exactly at the start of every
    window), aggregated over all series of the (sub)group.

Raw (profile-weighted) score per series::

    S = tpValue*TP_weighted + fpValue*FP_weighted + fnValue*FN + tnValue*TN

with the "standard" NAB profile::

    tpValue = 1.0, fpValue = 0.11, tnValue = 0.22, fnValue = 1.0

Reference for semantics:
    - Ahmad, S., Lavin, A., Purdy, S., Agha, Z. (2017). "Unsupervised real-time
      anomaly detection for streaming data." Neurocomputing.
    - Numenta NAB benchmark: https://github.com/numenta/NAB
"""

from __future__ import annotations

import enum

import numpy as np

class Profile(object):
    """Standard NAB scoring profile ("standard")."""

    def __init__(self, tp_value=1.0, fp_value=0.11, tn_value=0.22, fn_value=1.0,
                 alpha=0.8, beta=0.1, cluster_frac=50, fp_early_credit=0.5):
        self.tp_value = tp_value
        self.fp_value = fp_value
        self.tn_value = tn_value
        self.fn_value = fn_value
        # earliness penalty for detections *before* a window
        self.alpha = alpha
        # earliness bonus for detections *inside* a window
        self.beta = beta
        # number of points used to size the detection-clustering window
        self.cluster_frac = cluster_frac
        # how much proximity to a window discounts an FP weight (0 = no credit)
        self.fp_early_credit = fp_early_credit

    def cluster_window(self, n):
        k = max(1, int(n // self.cluster_frac))
        return k


class SeriesRawScore(object):
    __slots__ = ("tp", "fp", "tn", "fn", "n_windows")

    def __init__(self, tp=0.0, fp=0.0, tn=0.0, fn=0, n_windows=0):
        self.tp = tp
        self.fp = fp
        self.tn = tn
        self.fn = fn
        self.n_windows = n_windows

    @property
    def weighted(self):
        """Application-weighted score.

        True positives and true negatives are rewarded; false positives and
        false negatives are penalised (standard NAB profile orientation:
        tpValue=1.0, fpValue=0.11, tnValue=0.22, fnValue=1.0, with FP and FN
        entering as penalties)."""
        return (self.tp * 1.0 - self.fp * 0.11 + self.tn * 0.22 - self.fn * 1.0)

    def __add__(self, other):
        return SeriesRawScore(
            tp=self.tp + other.tp, fp=self.fp + other.fp,
            tn=self.tn + other.tn, fn=self.fn + other.fn,
            n_windows=self.n_windows + other.n_windows)

    def __repr__(self):
        return (f"SeriesRawScore(tp={self.tp:.3f}, fp={self.fp:.3f}, "
                f"tn={self.tn:.1f}, fn={self.fn}, n_windows={self.n_windows}, "
                f"S={self.weighted:.3f})")


def np_sort_unique(detection_times):
    """Sorted unique integer detection times (accepts list / numpy array)."""
    arr = np.asarray(detection_times, dtype=np.int64).ravel()
    return np.unique(arr)


def _cluster_detections(detection_times, window=1):
    """Cluster detection indices: consecutive timestamps within `window`
    steps form one cluster; return the earliest time of each cluster."""
    dets = np_sort_unique(detection_times)
    if len(dets) == 0:
        return []
    clusters = []
    current_start = dets[0]
    for d in dets[1:]:
        if d - current_start <= window:
            continue
        clusters.append(current_start)
        current_start = d
    clusters.append(current_start)
    return clusters


def _tp_weight(t, win, profile):
    """Earliness-weighted true-positive credit for a detection at index
    ``t`` w.r.t. window ``[s, e]``."""
    s, e = win
    if t < s:
        # detection before the window start: credit decays linearly with
        # normalised distance to the window start.
        if s > 0:
            w = 1.0 * (1.0 - profile.alpha * (s - t) / s)
            return max(w, 0.0)
        return 0.0
    # detection inside the window: earlier is better.
    if e > s:
        return 1.0 * (1.0 + profile.beta * (e - t) / (e - s))
    return 1.0 * (1.0 + profile.beta)


def _fp_weight(t, windows, profile, k):
    """Distance-aware false-positive weight.

    An FP that is close (within ``k`` points) to a real anomaly window is
    compatible with an (early) attempt at detection, so it is discounted
    linearly down to ``1 - fp_early_credit``.  FPs far from every window get
    the full weight 1.0.
    """
    best = None
    for (s, e) in windows:
        d = min(abs(t - s), abs(t - e))
        if best is None or d < best:
            best = d
    if best is None:
        return 1.0
    discount = profile.fp_early_credit * min(best / max(k, 1), 1.0)
    return 1.0 - discount


def score_series(detection_times, windows, n, profile=None):
    """Score a single series test period.

    Parameters
    ----------
    detection_times : list[int]
        anomaly timestamps (test-period point indices) produced by a detector.
    windows : list[tuple[int, int]]
        ground-truth anomaly windows restricted to the test period.
    n : int
        test-period length (point capacity).
    profile : Profile | None

    Returns
    -------
    SeriesRawScore
    """
    if profile is None:
        profile = Profile()
    n = int(n)
    k = profile.cluster_window(n)
    clusters = _cluster_detections(detection_times, window=k)

    if len(windows) == 0:
        # No anomalies possible: every detection is a false positive.
        fp = sum(_fp_weight(t, windows, profile, k) for t in clusters)
        tn = n
        return SeriesRawScore(tp=0.0, fp=fp, tn=tn, fn=0, n_windows=0)

    # Normalise windows: left-closed right-closed ranges clamped to [0, n-1].
    wins = []
    for (s, e) in windows:
        s = max(0, int(s)); e = min(n - 1, int(e))
        if e >= s:
            wins.append((s, e))

    tp = 0.0
    matched = set()
    fn = 0
    used = set()
    for i, (s, e) in enumerate(wins):
        # earliest cluster inside this window
        candidates = [c for c in clusters if s <= c <= e and c not in used]
        if candidates:
            c = min(candidates)
            tp += _tp_weight(c, (s, e), profile)
            used.add(c)
            matched.add(i)
        else:
            fn += 1

    fp = 0.0
    for c in clusters:
        if c in used:
            continue
        in_window = any(s <= c <= e for (s, e) in wins)
        if in_window:
            # cluster inside a window but not the earliest one is consumed by
            # the TP of that window -> not scored separately.
            continue
        fp += _fp_weight(c, wins, profile, k)

    # true negatives: every point that is not covered by any ground-truth
    # window (points inside windows are TP or FN, never TN) and not a FP.
    win_points = set()
    for (s, e) in wins:
        win_points.update(range(s, e + 1))
    tn = max(0, n - len(win_points))
    return SeriesRawScore(tp=tp, fp=fp, tn=tn, fn=fn, n_windows=len(wins))


def null_score(windows, n, profile=None):
    """NAB null detector: never fires."""
    if profile is None:
        profile = Profile()
    n = int(n)
    tn = 0
    wins = []
    for (s, e) in windows:
        s = max(0, int(s)); e = min(n - 1, int(e))
        if e >= s:
            wins.append((s, e))
    tn = max(0, n - sum(int(e - s) + 1 for (s, e) in wins))
    fn = len(wins)
    return SeriesRawScore(tp=0.0, fp=0.0, tn=tn, fn=fn, n_windows=len(wins))


def ideal_score(windows, n, profile=None):
    """NAB ideal detector: fires exactly at the start of every window."""
    if profile is None:
        profile = Profile()
    n = int(n)
    wins = []
    for (s, e) in windows:
        s = max(0, int(s)); e = min(n - 1, int(e))
        if e >= s:
            wins.append((s, e))
    tp = sum(_tp_weight(s_, (s_, e_), profile) for (s_, e_) in wins)
    tn = max(0, n - sum(int(e - s) + 1 for (s, e) in wins))
    return SeriesRawScore(tp=tp, fp=0.0, tn=tn, fn=0, n_windows=len(wins))


def aggregate_and_normalize(model_raw_scores, null_raw_scores, ideal_raw_scores):
    """Aggregate raw scores over a set of series and return the normalized
    NAB score in [0, 100] (null -> 0, ideal -> 100)."""
    S = sum(r.weighted for r in model_raw_scores)
    S_null = sum(r.weighted for r in null_raw_scores)
    S_ideal = sum(r.weighted for r in ideal_raw_scores)
    denom = S_ideal - S_null
    if abs(denom) < 1e-9:
        return 0.0
    return 100.0 * (S - S_null) / denom