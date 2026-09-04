# -*- coding: utf-8 -*-
"""SEP data loading, cleaning and feature engineering (arXiv:2303.08092).

Loads the frozen SEPTEBS.json, applies the paper's exclusion criteria
(Tmax < 100 MK and all six time-offset fields + MinDur non-negative),
builds the 12-feature design matrix + CausedSPE label, and computes the
feature-importance weights used by the Random Hivemind (chi^2 + mutual
information, normalised to [0,1]).
"""
import os
import json
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.normpath(os.path.join(HERE, "..", "..", "data", "SEPTEBBS.json"))

FEATURES = ["MinDur", "Tmax", "EMmax", "PrecisePeak",
            "StartToTmax", "TmaxToEnd", "StartToEMmax", "EMmaxToEnd",
            "StartToPeak", "PeakToEnd", "XCtr", "YCtr"]


def load_raw():
    with open(DATA, "r", encoding="utf-8") as f:
        rec = json.load(f)
    return rec


def build_matrix(rec):
    X = np.zeros((len(rec), 12), dtype=float)
    y = np.zeros(len(rec), dtype=bool)
    for i, r in enumerate(rec):
        for j, f in enumerate(FEATURES):
            X[i, j] = float(r[f])
        y[i] = bool(r["CausedSPE"])
    return X, y


def clean_mask(X):
    """Paper exclusion criteria: Tmax < 100 MK and all offsets/MinDur >= 0."""
    tmax = X[:, 1]
    offset_cols = [0, 4, 5, 6, 7, 8, 9]  # MinDur + 6 time offsets
    return (tmax < 100.0) & np.all(X[:, offset_cols] >= 0.0, axis=1)


def feature_importance(X, y):
    """Feature weights for RH: normalised chi^2 + normalised mutual information.

    Returns w (12,) summing to 1.  chi^2 computed on binned features (10 bins);
    MI via a nearest-neighbours estimator (sklearn).  Each is min-max normalised
    across features before averaging.
    """
    from sklearn.feature_selection import chi2
    from sklearn.feature_selection import mutual_info_classif

    # chi^2 needs non-negative inputs; all our features are non-negative after
    # cleaning.  Bin continuous features into 10 quantile bins to make chi^2
    # meaningful on non-Integer data.
    Xb = np.zeros_like(X)
    for j in range(X.shape[1]):
        v = X[:, j]
        if len(np.unique(v)) > 10:
            q = np.quantile(v, np.linspace(0, 1, 11))
            q = np.unique(q)
            Xb[:, j] = np.digitize(v, q[1:-1])
        else:
            Xb[:, j] = v
    chi, _ = chi2(Xb, y.astype(int))
    mi = mutual_info_classif(X, y.astype(int), random_state=0, n_neighbors=5)

    def norm01(a):
        a = np.asarray(a, dtype=float)
        lo, hi = a.min(), a.max()
        if hi - lo < 1e-12:
            return np.ones_like(a)
        return (a - lo) / (hi - lo)

    w = 0.5 * norm01(chi) + 0.5 * norm01(mi)
    w = np.maximum(w, 1e-6)
    return w / w.sum(), {"chi2": chi.tolist(), "mi": mi.tolist(), "weight": w.tolist()}


def load_clean():
    """Returns (X, y, summary_dict)."""
    rec = load_raw()
    X, y = build_matrix(rec)
    mask = clean_mask(X)
    Xc, yc = X[mask], y[mask]
    w, imp = feature_importance(Xc, yc)
    summary = {
        "total_rows": int(len(rec)),
        "total_sep": int(y.sum()),
        "clean_rows": int(mask.sum()),
        "clean_sep": int(yc.sum()),
        "n_features": 12,
        "features": FEATURES,
        "importance": imp,
    }
    return Xc, yc, w, summary


if __name__ == "__main__":
    X, y, w, s = load_clean()
    print("clean rows/SEP:", s["clean_rows"], s["clean_sep"])
    for f, wi in zip(FEATURES, w):
        print(f"  {f:12s} w={wi:.4f}")
