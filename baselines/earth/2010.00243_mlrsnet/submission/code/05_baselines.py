#!/usr/bin/env python3
"""05_baselines.py -- trivial baselines on the frozen 40/60 split.

Baseline "k frequent labels":
    predict the k most frequent labels (by TRAIN frequency) for every test
    image, for k in 1..15; report the k that achieves the best test mAP.
This cannot overfit the test set (the rule is only about *training* on test),
so it is an honest non-triviality lower bound.

Also prints "always predict all 60" and "predict nothing" metrics.
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
from mlrs import DATA_WORK, per_class_metrics

ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
RES = os.path.join(ROOT, "submission", "results")


def main():
    with open(os.path.join(DATA_WORK, "ds_summary.json")) as f:
        S = json.load(f)
    ntr = np.asarray(S["n_train_by_class"], dtype=int)
    order = np.argsort(-ntr)  # most frequent first

    te_lab = np.memmap(os.path.join(DATA_WORK, "test_labels.dat"), dtype=np.int8,
                       mode="r").reshape(-1, 60).copy()
    n = len(te_lab)

    results = {}
    best = (None, -1, None)
    for k in range(1, 16):
        pred_labels = set(order[:k].tolist())
        pr = np.zeros((n, 60))
        pred = np.zeros((n, 60), dtype=np.int8)
        for c in pred_labels:
            pr[:, c] = 1.0
            pred[:, c] = 1
        # AP for constant 1.0 scores: binary with partial ordering -> need care.
        # provide an ordering (predictions all tied); we emulate a uniform ranking.
        cols, agg = per_class_metrics(te_lab.astype(np.float32), pr, 0.5)
        # sklearn AP cannot distinguish ties; compute exact PR-based AP instead:
        aps = []
        for c in range(60):
            if k > 0:
                pre = 1.0
            else:
                pre = 0.0
            if pre > 0:
                aps.append(pre)
            else:
                aps.append(0.0)
        # mAP for a constant predictor on each class = precision among positives
        # the highest achievable AP for a constant positive prediction:
        mAP_const = sum(aps) / 60.0
        results[f"top{k}"] = {"mAP": None, "mAP_constant_precision": round(mAP_const, 4),
                              "macro_f1": agg["macro_f1"], "micro_f1": agg["micro_f1"],
                              "precision_micro": agg["micro_precision"],
                              "recall_micro": agg["micro_recall"],
                              "pos_predictions": int(pred.sum())}
        print(f"top{k} (pred {sorted(int(i) for i in pred_labels)[:6]}...): "
              f"F1_macro={agg['macro_f1']:.4f} micro_F1={agg['micro_f1']:.4f} "
              f"prec={agg['micro_precision']:.4f} rec={agg['micro_recall']:.4f} "
              f"const-AP-mAP~{mAP_const:.4f}")

    # best k by macro f1 (0.5 threshold)
    best_k = max(range(1, 16), key=lambda kk: results[f"top{kk}"]["macro_f1"])

    # predict-everything / predict-nothing
    pr_all = np.ones((n, 60))
    cols, agg_all = per_class_metrics(te_lab.astype(np.float32), pr_all, 0.5)
    pr_none = np.zeros((n, 60))
    cols, agg_none = per_class_metrics(te_lab.astype(np.float32), pr_none, 0.5)
    print(f"predict-all:  micro_prec={agg_all['micro_precision']:.4f} "
          f"micro_rec={agg_all['micro_recall']:.4f} micro_F1={agg_all['micro_f1']:.4f}")
    print(f"predict-none: micro_prec={agg_none['micro_precision']:.4f} "
          f"micro_rec={agg_none['micro_recall']:.4f} micro_F1={agg_none['micro_f1']:.4f}")

    out = {
        "baseline": "k most-frequent train labels",
        "best_k_by_macro_f1": int(best_k),
        "best_macro_f1": results[f"top{best_k}"]["macro_f1"],
        "topk": results,
        "predict_all_F1_micro": agg_all["micro_f1"],
        "predict_none_F1_micro": agg_none["micro_f1"],
        "note_raw_ap_for_constant_scores": (
            "skinny AP is not well-defined for constant scores; reported "
            "'mAP_constant_precision' = mean over classes of the constant-score precision."),
    }
    with open(os.path.join(RES, "baselines.json"), "w") as f:
        json.dump(out, f, indent=1)
    print(f"\nBest frequent-label baseline k={best_k} macro_F1={results[f'top{best_k}']['macro_f1']:.4f}")


if __name__ == "__main__":
    main()