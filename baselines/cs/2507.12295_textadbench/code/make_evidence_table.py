#!/usr/bin/env python3
"""Aggregate per-seed AUROC runs into the task's evidence table.

Inputs:  results/auroc_per_seed.json  (produced by run_experiment.py)
Outputs: results/evidence_table.csv  (columns:
         method, type, n_train, n_test, auroc(%), auroc_std, knn_rank,
         deep_max_minus_knn, paper_auroc)
"""
import argparse
import json
import os

import numpy as np

PAPER_ROW = {
    "knn": 93.96, "ae": 92.63, "dsvdd": 86.98, "dpad": 92.53,
    "iforest": 89.65, "ocsvm": 92.22, "lof": 91.47, "pca": 91.78,
    "kde": 92.14, "ecod": 85.26,
}

ORDER = ["knn", "ae", "dsvdd", "dpad", "iforest", "ocsvm", "lof", "pca", "kde", "ecod"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default="auroc_per_seed.json")
    ap.add_argument("--out", default="evidence_table.csv")
    args = ap.parse_args()

    full = []
    base = os.path.dirname(args.json) or "."
    per_method = sorted(
        fn for fn in os.listdir(base)
        if fn.startswith("auroc_") and fn.endswith(".json")
        and fn != "auroc_per_seed.json"
    )
    if per_method:
        for fn in per_method:
            with open(os.path.join(base, fn)) as f:
                full.append(json.load(f))
    elif os.path.isfile(args.json):
        with open(args.json) as f:
            full = json.load(f)
    full.sort(key=lambda r: r["method"])

    rows = {r["method"]: r for r in full}

    # rank KNN by AUROC among the reported methods (higher = better)
    methods_sorted = sorted(full, key=lambda m: rows[m]["mean"], reverse=True)
    knn_rank = methods_sorted.index("knn") + 1 if "knn" in rows else None

    deep_methods = [m for m in ["ae", "dsvdd", "dpad"] if m in rows]
    deep_max = max(rows[m]["mean"] for m in deep_methods) * 100.0 if deep_methods else float("nan")

    lines = ["method,type,n_train,n_test,auroc(%),auroc_std(%),knn_rank,deep_max_minus_knn(pp),paper_auroc(%)"]
    for m in ORDER:
        if m not in rows:
            continue
        r = rows[m]
        auroc_pct = r["mean"] * 100.0
        std_pct = r["std"] * 100.0
        dm_minus_knn = (deep_max - auroc_pct) if m == "knn" else ""
        lines.append(
            f"{m},{r['type']},{r['n_train']},{r['n_test']},{auroc_pct:.2f},"
            f"{std_pct:.2f},{knn_rank},{dm_minus_knn},{PAPER_ROW.get(m, '')}"
        )

    with open(args.out, "w", newline="") as f:
        f.write("\n".join(lines) + "\n")

    print("\n".join(lines))
    print(f"\nknn_rank = {knn_rank}  deep_max = {deep_max:.2f}%")

    meta = {
        "knn_rank": knn_rank,
        "deep_max_auroc": round(deep_max, 2) if deep_max == deep_max else None,
        "deep_max_minus_knn": round(deep_max - rows["knn"]["mean"] * 100.0, 2)
        if "knn" in rows and deep_max == deep_max else None,
    }
    with open(os.path.join(os.path.dirname(args.out), "summary_meta.json"), "w") as f:
        json.dump(meta, f, indent=2)


if __name__ == "__main__":
    main()