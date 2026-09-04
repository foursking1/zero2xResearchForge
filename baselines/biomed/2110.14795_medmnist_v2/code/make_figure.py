#!/usr/bin/env python3
"""Comparison figure: our test AUC/ACC vs paper anchor (ResNet-18@28)."""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
METRICS = os.path.join(HERE, "..", "results", "metrics.json")
OUT = os.path.join(HERE, "..", "evidence", "auc_vs_paper.png")
os.makedirs(os.path.dirname(OUT), exist_ok=True)

m = json.load(open(METRICS))
names = ["bloodmnist", "breastmnist", "dermamnist", "pneumoniamnist", "retinamnist"]
labels = ["Blood", "Breast", "Derma", "Pneumonia", "Retina"]
ours = [m["datasets"][n]["test_auc"] for n in names]
paper = [m["datasets"][n]["paper_auc"] for n in names]
acc = [m["datasets"][n]["test_acc"] for n in names]
n = np.arange(len(names))

fig, ax = plt.subplots(figsize=(8, 4.6))
w = 0.32
b1 = ax.bar(n - w, ours, w, label="Ours (ResNet-18@28, test)", color="#1f77b4")
b2 = ax.bar(n, paper, w, label="Paper anchor (Table 3)", color="#ff7f0e", alpha=0.85)
b3 = ax.bar(n + w, acc, w, label="Ours ACC", color="#2ca02c")
for b in list(b1) + list(b2) + list(b3):
    ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.01,
            f"{b.get_height():.3f}", ha="center", va="bottom", fontsize=7)
ax.axhline(0.90, ls="--", c="grey", lw=0.8)
ax.text(4.45, 0.905, "AUC=0.90 reference", fontsize=7, color="grey", ha="right")
ax.set_xticks(n)
ax.set_xticklabels(labels)
ax.set_ylim(0, 1.08)
ax.set_ylabel("Score")
ax.set_title("MedMNIST v2 2D: reproduced ResNet-18 vs paper anchor (task "
             "2110.14795_medmnist_v2)")
ax.legend(loc="lower right", fontsize=8)
ax.grid(axis="y", alpha=0.3)
plt.tight_layout()
plt.savefig(OUT, dpi=200)
print("saved", OUT)