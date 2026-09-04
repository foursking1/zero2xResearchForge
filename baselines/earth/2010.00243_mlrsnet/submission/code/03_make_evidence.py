#!/usr/bin/env python3
"""03_make_evidence.py -- build the per-class evidence table and metrics.json
from stored test predictions (logits), the frozen split and frozen labels.

For each model tag with a test_logits npz under ../preds/ it recomputes:
  - per-class n_train (frozen split), n_test, n_correct(TP), precision,
    recall, f1, AP  at threshold=0.5
  - overall macro mAP, macro/micro/per-image F1
and writes submission/results/evidence_table_<tag>.csv +
submission/results/metrics_<tag>.json.

Use --tag for a single model or --tag ensemble (fused logits handled by
04_fuse.py).
"""
import argparse
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
from mlrs import CLASS_NAMES, DATA_WORK, PREDS, per_class_metrics

ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
RES = os.path.join(ROOT, "submission", "results")
os.makedirs(RES, exist_ok=True)


def load_logits(tag):
    z = np.load(os.path.join(PREDS, f"{tag}_test_logits.npz"))
    return z["logits"].astype(np.float32), z["labels"].astype(np.int8)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tags", nargs="*", default=None,
                    help="model tags to process; None -> all found + 'ensemble' if present")
    args = ap.parse_args()

    with open(os.path.join(DATA_WORK, "ds_summary.json")) as f:
        S = json.load(f)
    ntr = np.asarray(S["n_train_by_class"], dtype=int)
    nte = np.asarray(S["n_test_by_class"], dtype=int)

    tags = args.tags or []
    if not tags:
        tags = [f[:-len("_test_logits.npz")]
                for f in os.listdir(PREDS) if f.endswith("_test_logits.npz")]
    tags = sorted(set(tags))

    rows_out = []
    for tag in tags:
        path = os.path.join(PREDS, f"{tag}_test_logits.npz")
        if not os.path.exists(path):
            print(f"SKIP {tag}: {path} missing")
            continue
        logits, labels = load_logits(tag)
        scores = 1.0 / (1.0 + np.exp(-logits))
        cols, agg = per_class_metrics(labels, scores, threshold=0.5)

        df = pd.DataFrame([
            {
                "label": c["label"],
                "class_name": c["class_name"],
                "n_train": int(ntr[c["label"]]),
                "n_test": int(nte[c["label"]]),
                "n_correct": c["n_correct"],
                "precision": c["precision"],
                "recall": c["recall"],
                "f1": c["f1"],
                "ap": c["ap"],
            }
            for c in cols.values()
        ])
        overall = {
            "label": "ALL",
            "class_name": "ALL (60-class mean)",
            "n_train": int(ntr.sum()),
            "n_test": int(len(labels)),
            "n_correct": int((labels * (scores >= 0.5)).sum()),
            "precision": agg["micro_precision"],
            "recall": agg["micro_recall"],
            "f1": agg["macro_f1"],
            "ap": agg["mAP"],
        }
        df = pd.concat([df, pd.DataFrame([overall])], ignore_index=True)
        csv = os.path.join(RES, f"evidence_table_{tag}.csv")
        df.to_csv(csv, index=False)

        # sampled-class sanity dump (labels used by the judge sampler)
        sampled = {c: cols[c] for c in (0, 30, 59)}

        metrics = {
            "tag": tag,
            "mAP": agg["mAP"],
            "F1_macro": agg["macro_f1"],
            "F1_micro": agg["micro_f1"],
            "F1_per_image": agg["per_image_f1"],
            "macro_precision": agg["macro_precision"],
            "macro_recall": agg["macro_recall"],
            "micro_precision": agg["micro_precision"],
            "micro_recall": agg["micro_recall"],
            "threshold": 0.5,
            "n_test_total": int(len(labels)),
            "per_class": {f"{c['label']}": c for c in cols.values()},
            "anchor": {"paper_mAP_40pct_DenseNet201": 88.77,
                       "diff_pp": round((agg["mAP"] - 88.77) * 100, 4)},
        }
        with open(os.path.join(RES, f"metrics_{tag}.json"), "w") as f:
            json.dump(metrics, f, indent=1)

        print(f"=== {tag} ===")
        print(f"  test mAP={agg['mAP']:.4f}  macro_F1={agg['macro_f1']:.4f} "
              f"micro_F1={agg['micro_f1']:.4f} per_image_F1={agg['per_image_f1']:.4f}")
        print(f"  vs anchor 88.77: {((agg['mAP'] - 0.8877) * 100):+5.2f} pp")
        print(f"  sampled AP  label 0/30/59: "
              f"{cols[0]['ap']:.4f} / {cols[30]['ap']:.4f} / {cols[59]['ap']:.4f} "
              f"(n_test {nte[0]}/{nte[30]}/{nte[59]})")
        rows_out.append((tag, agg["mAP"], agg["macro_f1"]))

    print("\nSummary:")
    for t, m, f1 in sorted(rows_out, key=lambda r: -r[1]):
        print(f"  {t:<20} mAP={m:.4f}  macro_F1={f1:.4f}")


if __name__ == "__main__":
    main()