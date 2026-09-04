"""Run all baselines for ONE (dataset, fold) and append to the shared results CSV.
Usage: python3 run_one_fold_baseline.py <dataset> <fold>
Recommended launch (pinned): for each (ds,fold): taskset -c a-b python3 run_one_fold_baseline.py
"""
from __future__ import annotations
import os, sys, time, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("OMP_NUM_THREADS", "3")
from sklearn.metrics import roc_auc_score
import lightgbm as lgb, xgboost as xgb
from sklearn.ensemble import RandomForestClassifier
from common import prepare_fold, topk_metrics, pick_threshold, threshold_metrics, ROOT

RESULTS = os.path.join(ROOT, "results")
os.makedirs(RESULTS, exist_ok=True)
CSV = os.path.join(RESULTS, "baselines_perfold.csv")

LGB = dict(n_estimators=400, learning_rate=0.05, num_leaves=48, min_child_samples=40,
           subsample=0.9, colsample_bytree=0.9, reg_lambda=1.0, n_jobs=3, verbosity=-1)
XGB = dict(n_estimators=400, learning_rate=0.05, max_depth=7, subsample=0.9,
           colsample_bytree=0.9, reg_lambda=1.0, n_jobs=3)
RF = dict(n_estimators=150, max_depth=18, min_samples_leaf=10, n_jobs=3)


def _append(row):
    old = pd.DataFrame()
    if os.path.exists(CSV):
        old = pd.read_csv(CSV)
    merged = pd.concat([old, pd.DataFrame([row])], ignore_index=True)
    merged = merged[~merged[["dataset", "fold", "model", "setting"]].duplicated(keep="last")]
    merged.to_csv(CSV, index=False)
    print(f"  [{row['dataset']}] fold{row['fold']} {row['model']}:{row['setting']} appended", flush=True)


def run(dataset, fold):
    d = prepare_fold(dataset, fold)
    X, y, Xv, Xt = d["X_train"], d["y_train"], d["X_val"], d["X_test"]
    yv, yt, it, sv_model = d["y_val"], d["y_test"], d["i_test"], {}
    rows = []

    t0 = time.time()
    m = lgb.LGBMClassifier(random_state=fold, **LGB).fit(X, y)
    sv = m.predict_proba(Xv)[:, 1]; st = m.predict_proba(Xt)[:, 1]
    [_append(r) for r in emit(dataset, fold, "lgbm", sv, st, yv, yt, it, time.time() - t0)]

    t0 = time.time()
    m = xgb.XGBClassifier(random_state=fold, eval_metric="auc", **XGB).fit(X, y)
    sv = m.predict_proba(Xv)[:, 1]; st = m.predict_proba(Xt)[:, 1]
    [_append(r) for r in emit(dataset, fold, "xgb", sv, st, yv, yt, it, time.time() - t0)]

    t0 = time.time()
    m = RandomForestClassifier(random_state=fold, **RF).fit(X, y)
    sv = m.predict_proba(Xv)[:, 1]; st = m.predict_proba(Xt)[:, 1]
    [_append(r) for r in emit(dataset, fold, "rf", sv, st, yv, yt, it, time.time() - t0)]

    t0 = time.time()
    idx_map = np.full(int(d["idx_train"].max()) + 1, -1)
    idx_map[d["idx_train"]] = np.arange(len(d["idx_train"]))
    grp_local = idx_map[d["groups"].astype(np.int64)]
    grp_sizes = [len(g) for g in grp_local]
    m = xgb.train({"objective": "rank:ndcg", "eta": 0.04, "max_depth": 6,
                   "min_child_weight": 8, "subsample": 0.9, "colsample_bytree": 0.9,
                   "gamma": 0.5, "nthread": 3, "eval_metric": "ndcg", "seed": fold},
                  _grp_matrix(X, y, grp_local, grp_sizes), num_boost_round=350)
    sv = m.predict(xgb.DMatrix(Xv)); st = m.predict(xgb.DMatrix(Xt))
    [_append(r) for r in emit(dataset, fold, "lambdamart", sv, st, yv, yt, it, time.time() - t0)]


def _grp_matrix(X, y, groups, sizes):
    dt = xgb.DMatrix(np.vstack([X[g] for g in groups]), label=np.vstack([y[g] for g in groups]))
    dt.set_group(sizes)
    return dt


def emit(dataset, fold, model, sv, st, yv, yt, it, secs):
    wp = topk_metrics(yt, st, it)
    thr = pick_threshold(yv, sv)
    wn = threshold_metrics(yt, st, it, thr)
    auc = float(roc_auc_score(yt, st))
    print(f"  [{dataset}] fold{fold} {model:11s} with_prior F1={wp['f1']:.4f} "
          f"loss={wp['financial_loss']:.2f} P={wp['precision']:.4f} S={wp['sensitivity']:.4f} "
          f"Sp={wp['specificity']:.4f} auc={auc:.4f} thr={thr:.3f} ({secs:.0f}s)", flush=True)
    rows = []
    for setting, m in (("with_prior", wp), ("without_prior", wn)):
        rows.append({"dataset": dataset, "fold": fold, "model": model, "setting": setting,
                     "f1": m["f1"], "financial_loss": m["financial_loss"],
                     "precision": m["precision"], "sensitivity": m["sensitivity"],
                     "specificity": m["specificity"], "auc": auc, "threshold": thr,
                     "seconds": round(secs, 1)})
    return rows


if __name__ == "__main__":
    run(sys.argv[1], int(sys.argv[2]))