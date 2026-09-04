#!/usr/bin/env python3
"""Class-difficulty & confusion analysis for the report (uses saved confusions)."""
import glob
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from evaluate import CLASS_NAMES, metrics_from_confusion


def main():
    results = os.path.abspath(os.path.join(os.path.dirname(__file__), "..",
                                           "results"))
    files = sorted(glob.glob(os.path.join(results, "preds_*.npz")))
    out_rows = []
    for f in files:
        d = np.load(f, allow_pickle=True)
        parts = os.path.basename(f).replace(".npz", "").split("_")
        ratio = float(parts[3].lstrip("r"))
        seed = int(parts[5].lstrip("s"))
        conf = d["confusion"]
        rows, _ = metrics_from_confusion(conf)
        for r in rows:
            r["train_ratio"] = ratio
            r["seed"] = seed
            out_rows.append(r)
    df = pd.DataFrame(out_rows)
    df.to_csv(os.path.join(results, "perclass_metrics_all_seeds.csv"), index=False)
    g = df.groupby(["train_ratio", "class_name"]).agg(
        recall_mean=("recall", "mean"), recall_std=("recall", "std"))
    g.to_csv(os.path.join(results, "perclass_recall_summary.csv"))
    print("Avg mean recall by ratio:")
    print(g.groupby("train_ratio").mean())
    # hardest classes per ratio (mean recall)
    for ratio in sorted(df.train_ratio.unique()):
        sub = df[df.train_ratio == ratio].groupby("class_name")["recall"].mean()
        worst = sub.sort_values().head(8)
        best = sub.sort_values(ascending=False).head(8)
        print("\nRatio %.2f worst 8:\n%s\nbest 8:\n%s" % (ratio, worst, best))
    # top confusions
    for f in files:
        d = np.load(f, allow_pickle=True)
        parts = os.path.basename(f).replace(".npz", "").split("_")
        ratio = float(parts[3].lstrip("r")); seed = int(parts[5].lstrip("s"))
        if ratio != 0.10 or seed != 20260813:
            continue
        conf = d["confusion"].astype(int)
        off = conf.copy(); np.fill_diagonal(off, 0)
        pairs = np.dstack(np.unravel_index(np.argsort(off, axis=None),
                                           off.shape))[0][::-1][:12]
        print("\nTop off-diagonal confusions (10%% run):")
        for (t, p) in pairs:
            if off[t, p] == 0:
                break
            print("  %-22s-> %-22s  %5d  (recall %.2f)" % (
                CLASS_NAMES[t], CLASS_NAMES[p], off[t, p],
                100 * off[t, p] / max(conf[t].sum(), 1)))
    print("\n[written] results/perclass_metrics_all_seeds.csv, "
          "perclass_recall_summary.csv")


if __name__ == "__main__":
    main()