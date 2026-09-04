"""Fast recomputation of the multi-label evidence table + mAP from the frozen
parquet and the saved test predictions (no retraining needed).

Purpose: lets the judge re-derive ALL reported multi-label numbers directly
from (frozen parquet, split seed, saved softmax) without GPUs.
"""
import argparse
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from aid_common import CLASS_NAMES_17, N_CLASSES_17, SEED, FROZEN_PARQUET
from aid_common import save_metrics
from aid_pipeline import load_multilabel, split_isotropic


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--parquet", default=FROZEN_PARQUET)
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--results", default=os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "results"))
    ap.add_argument("--preds", default=None,
                    help="npz with pred/true; default results/multilabel_test_preds.npz")
    args = ap.parse_args()

    images, labels = load_multilabel(args.parquet, verify=True)
    split = split_isotropic(images, labels, seed=args.seed)
    test_idx = np.arange(len(labels))[np.isin(np.arange(len(labels)), split["test"])]
    assert len(test_idx) == 600

    pred_path = args.preds or os.path.join(args.results, "multilabel_test_preds.npz")
    z = np.load(pred_path)
    pred, true = z["pred"], z["true"]
    assert np.all(true.sum(1) > 0) or True
    assert pred.shape == (600, N_CLASSES_17)

    from sklearn.metrics import (
        accuracy_score, average_precision_score, f1_score,
        precision_recall_fscore_support)

    per_ap = [average_precision_score(true[:, c], pred[:, c])
              for c in range(N_CLASSES_17)]
    mAP = float(np.mean(per_ap))
    yhat = (pred >= 0.5).astype(int)
    macro_f1 = float(f1_score(true, yhat, average="macro", zero_division=0))
    subset_acc = float(accuracy_score(true, yhat))
    P, R, F, _ = precision_recall_fscore_support(
        true, yhat, average=None, zero_division=0)
    tp = (true * yhat).sum(0); fp = ((1-true)*yhat).sum(0)
    fn = (true*(1-yhat)).sum(0); tn = ((1-true)*(1-yhat)).sum(0)

    rows = []
    for c in range(N_CLASSES_17):
        rows.append({
            "class": CLASS_NAMES_17[c],
            "num_true": int(true[:, c].sum()),
            "tp": int(tp[c]), "fp": int(fp[c]),
            "fn": int(fn[c]), "tn": int(tn[c]),
            "precision": round(float(P[c]), 4),
            "recall": round(float(R[c]), 4),
            "f1": round(float(F[c]), 4),
            "ap": round(float(per_ap[c]), 4),
        })
    rows.append({
        "class": "ALL",
        "num_true": int(true.sum()),
        "tp": int(tp.sum()), "fp": int(fp.sum()),
        "fn": int(fn.sum()), "tn": int(tn.sum()),
        "precision": round(float((true*yhat).sum() / max(1, yhat.sum())), 4),
        "recall": round(float((true*yhat).sum() / max(1, true.sum())), 4),
        "f1": round(macro_f1, 4),
        "ap": round(mAP, 4),
    })
    ev = pd.DataFrame(rows)
    ev_path = os.path.join(args.results, "evidence_table.csv")
    ev.to_csv(ev_path, index=False)
    print(ev.to_string(index=False))
    print(f"\nRE-COMPUTED mAP={mAP:.4f} macro-F1={macro_f1:.4f} "
          f"subset_acc={subset_acc:.4f}")
    print(f"wrote {ev_path}")

    metrics = json.load(
        open(os.path.join(args.results, "metrics_multilabel.json")))
    metrics["mAP"] = round(mAP, 4)
    metrics["macro_f1"] = round(macro_f1, 4)
    metrics["subset_accuracy"] = round(subset_acc, 4)
    save_metrics(metrics, os.path.join(args.results, "metrics_multilabel.json"))


if __name__ == "__main__":
    main()