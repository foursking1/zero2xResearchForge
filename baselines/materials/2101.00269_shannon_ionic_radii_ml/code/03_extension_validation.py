#!/usr/bin/env python3
"""
03_extension_validation.py

Optional-extension verification of the reproduced model + the extended
database:

 1. **ML-only predictions consistency**: a GPR trained purely on the 476
    Shannon-labeled rows is used to predict the 512 rows that only carry
    ML radii. These predictions are compared with the database's frozen
    `ml_radius_pm` (the *independent* GPR predictions published by the
    paper authors). High agreement implies the physical model generalizes
    to unseen (element, OS, CN) combinations.

 2. **Physical trends** (over all rows, incl. ML-only):
      (a) radius increases with coordination number (same element & OS);
      (b) radius decreases with oxidation state (same element & CN).
    We report how often the trend holds for adjacent pairs and an overall
    correlation coefficient per trend (Pearson within group).

 3. **Coverage statistics of the extended table**: distribution of new
    ML-predicted ions by element, OS and CN.

Outputs: results/extension_analysis.csv, results/extension_summary.json,
and figure results/figures/ml_comparison.png (if matplotlib available).
"""
import json
import os

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import Matern, WhiteKernel, ConstantKernel
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLEAN_CSV = os.path.join(ROOT, "results", "dataset_clean.csv")
EXT_CSV = os.path.join(ROOT, "results", "extension_analysis.csv")
EXT_JSON = os.path.join(ROOT, "results", "extension_summary.json")
FIG_DIR = os.path.join(ROOT, "results", "figures")
os.makedirs(FIG_DIR, exist_ok=True)


BLOCK_CODES = {"s": 0, "p": 1, "d": 2, "f": 3}


def build_X(lab, feats):
    cols = [c for c in feats if c != "block"]
    X = lab[cols].to_numpy(dtype=float)
    if "block" in feats:
        blk = lab["block"].map(BLOCK_CODES).to_numpy(dtype=float)[:, None]
        X = np.hstack([X, blk])
    return X


def group_trend(frame, group_cols, x_col, trend):
    """Check monotonic trend between consecutive sorted x within groups."""
    ok, tot = 0, 0
    corr_x, corr_y, corr_n = [], [], 0.0
    for _, g in frame.groupby(group_cols):
        g = g.sort_values(x_col).dropna(subset=["shannon_radius_pm_num",
                                                "ml_radius_pm"])
        if len(g) < 2:
            continue
        tg = g["ml_radius_pm"].to_numpy()
        tot += 0
        for j in range(1, len(g)):
            dx = g[x_col].iloc[j] - g[x_col].iloc[j - 1]
            dy = tg[j] - tg[j - 1]
            if dx == 0:
                continue
            tot += 1
            if (trend == "inc" and dy > 0) or (trend == "dec" and dy < 0):
                ok += 1
        if len(g) >= 3:
            rho, _ = stats.spearmanr(g[x_col], tg)
            corr_x.append(g[x_col].to_numpy())
            corr_y.append(tg)
            corr_n += 1
    if corr_n:
        allx = np.concatenate(corr_x)
        ally = np.concatenate(corr_y)
        pearson = float(stats.pearsonr(allx, ally)[0])
    else:
        pearson = np.nan
    return {"n_pairs": tot, "n_consistent": ok,
            "fraction_consistent": ok / tot if tot else np.nan,
            "pearson": pearson}


def main():
    df = pd.read_csv(CLEAN_CSV)
    lab = df[df["has_shannon"]].copy()
    y = lab["shannon_radius_angstrom"].to_numpy(float) * 100  # label in pm for plot
    lab = lab.assign(y_pm=y)

    # -- trend 1: radius vs coordination number (same element+OS) --
    t_cn = group_trend(lab, ["element", "oxidation_state"], "coordination_number", "inc")
    # -- trend 2: radius vs oxidation state (same element+CN) --
    t_os = group_trend(lab, ["element", "coordination_number"], "oxidation_state", "dec")

    # -- ML-only rows --
    ml_only = df[df["ml_only"]].copy()

    # -- model-based check: reproduce the "new predictions" with a GPR
    #    trained only on Shannon rows, then compare to the published ML
    #    radii (which are the paper authors' predictions stored in the
    #    extended table). Trains on 476 labeled rows; predicts 512 rows.
    basename = "GPR"
    n_feats = 5
    kernel = (ConstantKernel(1.0, (1e-3, 1e3)) * Matern(np.ones(n_feats), nu=1.5)
              + WhiteKernel(1e-3, (1e-8, 1e1)))
    gpr = make_pipeline(StandardScaler(),
                        GaussianProcessRegressor(kernel=kernel,
                                                 normalize_y=True))
    Xtr = build_X(lab.assign(electrons_in_ion=lab["atomic_number"]
                                         - lab["oxidation_state"]),
                  ["electrons_in_ion", "valence_electrons", "oxidation_state",
                   "coordination_number", "block"])
    ytr = (lab["shannon_radius_pm_num"].to_numpy(dtype=float) / 100.0)
    detail = ml_only.assign(
        electrons_in_ion=ml_only["atomic_number"] - ml_only["oxidation_state"])
    Xte = build_X(detail.drop(columns="ml_radius_pm"),
                  ["electrons_in_ion", "valence_electrons", "oxidation_state",
                   "coordination_number", "block"])
    gpr.fit(Xtr, ytr)
    pred_angle = gpr.predict(Xte)
    ml_only["our_gpr_radius_pm"] = pred_angle * 100.0
    resid = ml_only["our_gpr_radius_pm"] - ml_only["ml_radius_pm"]
    ml_model = {
        "our_gpr_vs_published_rmse_pm": float(np.sqrt((resid ** 2).mean())),
        "our_gpr_vs_published_mae_pm": float(resid.abs().mean()),
        "our_gpr_vs_published_median_abs_pm": float(resid.abs().median()),
        "pearson_our_vs_published": float(stats.pearsonr(
            ml_only["our_gpr_radius_pm"], ml_only["ml_radius_pm"])[0]),
        "n_ml_only_predicted": int(len(ml_only)),
    }

    results = {
        "shannon_rows": int(lab.shape[0]),
        "ml_only_rows": int(ml_only.shape[0]),
        "trend_radius_vs_cn_inc": {k: (float(v) if isinstance(v, np.floating) else v)
                                   for k, v in t_cn.items()},
        "trend_radius_vs_os_dec": {k: (float(v) if isinstance(v, np.floating) else v)
                                   for k, v in t_os.items()},
        "ml_only_element_coverage": int(ml_only["element"].nunique()),
        "ml_only_os_range": [int(ml_only["oxidation_state"].min()),
                             int(ml_only["oxidation_state"].max())],
        "ml_only_cn_range": [int(ml_only["coordination_number"].min()),
                             int(ml_only["coordination_number"].max())],
        "ml_only_radius_pm_range": [float(ml_only["ml_radius_pm"].min()),
                                    float(ml_only["ml_radius_pm"].max())],
        "ml_only_sd_pm_mean": float(ml_only["ml_sd_pm"].mean()),
        # compare Shannon rows where both labels exist (shannon vs ml agreement)
        "dual_rows": int(df["has_shannon"].sum()),
        "dual_shannon_vs_ml_mae_pm": float(
            (lab["shannon_radius_pm_num"] - lab["ml_radius_pm"]).abs().mean()),
        "dual_shannon_vs_ml_rmse_pm": float(
            np.sqrt(((lab["shannon_radius_pm_num"] - lab["ml_radius_pm"]) ** 2).mean())),
        "model_based_extension_check": ml_model,
    }

    out_rows = []
    for _, r in ml_only.iterrows():
        out_rows.append({"element": r["element"], "oxidation_state": r["oxidation_state"],
                         "coordination_number": r["coordination_number"],
                         "ml_radius_pm": r["ml_radius_pm"], "ml_sd_pm": r["ml_sd_pm"]})
    pd.DataFrame(out_rows).to_csv(EXT_CSV, index=False)

    # figure 1: shannon vs ML on dual rows
    fig, ax = plt.subplots(figsize=(5.5, 5))
    dual = lab.dropna(subset=["shannon_radius_pm_num", "ml_radius_pm"])
    ax.scatter(dual["shannon_radius_pm_num"], dual["ml_radius_pm"], s=8, alpha=0.45)
    lim = [dual["shannon_radius_pm_num"].min(), dual["shannon_radius_pm_num"].max()]
    ax.plot(lim, lim, "r--", lw=1)
    ax.set_xlabel("Shannon radius (pm)")
    ax.set_ylabel("Database ML radius (pm)")
    ax.set_title(f"Shannon vs published ML radius (n={len(dual)})")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "shannon_vs_ml.png"), dpi=150)
    plt.close(fig)

    # figure 2: our GPR predictions vs published ML on the 512 ML-only rows
    fig, ax = plt.subplots(figsize=(5.5, 5))
    ax.scatter(ml_only["ml_radius_pm"], ml_only["our_gpr_radius_pm"],
               s=8, alpha=0.5)
    lim = [min(ml_only["ml_radius_pm"].min(), ml_only["our_gpr_radius_pm"].min()),
           max(ml_only["ml_radius_pm"].max(), ml_only["our_gpr_radius_pm"].max())]
    ax.plot(lim, lim, "r--", lw=1)
    ax.set_xlabel("Published ML radius (pm)")
    ax.set_ylabel("Our GPR radius (pm)")
    ax.set_title(f"Our GPR vs published on ML-only rows (n={len(ml_only)})")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "our_gpr_vs_published_mlonly.png"), dpi=150)
    plt.close(fig)

    with open(EXT_JSON, "w") as f:
        json.dump(results, f, indent=2)
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()