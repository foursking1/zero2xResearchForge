"""Analysis exports for the report (run after both trainings finish):
- top-1-in-ground-truth single-label-perspective rate on the multi-label mirror
- class-difficulty correlation (AP vs training count)
- confusion matrix figure for the 30-class single-label model
"""
import argparse
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
    from sklearn.metrics import average_precision_score
    os.environ.setdefault("MPLBACKEND", "Agg")
    os.makedirs(args.evidence, exist_ok=True)

    # ---- single-label-perspective on multi-label mirror ----
    z = np.load(os.path.join(args.results, "multilabel_test_preds.npz"))
    pred, true = z["pred"], z["true"]
    top1 = pred.argmax(1)
    top1_hit = np.mean([true[i, top1[i]] for i in range(len(true))])
    print("multi-label mirror: top-1-in-GT = %.4f" % top1_hit)

    # ---- challenge: AP vs train count ----
    per_ap = [average_precision_score(true[:, c], pred[:, c]) for c in range(N_CLASSES_17)]
    ids = np.arange(N_CLASSES_17)
    print("AP by class (asc):")
    order = np.argsort(per_ap)
    for c in order:
        print(f"  {CLASS_NAMES_17[c]:12s} ap={per_ap[c]:.3f}")

    # ---- 30-class confusion matrix ----
    try:
        z30 = np.load(os.path.join(args.results, "singlelabel_test_preds.npz"))
        p30, t30 = z30["pred"], z30["true"]
        preds = p30.argmax(1)
        oa = float((preds == t30).mean())
        print("single-label 30-class OA = %.4f" % oa)
        cm_path = os.path.join(args.results, "confusion_30.npy")
        cm = np.load(cm_path)

        fig, ax = plt.subplots(figsize=(14, 12))
        im = ax.imshow(cm, cmap="Blues")
        ax.set_xticks(np.arange(N_CLASSES_30))
        ax.set_yticks(np.arange(N_CLASSES_30))
        ax.set_xticklabels(CLASS_NAMES_30, rotation=90, fontsize=6)
        ax.set_yticklabels(CLASS_NAMES_30, fontsize=6)
        ax.set_xlabel("Predicted")
        ax.set_ylabel("True")
        fig.colorbar(im)
        fig.tight_layout()
        fig.savefig(os.path.join(args.evidence, "confusion_30.png"), dpi=150)

        # wrong-class pairs
        rows = []
        for i in range(N_CLASSES_30):
            for j in range(N_CLASSES_30):
                if i != j and cm[i, j] > 0:
                    rows.append((int(cm[i, j]), CLASS_NAMES_30[i], CLASS_NAMES_30[j]))
        rows.sort(reverse=True)
        print("\nTop 15 confusion pairs (true->pred):")
        for n, a, b in rows[:15]:
            print(f"  {a:18s}->{b:18s} {n}")
    except Exception as e:
        print("30-class analysis deferred:", e)


if __name__ == "__main__":
    main()