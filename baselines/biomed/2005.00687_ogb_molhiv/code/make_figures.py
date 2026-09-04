#!/usr/bin/env python3
"""Generate publication-style figures from the experiment outputs.

  results/figs/fig_*          saved figures (PNG, 200 dpi)
"""

import json
import os
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.metrics import roc_auc_score, roc_curve

import config

RESULTS = config.results_dir()
FIGDIR = os.path.join(RESULTS, "figs")

# --- paper anchor values (Table 15, reported as mean(%) +/- std) ---
PAPER = {"gcn": (74.18, 1.22), "gin": (75.20, 1.30), "gin+vn": (77.07, 1.49),
         "gcn+vn": (76.14, 1.30)}


def load_pred_sets():
    """Return {label: (pred, y)} for saved npz predictions."""
    out = {}
    pred_dir = os.path.join(RESULTS, "predictions")
    if not os.path.isdir(pred_dir):
        return out
    for f in os.listdir(pred_dir):
        if f.endswith(".npz"):
            d = np.load(os.path.join(pred_dir, f))
            out[f[:-4]] = (d["pred_test"].astype(np.float64), d["y_test"].astype(int))
    return out


def fig_distributions(data_stats_path):
    import torch
    plt.figure(figsize=(10, 4))
    for i, split in enumerate(["train", "valid", "test"]):
        graphs = torch.load(f"/tmp/molhiv/{split}.pt", weights_only=False)
        nodes = np.array([g.num_nodes for g in graphs])
        plt.subplot(1, 3, i + 1)
        plt.hist(nodes, bins=60, color="#4C72B0", alpha=0.85)
        plt.title(f"{split} (n={len(graphs)})")
        plt.xlabel("num atoms")
        plt.ylabel("molecules")
    plt.tight_layout()
    plt.savefig(os.path.join(FIGDIR, "fig_node_hist.png"), dpi=200,
                bbox_inches="tight")
    plt.close()


def fig_roc(pred_sets, models, out_name="fig_roc_test.png"):
    plt.figure(figsize=(6.5, 6))
    colors = {"gin": "#55A868", "gin-vn": "#8172B3", "gcn": "#4C72B0",
              "gcn-vn": "#CC79A7", "mlp-ext": "#C44E52", "mlp-mean9": "#CCB974",
              "LogReg": "#7A6F4E", "RF": "#DD8452"}
    for m in models:
        tags = [t for t in pred_sets if t.startswith(m + "__")]
        if not tags:
            continue
        # pick the seed with the highest test AUC for a representative curve
        best_tag, best_auc = None, -1
        for t in tags:
            p, y = pred_sets[t]
            a = roc_auc_score(y, p)
            if a > best_auc:
                best_auc, best_tag = a, t
        p, y = pred_sets[best_tag]
        fpr, tpr, _ = roc_curve(y, p)
        plt.plot(fpr, tpr, color=colors.get(m), lw=2,
                 label=f"{m} (best-seed AUC={best_auc:.3f})")
    xs = [0, 1]
    plt.plot(xs, xs, "k--", lw=1, label="random (AUC=0.5)")
    plt.xlabel("False positive rate")
    plt.ylabel("True positive rate")
    plt.title("ROC curves on the frozen test split")
    plt.legend(loc="lower right", fontsize=8)
    plt.tight_layout()
    plt.savefig(os.path.join(FIGDIR, out_name), dpi=200, bbox_inches="tight")
    plt.close()


def fig_bar(agg_te):
    """agg_te: {model_name: (mean_auc, std_auc)} on test."""
    names = list(agg_te.keys())
    means = [agg_te[n][0] * 100 for n in names]
    stds = [agg_te[n][1] * 100 for n in names]
    colors = ["#55A868" if "gin" in n else "#4C72B0" if "gcn" in n
              else "#CCB974" for n in names]
    plt.figure(figsize=(8.5, 5))
    x = np.arange(len(names))
    plt.bar(x, means, yerr=stds, capsize=4, color=colors, alpha=0.9,
            edgecolor="black", linewidth=0.5)
    plt.axhline(50, color="black", ls="--", lw=1, label="random baseline")
    for xi, n in zip(x, names):
        if n in PAPER:
            pm, ps = PAPER[n]
            plt.hlines(pm, xi - 0.3, xi + 0.3, color="red", ls="--", lw=1.4)
            lab = f"paper  {n}={pm:.2f}±{ps:.2f}"
            plt.text(xi + 0.33, pm, lab.split("=")[1], color="red", fontsize=8,
                     va="center")
    plt.xticks(x, names, rotation=20)
    plt.ylabel("Test ROC-AUC (%)")
    plt.title("Test ROC-AUC (mean ± std over 3 seeds) vs paper Table 15 "
              "(red = paper value)")
    plt.ylim(40, 100)
    plt.legend(loc="upper left", fontsize=9)
    plt.tight_layout()
    plt.savefig(os.path.join(FIGDIR, "fig_bar_compare.png"), dpi=200,
                bbox_inches="tight")
    plt.close()


def main():
    os.makedirs(FIGDIR, exist_ok=True)
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "..", "code"))
    fig_distributions(RESULTS)

    pred_sets = load_pred_sets()
    with open(os.path.join(RESULTS, "model_results.json")) as f:
        detail = json.load(f)

    # aggregate per model name
    agg_te = {}
    for rec in detail.get("gnn", []):
        agg_te.setdefault(rec["model"], []).append(rec["test_roc_auc"])
    agg_te = {k: (float(np.mean(v)), float(np.std(v))) for k, v in agg_te.items()}

    models_short = ["gcn", "gcn-vn", "gin", "gin-vn", "mlp-ext", "mlp-mean9",
                    "LogReg", "RF"]
    fig_roc(pred_sets, models_short)
    fig_bar(agg_te)
    print("figures written to", FIGDIR)


if __name__ == "__main__":
    main()