"""Generate figures and analysis exported to evidence/ ."""
import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from aid_common import CLASS_NAMES_17, CLASS_NAMES_30, N_CLASSES_17, N_CLASSES_30


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default=os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "results"))
    ap.add_argument("--evidence", default=os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "evidence"))
    args = ap.parse_args()
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    os.makedirs(args.evidence, exist_ok=True)
    plt.rcParams.update({"font.size": 8})

    # ---- multi-label PR curves ----
    try:
        z = np.load(os.path.join(args.results, "multilabel_test_preds.npz"))
        pred, true = z["pred"], z["true"]
    except Exception as e:
        print("no preds yet:", e)
        return

    from sklearn.metrics import precision_recall_curve, roc_curve, auc

    fig, ax = plt.subplots(figsize=(6, 5))
    for c in range(N_CLASSES_17):
        p, r, _ = precision_recall_curve(true[:, c], pred[:, c])
        apc = auc(r, p)
        if apc < 0.5:
            ax.plot(r, p, lw=0.8, linestyle="--",
                    label=f"{CLASS_NAMES_17[c]} ({apc:.2f})")
        else:
            ax.plot(r, p, lw=0.8, label=f"{CLASS_NAMES_17[c]} ({apc:.2f})")
    ax.set_xlabel("Recall"); ax.set_ylabel("Precision")
    ax.set_title("Multi-label 17-class PR curves (test)")
    ax.legend(fontsize=5, loc="lower left", ncol=2)
    fig.tight_layout()
    fig.savefig(os.path.join(args.evidence, "pr_curves_17.png"), dpi=150)

    # per-class AP bar chart with counts
    fig, ax = plt.subplots(figsize=(9, 4))
    ap_list = []
    for c in range(N_CLASSES_17):
        if true[:, c].sum() == 0:
            ap_list.append(0.0)
            continue
        p, r, _ = precision_recall_curve(true[:, c], pred[:, c])
        ap_list.append(auc(r, p))
    ax.barh(np.arange(N_CLASSES_17)[::-1], ap_list[::-1])
    ax.set_yticks(np.arange(N_CLASSES_17)[::-1])
    ax.set_yticklabels(CLASS_NAMES_17[::-1])
    ax.set_xlabel("Average Precision")
    ax.set_title("Per-class AP (test)")
    fig.tight_layout()
    fig.savefig(os.path.join(args.evidence, "per_class_ap.png"), dpi=150)

    print("wrote evidence figures")


if __name__ == "__main__":
    main()