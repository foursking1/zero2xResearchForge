#!/usr/bin/env python3
"""Non-graph classical baselines (sklearn): logistic regression and random forest
trained on the per-graph aggregated atom-feature vectors (no graph structure)."""

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score


def fit_predict_logreg(Xtr, ytr, Xva, yva, Xte, yte, seed=0):
    scaler = StandardScaler().fit(Xtr)
    Xtr_s, Xva_s, Xte_s = scaler.transform(Xtr), scaler.transform(Xva), scaler.transform(Xte)
    model = LogisticRegression(max_iter=2000, C=0.1, random_state=seed)
    model.fit(Xtr_s, ytr)
    va = roc_auc_score(yva, model.predict_proba(Xva_s)[:, 1])
    te = roc_auc_score(yte, model.predict_proba(Xte_s)[:, 1])
    return {"model": "LogReg", "valid_roc_auc": va, "test_roc_auc": te,
            "virtual_node": False, "prototype": model}


def fit_predict_rf(Xtr, ytr, Xva, yva, Xte, yte, seed=0):
    model = RandomForestClassifier(n_estimators=300, max_depth=None,
                                   max_features="sqrt", n_jobs=-1, random_state=seed)
    model.fit(Xtr, ytr)
    va = roc_auc_score(yva, model.predict_proba(Xva)[:, 1])
    te = roc_auc_score(yte, model.predict_proba(Xte)[:, 1])
    return {"model": "RF", "valid_roc_auc": va, "test_roc_auc": te,
            "virtual_node": False, "prototype": model}


def fit_predict_xgb(Xtr, ytr, Xva, yva, Xte, yte, seed=0):
    pass  # xgboost may not be available offline; keep hook if installed


if __name__ == "__main__":
    import sys, torch, json, os
    from models import graph_features

    torch.manual_seed(0)
    results = {}
    feats, ys = {}, {}
    for split in ["train", "valid", "test"]:
        f, y = graph_features(torch.load(f"/tmp/molhiv/{split}.pt"))
        feats[split], ys[split] = f.numpy(), y.numpy()

    r_logreg = fit_predict_logreg(feats["train"], ys["train"], feats["valid"],
                                  ys["valid"], feats["test"], ys["test"])
    r_rf = fit_predict_rf(feats["train"], ys["train"], feats["valid"],
                          ys["valid"], feats["test"], ys["test"])
    for r in (r_logreg, r_rf):
        r.pop("prototype")
        print(r)
    with open(os.environ.get("RESULTS_JSON", "/tmp/baseline_results.json"), "w") as f:
        json.dump([r_logreg, r_rf], f, indent=2)