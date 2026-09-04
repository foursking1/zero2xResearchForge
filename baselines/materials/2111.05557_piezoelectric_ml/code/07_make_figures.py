"""07_make_figures.py
Bar charts comparing MAE / R2 across models and feature sets (from evidence_table.csv).
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from common import RESULTS_DIR, FIGURES_DIR

plt.rcParams.update({"font.size": 11})

ev = pd.read_csv(os.path.join(RESULTS_DIR, "evidence_table.csv"))
summary = ev[ev["split"] == "5fold_cv_mean"].copy()

# order and color
order = ["rf_basic", "rf_mid", "rf_enhanced",
         "svr_basic", "svr_mid", "svr_enhanced",
         "mpnn_composition_graph", "mlp_basic", "mlp_enhanced"]
label_map = {
    "rf_basic": "RF basic", "rf_mid": "RF mid", "rf_enhanced": "RF enhanced",
    "svr_basic": "SVM basic", "svr_mid": "SVM mid", "svr_enhanced": "SVM enhanced",
    "mpnn_composition_graph": "GNN (MPNN)",
    "mlp_basic": "MLP basic", "mlp_enhanced": "MLP enhanced",
}
summary["key"] = summary["model"] + "_" + summary["feature_set"]
summary = summary[summary["key"].isin(order)].set_index("key")

fig, axes = plt.subplots(1, 2, figsize=(13, 4.6))
mae = summary[summary["metric"] == "MAE"].loc[order]
r2 = summary[summary["metric"] == "R2"].loc[order]
x = np.arange(len(order))
axes[0].bar(x, mae["value"], yerr=mae["value_std"], capsize=3, color="#4472C4")
axes[0].set_xticks(x); axes[0].set_xticklabels([label_map[k] for k in order],
                                               rotation=40, ha="right")
axes[0].set_ylabel("5-fold CV MAE (C/m$^2$)")
axes[0].set_title("Mean MAE  (lower better)")
axes[0].axhline(0.953, color="red", ls="--", lw=1, label="paper RF all-features = 0.953")
axes[0].legend(fontsize=8)
axes[1].bar(x, r2["value"], yerr=r2["value_std"], capsize=3, color="#ED7D31")
axes[1].axhline(0, color="k", lw=0.8)
axes[1].set_xticks(x); axes[1].set_xticklabels([label_map[k] for k in order],
                                               rotation=40, ha="right")
axes[1].set_ylabel("5-fold CV R$^2$")
axes[1].set_title("Mean R$^2$  (higher better)")
fig.tight_layout()
fig.savefig(os.path.join(FIGURES_DIR, "model_comparison.png"), dpi=150)
print("saved evidence/figures/model_comparison.png")

# feature-set effect figure (MAE/R2 vs feature level) for RF and SVM
fig, axes = plt.subplots(1, 2, figsize=(12, 4.2))
levels = ["basic", "mid", "enhanced"]
for mi, metric in enumerate(["MAE", "R2"]):
    ax = axes[mi]
    df_plot = mae if metric == "MAE" else r2
    for model, color in [("rf", "#4472C4"), ("svr", "#ED7D31")]:
        vals = [float(df_plot.loc[f"{model}_{lv}", "value"]) for lv in levels]
        errs = [float(df_plot.loc[f"{model}_{lv}", "value_std"]) for lv in levels]
        ax.errorbar(levels, vals, yerr=errs, marker="o", label=model.upper(),
                    color=color, capsize=3)
    ax.set_xlabel("feature set (composition -> +structure -> +energy/mag/elec)")
    ax.set_ylabel(metric)
    ax.set_title(f"{metric} vs feature engineering")
    ax.legend()
fig.tight_layout()
fig.savefig(os.path.join(FIGURES_DIR, "feature_engineering_effect.png"), dpi=150)
print("saved evidence/figures/feature_engineering_effect.png")
print("done.")
