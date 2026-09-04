"""Assemble results/evidence_table.csv and results/metrics.json.

Both are derived from the JSON results produced by stage1/2/3.  The CSV has
columns: metric, value, unit, specification.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np

import common
from separability import PAPER_FDR_TARGETS
from mlp_oracle import PAPER_MCC_TARGETS

RESULTS = Path(__file__).resolve().parents[1] / "results"


def load(name: str):
    with open(RESULTS / name) as fh:
        return json.load(fh)


def main() -> None:
    s1 = load("stage1_fdr_results.json")
    s2 = load("mlp_architecture_sweep.json")
    s3 = load("stage3_ablation_results.json")

    map0 = s3["sensor_0based_to_paper_label"]  # sensor_0 -> S1
    critA = s3["distributional_shift_ablation"]["criticality"]
    critB = s3["delta_fdr_ablation"]["class_criticality"]
    normA = s3["distributional_shift_ablation"]["normalized_f1_per_class"]

    def to_paper(sensor_key: str) -> str:
        return map0.get(sensor_key, sensor_key)

    rows = []
    def add(metric, value, unit="", spec=""):
        if isinstance(value, (np.floating, float)):
            # 6 significant figures keeps tiny values (e.g. F2 ~ 1e-9)
            # from being rounded to 0.0.
            value = float(f"{float(value):.6g}")
        elif isinstance(value, (np.integer, int)):
            value = int(value)
        rows.append([metric, value, unit, spec])

    # ---------- C01: FDR -----------------------------------------------
    add("fdr_raw_paper_vs_scissors", s1["pairwise_fdr_max_raw"]["paper_vs_scissors"],
        "", "max-aggregated FDR over 72 features (raw feature matrix)")
    add("fdr_raw_rock_vs_paper", s1["pairwise_fdr_max_raw"]["rock_vs_paper"], "", "")
    add("fdr_raw_rock_vs_scissors", s1["pairwise_fdr_max_raw"]["rock_vs_scissors"], "", "")
    for k, v in s1["fdr_normalized_divide_max"].items():
        add(f"fdr_norm_divide_max_{k}", v, "", "normalized = raw/max_raw")
    add("fdr_norm_selected_method", s1["selected_normalization"], "", "min MAE vs paper")
    add("fdr_norm_mae_vs_paper", s1["selected_normalization_mae"], "", "MAE vs paper targets")
    for k, v in s1["absolute_error_selected_vs_paper"].items():
        add(f"fdr_abs_error_vs_paper_{k}", v, "", f"paper target {PAPER_FDR_TARGETS[k]}")
    for k, v in s1["difficulty_ratio_vs_paper_scissors"].items():
        add(f"fdr_difficulty_ratio_{k}", v, "x", "normalized FDR ratio vs paper_vs_scissors")
    add("f2_overlap_volume_paper_vs_scissors", s1["f2_overlap_volume"]["paper_vs_scissors"], "", "lower=better")
    add("f2_overlap_volume_rock_vs_paper", s1["f2_overlap_volume"]["rock_vs_paper"], "", "")
    add("f2_overlap_volume_rock_vs_scissors", s1["f2_overlap_volume"]["rock_vs_scissors"], "", "")
    add("f3_max_feature_efficiency_paper_vs_scissors", s1["f3_max_feature_efficiency"]["paper_vs_scissors"], "", "higher=better")
    add("f3_max_feature_efficiency_rock_vs_paper", s1["f3_max_feature_efficiency"]["rock_vs_paper"], "", "")
    add("f3_max_feature_efficiency_rock_vs_scissors", s1["f3_max_feature_efficiency"]["rock_vs_scissors"], "", "")
    pp_mean = s1["per_participant_fdr_max_mean_std"]
    add("fdr_participant_mean_paper_vs_scissors", pp_mean["paper_vs_scissors"]["mean"], "", "mean of 10 per-participant max-FDR")
    add("fdr_participant_mean_rock_vs_paper", pp_mean["rock_vs_paper"]["mean"], "", "")
    add("fdr_participant_mean_rock_vs_scissors", pp_mean["rock_vs_scissors"]["mean"], "", "")

    # ---------- C02: MLP -------------------------------------------------
    best = s2["best_architecture"]
    add("mlp_best_architecture", best, "", "lowest MAE vs paper MCC")
    add("mlp_best_mae_vs_paper", s2["best_results"]["mae_vs_paper"], "", "mean abs error vs paper")
    mcc = s2["best_results"]["mean_pairwise_mcc"]
    mcc_std = s2["best_results"]["std_pairwise_mcc"]
    for k in PAPER_MCC_TARGETS:
        add(f"mlp_mcc_mean_{k}", mcc[k], "", f"GroupKFold 10-fold mean; paper={PAPER_MCC_TARGETS[k]}")
        add(f"mlp_mcc_std_{k}", mcc_std[k], "", "")
    for k in PAPER_MCC_TARGETS:
        add(f"mlp_mcc_abs_error_vs_paper_{k}",
            s2["best_results"]["absolute_error_vs_paper"][k] if "absolute_error_vs_paper" in s2["best_results"]
            else round(abs(mcc[k] - PAPER_MCC_TARGETS[k]), 6),
            "", f"paper target {PAPER_MCC_TARGETS[k]}")

    # ---------- C03: sensor ablation -------------------------------------
    # Metric A: distributional-shift FDR (paper Fig.5)
    for cname, crit in critA.items():
        top = [to_paper(s) for s in crit["top_3"]]
        bot = [to_paper(s) for s in crit["bottom_3"]]
        add(f"ablationA_shiftFDR_top3_{cname}", "+".join(top), "",
            "signal-level ablation; F1(baseline, ablated), top-3 sensors")
        add(f"ablationA_shiftFDR_bottom3_{cname}", "+".join(bot), "", "bottom-3 sensors")
    for cname, norm in normA.items():
        for s, v in norm.items():
            add(f"ablationA_normShiftFDR_{cname}_{to_paper(s)}", v, "",
                "per-class normalised distributional-shift FDR")
    # Metric B: delta pairwise FDR (max-agg) + mean-agg criticality
    for cname, crit in critB.items():
        top = [to_paper(s) for s in crit["top_3"]]
        bot = [to_paper(s) for s in crit["bottom_3"]]
        add(f"ablationB_deltaFDR_top3_{cname}", "+".join(top), "",
            "feature-level ablation; avg delta pairwise FDR, top-3")
        add(f"ablationB_deltaFDR_bottom3_{cname}", "+".join(bot), "", "bottom-3")
    critBm = s3["delta_fdr_ablation"]["class_criticality_mean"]
    for cname, crit in critBm.items():
        top = [to_paper(s) for s in crit["top_3"]]
        bot = [to_paper(s) for s in crit["bottom_3"]]
        add(f"ablationB_deltaFDRmean_top3_{cname}", "+".join(top), "",
            "mean-agg delta pairwise FDR, top-3 sensors")
        add(f"ablationB_deltaFDRmean_bottom3_{cname}", "+".join(bot), "", "bottom-3")

    # FDR-MCC correlation
    for pair, v in s3["correlation"]["per_pair"].items():
        add(f"corr_fdr_mcc_r_{pair}", v["pearson_r"], "", "delta_FDR vs delta_MCC across 8 sensors")
        add(f"corr_fdr_mcc_p_{pair}", v["p_value"], "", "")
    ov = s3["correlation"]["overall_24_points"]
    add("corr_fdr_mcc_r_overall_24", ov["pearson_r"], "", "all 8 sensors x 3 pairs")
    add("corr_fdr_mcc_p_overall_24", ov["p_value"], "", "")

    # MLP seed robustness (if present)
    seed_path = RESULTS / "mlp_seed_robustness.json"
    if seed_path.exists():
        seed = json.loads(seed_path.read_text())
        for p, v in seed["mean_across_seeds"].items():
            add(f"mlp_mcc_seed_mean_{p}", v, "", "mean over 10 seeds, arch (64,)")
        for p, v in seed["std_across_seeds"].items():
            add(f"mlp_mcc_seed_std_{p}", v, "", "std over 10 seeds")

    # ---------- write ----------------------------------------------------
    RESULTS.mkdir(parents=True, exist_ok=True)
    with open(RESULTS / "evidence_table.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["metric", "value", "unit", "spec"])
        w.writerows(rows)

    metrics = {r[0]: r[1] for r in rows}
    with open(RESULTS / "metrics.json", "w") as fh:
        json.dump(metrics, fh, indent=2)

    print(f"wrote {len(rows)} metrics -> evidence_table.csv, metrics.json")


if __name__ == "__main__":
    main()
