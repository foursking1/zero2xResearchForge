#!/usr/bin/env python3
"""Generate summary figures from results/metrics.json (evidence artefacts)."""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def main():
    with open(os.path.join(ROOT, "results", "metrics.json")) as f:
        m = json.load(f)
    fig_dir = os.path.join(ROOT, "results", "figures")
    os.makedirs(fig_dir, exist_ok=True)

    names = list(m["per_model"].keys())
    st_clean = [m["per_model"][k]["std"]["clean_acc"] * 100 for k in names]
    st_rob = [m["per_model"][k]["std"]["robust_acc"] * 100 for k in names]
    at_clean = [m["per_model"][k]["at"]["clean_acc"] * 100 for k in names]
    at_rob = [m["per_model"][k]["at"]["robust_acc"] * 100 for k in names]

    # Figure 1: clean vs robust, std and AT (grouped bars)
    x = np.arange(len(names))
    w = 0.19
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(x - 1.5 * w, st_clean, w, label="std clean", color="#4C72B0")
    ax.bar(x - 0.5 * w, st_rob, w, label="std robust (PGD-L2 \u03b5=0.25)", color="#C44E52")
    ax.bar(x + 0.5 * w, at_clean, w, label="AT clean", color="#55A868")
    ax.bar(x + 1.5 * w, at_rob, w, label="AT robust (PGD-L2 \u03b5=0.25)", color="#CCB974")
    ax.set_xticks(x, names)
    ax.set_ylabel("Accuracy (%)")
    ax.set_title("URL use-case: standard vs adversarial training\n"
                 "clean & robust accuracy (PGD-L2, \u03b5=0.25)")
    ax.legend(fontsize=8)
    ax.set_ylim(0, 100)
    fig.tight_layout()
    fig.savefig(os.path.join(fig_dir, "grouped_bars.png"), dpi=150)

    # Figure 2: clean vs robust scatter, showing spread contrast
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.scatter(st_clean, st_rob, marker="o", s=70, label="standard", color="#C44E52")
    ax.scatter(at_clean, at_rob, marker="s", s=70, label="AT", color="#55A868")
    for i, n in enumerate(names):
        ax.annotate(n, (st_clean[i], st_rob[i]), fontsize=7, xytext=(3, 3),
                    textcoords="offset points")
    ax.set_xlabel("Clean (ID) accuracy (%)")
    ax.set_ylabel("Robust accuracy (%)")
    ax.set_title("ID accuracy vs robust accuracy (per model)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(fig_dir, "id_robust_scatter.png"), dpi=150)

    # Figure 3: robust range std vs AT (span subtitle plot)
    fig, ax = plt.subplots(figsize=(6, 4))
    y = [np.max(st_rob), np.max(at_rob)]
    ye = [np.max(st_rob) - np.min(st_rob), np.max(at_rob) - np.min(at_rob)]
    ax.bar(["standard", "AT"], y, yerr=ye, capsize=6, color=["#C44E52", "#55A868"])
    ax.set_ylabel("Robust accuracy (bar = max, error bar = spread)")
    ax.set_title("Robust-accuracy spread: std vs AT")
    fig.tight_layout()
    fig.savefig(os.path.join(fig_dir, "robust_spread.png"), dpi=150)
    print("figures saved to", fig_dir)


if __name__ == "__main__":
    main()