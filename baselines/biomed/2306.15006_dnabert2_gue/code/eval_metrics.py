"""Evaluation metrics following the DNABERT-2 / GUE paper conventions.

- promoter-type tasks (prom_300_all, prom_core_all): macro F1
- anything else (EMP_H3, mouse_0): Matthews Correlation Coefficient (MCC)
- accuracy reported alongside for completeness
"""
from __future__ import annotations

import numpy as np
from sklearn.metrics import accuracy_score, f1_score, matthews_corrcoef
from scipy.stats import spearmanr  # noqa: F401  (API convenience, rarely needed)


def macro_f1(y_true: list[int], y_pred: list[int]) -> float:
    return float(f1_score(y_true, y_pred, average="macro", zero_division=0))


def mcc(y_true: list[int], y_pred: list[int]) -> float:
    return float(matthews_corrcoef(y_true, y_pred))


def acc(y_true: list[int], y_pred: list[int]) -> float:
    return float(accuracy_score(y_true, y_pred))


def evaluate(y_true: list[int], y_pred: list[int], task_metric: str) -> dict[str, float]:
    """Compute the full metric bouquet; round to 4 decimals for reporting."""
    out = {"acc": round(acc(y_true, y_pred), 4)}
    out["f1"] = round(macro_f1(y_true, y_pred), 4)
    try:
        out["mcc"] = round(mcc(y_true, y_pred), 4)
    except Exception:  # MCC requires both classes present
        out["mcc"] = float("nan")
    out[task_metric] = out[task_metric if task_metric in ("f1", "mcc") else "mcc"]
    return out


def mcc_from_preds(y_true, y_pred_proba) -> float:
    """MCC at the best-threshold, useful for difference diagnostics."""
    yt = np.asarray(y_true)
    best = (-1.0, 0.0)
    for t in np.linspace(0.0, 1.0, 101):
        p = (np.asarray(y_pred_proba) >= t).astype(int)
        m = matthews_corrcoef(yt, p)
        if m > best[0]:
            best = (m, t)
    return best[0]