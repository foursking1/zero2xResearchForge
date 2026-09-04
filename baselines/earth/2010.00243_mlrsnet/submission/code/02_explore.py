#!/usr/bin/env python3
"""02_explore.py -- dataset-level description & diagnostics (frozen data only).

Produces figures:
  fig_label_distribution.png   per-class positive counts (train vs test)
  fig_labels_per_image.png     histogram of number of labels per image
  fig_cooccurrence_top.png     top co-occurring label pairs in the TRAIN split
and prints aggregate numbers used in the report.
"""
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch
from torch.utils.data import DataLoader

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
from mlrs import CLASS_NAMES, DATA_WORK, MLRSNetMemmap

ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
FIG = os.path.join(ROOT, "submission", "figures")
os.makedirs(FIG, exist_ok=True)

with open(os.path.join(DATA_WORK, "ds_summary.json")) as f:
    S = json.load(f)

ntr = np.array(S["n_train_by_class"], dtype=int)
nte = np.array(S["n_test_by_class"], dtype=int)

# ---- label distribution (train vs test) ----
fig, ax = plt.subplots(figsize=(14, 6))
x = np.arange(60)
ax.bar(x - 0.2, ntr, width=0.4, label="train", color="#4C72B0")
ax.bar(x + 0.2, nte, width=0.4, label="test", color="#DD8452")
ax.set_xticks(x)
ax.set_xticklabels([f"{i}:{CLASS_NAMES[i]}" for i in range(60)], rotation=90, fontsize=7)
ax.set_ylabel("positive images")
ax.set_title("MLRSNet 40/60 frozen split — per-class label frequencies")
ax.legend()
fig.tight_layout()
fig.savefig(os.path.join(FIG, "fig_label_distribution.png"), dpi=150)
plt.close(fig)

# ---- labels per image ----
tr_lab = MLRSNetMemmap(os.path.join(DATA_WORK, "train_labels.dat"))
te_lab = MLRSNetMemmap(os.path.join(DATA_WORK, "test_labels.dat"))
fig, ax = plt.subplots(figsize=(7, 4))
for name, lab in [("train", tr_lab.labels), ("test", te_lab.labels)]:
    n = lab.sum(1)
    ax.hist(n, bins=np.arange(0.5, 10.5, 1), alpha=0.5, label=f"{name} (μ={n.mean():.2f})")
ax.set_xlabel("number of labels per image")
ax.set_ylabel("images")
ax.set_title("Multi-label cardinality")
ax.legend()
fig.tight_layout()
fig.savefig(os.path.join(FIG, "fig_labels_per_image.png"), dpi=150)
plt.close(fig)

# ---- co-occurrence within TRAIN split only ----
mat = tr_lab.labels.astype(np.int8)
norm = mat.T @ mat
np.fill_diagonal(norm, 0)
i, j = np.unravel_index(np.argsort(norm, axis=None)[::-1][:10], norm.shape)
print("Top co-occurring label pairs (train only):")
pairs = []
for a_, b_, c_ in zip(i, j, norm[i, j]):
    if a_ < b_:
        pairs.append((int(a_), int(b_), int(c_)))
    print(f"  {a_}:{CLASS_NAMES[a_]:<26} <> {b_}:{CLASS_NAMES[b_]:<26}  n={int(c_)}")

fig, ax = plt.subplots(figsize=(8, 5))
mn = np.ma.masked_invalid(norm)
ax.imshow(norm.min(axis=1) - 1 + np.ones_like(norm), cmap="Blues", aspect="auto")
ax.axis("off")
ax.set_title("Label co-occurrence matrix (train split)")
fig.tight_layout()
fig.savefig(os.path.join(FIG, "fig_cooccurrence_top.png"), dpi=150)
plt.close(fig)

print("\nAggregates:")
print(f"  images total={S['n_images']} train={S['n_train']} test={S['n_test']}")
print(f"  mean labels/image train={S['mean_labels_train']:.3f} test={S['mean_labels_test']:.3f}")
print(f"  min/max labels/image = {S['min_labels']} / {S['max_labels']}")
print(f"  most frequent class (train): {CLASS_NAMES[int(ntr.argmax())]} n={int(ntr.max())}")
print(f"  rarest class (train): {CLASS_NAMES[int(ntr.argmin())]} n={int(ntr.min())}")
print(f"  most frequent class (test): {CLASS_NAMES[int(nte.argmax())]} n={int(nte.max())}")
print(f"  rarest class (test): {CLASS_NAMES[int(nte.argmin())]} n={int(nte.min())}")
print(f"  classes present in train: {(ntr>0).sum()}/60 ; in test: {(nte>0).sum()}/60")