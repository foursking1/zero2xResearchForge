#!/usr/bin/env python3
"""Step 6 - Collect all experiment artifacts into results/metrics.json.

Aggregates annotation statistics, evidence table, and paper-anchor comparison
into a single machine-readable record including the conclusion label.
"""
from __future__ import annotations
import csv
import json
import os
import os.path as osp

res_dir = osp.join(osp.dirname(osp.abspath(__file__)), "..", "results")

with open(osp.join(res_dir, "annotations_stats.json")) as f:
    stats = json.load(f)
with open(osp.join(res_dir, "evidence_table.csv")) as f:
    table = list(csv.DictReader(f))
with open(osp.join(res_dir, "classifier_detail.json")) as f:
    detail = json.load(f)

models_with_both = {r["model"] for r in table if abs(float(r["data_fraction"]) - 1.0) < 1e-6} \
    & {r["model"] for r in table if abs(float(r["data_fraction"]) - 0.1) < 1e-6}
_both_rows = [r for r in table if r["model"] in models_with_both]
best_100 = max([r for r in _both_rows if abs(float(r["data_fraction"]) - 1.0) < 1e-6],
               key=lambda r: float(r["weighted_f1"]))
# same-model comparison for data efficiency
best_10 = max([r for r in _both_rows
               if r["model"] == best_100["model"] and abs(float(r["data_fraction"]) - 0.1) < 1e-6],
              key=lambda r: float(r["weighted_f1"]))
delta = float(best_100["weighted_f1"]) - float(best_10["weighted_f1"])

paper_anchor = {
    "midog2022_full": {
        "virchow2_LoRA_weighted_f1": "0.81 +/- 0.014", "paper_table": "Table 4",
        "virchow2_LoRA_balanced_acc": "0.80 +/- 0.022", "paper_table": "Table 4",
        "virchow2_LoRA_auroc": "0.89 +/- 0.011", "paper_table": "Table 4",
        "resnet50_e2e_weighted_f1": "0.78 +/- 0.010", "paper_table": "Table 4",
        "virchow2_linprobe_10pct_weighted_f1": "0.72", "paper_table": "Table 12",
        "dataset_mitotic": 9501, "dataset_hard_negative": 11051,
    },
}

conclusion_reasons = []
lo = float(best_100["weighted_f1"])
if 0.6 <= lo <= 0.9:
    A1 = "full"
    conclusion_reasons.append(f"best frozen subset F1={lo:.3f} in [0.6,0.9] band")
elif 0.5 <= lo < 0.6:
    A1 = "half"
    conclusion_reasons.append(f"best frozen subset F1={lo:.3f} in [0.5,0.6) band")
else:
    A1 = "low"
    conclusion_reasons.append(f"best frozen subset F1={lo:.3f}")

if delta <= 0.15:
    A2 = "full"
    conclusion_reasons.append(f"10%-vs-100% F1 gap={delta:.3f} <= 0.15")
else:
    A2 = "partial"
    conclusion_reasons.append(f"10%-vs-100% F1 gap={delta:.3f} > 0.15")

# conclusion on the *critical claim* tested here (data-efficiency + feasible classif.)
labels = ["supported", "partially_supported", "contradicted", "inconclusive"]
if A1 == "full" and A2 == "full":
    conclusion = "supported"
elif A1 in ("full", "half") or A2 == "full":
    conclusion = "partially_supported"
else:
    conclusion = "inconclusive"

metrics = {
    "task_id": "2508.04441_mitotic_benchmark",
    "paper": "Benchmarking Foundation Models for Mitotic Figure Classification (arXiv:2508.04441)",
    "conclusion_label": conclusion,
    "conclusion_reasons": conclusion_reasons,
    "subset_statistics": {
        "images": ["002.png", "008.png", "024.png", "063.png"],
        "mitotic_figures": stats["subset_mitotic"],
        "hard_negative": stats["subset_hard_negative"],
        "total_annotations": stats["subset_total_annotations"],
        "per_image": {
            n: {"mitotic": stats["per_image_mitotic"][n],
                "hard_negative": stats["per_image_hard_negative"][n]}
            for n in ("002.png", "008.png", "024.png", "063.png")
        },
        "image_sizes_px": stats["image_sizes_px"],
        "patch_size_px": stats["patch_size_px"],
        "relationship_to_full": (
            "frozen subset = 4 of 405 training WSI (0.75% of the 9501+11051 "
            "annotated figures); full dataset counts per official JSON seen below"),
        "full_dataset_mitotic": stats["full_dataset_mitotic"],
        "full_dataset_hard_negative": stats["full_dataset_hard_negative"],
        "validation": stats["validation"],
    },
    "evidence_table": table,
    "best_model_100pct": {
        "model": best_100["model"], "balanced_acc": best_100["balanced_acc"],
        "weighted_f1": best_100["weighted_f1"], "auroc": best_100["auroc"],
    },
    "best_model_10pct": {
        "model": best_10["model"], "balanced_acc": best_10["balanced_acc"],
        "weighted_f1": best_10["weighted_f1"], "auroc": best_10["auroc"],
    },
    "data_efficiency": {
        "f1_gap_10_vs_100": round(delta, 4),
        "within_rubric_bound_0_15": bool(delta <= 0.15),
    },
    "classifier_detail": detail,
    "paper_anchor": paper_anchor,
    "environment": {
        "encoder_weights": ["torchvision ResNet18 IMAGENET1K_V1",
                            "torchvision ViT-B/16 IMAGENET1K_V1"],
        "pathology_foundation_models": "not available offline; ImageNet encoders used",
        "device": "feature extraction on CUDA, classifiers on CPU",
        "reproducibility": "fixed seeds (see code/03/05); pipeline fully re-runnable",
    },
}

with open(osp.join(res_dir, "metrics.json"), "w") as f:
    json.dump(metrics, f, indent=2, ensure_ascii=False)
print("wrote", osp.join(res_dir, "metrics.json"))
print("conclusion:", conclusion, "-", "; ".join(conclusion_reasons))