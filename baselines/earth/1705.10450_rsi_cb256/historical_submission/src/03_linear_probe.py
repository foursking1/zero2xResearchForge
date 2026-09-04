"""Fast baseline: logistic regression / linear probe on frozen ResNet18 features.

Uses sklearn LogisticRegression on the 512-d GAP features; reports OA (35-way
label_2), macro-F1 and label_1 accuracy. Nothing leaks into the test split:
the probe is fit only on train features, stats only on the test set.
"""
import os
import sys
import json

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import RESULTS_DIR, SEED, LABEL1_NAMES, LABEL2_NAMES, load_labels, set_seed  # noqa: E402

from sklearn.linear_model import LogisticRegression  # noqa: E402
from sklearn.metrics import accuracy_score, f1_score, precision_recall_fscore_support  # noqa: E402


def main():
    set_seed()
    d = np.load(os.path.join(RESULTS_DIR, "features_resnet18_224.npz"))
    feat = d["feat"]
    lab = load_labels()
    l1, l2 = lab["label_1"], lab["label_2"]
    split = lab["split"]
    tr, te = split == "train", split == "test"
    print(f"[probe] train {tr.sum()} test {te.sum()}")

    for C in (0.1, 0.3, 1.0, 3.0, 10.0):
        clf = LogisticRegression(max_iter=2000, C=C, n_jobs=8)
        clf.fit(feat[tr], l2[tr])
        pred = clf.predict(feat[te])
        oa = accuracy_score(l2[te], pred)
        mf1 = f1_score(l2[te], pred, average="macro")
        print(f"  C={C:5.2f}  test OA(label2,35c)={oa*100:.3f}%  macroF1={mf1*100:.2f}%")
    # keep best-C dict for reference
    res = {f"C={C}": float(accuracy_score(
        LogisticRegression(max_iter=2000, C=C, n_jobs=8).fit(feat[tr], l2[tr]).predict(feat[te]),
        l2[te])) for C in (0.1, 0.3, 1.0, 3.0, 10.0)}
    with open(os.path.join(RESULTS_DIR, "probe_summary.json"), "w") as fp:
        json.dump(res, fp, indent=2)
    print("[probe] summary saved")


if __name__ == "__main__":
    main()