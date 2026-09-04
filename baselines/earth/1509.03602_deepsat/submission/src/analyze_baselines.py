#!/usr/bin/env python3
"""Shallow / non-deep baselines for contrast (report support).

Computes, on the same fixed-seed 70/15/15 split:
  1. majority-class baseline  (predict the most frequent training class);
  2. linear (logistic regression) on flattened raw RGB pixels;
  3. (optional) k-nearest-neighbour on PCA features.

Only ever uses the train subset for fitting; metrics reported on the
held-out test subset. Nothing here is used for hyper-parameter tuning of
the reported CNN (which is why this is analysis, not the main result).
"""
import argparse
import time

import numpy as np
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import train_test_split

from common import CLASS_NAMES, decode_images, load_dataframe, resolve_data_path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=None)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--max-train", type=int, default=56700)
    args = ap.parse_args()

    df = load_dataframe(resolve_data_path(args.data))
    labels = df["label"].to_numpy(np.int64)
    images = decode_images(df).astype(np.float32) / 255.0
    n, h, w, c = images.shape
    X = images.reshape(n, -1)  # n x 2352

    all_idx = np.arange(n)
    tr0, tmp = train_test_split(all_idx, train_size=0.70,
                                random_state=args.seed, stratify=labels)
    va, te = train_test_split(tmp, train_size=0.50,
                              random_state=args.seed + 1, stratify=labels[tmp])
    if len(tr0) > args.max_train:
        tr0 = tr0[:args.max_train]

    Xtr, ytr = X[tr0], labels[tr0]
    Xte, yte = X[te], labels[te]

    majority = np.bincount(ytr).argmax()
    maj_acc = float((yte == majority).mean())
    print(f"[baseline] majority-class ({CLASS_NAMES[majority]}): "
          f"test accuracy = {maj_acc:.4f}")

    # fast linear baseline: logistic regression on PCA-reduced pixels.
    # Raw 2352-dim lbfgs is too slow on a shared CPU box; 90 principal
    # components retain ~all variance of these smooth 28x28 tiles.
    t = time.time()
    pca = PCA(n_components=90, random_state=args.seed).fit(Xtr)
    Xt_r, Xe_r = pca.transform(Xtr), pca.transform(Xte)
    print(f"[baseline] PCA {Xt_r.shape[1]} components, "
          f"explained-var {pca.explained_variance_ratio_.sum():.4f} "
          f"({time.time()-t:.0f}s)")
    t = time.time()
    clf = LogisticRegression(max_iter=500, C=1.0, solver="lbfgs", n_jobs=-1)
    clf.fit(Xt_r, ytr)
    yp = clf.predict(Xe_r)
    lr_acc = float(accuracy_score(yte, yp))
    print(f"[baseline] logistic-regression on PCA pixels: "
          f"test accuracy = {lr_acc:.4f}, "
          f"macro-F1 = {f1_score(yte, yp, average='macro'):.4f} "
          f"({time.time()-t:.0f}s)")

    param = {
        "majority_test_accuracy": round(maj_acc, 6),
        "majority_class": CLASS_NAMES[majority],
        "logreg_test_accuracy": round(lr_acc, 6),
        "logreg_test_macro_f1": round(float(f1_score(yte, yp, average="macro")), 6),
        "pca_components": int(pca.n_components),
        "train_size": int(len(tr0)), "test_size": int(len(te)),
        "seed": args.seed,
    }
    import json, os
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results",
                       "baselines.json")
    with open(out, "w") as f:
        json.dump(param, f, indent=2)
    print(f"[baseline] saved params -> {out}")


if __name__ == "__main__":
    main()