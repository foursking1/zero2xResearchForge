"""Stage 2 (C02): MLP validation oracle (participant-aware GroupKFold).

Runs the architecture sweep, selects the best architecture, and reports
pairwise MCC for the three gesture pairs.  Writes:
  results/mlp_architecture_sweep.json
  results/per_participant_mcc.json
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

import common
from mlp_oracle import architecture_sweep, PAPER_MCC_TARGETS

OUT_DIR = Path(__file__).resolve().parents[1] / "results"


def main() -> dict:
    F, Y, pids = common.load_features()
    sweep = architecture_sweep(F, Y, pids)

    best = sweep["best_architecture"]
    best_res = sweep["best_results"]

    summary = {
        "best_architecture": best,
        "best_mae_vs_paper": best_res["mae_vs_paper"],
        "paper_mcc_targets": PAPER_MCC_TARGETS,
        "mean_pairwise_mcc": best_res["mean_pairwise_mcc"],
        "std_pairwise_mcc": best_res["std_pairwise_mcc"],
        "overall_pairwise_mcc": best_res["overall_pairwise_mcc"],
        "absolute_error_vs_paper": {
            k: round(abs(best_res["mean_pairwise_mcc"][k] - PAPER_MCC_TARGETS[k]), 6)
            for k in PAPER_MCC_TARGETS
        },
        "per_architecture_mean_pairwise_mcc": {
            arch: res["mean_pairwise_mcc"] for arch, res in sweep["architectures"].items()
        },
        "per_architecture_mae": {
            arch: res["mae_vs_paper"] for arch, res in sweep["architectures"].items()
        },
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUT_DIR / "mlp_architecture_sweep.json", "w") as fh:
        json.dump(sweep, fh, indent=2, default=float)
    with open(OUT_DIR / "per_participant_mcc.json", "w") as fh:
        json.dump(best_res["fold_results"], fh, indent=2, default=float)

    print(json.dumps(summary, indent=2, default=float))
    return summary


if __name__ == "__main__":
    main()
