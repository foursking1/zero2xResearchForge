"""
plot_lpr_results.py
===================
Generate a 3-panel figure (one per experiment) showing performance, learning,
potential, and retention across modification steps, computed from the frozen
reproduction data.

Output: results/lpr_summary_figure.png
"""

import os
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

DATA_ROOT = r"F:/dataset/2604.04878v1"
RESULTS_DIR = os.path.join(DATA_ROOT, "results")
OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
os.makedirs(OUT_DIR, exist_ok=True)

EXPERIMENTS = ["single_shift", "single_shift_limited", "double_shift"]
TITLES = {
    "single_shift": "Single population shift",
    "single_shift_limited": "Single population shift (limited plasticity)",
    "double_shift": "Double population shift",
}

fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))

for ax, exp in zip(axes, EXPERIMENTS):
    with open(os.path.join(RESULTS_DIR, exp, "rep_1_result.json")) as f:
        result = json.load(f)

    diag = np.array([row[i] for i, row in enumerate(result["performance_matrix"])])
    steps = np.arange(len(diag))  # modification steps 0..4

    learning = [r["learning"] for r in result["learning"]]
    potential = [r["potential"] for r in result["potential"]]
    retention = [r["retention"] for r in result["retention"]]
    steps_m = np.arange(1, 5)  # metrics defined for modification steps 1..4

    ax.plot(steps, diag, "o-", color="black", label="Performance (AUROC)")
    ax.plot(steps_m, potential, "s--", color="tab:red", label="Potential")
    ax.plot(steps_m, learning, "D--", color="tab:blue", label="Learning")
    ax.plot(steps_m, retention, "^--", color="tab:green", label="Retention")
    ax.axhline(0.5, color="gray", lw=0.8, ls=":", label="Chance (0.5)")
    ax.set_title(TITLES[exp])
    ax.set_xlabel("Modification step")
    ax.set_xticks(range(5))
    ax.set_ylim(-0.25, 1.05)
    ax.grid(alpha=0.3)
    ax.legend(fontsize=7, loc="best")

fig.suptitle("LPR metrics from frozen reproduction data (n=1 repetition, seed=1042)",
             fontsize=12, y=1.02)
fig.tight_layout()
out = os.path.join(OUT_DIR, "lpr_summary_figure.png")
fig.savefig(out, dpi=150, bbox_inches="tight")
print("Saved:", out)
