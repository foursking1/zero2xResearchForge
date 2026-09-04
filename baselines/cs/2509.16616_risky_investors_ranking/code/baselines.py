"""Tabular / LETOR baselines: LightGBM, XGBoost, RandomForest, lambdaMART.

Each model is trained on train only, threshold/hyperparams on val, evaluated on test.
with-prior : top-1% selection on scores (primary, matches paper Tables 8/9).
without-prior: threshold set on val (max F1) then applied to test.
"""
from __future__ import annotations
import os, numpy as np
import lightgbm as lgb, xgboost as xgb
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score
from common import prepare_fold, topk_metrics, pick_threshold, ROOT

RESULTS = os.path.join(ROOT, "results")
os.makedirs(RESULTS, exist_ok=True)


def score_lgb(X, y, Xv, Xt, seed=0):
    m = lgb.LGBMClassifier(n_estimators=600, learning_rate=0.04, num_leaves=63,
                           min_child_samples=40, subsample=0.9, colsample_bytree=0.9,
                           reg_lambda=1.0, n_jobs=20, random_state=seed, verbosity=-1)
    m.fit(X, y)
    return m.predict_proba(Xv)[:, 1], m.predict_proba(Xt)[:, 1]


def score_xgb(X, y, Xv, Xt, seed=0):
    m = xgb.XGBClassifier(n_estimators=600, learning_rate=0.04, max_depth=7,
                          subsample=0.9, colsample_bytree=0.9, reg_lambda=1.0,
                          n_jobs=20, random_state=seed, eval_metric="auc")
    m.fit(X, y)
    return m.predict_proba(Xv)[:, 1], m.predict_proba(Xt)[:, 1]


def score_rf(X, y, Xv, Xt, seed=0):
    m = RandomForestClassifier(n_estimators=200, max_depth=20, min_samples_leaf=10,
                               n_jobs=20, random_state=seed)
    m.fit(X, y)
    return m.predict_proba(Xv)[:, 1], m.predict_proba(Xt)[:, 1]


def score_lambdamart(X, y, groups, Xv, Xt, seed=0):
    grp_sizes = [len(g) for g in groups]
    dtrain = xgb.DMatrix(np.vstack([X[g] for g in groups]), label=np.vstack([y[g] for g in groups]))
    dtrain.set_group(grp_sizes)
    params = {"objective": "rank:ndcg", "eta": 0.03, "max_depth": 6, "min_child_weight": 8,
              "subsample": 0.9, "colsample_bytree": 0.9, "gamma": 0.5, "nthread": 20,
              "eval_metric": "ndcg", "seed": seed}
    m = xgb.train(params, dtrain, num_boost_round=500)
    return m.predict(xgb.DMatrix(Xv)), m.predict(xgb.DMatrix(Xt))


def run_fold(dataset, fold):
    d = prepare_fold(dataset, fold)
    X, y, Xv, Xt = d["X_train"], d["y_train"], d["X_val"], d["X_test"]
    yv, yt, it = d["y_val"], d["y_test"], d["i_test"]
    models = {
        "lgbm": (lambda: score_lgb(X, y, Xv, Xt, seed=fold)),
        "xgb": (lambda: score_xgb(X, y, Xv, Xt, seed=fold)),
        "rf": (lambda: score_rf(X, y, Xv, Xt, seed=fold)),
        "lambdamart": (lambda: score_lambdamart(X, y, d["groups"], Xv, Xt, seed=fold)),
    }
    rows = []
    for model, f in models.items():
        sv, st = f()
        wp = topk_metrics(yt, st, it)
        thr = pick_threshold(yv, sv)
        auc = float(roc_auc_score(yt, st))
        row = {"dataset": dataset, "setting": "with_prior", "model": model, "fold": fold,
               **{k: wp[k] for k in ("f1", "financial_loss", "precision", "sensitivity", "specificity")},
               "auc": auc, "threshold": thr}
        rows.append(row)
        print(f"[{dataset}] fold{fold} {model:11s} F1={wp['f1']:.4f} loss={wp['financial_loss']:.2f} "
              f"P={wp['precision']:.4f} S={wp['sensitivity']:.4f} Sp={wp['specificity']:.4f} "
              f"auc={auc:.4f} thr={thr:.3f}", flush=True)
    return rows


if __name__ == "__main__":
    import pandas as pd, json
    all_rows = []
    for dataset in ("creditcard", "jobprofit"):
        for fold in (1, 2, 3):
            all_rows += run_fold(dataset, fold)
    out = os.path.join(RESULTS, "baselines_fold.csv")
    pd.DataFrame(all_rows).to_csv(out, index=False)
    print("saved", out)