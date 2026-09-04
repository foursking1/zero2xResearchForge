"""NAB (Numenta Anomaly Benchmark) scoring.

Faithful, self-contained re-implementation of the window-based NAB scoring
used in the ClouDens paper (src/nab_scoring.py of the reproduction package).

Supports the "standard" profile (penalty_fn=1.0, penalty_fp=0.11) and the
"reward_fn" / low-FN profile (penalty_fn=2.0).  A ground-truth anomaly window
is "detected" iff at least one predicted anomaly point falls inside it; the
score of a true positive is a scaled sigmoid of its relative position inside
the window.  False positives are scored with a scaled sigmoid of their
distance from the end of the last anomaly window (min -1).
"""
import math

import numpy as np
import pandas as pd


def sigmoid(x):
    return 1.0 / (1.0 + math.exp(-x))


def scaled_sigmoid(rel):
    if rel > 3.0:
        return -1.0
    return 2 * sigmoid(-5 * rel) - 1.0


def calculate_relative_position(df, true_col="true_anomaly", pred_col="predicted_anomaly"):
    """Add 'relative_position' to df: negative value for the first TP in each window."""
    df = df.copy()
    df["shift"] = df[true_col].shift(1, fill_value=0)
    df["start_window"] = (df[true_col] == 1) & (df["shift"] == 0)
    df["end_window"] = (df[true_col] == 0) & (df["shift"] == 1)
    windows = []
    start_time = None
    for t, row in df.iterrows():
        if row["start_window"]:
            start_time = t
        if row["end_window"] and start_time is not None:
            windows.append((start_time, t))
            start_time = None
    if start_time is not None:
        windows.append((start_time, df.index[-1]))
    df["relative_position"] = 0.0
    for start, end in windows:
        window_length = (end - start).total_seconds()
        if df.loc[start:end, pred_col].any():
            first_detection = df.loc[start:end, pred_col].idxmax()
            rel = -(end - first_detection).total_seconds() / window_length
            df.loc[first_detection, "relative_position"] = rel
    return df.drop(columns=["shift", "start_window", "end_window"])


def _window_bounds(df, true_col):
    shift = df[true_col].shift(1, fill_value=0)
    starts = (df[true_col] == 1) & (shift == 0)
    n_windows = int(starts.sum())
    return n_windows


def calculate_baseline_score(df, true_col="true_anomaly", penalty_fn=2.0):
    n_windows = _window_bounds(df, true_col)
    return -penalty_fn * n_windows


def calculate_perfect_score(df, true_col="true_anomaly", reward_tp=1.0):
    n_windows = _window_bounds(df, true_col)
    return reward_tp * n_windows, n_windows


def normalize_nab_score(score, baseline_score, perfect_score):
    if perfect_score == baseline_score:
        return 0.0
    return 100.0 * (score - baseline_score) / (perfect_score - baseline_score)


def calculate_nab_score(df, anomaly_windows_test, profile,
                        true_col="true_anomaly", pred_col="predicted_anomaly",
                        reward_tp=1.0, penalty_fp=0.11, penalty_fn=1.0):
    """Full NAB evaluation.

    Returns a dict with:
      raw, normalized         : raw & normalized NAB scores (profile-dependent)
      TP/TN/FP/FN             : point-wise confusion matrix (sum == len(df))
      tp_windows              : number of detected ground-truth windows
      detection_counters      : {'issue': {'count', 'ids'}, 'im': ..., 'testlog': ...}
                                ids are 0-based indices into anomaly_windows_test
    """
    if profile == "reward_fn":
        penalty_fn = 2.0
    elif profile != "standard":
        raise ValueError(f"Unsupported NAB profile: {profile}")

    df = calculate_relative_position(df, true_col=true_col, pred_col=pred_col)

    windows, src_map = [], {}
    for k, (_, row) in enumerate(anomaly_windows_test.iterrows()):
        start = pd.to_datetime(row["anomaly_window_start"])
        end = pd.to_datetime(row["anomaly_window_end"])
        src = int(row["anomaly_source"])
        windows.append((start, end))
        src_map[(start, end)] = (src, k)

    score = 0.0
    tp_windows = fn_windows = fp_points = 0
    counter = {"issue": {"count": 0, "ids": []},
               "im": {"count": 0, "ids": []},
               "testlog": {"count": 0, "ids": []}}

    # --- true positives / false negatives (window based) ---
    for start, end in windows:
        try:
            window_pred = df.loc[start:end, pred_col]
            detected = bool(window_pred.any())
        except KeyError:
            continue
        if detected:
            first_detection = window_pred.idxmax()
            rel = df.loc[first_detection, "relative_position"]
            score += reward_tp * scaled_sigmoid(rel)
            tp_windows += 1
            src, k = src_map[(start, end)]
            key = {1: "issue", 2: "im", 3: "testlog"}[src]
            counter[key]["count"] += 1
            counter[key]["ids"].append(k)
        else:
            score -= penalty_fn
            fn_windows += 1

    # --- false positives (point based, outside any window) ---
    pred = df[pred_col].to_numpy()
    true = df[true_col].to_numpy()
    tindex = df.index
    for i, t in enumerate(tindex):
        if pred[i] == 1 and not any(start <= t <= end for start, end in windows):
            fp_points += 1
            last_window = None
            for start, end in windows:
                if end < t:
                    last_window = (start, end)
                else:
                    break
            if last_window is not None:
                last_end = last_window[1]
                window_width = (last_end - last_window[0]).total_seconds()
                rel_fp = (t - last_end).total_seconds() / window_width
                if rel_fp > 3:
                    score -= 1.0 * penalty_fp
                else:
                    score += penalty_fp * scaled_sigmoid(rel_fp)

    # --- point-wise confusion ---
    in_window = np.zeros(len(df), dtype=bool)
    for start, end in windows:
        in_window |= np.asarray((tindex >= start) & (tindex <= end))
    tp = int(((true == 1) & (pred == 1)).sum())
    tn = int(((true == 0) & (pred == 0)).sum())
    fp = fp_points
    fn = int(((true == 1) & (pred == 0)).sum())

    baseline = calculate_baseline_score(df, true_col=true_col, penalty_fn=penalty_fn)
    perfect, _ = calculate_perfect_score(df, true_col=true_col, reward_tp=reward_tp)
    normalized = normalize_nab_score(score, baseline, perfect)

    return dict(raw=float(score), normalized=float(normalized),
                TP=int(tp), TN=int(tn), FP=int(fp), FN=int(fn),
                tp_windows=int(tp_windows), fn_windows=int(fn_windows),
                detection_counters=counter,
                n_gt_windows=len(windows))