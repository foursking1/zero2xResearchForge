# -*- coding: utf-8 -*-
"""Produce the analysis figures stored under evidence/:
  * per-class bar chart for repro vs enhanced: AUC (left) & F1 (right)
  * combined ROC curves for an example set of classes
Run:  python code/analysis_plots.py
"""
import os
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common  # noqa: E402

OUT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
EVID = os.path.join(OUT, "evidence")
CKPT = os.path.join(OUT, "code", "checkpoints")
os.makedirs(EVID, exist_ok=True)

from sklearn.metrics import roc_curve, auc


def load(model):
    d = np.load(os.path.join(CKPT, f"{model}_pred.npz"))
    return d["y_test"], d["p_test_ens"]


def main():
    yt_r, pr_r = load("repro")
    yt_e, pr_e = load("enhanced")

    # ---- Figure 1: per-class AUC / F1 side by side ----
    auc_r = common.per_class_auc(yt_r, pr_r)
    auc_e = common.per_class_auc(yt_e, pr_e)
    thr_e = np.load(os.path.join(CKPT, "enhanced_pred.npz"))["thresholds"]
    f1_r = common.per_class_f1(yt_r, (pr_r >= 0.5).astype(float))
    f1_e = common.per_class_f1(yt_e, (pr_e >= thr_e).astype(float))

    x = np.arange(len(common.LABELS))
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    ax = axes[0]
    w = 0.38
    ax.bar(x - w/2, auc_r, w, label="CheXNet repro (BCE, thr=0.5)", color="#4C72B0")
    ax.bar(x + w/2, auc_e, w, label="enhanced (Focal+thr tuning)", color="#DD8452")
    ax.axhline(0.79, color="#4C72B0", ls="--", lw=1, label="paper CheXNet\naverage AUC 0.79")
    ax.axhline(0.85, color="#DD8452", ls="--", lw=1, label="paper DACNet\naverage AUC 0.85")
    ax.set_xticks(x); ax.set_xticklabels(common.LABELS, rotation=45, ha="right")
    ax.set_ylabel("ROC-AUC"); ax.set_title("Per-class ROC-AUC (frozen test shard)")
    ax.legend(fontsize=8); ax.set_ylim(0.0, 1.0)

    ax = axes[1]
    ax.bar(x - w/2, f1_r, w, label="CheXNet repro (thr=0.5)", color="#4C72B0")
    ax.bar(x + w/2, f1_e, w, label="enhanced (tuned thr)", color="#DD8452")
    ax.set_xticks(x); ax.set_xticklabels(common.LABELS, rotation=45, ha="right")
    ax.set_ylabel("F1"); ax.set_title("Per-class F1 at (tuned) threshold")
    ax.legend(fontsize=8); ax.set_ylim(0.0, 1.0)
    fig.suptitle("NIH ChestX-ray14 frozen subset (1082 train / 162 val / 640 test) "
                 "- ImageNet DenseNet-121 fine-tune")
    fig.tight_layout()
    fig.savefig(os.path.join(EVID, "per_class_auc_f1.png"), dpi=140)
    plt.close(fig)

    # ---- Figure 2: ROC curves for a sample of classes, both models ----
    classes = ["Atelectasis", "Infiltration", "Mass", "Pneumonia"]
    fig, axes = plt.subplots(1, 4, figsize=(18, 5))
    for ax, cl in zip(axes, classes):
        c = common.LABELS.index(cl)
        for lbl, yt, pt, colr in [("repro", yt_r, pr_r, "#4C72B0"),
                                  ("enhanced", yt_e, pr_e, "#DD8452")]:
            if yt[:, c].sum() == 0:
                continue
            fpr, tpr, _ = roc_curve(yt[:, c], pt[:, c])
            ax.plot(fpr, tpr, color=colr, lw=1.6,
                    label=f"{lbl} (AUC={auc(fpr, tpr):.3f})")
        ax.plot([0, 1], [0, 1], color="gray", ls=":", lw=1)
        ax.set_title(f"{cl} (test n+ ={int(yt_r[:, c].sum())})")
        ax.set_xlabel("FPR")
        if c == 0:
            ax.set_ylabel("TPR")
        ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(EVID, "roc_examples.png"), dpi=140)
    plt.close(fig)
    print("figures written to", EVID)


if __name__ == "__main__":
    main()