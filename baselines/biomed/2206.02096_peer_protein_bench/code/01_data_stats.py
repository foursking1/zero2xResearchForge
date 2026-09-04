"""Step 1 — Data assembly statistics on the frozen PEER Solubility data.

Writes: results/data_stats.json  (counts, positive ratio, length stats)
"""
import os
import numpy as np
import pandas as pd

from common import load_split, ensure_dir, save_json, AA2IDX

SEED = 2024
HERE = os.path.dirname(__file__)
RESULTS = ensure_dir(os.path.join(HERE, "..", "results"))


def main():
    np.random.seed(SEED)
    stats = {}
    split_all = {}
    for split in ["train", "valid", "test"]:
        df = load_split(split)
        lens = df["sequence"].str.len()
        pos = int(df["label"].sum())
        n = len(df)
        split_all[split] = {
            "n": n,
            "n_positive": pos,
            "n_negative": n - pos,
            "positive_ratio": float(pos / n),
            "len_min": int(lens.min()),
            "len_median": int(lens.median()),
            "len_mean": float(lens.mean()),
            "len_max": int(lens.max()),
            "unique_sequences": int(df["sequence"].nunique()),
            "len_quantiles": {
                "q10": int(np.percentile(lens, 10)),
                "q25": int(np.percentile(lens, 25)),
                "q50": int(np.percentile(lens, 50)),
                "q75": int(np.percentile(lens, 75)),
                "q90": int(np.percentile(lens, 90)),
                "q99": int(np.percentile(lens, 99)),
            },
        }
        # also keep the length array for the overall histogram only (train)
        if split == "train":
            stats["train_len_bins"] = {
                "{}-{}".format(a, b): int(((lens >= a) & (lens < b)).sum())
                for a, b in [(0, 100), (100, 200), (200, 300), (300, 400),
                             (400, 500), (500, 600), (600, 800), (800, 1201)]
            }
    stats["split"] = split_all

    # global length descriptor of the package (concatenation of all splits)
    all_lens = np.concatenate([load_split(s)["sequence"].str.len().values
                               for s in ["train", "valid", "test"]])
    stats["package_length_range"] = {
        "min": int(all_lens.min()),
        "median": int(np.median(all_lens)),
        "max": int(all_lens.max()),
    }

    save_json(stats, os.path.join(RESULTS, "data_stats.json"))
    print(json_dump(stats))

    # quick table view for the report
    print("\n=== summary ===")
    for s in ["train", "valid", "test"]:
        d = split_all[s]
        print(f"{s:6s} n={d['n']:7d}  pos={d['positive_ratio']*100:5.1f}%  "
              f"len min/med/max = {d['len_min']}/{d['len_median']}/{d['len_max']}")


def json_dump(o):
    import json
    return json.dumps(o, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()