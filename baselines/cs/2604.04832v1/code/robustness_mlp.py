"""Robustness check: MLP MCC under multiple random seeds.

Re-runs the best architecture (64,) with 10 different seeds and reports
mean +/- std of the pairwise MCC (GroupKFold).  Writes
results/mlp_seed_robustness.json.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

import common
from mlp_oracle import group_kfold_mlp, PAPER_MCC_TARGETS

OUT_DIR = Path(__file__).resolve().parents[1] / "results"
SEEDS = [0, 1, 2, 3, 4, 5, 6, 7, 8, 42]


def main() -> dict:
    F, Y, pids = common.load_features()
    per_seed = {}
    pair_names = list(PAPER_MCC_TARGETS)
    for seed in SEEDS:
        res = group_kfold_mlp(F, Y, pids, hidden_layers=(64,),
                              random_state=seed)
        per_seed[str(seed)] = res["mean_pairwise_mcc"]
        print(f"  seed {seed:2d}: " + "  ".join(
            f"{p}={res['mean_pairwise_mcc'][p]:.4f}" for p in pair_names))

    summary = {
        "architecture": [64],
        "seeds": SEEDS,
        "per_seed_mean_pairwise_mcc": per_seed,
        "mean_across_seeds": {
            p: float(np.mean([per_seed[str(s)][p] for s in SEEDS]))
            for p in pair_names
        },
        "std_across_seeds": {
            p: float(np.std([per_seed[str(s)][p] for s in SEEDS]))
            for p in pair_names
        },
        "min_across_seeds": {
            p: float(np.min([per_seed[str(s)][p] for s in SEEDS]))
            for p in pair_names
        },
        "max_across_seeds": {
            p: float(np.max([per_seed[str(s)][p] for s in SEEDS]))
            for p in pair_names
        },
        "paper_targets": PAPER_MCC_TARGETS,
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUT_DIR / "mlp_seed_robustness.json", "w") as fh:
        json.dump(summary, fh, indent=2)
    print("\nmean across seeds:", {p: round(summary["mean_across_seeds"][p], 4)
                                   for p in pair_names})
    print("std across seeds :", {p: round(summary["std_across_seeds"][p], 4)
                                 for p in pair_names})
    return summary


if __name__ == "__main__":
    main()
