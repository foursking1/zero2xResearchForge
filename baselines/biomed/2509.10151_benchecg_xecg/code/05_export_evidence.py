#!/usr/bin/env python3
"""Step 5 - export the evidence artefacts expected by the rubric:

  - results/evidence_table.csv   (columns: model, metric, value[, std, n_runs])
  - results/metrics.json         (label statistics, model metrics, anchor deltas,
                                  conclusion tag)

Everything here is (re)computed by the preceding scripts; this script only
aggregates them. The AUROC / F1 rows that are directly comparable to the paper
anchors are reported as missing-NaN on purpose, with an explicit reason, because
the frozen parquet contains no diagnostic label column.
"""
import csv
import json
import os
import sys

import numpy as np

RESULTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")


def load_mm():
    return json.load(open(os.path.join(RESULTS, "model_metrics.json")))


def load_audit():
    return json.load(open(os.path.join(RESULTS, "data_audit.json")))


def load_pp():
    return json.load(open(os.path.join(RESULTS, "preprocessing.json")))


def main():
    mm = load_mm()
    audit = load_audit()
    pp = load_pp()
    cnn = mm["cnn_seed_summary"]

    # paper-anchor diagnostics are not computable from the frozen data (no labels);
    # the evidence table therefore reports the reproducible auxiliary-task metrics
    # and explicitly marks the non-computable anchor rows.
    aux_metrics = [
        ("cnn_multitask", "macro_auroc", cnn["macro_auroc"]["mean"], cnn["macro_auroc"]["std"], 3),
        ("cnn_multitask", "macro_f1@0.5", cnn["macro_f1@0.5"]["mean"], cnn["macro_f1@0.5"]["std"], 3),
        ("cnn_multitask", "sex_auroc", cnn["sex:auroc"]["mean"], cnn["sex:auroc"]["std"], 3),
        ("cnn_multitask", "age_ge65_auroc", cnn["age_ge65:auroc"]["mean"], cnn["age_ge65:auroc"]["std"], 3),
        ("logreg_manual_feats", "macro_auroc", mm["results"]["logreg_manual_feats"]["macro_auroc"], None, 1),
        ("logreg_manual_feats", "macro_f1@0.5", mm["results"]["logreg_manual_feats"]["macro_f1@0.5"], None, 1),
    ]

    header = ["model", "metric", "value", "std", "n_runs"]
    path = os.path.join(RESULTS, "evidence_table.csv")
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        for model, metric, value, std, n in aux_metrics:
            w.writerow([model, metric, value, std, n])
        for model, metric in (
            ("xecg_paper_anchor", "macro_auroc (diagnostic SCP superclass)"),
            ("xecg_paper_anchor", "macro_f1 (diagnostic SCP superclass)"),
            ("stmem_paper_anchor", "macro_auroc (diagnostic SCP superclass)"),
            ("stmem_paper_anchor", "macro_f1 (diagnostic SCP superclass)"),
        ):
            w.writerow([model, metric, "NA (label column absent in frozen schema)", "", 0])
    print("wrote", path)

    conclusion = "inconclusive"
    metrics = {
        "data_stats": {
            "train_samples": audit["train"]["rows"],
            "validation_samples": audit["validation"]["rows"],
            "total_samples": audit["total_records"],
            "leads": 12,
            "samples_per_lead_native": audit["train"]["signal_array_shape"][1],
            "native_fs_hz": 500,
            "target_fs_hz": pp["preprocessing"]["target_fs"],
            "label_columns_present_in_frozen_schema": False,
            "available_label_columns": audit["train"]["label_like_columns_found"],
            "diagnostic_superclass_targets": "absent",
            "auxiliary_targets_and_positive_counts": pp["label_stats_for_evidence"],
        },
        "model_metrics": {
            "cnn_multitask_aux": {
                "macro_auroc": {"mean": cnn["macro_auroc"]["mean"], "std": cnn["macro_auroc"]["std"]},
                "macro_f1": {"mean": cnn["macro_f1@0.5"]["mean"], "std": cnn["macro_f1@0.5"]["std"]},
                "sex_auroc": {"mean": cnn["sex:auroc"]["mean"], "std": cnn["sex:auroc"]["std"]},
                "age_ge65_auroc": {"mean": cnn["age_ge65:auroc"]["mean"], "std": cnn["age_ge65:auroc"]["std"]},
            },
            "logreg_manual_feats_aux": {
                "macro_auroc": mm["results"]["logreg_manual_feats"]["macro_auroc"],
                "macro_f1": mm["results"]["logreg_manual_feats"]["macro_f1@0.5"],
            },
        },
        "anchor_comparison": {
            "xecg_ptbxl_auroc": 0.853, "xecg_ptbxl_f1": 0.674,
            "stmem_ptbxl_auroc": 0.702, "stmem_ptbxl_f1": 0.436,
            "measured_diagnostic_auroc": None,
            "measured_diagnostic_f1": None,
            "absolute_delta_xecg_vs_measured": None,
            "reason_not_computed": (
                "Frozen parquet has no diagnostic (SCP superclass) label column; "
                "supervised diagnostic classification and the xECG-vs-ST-MEM gap "
                "cannot be reproduced from the frozen package alone."
            ),
        },
        "conclusion_label": conclusion,
        "limitations": [
            "Frozen subset is 1000+1000 records (2,000 of 21,837 PTB-XL records) and has no diagnostic labels.",
            "Diagnostic macro-AUROC / macro-F1 anchors (xECG 0.853/0.674, ST-MEM 0.702/0.436) could not be recomputed - no labels.",
            "Auxiliary target metrics (sex, age>=65) only demonstrate the metric pipeline and depth/gap structure; they are not comparable to the diagnostic anchors.",
            "Submitted models are lightweight 1-D CNNs, not the paper's xLSTM+SimDINOv2 pretrained models.",
        ],
    }
    with open(os.path.join(RESULTS, "metrics.json"), "w") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)
    print("wrote", os.path.join(RESULTS, "metrics.json"))
    print("conclusion:", conclusion)


if __name__ == "__main__":
    main()