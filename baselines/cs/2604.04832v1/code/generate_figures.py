"""Generate the evidence figures used in solution.md.

Figures (saved to results/figures/):
  fdr_comparison.png          - FDR (raw + normalised) per gesture pair
  mcc_comparison.png          - MLP MCC vs paper targets
  sensor_criticality.png      - Metric A: per-class per-sensor shift FDR
  class_criticality.png       - Metric B: per-class delta-FDR criticality
  fdr_mcc_correlation.png     - per-pair delta FDR vs delta MCC scatter
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from common import SENSOR_LABEL_1BASED

RESULTS = Path(__file__).resolve().parents[1] / "results"
FIG = RESULTS / "figures"
PAPER_FDR = {"paper_vs_scissors": 0.073, "rock_vs_paper": 0.842,
             "rock_vs_scissors": 1.000}
PAPER_MCC = {"paper_vs_scissors": 0.872, "rock_vs_paper": 0.990,
             "rock_vs_scissors": 1.000}
PAIR_SHORT = {"paper_vs_scissors": "Paper vs Scissors",
              "rock_vs_paper": "Rock vs Paper",
              "rock_vs_scissors": "Rock vs Scissors"}


def load(name):
    with open(RESULTS / name) as fh:
        return json.load(fh)


def fig_fdr(s1):
    pairs = list(PAIR_SHORT)
    ours = [s1["fdr_normalized_divide_max"][p] for p in pairs]
    paper = [PAPER_FDR[p] for p in pairs]
    x = np.arange(len(pairs))
    plt.figure(figsize=(7, 4))
    plt.bar(x - 0.18, paper, 0.36, label="Paper", color="tab:gray")
    plt.bar(x + 0.18, ours, 0.36, label="Ours (divide-max)", color="tab:blue")
    for xi, (a, b) in enumerate(zip(paper, ours)):
        plt.text(xi - 0.18, a + 0.02, f"{a:.3f}", ha="center", fontsize=8)
        plt.text(xi + 0.18, b + 0.02, f"{b:.3f}", ha="center", fontsize=8)
    plt.xticks(x, [PAIR_SHORT[p] for p in pairs], rotation=15)
    plt.ylabel("Normalised FDR")
    plt.title("Stage 1: FDR class separability")
    plt.legend()
    plt.tight_layout()
    plt.savefig(FIG / "fdr_comparison.png", dpi=150)


def fig_mcc(s2):
    pairs = list(PAIR_SHORT)
    res = s2["best_results"]
    ours = [res["mean_pairwise_mcc"][p] for p in pairs]
    stds = [res["std_pairwise_mcc"][p] for p in pairs]
    paper = [PAPER_MCC[p] for p in pairs]
    x = np.arange(len(pairs))
    plt.figure(figsize=(7, 4))
    plt.bar(x - 0.18, paper, 0.36, label="Paper", color="tab:gray")
    plt.bar(x + 0.18, ours, 0.36, yerr=stds, label=f"Ours ({res['architecture']})",
            color="tab:green", capsize=3)
    for xi, (a, b) in enumerate(zip(paper, ours)):
        plt.text(xi - 0.18, a + 0.02, f"{a:.3f}", ha="center", fontsize=8)
        plt.text(xi + 0.18, b + 0.02, f"{b:.3f}", ha="center", fontsize=8)
    plt.xticks(x, [PAIR_SHORT[p] for p in pairs], rotation=15)
    plt.ylabel("MCC")
    plt.ylim(0.7, 1.05)
    plt.title("Stage 2: MLP validation oracle (MCC)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(FIG / "mcc_comparison.png", dpi=150)


def fig_sensor_criticality(s3):
    """Metric A: distributional-shift FDR per class per sensor."""
    norm = s3["distributional_shift_ablation"]["normalized_f1_per_class"]
    classes = ["rock", "paper", "scissors"]
    sensors = [f"sensor_{i}" for i in range(8)]
    labels = SENSOR_LABEL_1BASED
    fig, axes = plt.subplots(1, 3, figsize=(13, 4), sharey=True)
    for ax, c in zip(axes, classes):
        vals = [norm[c][s] for s in sensors]
        cols = ["tab:red" if labels[i] == "S2" else
                ("tab:blue" if labels[i] in ("S6", "S7") else "tab:gray")
                for i in range(8)]
        ax.bar(labels, vals, color=cols)
        ax.set_title(c.capitalize())
        ax.set_ylim(0, 1.05)
        ax.set_ylabel("Norm. shift FDR" if c == "rock" else "")
    fig.suptitle("Metric A: sensor criticality (distributional-shift FDR)")
    fig.tight_layout()
    plt.savefig(FIG / "sensor_criticality.png", dpi=150)


def fig_class_criticality(s3):
    """Metric B (mean-FDR delta): per-class sensor criticality."""
    crit = s3["delta_fdr_ablation"]["class_criticality_mean"]
    classes = ["rock", "paper", "scissors"]
    labels = SENSOR_LABEL_1BASED
    fig, axes = plt.subplots(1, 3, figsize=(13, 4), sharey=True)
    for ax, c in zip(axes, classes):
        vals = [crit[c]["ranking"][i]["avg_delta_fdr_mean"] for i in range(8)]
        s_idx = [int(crit[c]["ranking"][i]["sensor"].split("_")[1]) for i in range(8)]
        cols = ["tab:red" if labels[i] == "S2" else
                ("tab:blue" if labels[i] in ("S6", "S7") else "tab:gray")
                for i in s_idx]
        ax.bar([labels[i] for i in s_idx], vals, color=cols)
        ax.set_title(c.capitalize())
        ax.set_ylabel("Avg delta-FDR (mean)" if c == "rock" else "")
    fig.suptitle("Metric B: sensor criticality (delta pairwise FDR, mean-agg)")
    fig.tight_layout()
    plt.savefig(FIG / "class_criticality.png", dpi=150)


def fig_fdr_mcc_correlation(s3):
    corr = s3["correlation"]
    per_sensor = corr["per_sensor"]
    pairs = ["paper_vs_scissors", "rock_vs_paper", "rock_vs_scissors"]
    fig, axes = plt.subplots(1, 3, figsize=(13, 4))
    for ax, pair in zip(axes, pairs):
        x = [per_sensor[f"sensor_{i}"][pair]["delta_fdr_mean"] for i in range(8)]
        y = [per_sensor[f"sensor_{i}"][pair]["delta_mcc"] for i in range(8)]
        ax.scatter(x, y, c="tab:blue")
        r = corr["per_pair"][pair]["pearson_r"]
        ax.set_title(f"{PAIR_SHORT[pair]}\nr={r:.2f}")
        ax.set_xlabel("delta FDR (mean)")
        ax.set_ylabel("delta MCC")
    fig.suptitle("FDR vs MCC across 8 sensor ablations")
    fig.tight_layout()
    plt.savefig(FIG / "fdr_mcc_correlation.png", dpi=150)


def main():
    s1 = load("stage1_fdr_results.json")
    s2 = load("mlp_architecture_sweep.json")
    s3 = load("stage3_ablation_results.json")
    FIG.mkdir(parents=True, exist_ok=True)
    fig_fdr(s1)
    fig_mcc(s2)
    fig_sensor_criticality(s3)
    fig_class_criticality(s3)
    fig_fdr_mcc_correlation(s3)
    print("figures written to", FIG)


if __name__ == "__main__":
    main()
