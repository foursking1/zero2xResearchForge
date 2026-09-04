# -*- coding: utf-8 -*-
"""Metrics for SEP classification (paper Eq. definitions).

TSS = TPR - FPR = Recall - FP/(FP+TN)
HSS = 2*(TP*TN - FP*FN) / ((TP+FN)*(FN+TN) + (TP+FP)*(FP+TN))  (Heidke)
precision = TP/(TP+FP), recall = TP/(TP+FN), accuracy = (TP+TN)/N
ROC AUC from the predicted probabilities (not just the hard threshold).
"""
import numpy as np
from sklearn.metrics import roc_auc_score


def best_threshold(y_tr, p_tr):
    """Youden-J threshold: threshold on training probabilities that maximises
    TSS (= recall - fpr).  Standard operating-point selection for imbalanced
    SEP prediction; the paper's Table 2 confusion matrix (FP~237 / ~5470
    negatives, i.e. FPR~4%) shows it does NOT use a fixed 0.5 threshold on the
    raw probabilities.
    """
    y = np.asarray(y_tr, dtype=bool)
    p = np.asarray(p_tr, dtype=float)
    n_neg = int((~y).sum())
    n_pos = int(y.sum())
    # candidate thresholds: all unique probabilities + endpoints
    cands = np.unique(np.concatenate([[0.0], p, [1.0]]))
    best_t, best_tss = 0.5, -np.inf
    for t in cands:
        pred = p >= t
        tp = int((pred & y).sum())
        fn = n_pos - tp
        fp = int((pred & ~y).sum())
        tn = n_neg - fp
        recall = tp / n_pos if n_pos > 0 else 0.0
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
        tss = recall - fpr
        if tss > best_tss:
            best_tss, best_t = tss, float(t)
    return best_t, float(best_tss)


def compute_all(y_true, p_pos, method_name, threshold=0.5):
    y = np.asarray(y_true, dtype=bool)
    p = np.asarray(p_pos, dtype=float)
    pred = p >= threshold
    tp = int(np.sum(pred & y))
    tn = int(np.sum(~pred & ~y))
    fp = int(np.sum(pred & ~y))
    fn = int(np.sum(~pred & y))
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    tss = recall - fpr
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    accuracy = (tp + tn) / len(y)
    denom = (tp + fn) * (fn + tn) + (tp + fp) * (fp + tn)
    hss = 2.0 * (tp * tn - fp * fn) / denom if denom > 0 else 0.0
    try:
        auc = float(roc_auc_score(y, p))
    except ValueError:
        auc = float("nan")
    return {
        "method": method_name,
        "tp": tp, "tn": tn, "fp": fp, "fn": fn,
        "TSS": float(tss), "HSS": float(hss),
        "precision": float(precision), "recall": float(recall),
        "accuracy": float(accuracy), "AUC": auc,
        "n_test": int(len(y)),
    }
