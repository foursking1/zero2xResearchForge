"""03_train_ml.py
Traditional ML: Random Forest vs SVM (RBF) on basic / mid / enhanced features.
Protocol: fixed 5-fold CV (seed 42) for all models; SVR hyperparameters chosen by
INNER 3-fold CV on the training portion only (no leakage). Also reports a fixed
80/20 split run as a secondary protocol.
Outputs: results/model_results_cv.csv, results/evidence_table.csv,
         results/oof_predictions.csv, results/ml_metrics.json
"""
import os
import sys
import json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.svm import SVR
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import GridSearchCV, train_test_split

from common import (fixed_folds, run_cv, summarize_folds, mae_rmse_r2, SEED,
                    RESULTS_DIR)

np.random.seed(SEED)

d = np.load(os.path.join(RESULTS_DIR, "features.npz"), allow_pickle=True)
y = d["y"]
FEATURE_SETS = {
    "basic": d["Xb"],
    "mid": d["Xm"],
    "enhanced": d["Xe"],
}

folds = fixed_folds(len(y), n_splits=5, seed=SEED)
print("5-fold CV folds fixed (seed=42):", [ (len(tr), len(va)) for tr, va in folds ])

SVR_GRID = {"C": [3, 10, 30], "gamma": ["scale", 0.001, 0.005]}


def make_rf():
    return RandomForestRegressor(n_estimators=500, max_features="sqrt",
                                 random_state=SEED, n_jobs=-1)


def make_svr_factory(X, tr):
    """Inner-CV hyperparameter selection for SVR, training portion only."""
    sc = StandardScaler()
    Xtr = sc.fit_transform(X.iloc[tr])
    gs = GridSearchCV(SVR(epsilon=0.1), SVR_GRID, cv=3,
                      scoring="neg_mean_absolute_error", n_jobs=-1)
    gs.fit(Xtr, y[tr])
    return gs.best_estimator_, sc, gs.best_params_


def factory_rf(X, tr, va):
    m = make_rf()
    m.fit(X.iloc[tr], y[tr])
    return m


def factory_svr(X, tr, va):
    best, sc, params = make_svr_factory(X, tr)
    best.fit(sc.transform(X.iloc[tr]), y[tr])
    class _Wrap:
        def __init__(self, model, scaler):
            self.model, self.scaler = model, scaler
        def predict(self, Xva):
            return self.model.predict(self.scaler.transform(Xva))
    return _Wrap(best, sc)


rows = []
all_results = {}
oof_all = {}

for fname, X in FEATURE_SETS.items():
    Xdf = pd.DataFrame(X)
    print(f"\n===== feature set: {fname} ({X.shape[1]} dims) =====")
    for model_name in ["rf", "svr"]:
        fac = (lambda tr, va, Xd=Xdf: factory_rf(Xd, tr, va)) \
            if model_name == "rf" else \
            (lambda tr, va, Xd=Xdf: factory_svr(Xd, tr, va))
        per_fold, pooled, oof = run_cv(fac, Xdf, y, folds)
        summary = summarize_folds(per_fold)
        print(f"[{model_name}] per-fold MAE: "
              + ", ".join(f"{r['MAE']:.4f}" for r in per_fold))
        print(f"[{model_name}] per-fold R2 : "
              + ", ".join(f"{r['R2']:.4f}" for r in per_fold))
        print(f"[{model_name}] pooled  -> MAE {pooled['MAE']:.4f}, RMSE {pooled['RMSE']:.4f}, R2 {pooled['R2']:.4f}, Spearman {pooled['Spearman']:.4f}")
        print(f"[{model_name}] mean    -> MAE {summary['MAE']:.4f}+-{summary['MAE_std']:.4f}, R2 {summary['R2']:.4f}+-{summary['R2_std']:.4f}")
        for r in per_fold:
            rows.append({"model": model_name, "feature_set": fname,
                         "split": "5fold_cv_fold%d" % r["fold"],
                         "metric": "MAE", "value": r["MAE"], "value_std": np.nan})
            rows.append({"model": model_name, "feature_set": fname,
                         "split": "5fold_cv_fold%d" % r["fold"],
                         "metric": "R2", "value": r["R2"], "value_std": np.nan})
            rows.append({"model": model_name, "feature_set": fname,
                         "split": "5fold_cv_fold%d" % r["fold"],
                         "metric": "RMSE", "value": r["RMSE"], "value_std": np.nan})
        for metric in ["MAE", "RMSE", "R2", "Spearman"]:
            rows.append({"model": model_name, "feature_set": fname,
                         "split": "5fold_cv_mean", "metric": metric,
                         "value": summary[metric], "value_std": summary[f"{metric}_std"]})
            rows.append({"model": model_name, "feature_set": fname,
                         "split": "5fold_cv_pooled", "metric": metric,
                         "value": pooled[metric], "value_std": np.nan})
        all_results[f"{model_name}__{fname}"] = {
            "per_fold": per_fold, "pooled": pooled, "summary": summary,
        }
        oof_all[f"{model_name}__{fname}"] = oof

# ---- fixed 80/20 split (secondary protocol) -------------------------------
tr_idx, va_idx = train_test_split(np.arange(len(y)), test_size=0.2,
                                  random_state=SEED, shuffle=True)
folds80 = [(tr_idx, va_idx)]
for fname, X in FEATURE_SETS.items():
    Xdf = pd.DataFrame(X)
    for model_name in ["rf", "svr"]:
        fac = (lambda tr, va, Xd=Xdf: factory_rf(Xd, tr, va)) \
            if model_name == "rf" else \
            (lambda tr, va, Xd=Xdf: factory_svr(Xd, tr, va))
        per_fold, pooled, oof = run_cv(fac, Xdf, y, folds80)
        print(f"[80/20] {model_name} {fname}: MAE {pooled['MAE']:.4f}, R2 {pooled['R2']:.4f}")
        for metric in ["MAE", "RMSE", "R2", "Spearman"]:
            rows.append({"model": model_name, "feature_set": fname,
                         "split": "train80_test20", "metric": metric,
                         "value": pooled[metric], "value_std": np.nan})
        all_results[f"{model_name}__{fname}"]["test20"] = pooled

ev = pd.DataFrame(rows)
ev.to_csv(os.path.join(RESULTS_DIR, "evidence_table.csv"), index=False)
print("\nsaved results/evidence_table.csv (%d rows)" % len(ev))

# OOF predictions for auditability
oof_df = pd.DataFrame({"formula": d["formula"], "mp_id": d["mp_id"], "y": y})
for k, oof in oof_all.items():
    oof_df[k.replace("__", "_") + "_oof"] = oof
oof_df.to_csv(os.path.join(RESULTS_DIR, "oof_predictions.csv"), index=False)

# ---- serialize metrics -----------------------------------------------------
def _to_json(obj):
    if isinstance(obj, dict):
        return {k: _to_json(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_to_json(v) for v in obj]
    if isinstance(obj, (np.floating, float)):
        return float(obj)
    if isinstance(obj, (np.integer, int)):
        return int(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    return str(obj)

out = {"n_samples": int(len(y)), "seed": SEED,
       "feature_sets": {k: int(v.shape[1]) for k, v in FEATURE_SETS.items()},
       "models": _to_json(all_results)}
with open(os.path.join(RESULTS_DIR, "ml_metrics.json"), "w") as f:
    json.dump(out, f, indent=2, default=str)
print("saved results/ml_metrics.json")
print("done.")
