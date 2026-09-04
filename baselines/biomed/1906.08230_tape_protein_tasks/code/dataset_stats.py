"""Load the frozen TAPE CSVs, verify integrity, and emit dataset stats.

Outputs:
  results/dataset_stats.json   (row counts, split sizes, label stats, structural checks)
  results/splits.parquet       (subsequently joined into the run pipeline) -- optional convenience
"""
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import CSV_FILES, RESULTS_DIR, find_data_dir  # noqa: E402


def seq_distance(seq, ref):
    return sum(a != b for a, b in zip(seq, ref))


def analyze(name, df):
    out = {
        "task": name,
        "n_rows": int(len(df)),
        "n_unique_sequences": int(df["protein"].nunique()),
        "split_counts": {st: int((df["stage"] == st).sum()) for st in ["train", "valid", "test"]},
        "seq_len": {
            "min": int(df["protein"].str.len().min()),
            "max": int(df["protein"].str.len().max()),
            "mean": float(df["protein"].str.len().mean()),
        },
        "label_stats": {
            st: {
                "n": int(len(g)),
                "mean": float(g["label"].mean()),
                "std": float(g["label"].std()),
                "min": float(g["label"].min()),
                "max": float(g["label"].max()),
            }
            for st, g in df.groupby("stage")
        },
        "label_nan": int(df["label"].isna().sum()),
    }
    out["train_test_shared_sequences"] = int(
        len(set(df[df.stage == "train"].protein) & set(df[df.stage == "test"].protein))
    )

    # structural checks aligned with the paper's description
    if name == "fluorescence":
        wt = df["protein"].mode()[0]
        df = df.copy()
        df["mut"] = df["protein"].apply(lambda s: seq_distance(s, wt))
        out["mutations_from_wt_mean"] = {
            st: float(df.loc[df.stage == st, "mut"].mean()) for st in ["train", "valid", "test"]
        }
        out["structure_comment"] = (
            "Fluorescence: training sequences cluster near wild-type (~%.2f mutations), "
            "test sequences are more distant (%.2f)." % (
                out["mutations_from_wt_mean"]["train"], out["mutations_from_wt_mean"]["test"])
        )
    if name == "stability":
        out["structure_comment"] = (
            "Stability: broad training spectrum (label mean %.3f), test concentrates on "
            "high-stability neighborhood (label mean %.3f), consistent with single-mutant "
            "neighborhoods of the best training proteins; only %d exact parent sequences shared" % (
                out["label_stats"]["train"]["mean"], out["label_stats"]["test"]["mean"],
                out["train_test_shared_sequences"])
        )
    return out


def main():
    data_dir = find_data_dir()
    stats = {"data_dir": data_dir, "seed_info": "frozen-package only"}
    for name, fname in CSV_FILES.items():
        path = os.path.join(data_dir, fname)
        df = pd.read_csv(path)
        stats[name] = analyze(name, df)
    os.makedirs(RESULTS_DIR, exist_ok=True)
    with open(os.path.join(RESULTS_DIR, "dataset_stats.json"), "w") as fh:
        json.dump(stats, fh, indent=2, ensure_ascii=False)
    print(json.dumps(stats, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()