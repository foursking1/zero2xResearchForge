#!/usr/bin/env python3
"""08_figures.py — generate the analysis figures for the report."""
import json
import os
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import SUBSET_SEEDS
SEEDS = SUBSET_SEEDS

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results")
FIG = os.path.join(ROOT, "figures")
os.makedirs(FIG, exist_ok=True)
N_VALUES = [10, 50, 100]
META = ["airplane","automobile","bird","cat","deer","dog","frog","horse","ship","truck"]

def load_runs():
    out = {}
    for cfg in ["balanced", "imbalanced"]:
        for N in N_VALUES:
            for seed in SEEDS:
                p = os.path.join(RES, "students", f"{cfg}_N{N}_seed{seed}", "metrics.json")
                if os.path.exists(p):
                    with open(p) as f:
                        out[f"{cfg}_N{N}_s{seed}"] = json.load(f)
    return out

def main():
    runs = load_runs()

    # ---- Figure 1: teacher curve ----
    if os.path.exists(os.path.join(RES, "teacher_metrics.json")):
        t = json.load(open(os.path.join(RES, "teacher_metrics.json")))
        ep = list(range(1, t["epochs"] + 1))
        plt.figure(figsize=(6, 4))
        plt.plot(ep, t["test_acc_per_epoch"], label="teacher test acc@CIFAR-10")
        plt.plot(ep, t["train_acc_per_epoch"], alpha=.6, label="train acc")
        plt.xlabel("epoch"); plt.ylabel("acc (%)"); plt.title("VGG-16 teacher (from scratch)")
        plt.legend(); plt.grid(alpha=.3)
        plt.savefig(os.path.join(FIG, "teacher_curve.png"), dpi=150, bbox_inches="tight")
        plt.close()

    # ---- Figure 2: balanced vs imbalanced per N ----
    bal = {N: [] for N in N_VALUES}
    imb = {N: [] for N in N_VALUES}
    for N in N_VALUES:
        for s in SEEDS:
            if f"balanced_N{N}_s{s}" in runs:
                bal[N].append(runs[f"balanced_N{N}_s{s}"]["test_acc"])
            if f"imbalanced_N{N}_s{s}" in runs:
                imb[N].append(runs[f"imbalanced_N{N}_s{s}"]["test_acc"])

    xs = np.arange(len(N_VALUES))
    b_mean = np.array([np.mean(bal[N]) for N in N_VALUES])
    b_std = np.array([np.std(bal[N]) for N in N_VALUES])
    i_mean = np.array([np.mean(imb[N]) for N in N_VALUES])
    i_std = np.array([np.std(imb[N]) for N in N_VALUES])

    plt.figure(figsize=(7, 4.6))
    w = 0.35
    plt.bar(xs - w/2, b_mean, w, yerr=b_std, capsize=4, label="balanced")
    plt.bar(xs + w/2, i_mean, w, yerr=i_std, capsize=4, label="long-tail imbalanced (r=100)")
    for i, (b, d) in enumerate(zip(b_mean, i_mean - b_mean)):
        plt.annotate(f"Δ={d:+.2f}pp", (xs[i] + w/3, i_mean[i] + 1.2),
                     fontsize=9, color="darkred", ha="center")
    plt.xticks(xs, [f"N={N}\n({len(bal[N])} repeats)" for N in N_VALUES])
    plt.ylabel("test top-1 acc (%)"); plt.title("Few-shot KD compression on CIFAR-10")
    plt.legend(); plt.grid(alpha=.3, axis="y")
    plt.savefig(os.path.join(FIG, "kd_acc_delta.png"), dpi=150, bbox_inches="tight")
    plt.close()

    # ---- Figure 3: per-class counts (primary seed 42) ----
    subs = json.load(open(os.path.join(RES, "subsets_summary.json")))["subsets"]
    fig, axes = plt.subplots(1, len(N_VALUES), figsize=(13, 3.6), sharey=True)
    for ax, N in zip(axes, N_VALUES):
        b = next(r for r in subs if r["N"] == N and r["seed"] == 42 and r["config"] == "balanced")
        im = next(r for r in subs if r["N"] == N and r["seed"] == 42 and r["config"] == "imbalanced")
        bx = [b[f"n_{i}_{m}"] for i, m in enumerate(META)]
        ix = [im[f"n_{i}_{m}"] for i, m in enumerate(META)]
        x = np.arange(len(bx))
        w = 0.4
        ax.bar(x - w/2, bx, w, label="balanced")
        ax.bar(x + w/2, ix, w, label="imbalanced")
        ax.set_yscale("symlog")
        ax.set_title(f"N={N} (total {len(bx)*N})")
        ax.set_xticks(x); ax.set_xticklabels([m[:3] for m in META], rotation=45, fontsize=7)
        ax.legend(fontsize=7)
    axes[0].set_ylabel("samples per class (log scale)")
    plt.tight_layout()
    plt.savefig(os.path.join(FIG, "per_class_counts.png"), dpi=150, bbox_inches="tight")
    plt.close()
    print("[figures] wrote figures/teacher_curve.png, kd_acc_delta.png, per_class_counts.png")

if __name__ == "__main__":
    main()