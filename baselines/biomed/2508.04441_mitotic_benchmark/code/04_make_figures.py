#!/usr/bin/env python3
"""Step 4 - Figures for the report (evidence/).

Produces:
  evidence/crop_montage.png   sample mitotic vs hard-negative crops
  evidence/roc_best_models.png  ROC for best 100% and 10% configs
  evidence/data_efficiency.png  10% vs 100% comparison bar chart
  evidence/annotations_by_image.png  per-image positive/negative counts
"""
from __future__ import annotations
import csv
import json
import os
import os.path as osp

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.metrics import roc_curve, auc

res_dir = osp.join(osp.dirname(osp.abspath(__file__)), "..", "results")
ev_dir = osp.join(osp.dirname(osp.abspath(__file__)), "..", "evidence")
os.makedirs(ev_dir, exist_ok=True)

pz = np.load(osp.join(res_dir, "patches.npz"), allow_pickle=True)
X, y = pz["X"], pz["y"]
with open(osp.join(res_dir, "annotations_stats.json")) as f:
    stats = json.load(f)

# --- 1. crop montage -------------------------------------------------------
rng = np.random.RandomState(0)
pos = np.where(y == 1)[0]
neg = np.where(y == 0)[0]
sel_pos = rng.choice(pos, size=min(8, len(pos)), replace=False)
sel_neg = rng.choice(neg, size=min(8, len(neg)), replace=False)
fig, axes = plt.subplots(2, 8, figsize=(16, 4.2))
for j in range(8):
    for row, sel in ((0, sel_pos), (1, sel_neg)):
        img = X[sel[j]][:, :, :3]
        lo, hi = np.percentile(img, 1), np.percentile(img, 99)
        img = np.clip((img.astype(float) - lo) / max(1.0, hi - lo), 0, 1)
        axes[row, j].imshow(img)
        axes[row, j].axis("off")
axes[0, 0].set_title("mitotic figures")
axes[1, 0].set_title("hard negatives")
plt.suptitle("MIDOG2022 frozen-subset 224x224 crops (RGB, contrast stretched)")
plt.tight_layout()
plt.savefig(osp.join(ev_dir, "crop_montage.png"), dpi=120)
plt.close()

# --- 2. ROC for best configs ------------------------------------------------
with open(osp.join(res_dir, "fold_predictions.csv")) as f:
    preds = list(csv.DictReader(f))
with open(osp.join(res_dir, "evidence_table.csv")) as f:
    table = list(csv.DictReader(f))
best100 = max([r for r in table if abs(float(r["data_fraction"]) - 1.0) < 1e-6],
              key=lambda r: float(r["weighted_f1"]))["model"]
# pick a model that has BOTH 100% and 10% evidence rows for the efficiency plot
both = {r["model"] for r in table if abs(float(r["data_fraction"]) - 1.0) < 1e-6} \
       & {r["model"] for r in table if abs(float(r["data_fraction"]) - 0.1) < 1e-6}
best_both = max([r for r in table if r["model"] in both and float(r["data_fraction"]) == 1.0],
                key=lambda r: float(r["weighted_f1"]))["model"]
cfg100 = f"{best_both}|100%"
cfg10 = f"{best_both}|10%"
fig, ax = plt.subplots(figsize=(5.2, 5.2))
for cfg, label in ((cfg100, "100% train data"), (cfg10, "10% train data")):
    t = np.array([[float(r["true_label"]), float(r["prob_positive"])]
                  for r in preds if r["config"] == cfg])
    fpr, tpr, _ = roc_curve(t[:, 0], t[:, 1])
    ax.plot(fpr, tpr, label=f"{label} (AUC={auc(fpr, tpr):.3f})")
ax.plot([0, 1], [0, 1], "--", color="grey", lw=0.8)
ax.set_xlabel("False positive rate"); ax.set_ylabel("True positive rate")
ax.set_title(f"ROC (pooled 5-fold CV) - {best_both}")
ax.legend()
plt.tight_layout()
plt.savefig(osp.join(ev_dir, "roc_best_models.png"), dpi=120)
plt.close()

# --- 3. data efficiency -----------------------------------------------------
fig, ax = plt.subplots(figsize=(6, 3.6))
fracs = ["100%", "10%"]
vals = {r["model"]: (float(r["data_fraction"]) == 1.0) for r in table}
models = ["ResNet18_ImageNet|linprobe", "ResNet18_ImageNet|mlp",
          "ViT_B16_ImageNet|linprobe", "ViT_B16_ImageNet|mlp"]
import numpy as np
x = np.arange(len(models)); w = 0.35
f1_100 = [float(next(r["weighted_f1"] for r in table if r["model"] == m and float(r["data_fraction"]) == 1.0)) for m in models]
f1_10 = [float(next(r["weighted_f1"] for r in table if r["model"] == m and float(r["data_fraction"]) == 0.1)) for m in models]
ax.bar(x - w / 2, f1_100, w, label="100%", color="#4C72B0")
ax.bar(x + w / 2, f1_10, w, label="10%", color="#DD8452")
ax.axhline(0.72, color="grey", ls=":", lw=1)
ax.text(len(models) - 0.55, 0.725, "paper 10% Virchow2 linprobe F1=0.72", fontsize=7, color="grey")
ax.set_xticks(x); ax.set_xticklabels([m.split("|")[0] + "\n" + m.split("|")[1] for m in models], fontsize=8)
ax.set_ylabel("Weighted F1 (pooled 5-fold CV)")
ax.set_ylim(0, 0.95)
ax.legend(title="train data")
ax.set_title("Data efficiency: 10% vs 100% of frozen subset")
plt.tight_layout()
plt.savefig(osp.join(ev_dir, "data_efficiency.png"), dpi=120)
plt.close()

# --- 4. annotations by image ------------------------------------------------
fig, ax = plt.subplots(figsize=(5.6, 3.4))
names = ["002.png", "008.png", "024.png", "063.png"]
pos_c = [stats["per_image_mitotic"][n] for n in names]
neg_c = [stats["per_image_hard_negative"][n] for n in names]
x = np.arange(len(names)); w = 0.38
ax.bar(x - w / 2, pos_c, w, label="mitotic", color="#C44E52")
ax.bar(x + w / 2, neg_c, w, label="hard negative", color="#55A868")
ax.set_xticks(x); ax.set_xticklabels(names, fontsize=8)
ax.set_ylabel("annotations")
ax.legend()
ax.set_title("Frozen subset annotations (total 62 + 91)")
plt.tight_layout()
plt.savefig(osp.join(ev_dir, "annotations_by_image.png"), dpi=120)
plt.close()

print("figures written to", ev_dir)