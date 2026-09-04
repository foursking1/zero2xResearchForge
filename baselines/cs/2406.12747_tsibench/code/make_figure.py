#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Figure: ETT_h1, 10% point missingness, test MAE per imputer across the three
fixed masks seeds {42, 43, 44} vs. paper Table 2 values.

Writes: ../evidence/seed_sensitivity.png  and  ../evidence/mae_by_baseline.csv
"""
import os
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "..", "results")
EVIDENCE = os.path.join(HERE, "..", "evidence")
os.makedirs(EVIDENCE, exist_ok=True)

with open(os.path.join(RESULTS, "metrics.json")) as f:
    m = json.load(f)

order = ["Linear", "LOCF", "Median", "Mean"]
paper = {"Linear": 0.197, "LOCF": 0.315, "Median": 0.71, "Mean": 0.737}
seeds = m["seeds"]

per_seed_mae = {b: m["aggregated"][b]["per_seed_mae"] for b in order}
mean = {b: m["aggregated"][b]["mae_mean"] for b in order}
std = {b: m["aggregated"][b]["mae_std"] for b in order}

rows = []
for b in order:
    for s, v in zip(seeds, per_seed_mae[b]):
        rows.append({"baseline": b, "seed": s, "mae": v})
    rows.append({"baseline": b, "seed": "paper_table2", "mae": paper[b]})
pdf = pd.DataFrame(rows)
pdf.to_csv(os.path.join(EVIDENCE, "mae_by_baseline.csv"), index=False)

colors = ["#4C72B0", "#DD8452", "#55A868", "#C44E52"]
fig, ax = plt.subplots(figsize=(9.5, 5.2))
x = np.arange(len(order))
w = 0.22
for i, s in enumerate(seeds):
    ax.bar(x + (i - 1) * w, [per_seed_mae[b][i] for b in order], w,
           label=f"this work, seed={s}", color=colors[i], alpha=0.92)
ax.errorbar(x, [mean[b] for b in order], yerr=[std[b] for b in order],
            fmt="ko", capsize=5, ms=4, label="mean $\\pm$ std (our 3 seeds)")
ax.scatter(x, [paper[b] for b in order], marker="D", s=64, facecolors="none",
           edgecolors="black", zorder=5, label="paper Table 2 (TSI-Bench)")

for i, b in enumerate(order):
    ax.annotate(f"{mean[b]:.3f}", (i, mean[b] + max(std.values()) + 0.03),
                ha="center", fontsize=10, fontweight="bold")

ax.set_xticks(x)
ax.set_xticklabels(order, fontsize=12)
ax.set_ylabel("Test MAE (standardized units)", fontsize=12)
ax.set_title("ETT_h1, 10% single-point missingness: simple-baseline imputation MAE\n"
             "(mask evaluated only on test masked positions; train-only z-score)",
             fontsize=12)
ax.legend(fontsize=9, loc="upper left")
ax.grid(axis="y", alpha=0.3)
ax.set_ylim(0, 1.1)
plt.tight_layout()
plt.savefig(os.path.join(EVIDENCE, "seed_sensitivity.png"), dpi=150)
print("saved", os.path.join(EVIDENCE, "seed_sensitivity.png"))
print("saved", os.path.join(EVIDENCE, "mae_by_baseline.csv"))