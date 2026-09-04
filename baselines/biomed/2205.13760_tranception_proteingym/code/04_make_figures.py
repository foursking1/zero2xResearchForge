"""Figures for the ProteinGym replication.

Produces:
  - results/figures/rho_by_assay.png   grouped bar chart (rho per assay x method)
  - results/figures/scatter_representative.png   ESM-2 650M score vs DMS_score
      for BRCA1, PTEN and GFP (subset)
  - results/figures/rho_by_msa_depth.png   LM vs baseline rho vs MSA Neff
"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common import ASSAYS, ROOT, get_meta, load_reference

SCORES = os.path.join(ROOT, "results")

METHODS_PLOT = [
    ("LM_esm2_650M", "ESM-2 650M"),
    ("LM_esm2_8M", "ESM-2 8M"),
    ("baseline_blosum62", "BLOSUM62"),
    ("baseline_null", "Null (noise)"),
]


def load_scores(fid, method):
    if method.startswith("LM_"):
        model = "esm2_t33_650M" if "650M" in method else "esm2_t6_8M"
        p = os.path.join(SCORES, "lm_scores", "tables", model, f"{fid}.csv")
    else:
        p = os.path.join(SCORES, "baseline_scores", f"{method}__{fid}.csv")
    return pd.read_csv(p)[["mutant", "DMS_score", "score"]].dropna(subset=["score"])


def main():
    ref = load_reference()
    os.makedirs(os.path.join(ROOT, "results", "figures"), exist_ok=True)

    rho = {}
    for fid in ASSAYS:
        rho[fid] = {}
        for method, _ in METHODS_PLOT:
            df = load_scores(fid, method)
            r, _ = spearmanr(df["score"], df["DMS_score"])
            rho[fid][method] = r

    # ---- grouped bar chart ----
    fig, ax = plt.subplots(figsize=(11, 5))
    x = np.arange(len(ASSAYS))
    width = 0.9 / len(METHODS_PLOT)
    colors = ["#1f77b4", "#7fbfbf", "#d95f02", "#bdbdbd"]
    for j, (method, lab) in enumerate(METHODS_PLOT):
        vals = [rho[f][method] for f in ASSAYS]
        ax.bar(x + (j - len(METHODS_PLOT) / 2 + 0.5) * width, vals, width,
               label=lab, color=colors[j])
    ax.set_xticks(x)
    ax.set_xticklabels([f.split("_")[0] for f in ASSAYS], rotation=20, ha="right")
    ax.set_ylabel("Spearman $\\rho$ vs DMS_score")
    ax.set_title("Zero-shot variant-effect prediction on frozen ProteinGym assays "
                 "(higher = better)")
    ax.axhline(0, color="k", lw=0.5)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(os.path.join(SCORES, "figures", "rho_by_assay.png"), dpi=150)

    # ---- scatter for representative assays ----
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.5))
    for ax, fid in zip(axes, ["BRCA1_HUMAN_Findlay_2018",
                              "PTEN_HUMAN_Matreyek_2021",
                              "GFP_AEQVI_Sarkisyan_2016"]):
        df = load_scores(fid, "LM_esm2_650M")
        if len(df) > 8000:
            df = df.sample(8000, random_state=42)
        ax.scatter(df["score"], df["DMS_score"], s=4, alpha=0.15, color="#1f77b4")
        r, _ = spearmanr(df["score"], df["DMS_score"])
        ax.set_title(f"{fid.split('_')[0]}   $\\rho$={r:.3f}")
        ax.set_xlabel("ESM-2 650M masked-marginal score")
        if ax is axes[0]:
            ax.set_ylabel("DMS_score (higher = higher fitness)")

    fig.tight_layout()
    fig.savefig(os.path.join(SCORES, "figures", "scatter_representative.png"), dpi=150)

    # ---- LM vs baseline by MSA depth ----
    fig, ax = plt.subplots(figsize=(7.5, 5))
    for method, lab, col in [("LM_esm2_650M", "ESM-2 650M", "#1f77b4"),
                             ("baseline_blosum62", "BLOSUM62", "#d95f02")]:
        xs, ys = [], []
        for fid in ASSAYS:
            neff = get_meta(load_reference(), fid)["MSA_Neff"]
            xs.append(neff)
            ys.append(rho[fid][method])
        ax.scatter(xs, ys, label=lab, color=col, s=60, zorder=3)
    ax.set_xscale("log")
    for fid in ASSAYS:
        neff = get_meta(load_reference(), fid)["MSA_Neff"]
        ax.annotate(fid.split("_")[0], (neff, rho[fid]["LM_esm2_650M"]),
                    xytext=(0, 5), textcoords="offset points", fontsize=8)
    ax.set_xlabel("Reference MSA depth $N_{eff}$ (log)")
    ax.set_ylabel("Spearman $\\rho$")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(os.path.join(SCORES, "figures", "rho_by_msa_depth.png"), dpi=150)
    print("figures written to", os.path.join(SCORES, "figures"))


if __name__ == "__main__":
    main()