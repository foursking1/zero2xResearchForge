#!/usr/bin/env python3
"""04_fuse.py -- average logits (in logit space, or probability space) of
several trained models on the frozen test split, then evaluate the ensemble.

Usage:
    python3 04_fuse.py --tags tagA tagB [--outtag ensemble] [--space logit|prob]
"""
import argparse
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
from mlrs import DATA_WORK, PREDS, per_class_metrics

ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
RES = os.path.join(ROOT, "submission", "results")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tags", nargs="+", required=True)
    ap.add_argument("--outtag", default="ensemble")
    ap.add_argument("--space", choices=["logit", "prob"], default="logit")
    args = ap.parse_args()

    acc = None
    labels_ref = None
    for t in args.tags:
        z = np.load(os.path.join(PREDS, f"{t}_test_logits.npz"))
        l = z["logits"].astype(np.float32)
        assert np.all(z["labels"] == z["labels"]), "labels mismatch across models"
        if labels_ref is None:
            labels_ref = z["labels"].astype(np.int8)
        acc = l if acc is None else acc + l
    mean_logit = acc / len(args.tags)
    if args.space == "prob":
        p1 = 1.0 / (1.0 + np.exp(-mean_logit))
        # un-average in prob space: back out to mean-prob logit
        p1 = np.clip(p1, 1e-7, 1 - 1e-7)
        mean_logit = np.log(p1 / (1 - p1))
    np.savez_compressed(os.path.join(PREDS, f"{args.outtag}_test_logits.npz"),
                        logits=mean_logit.astype(np.float16), labels=labels_ref,
                        members=args.tags, space=args.space)

    scores = 1.0 / (1.0 + np.exp(-mean_logit))
    cols, agg = per_class_metrics(labels_ref, scores, 0.5)
    print(f"ensemble {args.tags} in {args.space}-space:")
    print(f"  test mAP={agg['mAP']:.4f} macro_F1={agg['macro_f1']:.4f} "
          f"micro_F1={agg['micro_f1']:.4f} per_image_F1={agg['per_image_f1']:.4f}")


if __name__ == "__main__":
    main()