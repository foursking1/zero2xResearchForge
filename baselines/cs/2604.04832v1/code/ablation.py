"""Sensor ablation audit.

Two complementary definitions are implemented:

A) *Distributional-shift FDR* (paper's Stage-2 method, Fig. 5):
   nullify one sensor's raw signal *before* feature extraction, then measure
   F1 = max_k FDR between the baseline and the ablated feature distribution
   of the *same* gesture class.  Large shift  => sensor critical for class.

B) *Delta pairwise FDR* (the reproduction-pipeline metric):
   zero the sensor's 9 feature columns, recompute the one-vs-one pairwise
   FDR for the 3 gesture pairs, then delta = FDR_baseline - FDR_ablated.
   Averaged over the two pairs involving a class => class-level criticality.
"""
from __future__ import annotations

import numpy as np

from common import (NUM_SENSORS, NUM_FEATURES_PER_SENSOR, extract_sample_features)
from separability import (PAIR_DEFS, pairwise_fdr, f2_overlap_volume,
                          f3_max_feature_efficiency, fdr_per_feature)

EPS = 1e-10

# pairs that involve each gesture class (used for class-level delta FDR)
CLASS_PAIRS = {
    "paper": ["paper_vs_scissors", "rock_vs_paper"],
    "rock": ["rock_vs_paper", "rock_vs_scissors"],
    "scissors": ["paper_vs_scissors", "rock_vs_scissors"],
}


def ablate_signal(X: np.ndarray, sensor_idx: int) -> np.ndarray:
    """Set sensor_idx channel (length-400 window) to zero before features."""
    out = X.copy()
    out[:, sensor_idx, :] = 0.0
    return out


def ablate_features(F: np.ndarray, sensor_idx: int) -> np.ndarray:
    """Zero the 9 feature columns belonging to one sensor (metric B)."""
    out = F.copy()
    start = sensor_idx * NUM_FEATURES_PER_SENSOR
    out[:, start:start + NUM_FEATURES_PER_SENSOR] = 0.0
    return out


# ---------------------------------------------------------------------------
# Metric A: distributional shift FDR (paper's Fig. 5)
# ---------------------------------------------------------------------------
def distributional_shift_ablation(X: np.ndarray, Y: np.ndarray) -> dict:
    """For each class and sensor, F1/F2/F3 between baseline vs ablated.

    Returns
    -------
    {"per_class": {class: {sensor: {f1_shift, f2_shift, f3_shift}}},
     "criticality": {class: ranked list}, "normalized_f1": {...}}
    """
    base_feats = extract_sample_features(X)
    per_class = {}

    for c in sorted(np.unique(Y)):
        cname = {0: "rock", 1: "paper", 2: "scissors"}[int(c)]
        mask = Y == c
        F_base = base_feats[mask]
        per_class[cname] = {}
        for s in range(NUM_SENSORS):
            X_abl = ablate_signal(X, s)
            F_abl = extract_sample_features(X_abl)[mask]
            f1 = pairwise_fdr(F_base, F_abl, "max")          # larger = critical
            f2 = f2_overlap_volume(F_base, F_abl)            # smaller = critical
            f3 = f3_max_feature_efficiency(F_base, F_abl)    # larger = critical
            per_class[cname][f"sensor_{s}"] = {
                "f1_shift": float(f1),
                "f2_shift": float(f2),
                "f3_shift": float(f3),
            }

    # Normalise f1_shift per class (divide by class max) -> paper's Fig.5 bars
    normalized = {}
    for cname, sensors in per_class.items():
        vals = np.array([d["f1_shift"] for d in sensors.values()])
        vmax = vals.max() if vals.max() > EPS else 1.0
        normalized[cname] = {
            s: float(sensors[s]["f1_shift"] / vmax) for s in sensors
        }

    # Rankings (f1_shift descending)
    rankings = {}
    for cname, sensors in per_class.items():
        ranked = sorted(sensors.items(), key=lambda kv: kv[1]["f1_shift"], reverse=True)
        rankings[cname] = {
            "ranking": [{"sensor": s, "f1_shift": d["f1_shift"]} for s, d in ranked],
            "top_3": [s for s, _ in ranked[:3]],
            "bottom_3": [s for s, _ in ranked[-3:]],
        }
    return {"per_class": per_class, "normalized_f1": normalized,
            "criticality": rankings}


# ---------------------------------------------------------------------------
# Metric B: delta pairwise FDR (feature-level ablation)
# ---------------------------------------------------------------------------
def delta_fdr_ablation(F: np.ndarray, Y: np.ndarray) -> dict:
    """Delta pairwise FDR for each sensor; class-level criticality.

    delta_fdr[sensor][pair] = FDR_baseline(pair) - FDR_ablated(pair).
    """
    base_fdr_max = {}
    base_fdr_mean = {}
    for pair, la, lb in PAIR_DEFS:
        fa, fb = F[Y == la], F[Y == lb]
        base_fdr_max[pair] = pairwise_fdr(fa, fb, "max")
        base_fdr_mean[pair] = pairwise_fdr(fa, fb, "mean")

    delta_max, delta_mean, ablated_fdr = {}, {}, {}
    for s in range(NUM_SENSORS):
        Fa = ablate_features(F, s)
        key = f"sensor_{s}"
        delta_max[key], delta_mean[key], ablated_fdr[key] = {}, {}, {}
        for pair, la, lb in PAIR_DEFS:
            fa, fb = Fa[Y == la], Fa[Y == lb]
            fdr_max = pairwise_fdr(fa, fb, "max")
            fdr_mean = pairwise_fdr(fa, fb, "mean")
            ablated_fdr[key][pair] = {"max": fdr_max, "mean": fdr_mean}
            delta_max[key][pair] = base_fdr_max[pair] - fdr_max
            delta_mean[key][pair] = base_fdr_mean[pair] - fdr_mean

    # Normalised delta (delta / baseline) per pair
    delta_norm = {}
    for key in delta_max:
        delta_norm[key] = {}
        for pair in delta_max[key]:
            b = base_fdr_max[pair]
            delta_norm[key][pair] = (
                0.0 if b < EPS else delta_max[key][pair] / b)

    # per-pair sensor criticality rankings
    sensor_criticality = {}
    for pair, _, _ in PAIR_DEFS:
        scores = {f"sensor_{s}": delta_max[f"sensor_{s}"][pair]
                  for s in range(NUM_SENSORS)}
        ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
        sensor_criticality[pair] = {
            "ranking": [{"sensor": s, "delta_fdr": float(d)} for s, d in ranked],
            "top_3": [s for s, _ in ranked[:3]],
            "bottom_3": [s for s, _ in ranked[-3:]],
        }

    # per-class criticality (avg delta over the two pairs involving the class)
    class_criticality = {}
    for cname, pair_list in CLASS_PAIRS.items():
        scores = {
            f"sensor_{s}": float(np.mean([delta_max[f"sensor_{s}"][p]
                                          for p in pair_list]))
            for s in range(NUM_SENSORS)
        }
        ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
        class_criticality[cname] = {
            "ranking": [{"sensor": s, "avg_delta_fdr": float(d)} for s, d in ranked],
            "top_3": [s for s, _ in ranked[:3]],
            "bottom_3": [s for s, _ in ranked[-3:]],
        }

    # --- per-class criticality from MEAN-aggregated FDR (better spread) ---
    class_criticality_mean = {}
    for cname, pair_list in CLASS_PAIRS.items():
        scores = {
            f"sensor_{s}": float(np.mean([delta_mean[f"sensor_{s}"][p]
                                          for p in pair_list]))
            for s in range(NUM_SENSORS)
        }
        ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
        class_criticality_mean[cname] = {
            "ranking": [{"sensor": s, "avg_delta_fdr_mean": float(d)}
                        for s, d in ranked],
            "top_3": [s for s, _ in ranked[:3]],
            "bottom_3": [s for s, _ in ranked[-3:]],
        }

    return {
        "baseline_fdr_max": base_fdr_max,
        "baseline_fdr_mean": base_fdr_mean,
        "ablated_fdr": ablated_fdr,
        "delta_fdr_max": delta_max,
        "delta_fdr_mean": delta_mean,
        "delta_fdr_normalized": delta_norm,
        "sensor_criticality": sensor_criticality,
        "class_criticality": class_criticality,
        "class_criticality_mean": class_criticality_mean,
    }
