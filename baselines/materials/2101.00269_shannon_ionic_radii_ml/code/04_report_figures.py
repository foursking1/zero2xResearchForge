#!/usr/bin/env python3
"""04_report_figures.py -- supplementary figures for report.md.

1. CV predicted vs true for the primary GPR (paper-mirroring features,
   7-fold shuffled CV) -- results/figures/gpr_cv_fit_paper.png
2. Per-model RMSE bar chart -- results/figures/rmse_bar_comparison.png
"""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import ConstantKernel, Matern, WhiteKernel
from sklearn.model_selection import KFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLEAN_CSV = os.path.join(ROOT, "results", "dataset_clean.csv")
EVIDENCE_CSV = os.path.join(ROOT, "results", "evidence_table.csv")
FIG_DIR = os.path.join(ROOT, "results", "figures")
os.makedirs(FIG_DIR, exist_ok=True)

BLOCK_CODES = {"s": 0, "p": 1, "d": 2, "f": 3}


def build_X(lab, feats):
    cols = [c for c in feats if c != "block"]
    X = lab[cols].to_numpy(dtype=float)
    if "block" in feats:
        X = np.hstack([X, lab["block"].map(BLOCK_CODES).to_numpy(float)[:, None]])
    return X


def main():
    df = pd.read_csv(CLEAN_CSV)
    lab = df[df["has_shannon"]].copy()
    y = lab["shannon_radius_angstrom"].to_numpy(float)
    X = build_X(lab, ["period", "group", "valence_electrons", "oxidation_state",
                      "coordination_number", "ionization_potential_eV"])
    n_feats = X.shape[1]
    kernel = (ConstantKernel(1.0, (1e-3, 1e3))
              * Matern(length_scale=np.ones(n_feats), nu=1.5)
              + WhiteKernel(1e-3, (1e-8, 1e1)))
    gpr = make_pipeline(StandardScaler(),
                        GaussianProcessRegressor(kernel=kernel, normalize_y=True,
                                                 random_state=42))
    yp = np.full_like(y, np.nan)
    kf = KFold(n_splits=7, shuffle=True, random_state=42)
    for tr, te in kf.split(X):
        gpr.fit(X[tr], y[tr])
        yp[te] = gpr.predict(X[te])

    fig, ax = plt.subplots(figsize=(5.5, 5))
    ax.scatter(y, yp, s=9, alpha=0.55)
    lim = [y.min(), y.max()]
    ax.plot(lim, lim, "r--", lw=1)
    ax.set_xlabel("True Shannon radius (A)")
    ax.set_ylabel("GPR CV prediction (A)")
    ax.set_title("GPR 7-fold CV fit (paper features, n=476)")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "gpr_cv_fit_paper.png"), dpi=150)
    plt.close(fig)

    ev = pd.read_csv(EVIDENCE_CSV)
    evA = ev[(ev["split"] == "7fold_shuffled") & (ev["metric"] == "rmse_angstrom")]
    pivot = evA.pivot(index="feature_set", columns="model", values="value")
    order = ["F0_atomic_no_os_cn", "F1_period_group_os_cn", "F2_paper_full",
             "F3_paper_full_block", "F4_enhanced_eion"]
    pivot = pivot.loc[[o for o in order if o in pivot.index]]
    fig, ax = plt.subplots(figsize=(8, 4.5))
    pivot[["GPR", "Ridge", "MLP"]].plot(kind="bar", ax=ax)
    ax.axhline(0.0332, color="k", ls="--", lw=1, label="paper RMSE 0.0332 A")
    ax.set_ylabel("RMSE (A)")
    ax.set_title("RMSE by feature set / model (7-fold shuffled CV)")
    ax.legend(ncol=2, fontsize=8)
    ax.tick_params(axis="x", labelsize=8, rotation=15)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "rmse_bar_comparison.png"), dpi=150)
    plt.close(fig)
    print("figures written to", FIG_DIR)


if __name__ == "__main__":
    main()