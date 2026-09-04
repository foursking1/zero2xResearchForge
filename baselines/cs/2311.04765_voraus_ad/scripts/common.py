"""common.py — shared data access + evaluation helpers.

All functions are small so the judge can recompute the reported numbers from
the frozen parquet with a fixed seed. AUROC uses sklearn's roc_auc_score
(average tie rule), which is the de-facto standard and reproducible.
"""
import os

import numpy as np

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_NPZ = os.path.join(BASE, "data", "voraus_data.npz")

CATEGORY_NAMES = {
    0: "axis_friction",
    1: "axis_weight",
    2: "collision_foam",
    3: "collision_cable",
    4: "collision_carton",
    5: "miss_can",
    6: "lose_can",
    7: "can_weight",
    8: "entangled",
    9: "invalid_position",
    10: "motor_commutation",
    11: "wobbling_station",
}
NORMAL_CATEGORY = 12


def load_cache():
    """Returns the cached arrays produced by 01_prepare_data.py."""
    return np.load(DATA_NPZ, allow_pickle=True)


def get_train_test_masks(setting):
    """Official split: train == setting 72 (PRE_A); test == everything else."""
    mask = setting == 72
    return mask, ~mask


def auroc_global(scores_neg, scores_pos):
    """Per-category AUROC (positive = anomaly class, negative = all test-normal).

    When several categories are evaluated they all share the same set of
    419 test-normal samples as negatives (paper Sec. V-A protocol).
    """
    from sklearn import metrics

    if len(scores_neg) == 0 or len(scores_pos) == 0:
        return float("nan")
    y = np.concatenate([np.zeros(len(scores_neg)), np.ones(len(scores_pos))])
    s = np.concatenate([scores_neg, scores_pos])
    return float(metrics.roc_auc_score(y, s))


def evaluate_method(anomaly_scores, anomaly, category, test_mask):
    """Per-category AUROC + 12-class mean from a per-sample anomaly score vector.

    Convention: higher anomaly score == more anomalous. Mean is the simple
    average over the 12 per-category AUROC values, exactly as in paper Table VI.
    """
    normal_idx = np.where(test_mask & ~anomaly)[0]
    aucs = {}
    for cat in range(12):
        pos_idx = np.where(test_mask & anomaly & (category == cat))[0]
        if len(pos_idx) == 0:
            aucs[cat] = float("nan")
            continue
        aucs[cat] = auroc_global(anomaly_scores[normal_idx], anomaly_scores[pos_idx])
    return aucs