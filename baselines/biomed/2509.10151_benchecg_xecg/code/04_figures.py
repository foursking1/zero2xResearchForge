#!/usr/bin/env python3
"""Step 4 - figures for the report (ECG example, ROC curves, comparison chart).

All inputs come from results/ artefacts produced by the previous scripts (all on
the frozen data). US-ASCII-safe labels; matplotlib default backend (Agg).
"""
import json
import os
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.metrics import roc_curve, auc

RESULTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")


def load_prep():
    d = np.load(os.path.join(RESULTS, "preprocessed.npz"), allow_pickle=False)
    return d


def fig_ecg_example(d):
    X = d["Xtrain"]  # (n, T, ch) at 100 Hz
    idx = 0
    leads_names = ["I", "II", "III", "aVR", "aVL", "aVF", "V1", "V2", "V3", "V4", "V5", "V6"]
    t = np.arange(X.shape[1]) / 100.0
    fig, axes = plt.subplots(12, 1, figsize=(9, 10), sharex=True)
    for j, ax in enumerate(axes):
        ax.plot(t, X[idx, :, j], lw=0.6, color="C0")
        ax.set_ylabel(leads_names[j], fontsize=8)
        ax.yaxis.set_ticks([])
        ax.spines[["top", "right", "left"]].set_visible(False)
    axes[-1].set_xlabel("time [s]")
    fig.suptitle("Example 12-lead ECG (PTB-XL-small, frozen validation split, record #%d, 100 Hz)" % idx)
    fig.tight_layout()
    fig.savefig(os.path.join(RESULTS, "fig_ecg_example.png"), dpi=140)
    plt.close(fig)


def fig_roc(d, preds):
    tva = np.asarray(preds["tva"])
    y_cnn = np.asarray(preds["cnn_preds_seed42"])
    y_lr = np.asarray(preds["lr_preds"])
    tasks = ["sex", "age_ge65"]
    fig, axes = plt.subplots(1, 2, figsize=(9, 4))
    for j, task in enumerate(tasks):
        for y, label, style in [
            (y_cnn, "1D-CNN (seed 42)", "-"),
            (y_lr, "LogReg handcrafted feats", "--"),
        ]:
            fpr, tpr, _ = roc_curve(tva[:, j], y[:, j])
            axes[j].plot(fpr, tpr, style, lw=1.5, label=f"{label} (AUC={auc(fpr, tpr):.3f})")
        axes[j].plot([0, 1], [0, 1], ":", color="grey", lw=1)
        axes[j].set_xlabel("FPR"); axes[j].set_ylabel("TPR")
        axes[j].set_title(f"ROC - target: {task}")
        axes[j].legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(os.path.join(RESULTS, "fig_roc_curves.png"), dpi=140)
    plt.close(fig)


def fig_compare():
    mm = json.load(open(os.path.join(RESULTS, "model_metrics.json")))
    cnn = mm["cnn_seed_summary"]
    lr = mm["results"]["logreg_manual_feats"]
    cats = ["macro AUROC", "macro F1 @0.5"]
    cnn_vals = [cnn["macro_auroc"]["mean"], cnn["macro_f1@0.5"]["mean"]]
    lr_vals = [lr["macro_auroc"], lr["macro_f1@0.5"]]
    x = np.arange(len(cats))
    fig, ax = plt.subplots(figsize=(6.5, 4))
    ax.bar(x - 0.2, cnn_vals, 0.4, label="1D-CNN (mean over 3 seeds)")
    ax.bar(x + 0.2, lr_vals, 0.4, label="LogReg handcrafted feats", color="C3")
    for xi, (cv, lv) in enumerate(zip(cnn_vals, lr_vals)):
        ax.text(xi - 0.2, cv + 0.01, f"{cv:.3f}", ha="center", fontsize=9)
        ax.text(xi + 0.2, lv + 0.01, f"{lv:.3f}", ha="center", fontsize=9)
    ax.set_ylim(0, 1.0)
    ax.set_xticks(x); ax.set_xticklabels(cats)
    ax.set_ylabel("score")
    ax.legend(fontsize=9)
    ax.set_title(
        "Auxiliary frozen-target tasks (sex, age>=65): deep vs shallow baseline\n"
        "(NOT the paper's diagnostic task - frozen package has no diagnostic labels)"
    )
    fig.tight_layout()
    fig.savefig(os.path.join(RESULTS, "fig_model_compare.png"), dpi=140)
    plt.close(fig)


def main():
    d = load_prep()
    preds = json.load(open(os.path.join(RESULTS, "predictions_for_figs.json")))
    fig_ecg_example(d)
    fig_roc(d, preds)
    fig_compare()
    print("figures written to", RESULTS)


if __name__ == "__main__":
    main()