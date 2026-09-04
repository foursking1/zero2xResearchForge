"""Stage 1 (C01): FDR-based task complexity analysis on the frozen features.

Runs the one-vs-one FDR (max and mean aggregation), F2/F3 overlap metrics,
the FDR normalisation investigation and per-participant FDR.  Writes:
  results/stage1_fdr_results.json
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

import common
from separability import (analyze_separability, PAPER_FDR_TARGETS)

OUT_DIR = Path(__file__).resolve().parents[1] / "results"


def main() -> dict:
    F, Y, pids = common.load_features()
    assert F.shape[1] == 72 and F.shape[0] == 900

    # Also check the z-scored frozen features give a different FDR scaling.
    d = np.load(common.FEATURES_NORM_PATH, allow_pickle=True)
    F_z = np.asarray(d["X"], dtype=float)

    res = analyze_separability(F, Y, pids)
    res_z = analyze_separability(F_z, Y, None)

    # ---- assemble summary -------------------------------------------------
    norm_max = res["normalization_max"]
    summary = {
        "n_samples": int(len(Y)),
        "n_per_class": {common.CLASS_NAMES[c]: int(np.sum(Y == c))
                        for c in sorted(np.unique(Y))},
        "feature_dim": int(F.shape[1]),
        "pairwise_fdr_max_raw": res["pairwise_fdr_max_raw"],
        "pairwise_fdr_mean_raw": res["pairwise_fdr_mean_raw"],
        "fdr_normalized_divide_max": norm_max["divide_max"],
        "fdr_normalized_minmax": norm_max["minmax"],
        "fdr_normalized_cap_at_1": norm_max["cap_at_1"],
        "selected_normalization": norm_max["selected_method"],
        "selected_normalization_mae": norm_max[f"{norm_max['selected_method']}_mae"],
        "paper_targets": PAPER_FDR_TARGETS,
        "absolute_error_selected_vs_paper": {
            k: abs(round(norm_max["selected_values"][k] - PAPER_FDR_TARGETS[k], 6))
            for k in PAPER_FDR_TARGETS
        },
        "f2_overlap_volume": res["f2_overlap_volume"],
        "f3_max_feature_efficiency": res["f3_max_feature_efficiency"],
        "best_feature_per_pair": res["pairwise_fdr_best_feature"],
        "per_participant_fdr_max": res["per_participant_fdr_max"],
        "per_participant_fdr_max_mean_std": {
            p: {"mean": float(np.mean(list(v.values()))),
                "std": float(np.std(list(v.values())))}
            for p, v in res["per_participant_fdr_max"].items()
        },
        "zscored_note": "FDR computed on frozen z-scored features for comparison",
        "zscored_fdr_max_raw": res_z["pairwise_fdr_max_raw"],
        "zscored_normalization_divide_max": res_z["normalization_max"]["divide_max"],
    }

    # ratio supporting 'paper-vs-scissors >10x more difficult'
    rv = norm_max["selected_values"]
    summary["difficulty_ratio_vs_paper_scissors"] = {
        "paper_vs_scissors": 1.0,
        "rock_vs_paper": round(rv["rock_vs_paper"] / rv["paper_vs_scissors"], 2),
        "rock_vs_scissors": round(rv["rock_vs_scissors"] / rv["paper_vs_scissors"], 2),
    }

    out_path = OUT_DIR / "stage1_fdr_results.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as fh:
        json.dump(summary, fh, indent=2, default=float)

    print(json.dumps({
        "pairwise_fdr_max_raw": summary["pairwise_fdr_max_raw"],
        "normalized (selected=" + summary["selected_normalization"] + ")":
            summary["selected_values"] if False else norm_max["selected_values"],
        "difficulty_ratio": summary["difficulty_ratio_vs_paper_scissors"],
    }, indent=2, default=float))
    return summary


if __name__ == "__main__":
    main()
