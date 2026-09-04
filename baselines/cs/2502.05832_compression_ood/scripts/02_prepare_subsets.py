#!/usr/bin/env python3
"""02_prepare_subsets.py — build balanced / long-tail imbalanced CIFAR-10 subsets
for N in {10, 50, 100}, equal total = 10N, fixed reproducible seeds.

Outputs:
  results/subsets_summary.json        per-(N, seed, config) per-class counts + totals
  results/per_class_counts.csv        the same as a table
  models/subsets_<seed>.npz           index arrays (evidence for reproducibility)
No test-batch data is read or written here.
"""
import json
import os
import sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (build_subsets, META, NUM_CLASSES, SUBSET_SEEDS, get_data_dir,
                    load_frozen_cifar10)

N_VALUES = [10, 50, 100]


def main():
    out_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    res_dir = os.path.join(out_root, "results")
    model_dir = os.path.join(out_root, "models")
    os.makedirs(res_dir, exist_ok=True)
    os.makedirs(model_dir, exist_ok=True)

    data = load_frozen_cifar10(train_only=True)
    subsets = build_subsets(N_VALUES, data=data)

    rows = []
    for s in subsets:
        N, seed = s["N"], s["seed"]
        for config, sizes, idx in [("balanced", s["balanced_sizes"], s["balanced_idx"]),
                                    ("imbalanced", s["imbalanced_sizes"], s["imbalanced_idx"])]:
            row = {
                "N": N, "seed": seed, "config": config,
                "total": int(len(idx)),
                "majority_class": int(sizes[0]),
                "minority_class": int(sizes[-1]),
                "imbalance_ratio_eff": round(sizes[0] / sizes[-1], 2),
            }
            for c, m in enumerate(META):
                row[f"n_{c}_{m}"] = int(sizes[c])
            rows.append(row)
            if seed == SUBSET_SEEDS[0]:
                np.savez_compressed(os.path.join(model_dir, f"subsets_{config}_N{N}.npz"),
                                    idx=idx, sizes=np.asarray(sizes, dtype=np.int64),
                                    seed=seed)

    # evidence: primary seed (42) per-class counts as a clean table
    import csv
    with open(os.path.join(res_dir, "per_class_counts.csv"), "w", newline="") as f:
        w = csv.writer(f)
        hdr = ["N", "config", "total"] + [f"{i}_{m}" for i, m in enumerate(META)]
        w.writerow(hdr)
        for r in rows:
            if r["seed"] != SUBSET_SEEDS[0]:
                continue
            w.writerow([r["N"], r["config"], r["total"]] +
                       [r[f"n_{i}_{m}"] for i, m in enumerate(META)])

    with open(os.path.join(res_dir, "subsets_summary.json"), "w") as f:
        json.dump({"n_values": N_VALUES, "subset_seeds": SUBSET_SEEDS,
                   "protocol": ("balanced: N per class; imbalanced: long-tail ratio 100, "
                                "equal total 10N, floor 1/class"),
                   "subsets": rows}, f, indent=2)
    print(f"[subsets] wrote {len(rows)} config rows")
    for r in rows:
        if r["seed"] == SUBSET_SEEDS[0]:
            sizes = [r[f"n_{i}_{m}"] for i, m in enumerate(META)]
            print(f"  N={r['N']:3d} {r['config']:9s} total={r['total']:4d} "
                  f"sizes={sizes}  eff_ratio={r['imbalance_ratio_eff']}")


if __name__ == "__main__":
    main()