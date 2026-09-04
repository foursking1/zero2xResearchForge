"""Publication-style figures for the report (evidence/)."""

import argparse
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

plt.rcParams.update({"font.size": 11, "axes.spines.top": False,
                     "axes.spines.right": False})


def fig_robust_bar(ev, out=None, seed=0):
    d = ev[ev["seed"] == seed].copy()
    models = d["model"].tolist()
    x = np.arange(len(models))
    w = 0.35
    clean = d["clean_acc"].to_numpy()
    cpgd = d["robust_acc_cpgd"].to_numpy()
    capgd = d["robust_acc_capgd"].to_numpy()
    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    ax.bar(x - w, cpgd, w, label="CPGD (ours)", color="#4C72B0")
    ax.bar(x, capgd, w, label="CAPGD (ours)", color="#DD8452")
    ax.bar(x + w, clean, w, label="Clean (critical class)", color="#8bb8a7", alpha=.7)
    ax.set_xticks(x, [m.upper() for m in models])
    ax.set_ylabel("accuracy (%) on attacked phishing test samples")
    ax.set_ylim(0, 105)
    for xi, v in zip(x - w, cpgd):
        ax.text(xi, v + 1, f"{v:.1f}", ha="center", fontsize=9)
    for xi, v in zip(x, capgd):
        ax.text(xi, v + 1, f"{v:.1f}", ha="center", fontsize=9)
    ax.legend(frameon=False)
    ax.set_title(f"Robust accuracy: CAPGD vs CPGD (seed {seed}, L2, $\\epsilon=0.5$)")
    fig.tight_layout()
    if out:
        fig.savefig(out, dpi=200)
    plt.close(fig)


def fig_cs_rate(ev, out=None, seed=0):
    d = ev[ev["seed"] == seed]
    models = d["model"].tolist()
    x = np.arange(len(models))
    fig, ax = plt.subplots(figsize=(6.4, 3.4))
    cs = d["capgd_constraint_satisfaction_rate"].to_numpy() * 100
    we = d["capgd_within_eps_rate"].to_numpy() * 100
    ax.bar(x - 0.2, cs, 0.4, label="CAPGD constraint-satisfaction", color="#55A868")
    ax.bar(x + 0.2, we, 0.4, label="CAPGD within-$\\epsilon$", color="#C44E52")
    ax.set_xticks(x, [m.upper() for m in models])
    ax.set_ylim(90, 102)
    ax.set_ylabel("%")
    ax.legend(frameon=False)
    fig.tight_layout()
    if out:
        fig.savefig(out, dpi=200)
    plt.close(fig)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--evidence", default="results/evidence_table.csv")
    ap.add_argument("--outdir", default="evidence")
    a = ap.parse_args()
    ev = pd.read_csv(a.evidence)
    os.makedirs(a.outdir, exist_ok=True)
    fig_robust_bar(ev, out=f"{a.outdir}/fig_robust_accuracy.png", seed=0)
    fig_cs_rate(ev, out=f"{a.outdir}/fig_constraint_satisfaction.png", seed=0)
    fig_robust_bar(ev, out=f"{a.outdir}/fig_robust_accuracy_seed1.png", seed=1)
    print("figures written to", a.outdir)