"""Step 6 — Figures for the report.

Reads results/*.json and renders:
  * figures/length_distribution.png  (train sequence lengths histogram)
  * figures/accuracy_comparison.png  (our vs paper accuracy bar chart)
Safe to run any time after steps 1-4.
"""
import os
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from common import ensure_dir

HERE = os.path.dirname(__file__)
RESULTS = ensure_dir(os.path.join(HERE, "..", "results"))
FIGURES = ensure_dir(os.path.join(HERE, "..", "figures"))

PAPER = {"DDE": 59.77, "Moran": 57.73, "CNN": 64.43, "LSTM": 70.18,
         "ESM-1b": 70.23}


def load(p):
    with open(p) as f:
        return json.load(f)


def fig_length_distribution(stats):
    labels = list(stats["train_len_bins"].keys())
    vals = list(stats["train_len_bins"].values())
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(range(len(vals)), vals, color="#4c72b0")
    ax.set_xticks(range(len(vals)))
    ax.set_xticklabels(labels, rotation=45, ha="right")
    ax.set_xlabel("sequence length bin")
    ax.set_ylabel("train sequences")
    ax.set_title("PEER Solubility train: sequence length distribution (n=62478)")
    ax.axvline(6.3, color="red", ls="--", lw=1)
    ax.text(6.35, max(vals) * 0.9, "max_len bin\n(encoders truncate at 512)",
            color="red", fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(FIGURES, "length_distribution.png"), dpi=150)
    plt.close(fig)


def fig_accuracy(models):
    ours = {k: models[k]["accuracy_pct"] for k in ["DDE", "Moran", "CNN", "LSTM"]}
    errs = {k: models[k].get("std_pct", 0.0) for k in ["DDE", "Moran", "CNN", "LSTM"]}
    names = list(ours.keys())
    x = np.arange(len(names))
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(x - 0.18, [ours[k] for k in names], 0.36, yerr=[errs[k] for k in names],
           capsize=3, label="this work (frozen data)", color="#4c72b0")
    ax.bar(x + 0.18, [PAPER[k] for k in names], 0.36,
           label="PEER Table 3", color="#dd8452", alpha=0.85)
    ax.set_xticks(x)
    ax.set_xticklabels(names)
    ax.set_ylabel("test accuracy (%)")
    ax.set_ylim(40, 80)
    ax.grid(axis="y", alpha=0.3)
    ax.axhline(50, color="grey", ls=":", lw=1)
    ax.text(3.42, 50.5, "random guess", fontsize=8, color="grey")
    ax.legend()
    ax.set_title("Solubility classification accuracy: this work vs PEER")
    fig.tight_layout()
    fig.savefig(os.path.join(FIGURES, "accuracy_comparison.png"), dpi=150)
    plt.close(fig)


def main():
    stats = load(os.path.join(RESULTS, "data_stats.json"))
    mm = load(os.path.join(RESULTS, "metrics.json"))
    fig_length_distribution(stats)
    fig_accuracy(mm["models"])
    print("wrote figures:", os.listdir(FIGURES))


if __name__ == "__main__":
    main()