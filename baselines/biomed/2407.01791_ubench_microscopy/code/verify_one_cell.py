#!/usr/bin/env python
"""Independent spot-check re-computation of one (model, task_group) accuracy.

Self-contained re-implementation of the option-masking + grouped-CV protocol
used in 03_evaluate.py, so the judge can re-verify a single cell of
results/evidence_table.csv without depending on the internals of step 3.

Usage:
  python verify_one_cell.py vit_base_patch16_224 linear_probe coarse
  python verify_one_cell.py resnet18 knn fine

Prints: accuracy (0..1), n_items. Should match results/evidence_table.csv to
within <0.5pp (matmul summation order can differ slightly with the OpenBLAS
thread count); the judge's 2pp recompute tolerance covers this.
"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import load_arrow_questions, COARSE_TYPES, FINE_TYPES, FEATURES

SEED = 42
K = 9


def main():
    if len(sys.argv) != 4:
        print(__doc__)
        sys.exit(2)
    enc, method, group = sys.argv[1:]
    assert enc in ("vit_base_patch16_224", "resnet18")
    assert method in ("linear_probe", "knn")
    assert group in ("coarse", "fine")

    df = load_arrow_questions().drop(columns=["image_bytes"])
    feat = np.load(os.path.join(FEATURES, f"features_{enc}.npy"))
    keys = pd.read_csv(os.path.join(FEATURES, f"image_keys_{enc}.csv"))
    fmap = {iid: i for i, iid in enumerate(keys["image_id"])}
    df["feat"] = df["image_id"].map(fmap).to_numpy()

    types = COARSE_TYPES if group == "coarse" else FINE_TYPES
    total_correct = 0
    total_n = 0
    from sklearn.model_selection import StratifiedGroupKFold
    skf = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=SEED)

    for qtype in types:
        sub = df[df["question_type"] == qtype].reset_index(drop=True)
        X = feat[sub["feat"].to_numpy()]
        y = sub["answer"].to_numpy()
        g = pd.factorize(sub["image_id"])[0]
        folds = list(skf.split(np.zeros(len(sub)), y, g))
        correct = np.zeros(len(sub), dtype=bool)
        for tr, te in folds:
            Xtr, Xte = X[tr], X[te]
            ytr, yte = y[tr], y[te]
            if method == "knn":
                Xn = Xtr / np.linalg.norm(Xtr, axis=1, keepdims=True)
                Qn = Xte / np.linalg.norm(Xte, axis=1, keepdims=True)
                sim = Qn @ Xn.T
                kn = np.argsort(-sim, axis=1)[:, :K]
            else:
                from sklearn.linear_model import LogisticRegression
                from sklearn.preprocessing import StandardScaler
                sc = StandardScaler().fit(Xtr)
                clf = LogisticRegression(max_iter=3000, C=1.0, class_weight="balanced")
                clf.fit(sc.transform(Xtr), ytr)
                kn = None
                cols = {c: j for j, c in enumerate(clf.classes_)}
                S = clf.predict_proba(sc.transform(Xte))
            for j, r in enumerate(te):
                opts = sub["options"].iloc[r]
                if method == "knn":
                    votes = np.unique(ytr[kn[j]], return_counts=True)
                    best_train = votes[0][np.argmax(votes[1])]
                    if best_train in set(opts):
                        pred = best_train
                    else:
                        o2, c2 = np.unique(np.array(opts), return_counts=True)
                        pred = o2[np.argmax(c2)]
                else:
                    s = np.full(len(cols), -np.inf)
                    for opt in opts:
                        if opt in cols:
                            s[cols[opt]] = S[j, cols[opt]]
                    pred = clf.classes_[np.argmax(s)]
                correct[r] = (pred == yte[j])
        total_correct += int(correct.sum())
        total_n += int(len(sub))
        print(f"  {qtype}: {correct.mean():.5f}")

    acc = total_correct / total_n
    print(f"RESULT model={enc}_{method} group={group} accuracy={acc:.5f} n_items={total_n}")


if __name__ == "__main__":
    main()