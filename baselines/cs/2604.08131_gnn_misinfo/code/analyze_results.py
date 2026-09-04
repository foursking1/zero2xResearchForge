"""
Post-hoc analysis: build evidence table, figures and claim verdicts from the
pipeline outputs in ../results.

Usage:
    python analyze_results.py [--results ../results]
Produces:
    results/figures/f1_comparison.png
    results/figures/graphsage_curves.png
    results/figures/mlp_curves.png
"""

import argparse
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ANCHORS = {"graphsage": 91.9, "mlp": 66.8}


def load_perseed(results_dir):
    p = os.path.join(results_dir, "metrics_perseed.csv")
    df = pd.read_csv(p)
    return df


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default=os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "results"))
    args = ap.parse_args()

    df = load_perseed(args.results)
    agg = df.groupby("model").agg(f1_mean=("f1", "mean"), f1_std=("f1", "std"),
                                  precision_mean=("precision", "mean"),
                                  recall_mean=("recall", "mean"),
                                  n_mean=("n", "mean")).reset_index()

    # ---- figure 1: per-model F1 bars with anchors ----
    fig, ax = plt.subplots(figsize=(7, 4.2))
    models = agg["model"].tolist()
    x = np.arange(len(models))
    means = agg["f1_mean"].to_numpy() * 100
    stds = agg["f1_std"].to_numpy() * 100
    bars = ax.bar(x, means, yerr=stds, capsize=6, color=["#2c7bb6", "#d7191c"],
                  alpha=0.85, edgecolor="black")
    for i, m in enumerate(models):
        ax.axhspan(ANCHORS[m] * 0.95, ANCHORS[m] * 1.05,
                    color="#2c7bb6" if m == "graphsage" else "#d7191c",
                    alpha=0.12)
        ax.text(x[i], means[i] + max(stds) + 1.5,
                f"{means[i]:.1f}±{stds[i]:.1f}", ha="center", fontsize=10)
    ax.axhline(ANCHORS["graphsage"], color="#2c7bb6", ls=":", lw=1)
    ax.axhline(ANCHORS["mlp"], color="#d7191c", ls=":", lw=1)
    ax.set_xticks(x)
    ax.set_xticklabels([f"GraphSAGE\n(paper 91.9)" if m == "graphsage"
                        else f"MLP\n(paper 66.8)" for m in models])
    ax.set_ylabel("Test F1 (%)")
    ax.set_ylim(0, 105)
    ax.set_title("WELFake (80/10/10, TF-IDF 5k, k-NN K=5) — test F1, "
                 "mean±std over 3 seeds")
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    figdir = os.path.join(args.results, "figures")
    os.makedirs(figdir, exist_ok=True)
    fig.savefig(os.path.join(figdir, "f1_comparison.png"), dpi=150)
    plt.close(fig)
    print("saved figures/f1_comparison.png")

    # ---- figure 2: training curves ----
    for mname in ("graphsage", "mlp"):
        files = [f for f in os.listdir(args.results)
                 if f.startswith(f"history_{mname}_seed") and f.endswith(".csv")]
        fig, axes = plt.subplots(1, 2, figsize=(11, 4))
        for f in files:
            h = pd.read_csv(os.path.join(args.results, f))
            seed = int(f.split(f"history_{mname}_seed")[-1].split(".")[0])
            axes[0].plot(h["step"], h["train_loss"], label=f"seed {seed}")
            axes[1].plot(h["step"], h["f1"] * 100, label=f"seed {seed}")
        axes[0].set_xlabel("epoch / iteration")
        axes[0].set_ylabel("train loss")
        axes[0].legend()
        axes[0].set_title(f"{mname} train loss")
        axes[1].set_xlabel("epoch / iteration")
        axes[1].set_ylabel("val F1 (%)")
        axes[1].legend()
        axes[1].set_title(f"{mname} validation F1")
        fig.tight_layout()
        fig.savefig(os.path.join(figdir, f"{mname}_curves.png"), dpi=150)
        plt.close(fig)
        print(f"saved figures/{mname}_curves.png")

    # ---- claim verdicts ----
    f1_map = dict(zip(agg["model"], agg["f1_mean"]))
    g = f1_map["graphsage"] * 100
    m = f1_map["mlp"] * 100
    gap = g - m
    print("\nGraphSAGE test F1: %.2f%% (paper 91.9)" % g)
    print("MLP test F1:       %.2f%% (paper 66.8)" % m)
    print("gap: %.2f pp (paper +25.1 pp)" % gap)

    def verdict(label, cond, detail):
        print(f"claim({label}): {'SUPPORTED' if cond else 'NOT supported'} "
              f"— {detail}")

    verdict("a) graphsage near 91.9 (±5pp)",
            86.9 <= g <= 96.9, f"observed {g:.1f}")
    verdict("b) graphsage - mlp >= 15pp", gap >= 15,
            f"observed {gap:.1f}pp")
    verdict("c) graphsage > mlp", g > m, f"observed {g:.1f} vs {m:.1f}")
    return agg


if __name__ == "__main__":
    main()