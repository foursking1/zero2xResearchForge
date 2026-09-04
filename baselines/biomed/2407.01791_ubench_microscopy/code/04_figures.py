#!/usr/bin/env python
"""Step 4: make evidence figures from results/.
Outputs: evidence/coarse_fine_acc.png, evidence/per_type_acc.png,
         evidence/dataset_composition.png
"""
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import RESULTS, EVIDENCE

plt.rcParams.update({"font.size": 10, "axes.grid": True, "grid.alpha": 0.3})

ev = pd.read_csv(os.path.join(RESULTS, "evidence_table.csv"))
per_type = pd.read_csv(os.path.join(RESULTS, "per_type_accuracy.csv"))
df_stats = json.load(open(os.path.join(RESULTS, "dataset_stats.json")))


def short(name):
    return name.replace("vit_base_patch16_224", "ViT-B/16").replace(
        "resnet18", "ResNet-18").replace("_linear_probe", "·linear-probe").replace(
        "_knn", "·kNN").replace("_", " ")


def enc_name(name):
    if "vit" in name:
        return "ViT-B/16"
    if "resnet" in name:
        return "ResNet-18"
    return "baseline"


# ---- figure 1: coarse vs fine per model with GPT-4o reference ----
real = ev[~ev["model"].str.startswith("majority")]
models = list(real["model"].unique())
lab = [short(m) for m in models]
x = np.arange(len(models) * 2)
fig, ax = plt.subplots(figsize=(9.5, 4.6))
coarse = real[real["task_group"] == "coarse"]
fine = real[real["task_group"] == "fine"]
colors = {"ViT-B/16": "#4C72B0", "ResNet-18": "#DD8452"}
for j, m in enumerate(models):
    c = coarse[coarse["model"] == m]
    f = fine[fine["model"] == m]
    kw = {"facecolor": colors[enc_name(m)], "edgecolor": "black", "linewidth": 0.6}
    yc, yf = c["accuracy"].iloc[0] * 100, f["accuracy"].iloc[0] * 100
    yerr_c = [[(c["accuracy"].iloc[0] - c["ci_low"].iloc[0]) * 100],
              [(c["ci_high"].iloc[0] - c["accuracy"].iloc[0]) * 100]]
    yerr_f = [[(f["accuracy"].iloc[0] - f["ci_low"].iloc[0]) * 100],
              [(f["ci_high"].iloc[0] - f["accuracy"].iloc[0]) * 100]]
    marker_c = "s" if "knn" in m else "o"
    marker_f = "^" if "knn" in m else "D"
    ax.errorbar(x[2 * j], yc, yerr=yerr_c, fmt=marker_c,
                color=colors[enc_name(m)], capsize=3, ms=5,
                label=lab[j] if "knn" not in m else None)
    ax.errorbar(x[2 * j + 1], yf, yerr=yerr_f, fmt=marker_f,
                color=colors[enc_name(m)], capsize=3, ms=5)
ax.axhline(62.6, ls="--", color="#4C72B0", alpha=0.55)
ax.axhline(51.7, ls="--", color="#C44E52", alpha=0.55)
ax.annotate("GPT-4o coarse (paper) 62.6%", xy=(0.02, 62.6), xytext=(0.02, 87),
            fontsize=8, color="#4C72B0")
ax.annotate("GPT-4o fine (paper) 51.7%", xy=(0.02, 51.7), xytext=(0.02, 44.7),
            fontsize=8, color="#C44E52")
ax.set_xticks([x[2 * j] + 0.5 for j in range(len(models))])
ax.set_xticklabels([short(m).split("·")[0] for m in models], fontsize=9)
ax.set_ylabel("accuracy (%)")
ax.set_ylim(0, 108)
from matplotlib.lines import Line2D
h1 = [Line2D([0], [0], marker=o, color="none", markerfacecolor=c, markersize=8,
             label=l) for o, c, l in
      [("o", "#4C72B0", "coarse — linear-probe"), ("D", "#4C72B0", "fine — linear-probe"),
       ("s", "#DD8452", "coarse — kNN"), ("^", "#DD8452", "fine — kNN")]]
h2 = [Patch(color=colors[k], label=k) for k in colors]
ax.legend(handles=h1 + h2, loc="upper left", fontsize=8, ncol=1)
fig.tight_layout()
fig.savefig(os.path.join(EVIDENCE, "coarse_fine_acc.png"), dpi=200)
plt.close(fig)

# ---- figure 2: per-question-type accuracy ----
order = ["modality", "submodality", "domain", "subdomain", "stain", "classification"]
types = [t for t in order if t in set(per_type["question_type"])]
fig, ax = plt.subplots(figsize=(8.5, 4.8))
cols = {"vit_base_patch16_224": "#4C72B0", "resnet18": "#DD8452"}
styles = {"_linear_probe": "o-", "_knn": "s--"}
for m in per_type["model"].unique():
    sub = per_type[per_type["model"] == m].set_index("question_type")
    y = [sub.loc[t, "accuracy"] * 100 if t in sub.index else np.nan for t in types]
    err_lo = [max(0, (sub.loc[t, "accuracy"] - sub.loc[t, "ci_low"]) * 100) if t in sub.index else 0 for t in types]
    err_hi = [max(0, (sub.loc[t, "ci_high"] - sub.loc[t, "accuracy"]) * 100) if t in sub.index else 0 for t in types]
    base = m.replace("_linear_probe", "").replace("_knn", "")
    method = "_linear_probe" if m.endswith("linear_probe") else "_knn"
    ax.errorbar(types, y, yerr=[err_lo, err_hi], fmt=styles[method],
                color=cols[base], alpha=0.65 if method == "_knn" else 1.0,
                label=short(m), capsize=3)
ax.axhline(0.70 * 100, ls=":", color="gray", alpha=0.7)
ax.annotate("70% (claim threshold)", xy=(0.02, 71), fontsize=8, color="gray")
ax.set_ylabel("accuracy (%)")
ax.set_ylim(30, 105)
ax.set_title("Accuracy by question type (grouped 5-fold CV)")
ax.legend(fontsize=8)
fig.tight_layout()
fig.savefig(os.path.join(EVIDENCE, "per_type_acc.png"), dpi=200)
plt.close(fig)

# ---- figure 3: modal/domain composition of the shard ----
fig, axes = plt.subplots(1, 3, figsize=(11, 3.4))
for ax, key, title in zip(axes, ["modality_counts", "domain_counts", "submodality_counts"],
                          ["Modality", "Domain", "Submodality"]):
    d = df_stats[key]
    labels = list(d.keys())
    vals = list(d.values())
    bars = ax.barh(labels, vals, color="#4C72B0")
    ax.invert_yaxis()
    ax.set_title(title)
    ax.tick_params(axis="y", labelsize=7)
    for r, v in zip(bars, vals):
        ax.text(v + 5, r.get_y() + r.get_height() / 2, str(v), va="center", fontsize=7)
    ax.set_xlim(0, max(vals) * 1.15)
fig.tight_layout()
fig.savefig(os.path.join(EVIDENCE, "dataset_composition.png"), dpi=200)
plt.close(fig)
print("figures written to", EVIDENCE)