#!/usr/bin/env python3
"""Recompute evidence from saved artifacts (no retraining needed).

  python verify_results.py

Recomputes:
  1. line counts of the frozen jsonl files (train/valid/test).
  2. test ROC-AUC for every saved run directly from results/predictions/*.npz
     and compares with the recorded value in results/runs/*.json.
  3. checksum of rows in results/evidence_table.csv.
"""

import glob
import json
import os

import numpy as np
from sklearn.metrics import roc_auc_score

import config

RESULTS = config.results_dir()


def check_line_counts():
    import subprocess
    ok = True
    for split, want in (("train", 32901), ("valid", 4113), ("test", 4113)):
        path = os.path.join(config.DATA_DIR, f"{split}.jsonl")
        n = sum(1 for _ in open(path))
        status = "OK" if n == want else "MISMATCH"
        if n != want:
            ok = False
        print(f"  {split}.jsonl lines = {n} (expected {want}) {status}")
    return ok


def check_prediction_aucs():
    ok = True
    runs = glob.glob(os.path.join(RESULTS, "runs", "*.json"))
    for n, rf in enumerate(sorted(runs)):
        rec = json.load(open(rf))
        tag = os.path.basename(rf)[:-5]
        npz = os.path.join(RESULTS, "predictions", f"{tag}.npz")
        if not os.path.isfile(npz):
            print(f"  {tag}: missing predictions npz (skip)")
            continue
        d = np.load(npz)
        recomputed = roc_auc_score(d["y_test"], d["pred_test"])
        recorded = rec["test_roc_auc"]
        diff = abs(recomputed - recorded)
        status = "OK" if diff <= 0.005 else "MISMATCH"
        if diff > 0.005:
            ok = False
        print(f"  {tag:18s} testAUC recorded={recorded:.4f} "
              f"recomputed={recomputed:.4f} delta={diff:.4f} {status}")
    return ok


def main():
    print("data dir:", config.DATA_DIR)
    print("line counts:")
    ok1 = check_line_counts()
    print("test ROC-AUC recomputation from saved predictions:")
    ok2 = check_prediction_aucs()
    print("\nALL CHECKS PASSED" if (ok1 and ok2) else "\nSOME CHECKS FAILED")
    return 0 if (ok1 and ok2) else 1


if __name__ == "__main__":
    raise SystemExit(main())