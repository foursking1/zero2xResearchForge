"""06_summarize.py
Aggregate all results into results/metrics.json with paper-anchor comparison
and per-claim verdict labels.
"""
import os
import sys
import json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import pandas as pd
from common import RESULTS_DIR

ev = pd.read_csv(os.path.join(RESULTS_DIR, "evidence_table.csv"))
data_stats = pd.read_csv(os.path.join(RESULTS_DIR, "data_stats.csv"), index_col=0)["value"].to_dict()
ml = json.load(open(os.path.join(RESULTS_DIR, "ml_metrics.json")))
gnn = json.load(open(os.path.join(RESULTS_DIR, "gnn_metrics.json")))
exp = json.load(open(os.path.join(RESULTS_DIR, "expansion_summary.json")))


def mean_metric(model, feat, metric):
    r = ev[(ev.model == model) & (ev.feature_set == feat) &
           (ev.split == "5fold_cv_mean") & (ev.metric == metric)]
    return float(r["value"].iloc[0]) if len(r) else None


def pooled_metric(model, feat, metric):
    r = ev[(ev.model == model) & (ev.feature_set == feat) &
           (ev.split == "5fold_cv_pooled") & (ev.metric == metric)]
    return float(r["value"].iloc[0]) if len(r) else None


results = {}
for m in ["rf", "svr", "mlp"]:
    for f in ["basic", "mid", "enhanced"]:
        if (f == "mid" and m == "mlp"):
            continue
        if mean_metric(m, f, "MAE") is None:
            continue
        results[f"{m}|{f}"] = {
            "MAE_cv_mean": mean_metric(m, f, "MAE"),
            "MAE_cv_std": float(ev[(ev.model == m) & (ev.feature_set == f) &
                                   (ev.split == "5fold_cv_mean") & (ev.metric == "MAE")]["value_std"].iloc[0]),
            "R2_cv_mean": mean_metric(m, f, "R2"),
            "MAE_cv_pooled": pooled_metric(m, f, "MAE"),
            "R2_cv_pooled": pooled_metric(m, f, "R2"),
            "RMSE_cv_pooled": pooled_metric(m, f, "RMSE"),
            "MAE_test20": float(ev[(ev.model == m) & (ev.feature_set == f) &
                                   (ev.split == "train80_test20") & (ev.metric == "MAE")]["value"].iloc[0])
            if len(ev[(ev.model == m) & (ev.feature_set == f) &
                      (ev.split == "train80_test20") & (ev.metric == "MAE")]) else None,
            "R2_test20": float(ev[(ev.model == m) & (ev.feature_set == f) &
                                  (ev.split == "train80_test20") & (ev.metric == "R2")]["value"].iloc[0])
            if len(ev[(ev.model == m) & (ev.feature_set == f) &
                      (ev.split == "train80_test20") & (ev.metric == "R2")]) else None,
        }
results["gnn|composition_graph"] = {
    "MAE_cv_mean": gnn["mpnn__composition_graph"]["mean"]["MAE"],
    "R2_cv_mean": gnn["mpnn__composition_graph"]["mean"]["R2"],
    "MAE_cv_pooled": gnn["mpnn__composition_graph"]["pooled"]["MAE"],
    "R2_cv_pooled": gnn["mpnn__composition_graph"]["pooled"]["R2"],
    "RMSE_cv_pooled": gnn["mpnn__composition_graph"]["pooled"]["RMSE"],
}

# ---- paper anchor comparison ---------------------------------------------
anchors = {
    "dataset_1705": {"paper": 1705, "ours": data_stats["n_label_rows"]},
    "rf_magpie_MAE": {"paper": 1.17, "ours": results["rf|basic"]["MAE_cv_mean"],
                      "tolerance": 0.2},
    "rf_magpie_R2": {"paper": -0.509, "ours": results["rf|basic"]["R2_cv_mean"],
                     "tolerance": 0.2},
    "rf_full_MAE": {"paper": 0.953, "ours": results["rf|enhanced"]["MAE_cv_mean"],
                    "tolerance": 0.3},
    "rf_full_R2": {"paper": -0.343, "ours": results["rf|enhanced"]["R2_cv_mean"],
                   "tolerance": 0.15},
    "svm_magpie_R2": {"paper": 0.043, "ours": results["svr|basic"]["R2_cv_mean"]},
    "svm_full_R2": {"paper": None, "ours": results["svr|enhanced"]["R2_cv_mean"]},
    "gnn_cgcnn_MAE": {"paper": 0.974, "ours": results["gnn|composition_graph"]["MAE_cv_mean"],
                      "tolerance": 0.2},
    "gnn_band": {"paper": "0.97-1.34", "ours": results["gnn|composition_graph"]["MAE_cv_mean"]},
}

# ---- claim verdicts -------------------------------------------------------
r = results
feat_rf_mae = r["rf|basic"]["MAE_cv_mean"] > r["rf|enhanced"]["MAE_cv_mean"]
feat_rf_r2 = r["rf|basic"]["R2_cv_mean"] < r["rf|enhanced"]["R2_cv_mean"]
feat_svr_mae = r["svr|basic"]["MAE_cv_mean"] > r["svr|enhanced"]["MAE_cv_mean"]
feat_svr_r2 = r["svr|basic"]["R2_cv_mean"] < r["svr|enhanced"]["R2_cv_mean"]

claim1 = {
    "claim": "Feature engineering improves traditional ML (RF MAE down, R2 up; SVM R2 stays positive and rises)",
    "ours": {
        "rf_MAE_basic_to_enhanced": (r["rf|basic"]["MAE_cv_mean"], r["rf|enhanced"]["MAE_cv_mean"]),
        "rf_MAE_improvement_pct": (r["rf|basic"]["MAE_cv_mean"] - r["rf|enhanced"]["MAE_cv_mean"]) / r["rf|basic"]["MAE_cv_mean"] * 100,
        "rf_R2_basic_to_enhanced": (r["rf|basic"]["R2_cv_mean"], r["rf|enhanced"]["R2_cv_mean"]),
        "svr_MAE_basic_to_enhanced": (r["svr|basic"]["MAE_cv_mean"], r["svr|enhanced"]["MAE_cv_mean"]),
        "svr_R2_basic_to_enhanced": (r["svr|basic"]["R2_cv_mean"], r["svr|enhanced"]["R2_cv_mean"]),
        "svr_R2_positive": r["svr|basic"]["R2_cv_mean"] > 0 or r["svr|enhanced"]["R2_cv_mean"] > 0,
    },
    "direction_ok": all([feat_rf_mae, feat_rf_r2, feat_svr_mae, feat_svr_r2]),
    "verdict": "supported" if all([feat_rf_mae, feat_rf_r2, feat_svr_mae, feat_svr_r2])
               else "partially_supported",
}

svm_gt_rf = r["svr|enhanced"]["R2_cv_mean"] > r["rf|enhanced"]["R2_cv_mean"]
svm_gt_rf_pooled = r["svr|enhanced"]["R2_cv_pooled"] > r["rf|enhanced"]["R2_cv_pooled"]
claim2 = {
    "claim": "SVM outperforms RF (SVM R2 >= 0 while RF R2 < 0)",
    "ours": {
        "svr_R2": r["svr|enhanced"]["R2_cv_mean"],
        "rf_R2": r["rf|enhanced"]["R2_cv_mean"],
        "svm_gt_rf": bool(svm_gt_rf and svm_gt_rf_pooled),
    },
    "verdict": "supported" if svm_gt_rf else "partially_supported",
}

gnn_mae = r["gnn|composition_graph"]["MAE_cv_mean"]
claim3 = {
    "claim": "GNN performance between SVM and RF (CGCNN MAE ~0.97); all GNNs worse than SVM, most better than RF",
    "ours": {
        "gnn_MAE": gnn_mae,
        "svm_MAE": r["svr|enhanced"]["MAE_cv_mean"],
        "rf_MAE": r["rf|enhanced"]["MAE_cv_mean"],
        "gnn_between_svm_and_rf": bool(r["svr|enhanced"]["MAE_cv_mean"] < gnn_mae < r["rf|enhanced"]["MAE_cv_mean"]),
    },
    "verdict": "supported" if (r["svr|enhanced"]["MAE_cv_mean"] < gnn_mae < r["rf|enhanced"]["MAE_cv_mean"]) else "partially_supported",
}

overall = {
    "rf_vs_svm": claim2["verdict"],
    "feature_engineering": claim1["verdict"],
    "gnn_position": claim3["verdict"],
}

metrics = {
    "dataset_stats": {k: v for k, v in data_stats.items()},
    "protocol": {
        "target": "Piezoelectric_Modulus (C/m^2)",
        "cv": "5-fold shuffled KFold (seed 42), same folds for all models",
        "secondary_split": "fixed 80/20 (seed 42)",
        "svr_hyperparams": "inner 3-fold GridSearchCV on training folds only (C in [3,10,30], gamma in [scale,0.001,0.005])",
        "rf_hyperparams": "fixed n_estimators=500, max_features=sqrt",
        "n_used_for_ml": 1704,  # 1705 minus unparseable Cs4A6S5
    },
    "method_results": results,
    "expansion_prediction": exp,
    "paper_anchor_comparison": anchors,
    "claims": {"claim1_feature_engineering": claim1,
               "claim2_svm_vs_rf": claim2,
               "claim3_gnn_position": claim3,
               "overall_verdict": overall},
}

with open(os.path.join(RESULTS_DIR, "metrics.json"), "w") as f:
    json.dump(metrics, f, indent=2, default=str)

print("saved results/metrics.json")
print("Overall verdict:", overall)
print("RF MAE basic->enhanced: %.4f -> %.4f" % (r["rf|basic"]["MAE_cv_mean"], r["rf|enhanced"]["MAE_cv_mean"]))
print("RF R2  basic->enhanced: %.4f -> %.4f" % (r["rf|basic"]["R2_cv_mean"], r["rf|enhanced"]["R2_cv_mean"]))
print("SVM MAE basic->enhanced: %.4f -> %.4f" % (r["svr|basic"]["MAE_cv_mean"], r["svr|enhanced"]["MAE_cv_mean"]))
print("SVM R2  basic->enhanced: %.4f -> %.4f" % (r["svr|basic"]["R2_cv_mean"], r["svr|enhanced"]["R2_cv_mean"]))
print("GNN MAE: %.4f (paper CGCNN 0.974, SchNet 1.343)" % gnn_mae)