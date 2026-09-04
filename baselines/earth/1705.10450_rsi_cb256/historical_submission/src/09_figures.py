"""Generate report figures (matplotlib, Agg backend).

Figure 1: per-class test accuracy vs train support (label_2, 35 classes).
Figure 2: top confusion pairs (model-directed).
Figure 3: coarse vs fine label agreement (label_1 vs label_2 mappings sanity).
"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import LABEL2_NAMES, RESULTS_DIR, EVIDENCE_DIR, load_labels  # noqa: E402

import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

plt.rcParams.update({"font.size": 9})


def main():
    os.makedirs(EVIDENCE_DIR, exist_ok=True)
    d = np.load(os.path.join(RESULTS_DIR, "predictions.npz"), allow_pickle=False)
    t2, p2, t1, p1 = d["true_l2"], d["pred2"], d["true_l1"], d["pred1"]
    lab = load_labels()
    l1, l2, split = lab["label_1"], lab["label_2"], lab["split"]
    tr = split == "train"
    te = split == "test"

    # figure 1: accuracy vs support
    acc = (p2 == t2)
    fig, ax = plt.subplots(figsize=(7, 4.5))
    for c in range(35):
        sup = int((l2[tr] == c).sum())
        ca = float(acc[t2 == c].mean()) if (t2 == c).any() else 0
        ax.scatter(sup, ca, s=28, alpha=0.75)
        ax.annotate(LABEL2_NAMES[c], (sup, ca), fontsize=6, alpha=0.8)
    ax.axhline(0.95, ls="--", color="orange", lw=1, label="anchor 95.13% band")
    ax.set_xlabel("train support (instances)"); ax.set_ylabel("test accuracy")
    ax.set_title("RSI-CB256 label_2 (35 classes): per-class test accuracy vs train support")
    ax.legend()
    fig.tight_layout(); fig.savefig(os.path.join(EVIDENCE_DIR, "figure_accuracy_vs_support.png"), dpi=150)
    plt.close(fig)

    # figure 2: top confusion pairs
    from sklearn.metrics import confusion_matrix
    conf = confusion_matrix(t2, p2, labels=list(range(35)))
    pairs = []
    for i in range(35):
        for j in range(35):
            if i != j and conf[i, j] > 0:
                pairs.append((conf[i, j], i, j))
    pairs.sort(reverse=True)
    top = pairs[:10]
    fig, ax = plt.subplots(figsize=(7, 3.6))
    ypos = np.arange(len(top))
    names = [f"{LABEL2_NAMES[a]} -> {LABEL2_NAMES[b]}" for _, a, b in top]
    ax.barh(ypos, [c for c, _, _ in top], color="crimson", alpha=0.8)
    ax.set_yticks(ypos); ax.set_yticklabels(names); ax.invert_yaxis()
    ax.set_xlabel("# test images misclassified"); ax.set_title("Top-10 confusion pairs (label_2)")
    fig.tight_layout(); fig.savefig(os.path.join(EVIDENCE_DIR, "figure_confusion_top.png"), dpi=150)
    plt.close(fig)

    # figure 3: hierarchy consistency of model outputs
    # canonical fine->coarse mapping learned from TRAIN labels only
    canon = {}
    for c in range(35):
        coarse = l1[tr][l2[tr] == c]
        canon[c] = int(np.bincount(coarse, minlength=7).argmax()) if len(coarse) else -1
    consistency = float((p1 == np.array([canon[c] for c in p2])).mean())
    print(f"[fig] hierarchy consistency (pred coarse == canonical of pred fine): "
          f"{consistency*100:.2f}%")
    hier = pd.DataFrame({"fine_class": LABEL2_NAMES,
                         "canonical_coarse_id": [canon[c] for c in range(35)]})
    hier.to_csv(os.path.join(RESULTS_DIR, "hierarchy_mapping.csv"), index=False)
    top_pairs = pd.DataFrame([
        {"n_misclassified": int(c), "true_class": LABEL2_NAMES[a],
         "pred_class": LABEL2_NAMES[b]} for c, a, b in pairs[:15]])
    top_pairs.to_csv(os.path.join(RESULTS_DIR, "confusion_top_pairs.csv"), index=False)
    print("[fig] saved figures to evidence/")


if __name__ == "__main__":
    main()