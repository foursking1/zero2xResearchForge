"""Evaluation utilities shared by finetune + final eval.

All metrics are computed from predictions produced on the frozen test subset.
"""
import numpy as np
import torch
from sklearn.metrics import (accuracy_score, confusion_matrix,
                             f1_score, precision_recall_fscore_support)

from common import N_L1, N_L2, normalize  # noqa: E402


def predict_test(model, imgmem, l2, l1, te, batch=64, return_probs=False):
    """Run the frozen test subset through the model (eval, no grad)."""
    te_idx = np.where(te)[0]
    model.eval()
    p2_all, p1_all = [], []
    with torch.no_grad():
        for s in range(0, len(te_idx), batch):
            ids = te_idx[s:s + batch]
            xb = np.ascontiguousarray(imgmem[ids])
            xt = torch.tensor(normalize(xb).transpose(0, 3, 1, 2))
            logits2, logits1, _ = model.embed_and_logits(xt)
            p2_all.append(logits2.softmax(-1).numpy())
            p1_all.append(logits1.softmax(-1).numpy())
    p2 = np.concatenate(p2_all).astype(np.float32)
    p1 = np.concatenate(p1_all).astype(np.float32)
    return np.argmax(p2, 1), np.argmax(p1, 1), p2, p1


def class_metrics(y_true, y_pred, n_classes):
    """Per-class and aggregate metrics. TP/FP/TN/FN are one-vs-rest."""
    ps, rs, fs, sup = precision_recall_fscore_support(
        y_true, y_pred, labels=list(range(n_classes)), zero_division=0)
    rows = []
    conf = confusion_matrix(y_true, y_pred, labels=list(range(n_classes)))
    for c in range(n_classes):
        tp = int(conf[c, c])
        fn = int(conf[c, :].sum()) - tp
        fp = int(conf[:, c].sum()) - tp
        tn = int(conf.sum()) - tp - fp - fn
        rows.append({
            "split": "test", "class_level": 2 if n_classes == 35 else 1,
            "class_id": c, "tp": tp, "fp": fp, "tn": tn, "fn": fn,
            "precision": float(ps[c]), "recall": float(rs[c]),
            "f1": float(fs[c]), "accuracy": float((tp + tn) / conf.sum()),
        })
    oa = accuracy_score(y_true, y_pred)
    mf1 = f1_score(y_true, y_pred, average="macro", labels=list(range(n_classes)),
                   zero_division=0)
    return rows, oa, mf1


def evaluate_model(model, imgmem, l2, l1, te, quick=False, batch=64):
    """Full or batched-diagnostic evaluation; returns (oa, l1_acc, mf1)."""
    if quick:
        te_idx = np.where(te)[0]
        rng = np.random.RandomState(0)
        ids = rng.choice(te_idx, size=min(4000, te_idx.size), replace=False)
        teb = np.zeros_like(te)
        teb[ids] = True
        pred2, pred1, _, _ = predict_test(model, imgmem, l2, l1, teb, batch)
        oa = accuracy_score(l2[teb], pred2)
        l1a = accuracy_score(l1[teb], pred1)
        mf1 = f1_score(l2[teb], pred2, average="macro", zero_division=0)
        return float(oa), float(l1a), float(mf1)
    pred2, pred1, p2, p1 = predict_test(model, imgmem, l2, l1, te, batch)
    oa = accuracy_score(l2[te], pred2)
    l1a = accuracy_score(l1[te], pred1)
    mf1 = f1_score(l2[te], pred2, average="macro", zero_division=0)
    return float(oa), float(l1a), float(mf1), pred2, pred1, p2, p1