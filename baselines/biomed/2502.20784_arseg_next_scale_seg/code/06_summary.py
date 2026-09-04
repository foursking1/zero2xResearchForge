#!/usr/bin/env python3
"""Assemble results/evidence_table.csv + results/metrics.json (+ anchor deltas, conclusion)."""
from __future__ import annotations
import os, sys, json
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RES = os.path.join(ROOT, "results")

PAPER_ANCHORS = {
    "lidc_soft_dice_arseg": {"value": 0.658, "origin": "Table 1 (16 samples)"},
    "lidc_soft_dice_berdiff": {"value": 0.644, "origin": "Table 1"},
    "brats_dice_arseg": {"value": 86.97, "origin": "Table 2"},
    "brats_dice_nnunet": {"value": 84.57, "origin": "Table 2"},
}


def load_json(path):
    with open(path) as f:
        return json.load(f)


def main():
    rows = []
    dbase = load_json(os.path.join(RES, "lidc", "unet_baseline.json"))
    dar = load_json(os.path.join(RES, "lidc", "arseg_nextscale.json"))
    # BraTS primary protocol = binary WT (04b); 4-class (04) kept as auxiliary analysis
    bbase = load_json(os.path.join(RES, "brats", "unet_baseline_wt.json"))
    bar = load_json(os.path.join(RES, "brats", "arseg_nextscale_wt.json"))
    b4_base = load_json(os.path.join(RES, "brats", "unet_baseline.json"))
    b4_ar = load_json(os.path.join(RES, "brats", "arseg_nextscale.json"))

    def add(model, dataset, metric, value):
        rows.append({"model": model, "dataset": dataset, "metric": metric,
                     "value": round(float(value), 4)})

    # --- LIDC (Soft-Dice primary; also hard Dice + IoU; single-pass + consensus) ---
    for tag in ("single", "consensus_k8"):
        add("unet_baseline", "LIDC", f"soft_dice_{tag}", dbase["test"][tag]["soft_dice"])
        add("unet_baseline", "LIDC", f"hard_dice_{tag}", dbase["test"][tag]["hard_dice"])
        add("unet_baseline", "LIDC", f"iou_{tag}", dbase["test"][tag]["iou"])
        add("arseg_nextscale", "LIDC", f"soft_dice_{tag}", dar["test"][tag]["soft_dice"])
        add("arseg_nextscale", "LIDC", f"hard_dice_{tag}", dar["test"][tag]["hard_dice"])
        add("arseg_nextscale", "LIDC", f"iou_{tag}", dar["test"][tag]["iou"])
    add("unet_baseline", "LIDC", "test_patches", dbase["test_patches"])
    add("arseg_nextscale", "LIDC", "test_patches", dar["test_patches"])

    # --- BraTS primary protocol: binary Whole-Tumor ---
    for tag in ("single", "consensus_k8"):
        add("unet_baseline", "BraTS2021_mini", f"WT_soft_dice_{tag}",
            bbase["test"][tag]["soft_dice"])
        add("unet_baseline", "BraTS2021_mini", f"WT_hard_dice_{tag}",
            bbase["test"][tag]["hard_dice"])
        add("unet_baseline", "BraTS2021_mini", f"WT_iou_{tag}",
            bbase["test"][tag]["iou"])
        add("arseg_nextscale", "BraTS2021_mini", f"WT_soft_dice_{tag}",
            bar["test"][tag]["soft_dice"])
        add("arseg_nextscale", "BraTS2021_mini", f"WT_hard_dice_{tag}",
            bar["test"][tag]["hard_dice"])
        add("arseg_nextscale", "BraTS2021_mini", f"WT_iou_{tag}",
            bar["test"][tag]["iou"])
    add("unet_baseline", "BraTS2021_mini", "test_slices", bbase["test_slices"])
    add("arseg_nextscale", "BraTS2021_mini", "test_slices", bar["test_slices"])
    # --- BraTS auxiliary 4-class analysis (ET/TC/WT region Dice x100) ---
    for tag in ("single", "consensus_k8"):
        add("unet_baseline", "BraTS2021_mini_4class", f"dice_mean_region_{tag}",
            b4_base["test"][tag]["mean_region_dice"] * 100)
        add("unet_baseline", "BraTS2021_mini_4class", f"dice_et_{tag}",
            b4_base["test"][tag]["dice_et"] * 100)
        add("unet_baseline", "BraTS2021_mini_4class", f"dice_tc_{tag}",
            b4_base["test"][tag]["dice_tc"] * 100)
        add("unet_baseline", "BraTS2021_mini_4class", f"dice_wt_{tag}",
            b4_base["test"][tag]["dice_wt"] * 100)
        add("arseg_nextscale", "BraTS2021_mini_4class", f"dice_mean_region_{tag}",
            b4_ar["test"][tag]["mean_region_dice"] * 100)
        add("arseg_nextscale", "BraTS2021_mini_4class", f"dice_et_{tag}",
            b4_ar["test"][tag]["dice_et"] * 100)
        add("arseg_nextscale", "BraTS2021_mini_4class", f"dice_tc_{tag}",
            b4_ar["test"][tag]["dice_tc"] * 100)
        add("arseg_nextscale", "BraTS2021_mini_4class", f"dice_wt_{tag}",
            b4_ar["test"][tag]["dice_wt"] * 100)

    ev = pd.DataFrame(rows)
    ev.to_csv(os.path.join(RES, "evidence_table.csv"), index=False)

    # ---- metrics.json ----
    lidc_ar_sd = dar["test"]["single"]["soft_dice"]
    lidc_base_sd = dbase["test"]["single"]["soft_dice"]
    brats_ar = bar["test"]["single"]["hard_dice"] * 100
    brats_base = bbase["test"]["single"]["hard_dice"] * 100

    anchor_compare = {
        "LIDC_SoftDice_vs_paper_AR-Seg_0.658": {
            "ours_ARstyle_single": round(lidc_ar_sd, 4),
            "abs_diff": round(lidc_ar_sd - 0.658, 4),
            "rel_diff_pct": round((lidc_ar_sd - 0.658) / 0.658 * 100, 2),
            "note": "protocol differs (pseudo-mask, deterministic, subset); used for context only",
        },
        "LIDC_SoftDice_vs_paper_BerDiff_0.644": {
            "ours_ARstyle_single": round(lidc_ar_sd, 4),
            "abs_diff": round(lidc_ar_sd - 0.644, 4),
        },
        "BraTS_WT_hardDice_vs_paper_AR-Seg_meanDice_86.97": {
            "ours_ARstyle_WT_hardDice_pct": round(brats_ar, 2),
            "abs_diff_pts": round(brats_ar - 86.97, 2),
            "note": "2D binary-WT on 10-case single-modality mini vs full 4-modality BraTS2021; "
                    "metric/protocol differ, context only",
        },
        "BraTS_WT_hardDice_vs_paper_nnU-Net_meanDice_84.57": {
            "ours_baseline_WT_hardDice_pct": round(brats_base, 2),
            "abs_diff_pts": round(brats_base - 84.57, 2),
        },
    }

    # ---- conclusion logic ----
    nsup_p = os.path.join(RES, "lidc", "arseg_noscale_sup.json")
    nsup = load_json(nsup_p) if os.path.exists(nsup_p) else None

    mech_supported = (lidc_ar_sd >= lidc_base_sd) and (brats_ar >= brats_base)
    # AR > baseline on both datasets -> mechanism direction agrees with paper
    if mech_supported:
        conclusion = "partially_supported"
        rationale = ("Both simplified protocols reproduce the sign of the paper's central "
                     "claim (AR-style multi-scale/next-scale model >= single-scale baseline on "
                     "the same fixed protocol), but on frozen subsets / simplified 2D protocol / "
                     "pseudo-masks, with absolute numbers far from the paper's full-scale values; "
                     "a full AR-Seg (tokenized next-scale transformer + consensus over many samples) "
                     "was not reproduced, so the exact quantitative claims are not verified.")
    else:
        conclusion = "inconclusive"
        rationale = ("mechanism gain not reproduced on the simplified protocols; see report")

    metrics = {
        "task": "2502.20784_arseg_next_scale_seg",
        "conclusion": conclusion,
        "rationale": rationale,
        "sample_stats": {
            "LIDC": {"patches_total": 40187, "patients": 875, "clusters": 2651,
                     "train_patches": 12000, "val_patches": 6334, "test_patches": 5583,
                     "relation_to_full": "frozen mirror covers 875 of 1,018 LIDC-IDRI subjects",
                     "pseudo_mask": True},
            "BraTS2021_mini": {"cases": 10, "slices_test": 132, "train_slices": 427,
                               "val_slices": 61, "test_slices": 132,
                               "relation_to_full": "10 of 1,251 BraTS2021 subjects, single modality",
                               "primary_protocol": "binary Whole-Tumor",
                               "auxiliary_protocol": "4-class ET/TC/WT"},
        },
        "results": {
            "LIDC": {
                "unet_baseline": {k: round(v, 4) for k, v in dbase["test"]["single"].items()},
                "arseg_nextscale": {k: round(v, 4) for k, v in dar["test"]["single"].items()},
                "arseg_consensus_k8": {k: round(v, 4) for k, v in dar["test"]["consensus_k8"].items()},
            },
            "BraTS2021_mini_WT": {
                "unet_baseline": {k: round(v, 4) for k, v in bbase["test"]["single"].items()},
                "arseg_nextscale": {k: round(v, 4) for k, v in bar["test"]["single"].items()},
                "arseg_consensus_k8": {k: round(v, 4) for k, v in bar["test"]["consensus_k8"].items()},
                "patient_pooled_soft_dice": {
                    "baseline": bbase.get("test_patient_pooled_soft_dice", {}),
                    "arseg": bar.get("test_patient_pooled_soft_dice", {})},
            },
            "BraTS2021_mini_4class_aux": {
                "unet_baseline": {k: (round(v * 100, 2) if k.startswith("dice") else v)
                                  for k, v in b4_base["test"]["single"].items()},
                "arseg_nextscale": {k: (round(v * 100, 2) if k.startswith("dice") else v)
                                    for k, v in b4_ar["test"]["single"].items()},
            },
        },
        "mechanism_ablation": {
            "arseg_noscale_sup": None if nsup is None else {
                "test_single": {k: round(v, 4) for k, v in nsup["test"]["single"].items()}},
            "nextscale_conditioning_ablation_path": "evidence/nextscale_ablation.json",
            "consensus_analysis_path": "evidence/consensus_analysis.json",
        },
        "anchor_comparison": anchor_compare,
        "paper_anchors": PAPER_ANCHORS,
        "train_time_s": {
            "LIDC_unet_baseline": dbase["train_time_s"], "LIDC_arseg": dar["train_time_s"],
            "BraTS_unet_baseline": bbase["train_time_s"], "BraTS_arseg": bar["train_time_s"],
        },
        "best_epoch": {"LIDC_base": dbase["best_epoch"], "LIDC_ar": dar["best_epoch"],
                       "BraTS_base": bbase["best_epoch"], "BraTS_ar": bar["best_epoch"]},
    }
    with open(os.path.join(RES, "metrics.json"), "w") as f:
        json.dump(metrics, f, indent=2)
    print("wrote evidence_table.csv (%d rows) and metrics.json" % len(ev))
    print("LIDC  AR-style soft_dice=%.4f vs baseline %.4f" % (lidc_ar_sd, lidc_base_sd))
    print("BraTS AR-style meanDice=%.2f vs baseline %.2f" % (brats_ar, brats_base))
    print("conclusion:", conclusion)


if __name__ == "__main__":
    main()