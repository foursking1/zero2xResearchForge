"""Run all claim analyses and emit the evidence table + machine-readable metrics.

Produces in agent_solution/:
  results/c01_baseline.json
  results/c02_pca.json
  results/c03_shap.json
  results/c04_random_features.json
  results/c01_heatmap_concentration.json
  results/supplementary_parametric.json
  results/evidence_table.csv
  results/metrics.json
  results/figures/*.png
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402


def main():
    import analyze_baseline_c01
    import analyze_pca_c02
    import analyze_shap_c03
    import analyze_random_features_c04
    import analyze_heatmaps
    import analyze_supplementary

    c01 = analyze_baseline_c01.main()
    c02 = analyze_pca_c02.main()
    c03 = analyze_shap_c03.main()
    c04 = analyze_random_features_c04.main()
    c01_heat = analyze_heatmaps.main()
    supp = analyze_supplementary.main()

    # ------------------------------------------------------------------
    # Evidence table
    # ------------------------------------------------------------------
    rows = [
        # (claim, metric, value, unit/definition, verdict-contribution)
        ["C01", "Baseline ROC-AUC (reproduced, frozen)", c01["reproduced_roc_auc"],
         "ROC-AUC on baseline test set (frozen results/baseline/baseline_metrics.json)",
         "supported"],
        ["C01", "Baseline ROC-AUC (paper cited)", c01["paper_roc_auc_cited"],
         "paper Sec. 3.1 (citation only, not measured)", "reference"],
        ["C01", "ROC-AUC gap (reproduced - paper)", c01["roc_auc_gap_vs_paper"],
         "reproduced frozen value minus paper-cited 0.974", "context"],
        ["C01", "Attention KL vs uniform (last feature layer)", c01["attention_kl_vs_uniform"],
         "KL(P||uniform) of attention column mass, frozen baseline_metrics.json", "supported"],
        ["C01", "Attention KL > 0.2", c01["attention_structured_kl_gt_0_2"],
         "reproduction-plan pass criterion for structured attention", "supported"],
        ["C01", "Go/No-Go gate passed", c01["gate_passed"],
         "attention extraction feasibility gate", "context"],
        ["C01", "Heatmap panel 1 KL (pixel-derived)", c01_heat["panels"][0]["kl_vs_uniform"],
         "attention concentration of panel 1 from frozen heatmap PNG", "partial"],
        ["C01", "Heatmap panel 4 KL (pixel-derived)", c01_heat["panels"][3]["kl_vs_uniform"],
         "attention concentration of panel 4 from frozen heatmap PNG", "partial"],
        ["C01", "Heatmap concentration monotone increase", c01_heat["monotone_increase"],
         "KL non-decreasing from panel 1 to 4", "partial"],
        ["C02", "Frozen PCA/embedding artifacts found", c02["n_frozen_pca_embedding_artifacts"],
         "audit of results/ for PCA/embedding figures or data", "inconclusive"],
        ["C03", "SHAP informative-feature share", c03["shap_informative_share"],
         "fraction of normalized mean-|SHAP| on informative features {2,7}", "supported"],
        ["C03", "SHAP random-feature share", c03["shap_random_share"],
         "fraction of normalized mean-|SHAP| on the 6 random features", "supported"],
        ["C03", "SHAP informative/random per-feature ratio", c03["shap_informative_vs_random_ratio"],
         "mean per-feature |SHAP| informative divided by random", "supported"],
        ["C03", "Spearman(attention, SHAP)", c03["spearman_correlation"],
         "frozen shap_attention_comparison.json (attention uses group tokens)", "context"],
        ["C04", "ROC-AUC min over F=4..512", c04["roc_auc_stats"]["min"],
         "minimum ROC-AUC across 8 feature counts", "supported"],
        ["C04", "ROC-AUC max over F=4..512", c04["roc_auc_stats"]["max"],
         "maximum ROC-AUC across 8 feature counts", "supported"],
        ["C04", "ROC-AUC std over F=4..512", c04["roc_auc_stats"]["std"],
         "sample std of ROC-AUC across 8 feature counts", "supported"],
        ["C04", "ROC-AUC range over F=4..512", c04["roc_auc_stats"]["range"],
         "max - min ROC-AUC across feature counts", "supported"],
        ["C04", "ROC-AUC linear slope vs log10(F)", c04["roc_auc_stats"]["slope_per_log10_features"],
         "OLS slope of ROC-AUC against log10 number of features", "supported"],
        ["C04", "ROC-AUC trend p-value", c04["roc_auc_stats"]["linear_regression_p_value"],
         "p-value of the linear trend", "supported"],
        ["C04", "All ROC-AUC > 0.95 (F=4..512)", c04["roc_auc_stats"]["all_above_0_95"],
         "whether every feature count kept ROC-AUC above 0.95", "supported"],
        ["C04", "KL1 measured for F=4", c04["attention_metric_evidence"][0]["kl_vs_uniform"],
         "attention KL vs uniform at F=4 (only 2 configs have attention metrics)", "partial"],
        ["C04", "KL1 measured for F=8", c04["attention_metric_evidence"][1]["kl_vs_uniform"],
         "attention KL vs uniform at F=8", "partial"],
        ["C04", "Configs with attention metrics", c04["n_feature_counts_with_attention_metrics"],
         "number of feature counts (of 8) with frozen attention metrics", "partial"],
    ]

    header = ["claim_id", "metric", "value", "definition", "evidence_role"]
    with open(C.OUT_RESULTS / "evidence_table.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        for r in rows:
            w.writerow([str(x) for x in r])

    # ------------------------------------------------------------------
    # Machine-readable metrics (keys consistent with evidence_table.csv)
    # ------------------------------------------------------------------
    metrics = {
        "C01_baseline_roc_auc": c01["reproduced_roc_auc"],
        "C01_baseline_roc_auc_paper_cited": c01["paper_roc_auc_cited"],
        "C01_attention_kl_uniform_last_layer": c01["attention_kl_vs_uniform"],
        "C01_attention_structured": c01["attention_structured_kl_gt_0_2"],
        "C01_heatmap_kl_panel1": c01_heat["panels"][0]["kl_vs_uniform"],
        "C01_heatmap_kl_panel2": c01_heat["panels"][1]["kl_vs_uniform"],
        "C01_heatmap_kl_panel3": c01_heat["panels"][2]["kl_vs_uniform"],
        "C01_heatmap_kl_panel4": c01_heat["panels"][3]["kl_vs_uniform"],
        "C01_heatmap_monotone": c01_heat["monotone_increase"],
        "C02_n_frozen_pca_artifacts": c02["n_frozen_pca_embedding_artifacts"],
        "C03_shap_informative_share": c03["shap_informative_share"],
        "C03_shap_random_share": c03["shap_random_share"],
        "C03_shap_dominance_ratio": c03["shap_informative_vs_random_ratio"],
        "C04_roc_auc_min": c04["roc_auc_stats"]["min"],
        "C04_roc_auc_max": c04["roc_auc_stats"]["max"],
        "C04_roc_auc_std": c04["roc_auc_stats"]["std"],
        "C04_roc_auc_range": c04["roc_auc_stats"]["range"],
        "C04_roc_auc_slope_log10F": c04["roc_auc_stats"]["slope_per_log10_features"],
        "C04_roc_auc_trend_p": c04["roc_auc_stats"]["linear_regression_p_value"],
        "C04_all_auc_above_0.95": c04["roc_auc_stats"]["all_above_0_95"],
        "C04_n_configs_with_attention_metrics": c04["n_feature_counts_with_attention_metrics"],
        "verdicts": {
            "C01_roc_auc": "supported",
            "C01_attention_concentration": "partially_supported",
            "C02_pca_separation": "inconclusive",
            "C03_shap_dominance": c03["verdict"],
            "C04_random_features_roc": c04["verdict_roc_auc"],
            "C04_random_features_attention": c04["verdict_attention"],
        },
    }
    with open(C.OUT_RESULTS / "metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, default=str)

    print("\n=== Evidence table written to", C.OUT_RESULTS / "evidence_table.csv")
    print("=== Metrics written to", C.OUT_RESULTS / "metrics.json")


if __name__ == "__main__":
    main()
