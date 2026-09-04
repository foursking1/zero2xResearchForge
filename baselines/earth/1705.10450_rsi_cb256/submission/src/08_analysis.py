"""Data characterization + confusion analysis used in the report.

Produces:
  results/data_stats.json      per-class counts, imbalance ratios, split stats
  results/confusion_top_pairs.csv  top confusable (true, predicted) pairs
  results/accuracy_vs_support.csv  per-class test accuracy vs train support
"""
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (LABEL1_NAMES, LABEL2_NAMES, N_L1, N_L2, RESULTS_DIR,  # noqa: E402
                    load_labels)


def main():
    lab = load_labels()
    l1, l2, split = lab["label_1"], lab["label_2"], lab["split"]
    tr, te = split == "train", split == "test"

    stats = {
        "total_rows": len(l2),
        "train": int(tr.sum()), "test": int(te.sum()),
        "n_label1_classes": int(np.unique(l1).size),
        "n_label2_classes": int(np.unique(l2).size),
        "label1_counts": {int(k): int(v) for k, v in zip(*np.unique(l1, return_counts=True))},
        "label2_counts_total": {int(k): int(v) for k, v in zip(*np.unique(l2, return_counts=True))},
        "label2_counts_train": {int(k): int(v) for k, v in zip(*np.unique(l2[tr], return_counts=True))},
        "label2_counts_test": {int(k): int(v) for k, v in zip(*np.unique(l2[te], return_counts=True))},
        "label2_train_min": int(np.min(np.bincount(l2[tr]))),
        "label2_train_max": int(np.max(np.bincount(l2[tr]))),
    }
    # imbalances
    counts = np.bincount(l2)
    stats["label2_imbalance_maxovermin"] = float(counts.max() / counts.min())
    with open(os.path.join(RESULTS_DIR, "data_stats.json"), "w") as fp:
        json.dump(stats, fp, indent=2)

    # confusion analysis on predictions
    d = np.load(os.path.join(RESULTS_DIR, "predictions.npz"),
                allow_pickle=False)
    t2, p2 = d["true_l2"], d["pred2"]
    from sklearn.metrics import confusion_matrix
    conf = confusion_matrix(t2, p2, labels=list(range(N_L2)))
    pairs = []
    for i in range(N_L2):
        for j in range(N_L2):
            if i != j and conf[i, j] > 0:
                pairs.append((int(conf[i, j]), i, j))
    pairs.sort(reverse=True)
    top = pd.DataFrame([
        {"n_misclassified": c, "true_id": i, "true_class": LABEL2_NAMES[i],
         "pred_id": j, "pred_class": LABEL2_NAMES[j]}
        for c, i, j in pairs[:15]])
    top.to_csv(os.path.join(RESULTS_DIR, "confusion_top_pairs.csv"), index=False)

    acc_vs = pd.DataFrame({
        "class_id": list(range(N_L2)),
        "class_name": LABEL2_NAMES,
        "train_support": np.bincount(l2[tr], minlength=N_L2),
        "test_support": np.bincount(l2[te], minlength=N_L2),
        "test_accuracy": np.diag(conf) / np.maximum(np.bincount(t2, minlength=N_L2), 1),
    })
    acc_vs.to_csv(os.path.join(RESULTS_DIR, "accuracy_vs_support.csv"), index=False)
    print("[analysis] stats + confusion saved")
    print("top confusion pairs:")
    for _, r in top.head(5).iterrows():
        print(f"  {r['true_class']} -> {r['pred_class']}: {r['n_misclassified']}")


if __name__ == "__main__":
    main()