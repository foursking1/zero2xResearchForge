"""Verify / recompute the headline metrics from saved evidence only (no retrain).

Reads evidence/predictions.npz (pred2/pred1, true_l2/true_l1) which was produced
by src/05_evaluate.py from the frozen parquet pipeline, and recomputes:
  - label_2 test overall accuracy
  - macro F1 (label_2)
  - label_1 accuracy
  - per-class precision/recall/F1 for a spot-check class

Exit code 0 and printed values matching results/metrics.json to <=0.5pp.
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import EVIDENCE_DIR, LABEL2_NAMES, N_L2, RESULTS_DIR  # noqa: E402
from sklearn.metrics import accuracy_score, f1_score, precision_recall_fscore_support  # noqa: E402


def main():
    p = os.path.join(EVIDENCE_DIR, "predictions.npz")
    d = np.load(p)
    pred2, pred1 = d["pred2"], d["pred1"]
    t2, t1 = d["true_l2"], d["true_l1"]

    oa = accuracy_score(t2, pred2)
    mf1 = f1_score(t2, pred2, average="macro", labels=list(range(N_L2)),
                   zero_division=0)
    l1a = accuracy_score(t1, pred1)
    ps, rs, fs, _ = precision_recall_fscore_support(
        t2, pred2, labels=list(range(N_L2)), zero_division=0)

    # spot-check class: the "highway" class (id 2), which is a known confusable one
    spot = {"class_id": 2, "name": LABEL2_NAMES[2],
            "precision": float(ps[2]), "recall": float(rs[2]),
            "f1": float(fs[2])}

    out = {
        "recomputed_overall_accuracy_label2": float(oa),
        "recomputed_macro_f1_label2": float(mf1),
        "recomputed_label1_accuracy": float(l1a),
        "spot_check": spot,
    }
    print(json.dumps(out, indent=2))

    # compare to stored metrics.json
    stored = json.load(open(os.path.join(RESULTS_DIR, "metrics.json")))
    err = abs(oa - stored["overall_accuracy"])
    print(f"delta vs metrics.json overall_accuracy: {err:.6f}")
    assert err <= 0.005, f"mismatch {err} > 0.005"
    print("VERIFY OK")


if __name__ == "__main__":
    main()