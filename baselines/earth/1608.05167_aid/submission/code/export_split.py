"""Export the fixed multi-label split indices (train/val/test) derived from the
frozen parquet + seed, so the exact split used is auditable without retraining.
Also appends the single-label-perspective top-1-in-ground-truth rate to metrics.
"""
import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from aid_common import FROZEN_PARQUET, SEED
from aid_pipeline import load_multilabel, split_isotropic


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default=os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "results"))
    args = ap.parse_args()

    images, labels = load_multilabel(FROZEN_PARQUET, verify=True)
    split = split_isotropic(images, labels, seed=SEED)
    out = {}
    for name, idx in split.items():
        out[name] = idx.tolist()
    with open(os.path.join(args.results, "split_indices.json"), "w") as f:
        json.dump({"seed": SEED, "split": out}, f, indent=1)

    # top-1-in-GT rate on the multi-label mirror test set
    z = np.load(os.path.join(args.results, "multilabel_test_preds.npz"))
    pred, true = z["pred"], z["true"]
    top1 = pred.argmax(1)
    top1_hit = float(np.mean([true[i, top1[i]] for i in range(len(true))]))
    mp = os.path.join(args.results, "metrics_multilabel.json")
    m = json.load(open(mp))
    m["top1_in_gt_test"] = round(top1_hit, 4)
    json.dump(m, open(os.path.join(args.results, "metrics_multilabel.json"), "w"),
              indent=2, ensure_ascii=False)
    print("split indices + top1-in-GT=%.4f exported" % top1_hit)


if __name__ == "__main__":
    main()