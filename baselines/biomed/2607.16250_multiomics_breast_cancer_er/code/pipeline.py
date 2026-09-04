#!/usr/bin/env python3
"""pipeline.py — Shared stratified 5-fold CV pipeline with fold-internal
feature selection (anti-leakage) for ER-status classification.

Design decisions (all documented in report.md):
  * Fixed seed + StratifiedKFold(5) -> every configuration sees the SAME folds.
  * Feature selection is computed ONLY on the training part of each fold
    (no test-fold statistics). Two selectors are supported:
        - 'variance'   : rank by per-feature variance (train-fold), keep top-N
        - 'univariate' : rank by ANOVA F-statistic vs train labels, keep top-N
    Both drop constant features within the training fold first.
  * Per-omic top-N mirror the paper's post-selection sizes:
        RNA=604, CNV=860, RPPA=all available (paper reports 223; frozen file
        ships 198 proteins).
  * RPPA NaN values are median-imputed using TRAIN-fold statistics only.
  * StandardScaler fit on TRAIN fold only (matters for SVM/LR).
  * Fixed moderate hyperparameters per model (no tuning on the full data,
    which would itself leak).
"""
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, balanced_accuracy_score, f1_score, roc_auc_score
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
from catboost import CatBoostClassifier

SEED = 42
N_JOBS = 4  # modest thread count: parallel tasks on the box cause thrash with -1
OMIC_SETS = {
    "RNA":        ["rna"],
    "CNV":        ["cna"],
    "RPPA":       ["rppa"],
    "RNA+CNV":    ["rna", "cna"],
    "RNA+CNV+RPPA": ["rna", "cna", "rppa"],
}
TOP_N = {"rna": 604, "cna": 860, "rppa": None}  # None -> keep all


def get_model(name, seed=SEED, scale_pos_weight=1.0):
    return {
        "RF": RandomForestClassifier(n_estimators=300, class_weight="balanced",
                                     random_state=seed, n_jobs=N_JOBS),
        "XGBoost": XGBClassifier(n_estimators=300, max_depth=4, learning_rate=0.05,
                                 subsample=0.8, colsample_bytree=0.8,
                                 tree_method="hist", eval_metric="logloss",
                                 scale_pos_weight=scale_pos_weight,
                                 random_state=seed, n_jobs=N_JOBS),
        "LightGBM": LGBMClassifier(n_estimators=300, num_leaves=31, learning_rate=0.05,
                                   class_weight="balanced", verbose=-1,
                                   random_state=seed, n_jobs=N_JOBS),
        "CatBoost": CatBoostClassifier(iterations=300, depth=6, learning_rate=0.05,
                                       auto_class_weights="Balanced", verbose=0,
                                       random_seed=seed, thread_count=N_JOBS),
        "SVM": SVC(C=1.0, kernel="rbf", gamma="scale", class_weight="balanced",
                   probability=True, random_state=seed),
        "LR": LogisticRegression(C=1.0, max_iter=3000, solver="liblinear",
                                 class_weight="balanced", random_state=seed),
    }[name]


def _drop_constant(X, tr_idx):
    tr_std = X[tr_idx].std(axis=0)
    keep = tr_std > 0
    if keep.all():
        return X, np.arange(X.shape[1])
    return X[:, keep], np.where(keep)[0]


def _select_top_n(X, tr_idx, y_tr, n, method):
    X_ = X[tr_idx]
    if method == "variance":
        score = X_.var(axis=0)
    else:  # univariate ANOVA F-test vs labels (vectorized over features)
        n0 = int((y_tr == 0).sum())
        n1 = int((y_tr == 1).sum())
        g0 = X_[y_tr == 0]
        g1 = X_[y_tr == 1]
        m0 = g0.mean(axis=0)
        m1 = g1.mean(axis=0)
        m = X_.mean(axis=0)
        ss_between = n0 * (m0 - m) ** 2 + n1 * (m1 - m) ** 2
        ss_within = ((g0 - m0) ** 2).sum(axis=0) + ((g1 - m1) ** 2).sum(axis=0)
        with np.errstate(divide="ignore", invalid="ignore"):
            score = np.where(ss_within > 0, ss_between / np.maximum(ss_within, 1e-12), 0.0)
    score = np.nan_to_num(score, nan=0.0)
    if n is None or n >= X_.shape[1]:
        n = X_.shape[1]
    order = np.argsort(-score, kind="mergesort")[:n]
    return X[:, order], order


def _median_impute(X, tr_idx):
    if not np.isnan(X).any():
        return X
    med = np.nanmedian(X[tr_idx], axis=0)
    X = np.where(np.isnan(X), med, X)
    return X


def run_cv(X_by_omic, y, omic_set, model_name, method="variance",
           scope="fold_internal", n_splits=5, seed=SEED):
    """Run stratified 5-fold CV with fold-internal (or full-data) feature selection.

    Returns dict with per-fold metrics and mean/std.
    """
    omics = OMIC_SETS[omic_set]
    rng = np.random.RandomState(seed)
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=seed)
    folds = list(skf.split(X_by_omic["rna"], y))

    metrics = {k: [] for k in ["balanced_acc", "macro_f1", "roc_auc", "acc"]}
    sel_size = {}
    for fold_id, (tr_idx, te_idx) in enumerate(folds):
        Xtr = []
        Xte = []
        for om in omics:
            X = X_by_omic[om].copy()
            X = _median_impute(X, tr_idx)
            if scope == "fold_internal":
                X, keep_const = _drop_constant(X, tr_idx)
                X, keep_sel = _select_top_n(X, tr_idx, y[tr_idx], TOP_N[om], method)
                cols = keep_const[keep_sel]
            else:  # leak: statistics estimated on ALL samples
                X, keep_const = _drop_constant(X, np.arange(X.shape[0]))
                X, keep_sel = _select_top_n(X, np.arange(X.shape[0]), y, TOP_N[om], method)
                cols = keep_const[keep_sel]
            sel_size.setdefault(om, len(cols))
            sc = StandardScaler()
            if scope == "fold_internal":
                sc.fit(X[tr_idx])
            else:
                sc.fit(X)
            Xtr.append(sc.transform(X[tr_idx]))
            Xte.append(sc.transform(X[te_idx]))
        Xtr = np.hstack(Xtr)
        Xte = np.hstack(Xte)

        model = get_model(model_name, seed=seed + fold_id,
                          scale_pos_weight=(y[tr_idx] == 0).sum() / max(1, (y[tr_idx] == 1).sum()))
        model.fit(Xtr, y[tr_idx])

        if hasattr(model, "predict_proba"):
            p = model.predict_proba(Xte)[:, 1]
        else:
            p = model.decision_function(Xte)
        pred = model.predict(Xte)
        metrics["balanced_acc"].append(balanced_accuracy_score(y[te_idx], pred))
        metrics["macro_f1"].append(f1_score(y[te_idx], pred, average="macro"))
        metrics["roc_auc"].append(roc_auc_score(y[te_idx], p))
        metrics["acc"].append(accuracy_score(y[te_idx], pred))

    out = {"omic_set": omic_set, "model": model_name, "method": method,
           "scope": scope, "fold": None}
    for k, v in metrics.items():
        out[k] = float(np.mean(v))
        out[k + "_std"] = float(np.std(v))
        out[k + "_perfold"] = [float(x) for x in v]
    out["n_features_selected"] = sum(sel_size.values())
    out["n_features_per_omic"] = sel_size
    return out


def cv_to_row(out):
    return {
        "model": out["model"],
        "omic_set": out["omic_set"],
        "feature_selection": f"{out['method']}_{out['scope']}",
        "balanced_acc": round(out["balanced_acc"], 4),
        "macro_f1": round(out["macro_f1"], 4),
        "roc_auc": round(out["roc_auc"], 4),
        "acc": round(out["acc"], 4),
        "n_features": out["n_features_selected"],
    }
