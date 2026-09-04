# -*- coding: utf-8 -*-
"""Combine per-seed runs into the official per-model predictions.

Reads predictions from tagged runs under code/checkpoints/<tag>/ and writes
the merged, official files into code/checkpoints/{repro,enhanced}_*.

    repro    <- checkpoints/repro_pred.npz (seed 42) + checkpoints/r43/*
    enhanced <- checkpoints/en_a75/*          + checkpoints/en_s43/*

The merged test probabilities are the average of the per-seed snapshot
ensembles.  The enhanced thresholds are re-tuned on the merged *validation*
probabilities (grid maximizing per-class F1); repro thresholds stay at 0.5
(the CheXNet-style fixed threshold).

Run:  python3 code/merge_seeds.py
"""
import json
import os
import sys

import numpy as np
from sklearn.metrics import f1_score

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common  # noqa: E402

N_CLASS = common.N_CLASS
OUT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CK = os.path.join(OUT, "code", "checkpoints")


def tune_thresholds(y_val, p_val):
    grid = np.arange(0.05, 0.96, 0.05)
    thr = np.ones(N_CLASS) * 0.5
    for c in range(N_CLASS):
        if y_val[:, c].sum() == 0:
            continue
        best_f1, best_t = -1.0, 0.5
        for t in grid:
            f1 = f1_score(y_val[:, c], (p_val[:, c] >= t).astype(int), zero_division=0)
            if f1 > best_f1:
                best_f1, best_t = f1, float(t)
        thr[c] = best_t
    return thr


def merge(tag_sources, model, threshold_mode):
    parts_t, parts_v, yte, yva, best_auc = [], [], None, None, -1.0
    seeds_detail = []
    seed_ids = []
    for tag in tag_sources:
        path = os.path.join(CK, tag, f"{model}_pred.npz") if tag else \
            os.path.join(CK, f"{model}_pred.npz")
        mp = os.path.join(CK, tag, f"{model}_meta.json") if tag else \
            os.path.join(CK, f"{model}_meta.json")
        d = np.load(path)
        parts_t.append(d["p_test_ens"])
        if "p_val_ens" in d:
            parts_v.append(d["p_val_ens"])
        else:
            parts_v.append(d["p_val"])
        yte, yva = d["y_test"], d["y_val"]
        best_auc = max(best_auc, float(d["best_auc"]))
        if os.path.isfile(mp):
            meta = json.load(open(mp))
            seeds_detail.append({"seed": meta.get("seed"),
                                 "best_val_mean_auc": round(float(d["best_auc"]), 4),
                                 "epochs": meta.get("epochs")})
            seed_ids.append(str(meta.get("seed")))
        else:
            seeds_detail.append({"seed": tag, "best_val_mean_auc": round(float(d["best_auc"]), 4)})
            seed_ids.append(tag)
    pt = np.mean(np.stack(parts_t), axis=0)
    pv = np.mean(np.stack(parts_v), axis=0)

    thr = tune_thresholds(yva, pv) if threshold_mode == "tune" \
        else np.ones(N_CLASS) * 0.5

    np.savez_compressed(
        os.path.join(CK, f"{model}_pred.npz"),
        p_val=pv, p_test=pt, p_test_ens=pt, p_val_ens=pv,
        y_val=yva, y_test=yte, thresholds=thr, best_auc=best_auc,
    )
    json.dump({"threshold": thr.tolist(), "best_val_auc": best_auc,
               "train_n_used": 920, "val_n": 162,
               "seed": ",".join(seed_ids), "seeds": ",".join(seed_ids),
               "seeds_detail": seeds_detail,
               "epochs": seeds_detail[0].get("epochs", 22)},
              open(os.path.join(CK, f"{model}_meta.json"), "w"), indent=2)
    aucs = common.per_class_auc(yte, pt)
    f1s = common.per_class_f1(yte, (pt >= thr).astype(float))
    print(f"[{model}] merged n_seeds={len(tag_sources)}  "
          f"mean AUC={np.nanmean(aucs):.4f}  mean F1={f1s.mean():.4f}")


if __name__ == "__main__":
    merge(["s42", "r43"], "repro", threshold_mode="fixed")
    merge(["en_s42b", "en_s43", "en_s44"], "enhanced", threshold_mode="tune")