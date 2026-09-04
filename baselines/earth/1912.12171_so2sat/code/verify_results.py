"""Fast verification: recompute all metrics from saved predictions + frozen labels.
This lets the judge re-derive OA/WA/AA/Kappa and the evidence table in seconds.

Usage:
  python code/verify_results.py                    # all configs in results/
  python code/verify_results.py --tag s2_l         # one config
"""
import argparse
import glob
import json
import os

import numpy as np

from metrics import compute_metrics

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RES = os.path.join(ROOT, "results")
DATA = os.path.join(ROOT, "data")
SEED = 42


def verify(tag):
    preds_path = os.path.join(RES, f"preds_{tag}.npy")
    if not os.path.exists(preds_path):
        print("missing", preds_path)
        return None
    preds = np.load(preds_path)
    labels = np.load(os.path.join(DATA, "val_y.npy"))
    assert labels.shape == preds.shape, f"{tag}: shape mismatch {labels.shape} vs {preds.shape}"
    bands = "s1s2" if "s1s2" in tag else ("s1" if tag.startswith("s1") else "s2")
    train_size = int(np.load(os.path.join(DATA, "train_y.npy")).shape[0])
    out_dir = os.path.join(RES, f"verify_{tag}")
    m, cm = compute_metrics(labels, preds, split="eval", bands=bands, seed=SEED,
                            train_size=train_size, out_dir=out_dir)
    return m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default=None)
    args = ap.parse_args()
    tags = [args.tag] if args.tag else sorted(
        f.split("preds_")[-1].replace(".npy", "")
        for f in glob.glob(os.path.join(RES, "preds_*.npy")))
    for t in tags:
        verify(t)


if __name__ == "__main__":
    main()