#!/usr/bin/env python3
"""Step 3 - Train lightweight classifiers on frozen-subset features.

Protocol (mirrors the paper's transfer-learning setup on the 4-image subset):

1.  Stratified 5-fold CV on annotations (crops). A single pool of fold
    partitions is fixed with `seed0`.
2.  Heads:
      - `linprobe` : L2-regularised logistic regression (paper's LinProb).
      - `mlp`      : small MLP (hidden 128) - shallow transfer head.
3.  Data efficiency: for every fold the classifier is fit either on the full
    fold-train set (100%, paper Table 4) or a stratified 10% draw of it
    (paper Table 12), evaluated on the *same* fold-test set. The 10% protocol
    is repeated `--seeds` times (different stratified draws) and predictions
    are pooled.
4.  `--augment` rotates training crops by 0/90/180/270 (rot90 features of
    training patches only; test features always rotation-0). This is standard
    for rotation-invariant mitotic-figure benchmarks and bolsters the
    small-data regime.

Metrics: from cross-validated *pooled* predictions (concatenated across folds)
computes balanced accuracy, weighted F1 and AUROC.

Outputs (agent_solution/results/)
    evidence_table.csv      model,data_fraction,balanced_acc,weighted_f1 (+auroc)
    fold_predictions.csv    per-crop pooled probabilities / true labels (re-computable)
    classifier_detail.json  per-config pooled metrics
"""
from __future__ import annotations
import argparse
import csv
import json
import os
import os.path as osp
import sys

# Limit BLAS threads: projects run in parallel on shared machines; thread
# oversubscription makes small sklearn fits pathologically slow.
for _k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ.setdefault(_k, os.environ.get(_k, "2"))

import numpy as np  # noqa: E402

sys.path.insert(0, osp.dirname(osp.abspath(__file__)))

from sklearn.linear_model import LogisticRegression  # noqa: E402
from sklearn.neural_network import MLPClassifier  # noqa: E402
from sklearn.preprocessing import StandardScaler  # noqa: E402
from sklearn.metrics import (  # noqa: E402
    balanced_accuracy_score,
    precision_recall_fscore_support,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold  # noqa: E402


def load():
    res_dir = osp.join(osp.dirname(osp.abspath(__file__)), "..", "results")
    fz = np.load(osp.join(res_dir, "features.npz"), allow_pickle=True)
    pz = np.load(osp.join(res_dir, "patches.npz"), allow_pickle=True)
    feats = {k: fz[k] for k in ("ResNet18_ImageNet", "ViT_B16_ImageNet")}
    return feats, pz["y"], pz["img_names"], res_dir


def make_head(name: str, seed: int):
    if name == "linprobe":
        return LogisticRegression(
            penalty="l2", C=1.0, max_iter=5000, solver="liblinear",
            class_weight="balanced", random_state=seed,
        )
    if name == "mlp":
        return MLPClassifier(
            hidden_layer_sizes=(128,), activation="tanh", solver="adam",
            alpha=0.01, max_iter=3000, random_state=seed,
        )
    raise ValueError(name)


def evaluate(y_true, y_prob):
    y_pred = (y_prob >= 0.5).astype(int)
    p, r, f, _ = precision_recall_fscore_support(y_true, y_pred, average="weighted", zero_division=0)
    return {
        "weighted_f1": float(f),
        "balanced_acc": float(balanced_accuracy_score(y_true, y_pred)),
        "auroc": float(roc_auc_score(y_true, y_prob)),
        "precision": float(p),
        "recall": float(r),
        "n_pos": int((y_true == 1).sum()),
        "n_neg": int((y_true == 0).sum()),
    }


def subsample_stratified(full_idx, y_full, fraction, seed, rng_seed):
    """Draw a stratified `fraction` of indices from full_idx (for the 10% run)."""
    rng = np.random.RandomState(rng_seed)
    n = max(2, int(round(len(full_idx) * fraction)))
    pos = full_idx[y_full[full_idx] == 1]
    neg = full_idx[y_full[full_idx] == 0]
    if len(pos) > 0 and len(neg) > 0:
        n_pos = max(1, int(round(n * 0.5)))
        n_pos = min(len(pos), n_pos)
        n_neg = min(len(neg), n - n_pos)
        sel = np.concatenate([
            rng.choice(pos, size=n_pos, replace=False),
            rng.choice(neg, size=n_neg, replace=False),
        ])
        return sel[np.argsort(sel)]
    return rng.choice(full_idx, size=n, replace=False)


def run(feats, y, head, fraction, augment, seeds, n_splits=5, seed0=0):
    """Pooled-bagged predictions: for each repetition `rep` a fresh stratified
    CV partition and (for fraction<1) a fresh stratified 10% training draw are
    used; pooled probabilities are averaged per patch across repetitions.
    Returns P = [patch_idx, true_label, prob_positive]."""
    n = len(y)
    acc = np.zeros((n, 3))
    acc[:, 1] = y
    reps = seeds
    for rep in range(reps):
        skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=seed0 + rep * 37)
        for tr_idx, te_idx in skf.split(np.arange(n), y):
            fit_idx = tr_idx
            if fraction < 1.0:
                fit_idx = subsample_stratified(tr_idx, y, fraction, rep, rng_seed=seed0 + rep * 101)
            Xtr = feats[fit_idx, 0]
            ytr = y[fit_idx]
            if augment:
                Xtr = np.concatenate([feats[fit_idx, r] for r in range(4)], axis=0)
                ytr = np.tile(ytr, 4)
            Xte = feats[te_idx, 0]
            yte = y[te_idx]
            sc = StandardScaler().fit(Xtr)
            clf = make_head(head, seed0 + rep * 13)
            clf.fit(sc.transform(Xtr), ytr)
            prob = clf.predict_proba(sc.transform(Xte))[:, 1]
            acc[te_idx, 2] += prob
    acc[:, 2] /= reps
    return acc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=8, help="repetitions for 10% runs")
    ap.add_argument("--folds", type=int, default=5)
    ap.add_argument("--augment", action="store_true", help="use rot90 train augmentation")
    args = ap.parse_args()

    feats, y, img_names, res_dir = load()
    print("features:", {k: v.shape for k, v in feats.items()})
    print("labels (0=hard-neg,1=mitotic):", dict(zip(*np.unique(y, return_counts=True))))

    rows, detail = [], {}
    pred_rows = []
    for model_key, F in feats.items():
        for head in ["linprobe", "mlp"]:
            for frac in (1.0, 0.1):
                P = run(F, y, head, frac, args.augment, args.seeds, args.folds)
                yt = P[:, 1].astype(int)
                pr = evaluate(yt, P[:, 2])
                tag = f"{model_key}|{head}|{int(frac*100)}%"
                detail[tag] = {"metrics": pr, "train_frac": frac,
                               "n_pooled_predictions": int(len(P)),
                               "n_bag_seeds": args.seeds}
                rows.append({
                    "model": f"{model_key}|{head}",
                    "data_fraction": frac,
                    "balanced_acc": round(pr["balanced_acc"], 4),
                    "weighted_f1": round(pr["weighted_f1"], 4),
                    "auroc": round(pr["auroc"], 4),
                })
                for i, (patch_idx, yt_) in enumerate(zip(P[:, 0], P[:, 1])):
                    pred_rows.append({"config": tag, "patch_idx": int(patch_idx),
                                      "true_label": int(yt_), "prob_positive": float(P[i, 2])})
            print()

    with open(osp.join(res_dir, "evidence_table.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["model", "data_fraction", "balanced_acc", "weighted_f1", "auroc"])
        w.writeheader()
        for r in rows:
            w.writerow(r)

    with open(osp.join(res_dir, "fold_predictions.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["config", "patch_idx", "true_label", "prob_positive"])
        w.writeheader()
        w.writerows(pred_rows)

    with open(osp.join(res_dir, "classifier_detail.json"), "w") as f:
        json.dump(detail, f, indent=2)

    print("\nevidence_table.csv")
    hdr = f"{'model':42s} {'frac':5s} {'BAcc':6s} {'F1':6s} {'AUROC':6s}"
    print(hdr)
    for r in rows:
        print(f"{r['model']:42s} {r['data_fraction']:<5} {r['balanced_acc']:<6.3f} {r['weighted_f1']:<6.3f} {r['auroc']:<6.3f}")


if __name__ == "__main__":
    main()