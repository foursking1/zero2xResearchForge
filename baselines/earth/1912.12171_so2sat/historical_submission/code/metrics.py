"""Shared metric computation. All metrics follow the paper's Table V definitions:
OA  = overall accuracy
WA  = weighted accuracy (weighted by class support) == OA
AA  = average accuracy (unweighted mean class recall)
Kappa = Cohen's kappa
"""
import json
import os
import numpy as np
from sklearn.metrics import accuracy_score, cohen_kappa_score, confusion_matrix

N_CLASSES = 17


def compute_metrics(labels, preds, split, bands, seed, train_size, out_dir):
    labels = np.asarray(labels, dtype=np.int64)
    preds = np.asarray(preds, dtype=np.int64)
    cm = confusion_matrix(labels, preds, labels=list(range(N_CLASSES)))
    tn = cm.sum(axis=1) - np.diag(cm)
    fp = cm.sum(axis=0) - np.diag(cm)
    tp = np.diag(cm)
    fn = cm.sum(axis=1) - tp
    support = cm.sum(axis=1)

    prec = np.divide(tp, tp + fp, out=np.full(N_CLASSES, np.nan), where=(tp + fp) > 0)
    rec = np.divide(tp, tp + fn, out=np.full(N_CLASSES, np.nan), where=(tp + fn) > 0)
    f1 = np.divide(2 * tp, 2 * tp + fp + fn, out=np.full(N_CLASSES, np.nan), where=(2 * tp + fp + fn) > 0)

    oa = accuracy_score(labels, preds)
    wa = oa  # weighted accuracy = eq. OA when weights = class support
    aa = float(np.nanmean(rec))
    kappa = float(cohen_kappa_score(labels, preds))

    rows = []
    os.makedirs(out_dir, exist_ok=True)
    for c in range(N_CLASSES):
        rows.append({
            "split": split, "class_id": int(c), "precision": float(prec[c]),
            "recall": float(rec[c]), "f1": float(f1[c]), "support": int(support[c]),
        })
    rows.append({
        "split": split, "class_id": -1, "precision": float(oa), "recall": float(aa),
        "f1": float(np.nanmean(f1)), "support": int(len(labels)),
    })
    ev_path = os.path.join(out_dir, "evidence_table.csv")
    with open(ev_path, "w") as fh:
        fh.write("split,class_id,precision,recall,f1,support\n")
        for r in rows:
            fh.write(f"{r['split']},{r['class_id']},{r['precision']:.6f},{r['recall']:.6f},{r['f1']:.6f},{r['support']}\n")

    metrics = {
        "overall_accuracy": float(oa),
        "weighted_accuracy": float(wa),
        "average_accuracy": float(aa),
        "kappa": float(kappa),
        "train_size": int(train_size),
        "seed": int(seed),
        "bands_used": str(bands),
    }
    with open(os.path.join(out_dir, "metrics.json"), "w") as fh:
        json.dump(metrics, fh, indent=2)
    np.save(os.path.join(out_dir, "confusion_matrix.npy"), cm)
    np.save(os.path.join(out_dir, "labels.npy"), labels)
    np.save(os.path.join(out_dir, "preds.npy"), preds)
    print(f"[{split}/{bands}] OA={oa:.4f} AA={aa:.4f} Kappa={kappa:.4f}")
    return metrics, cm