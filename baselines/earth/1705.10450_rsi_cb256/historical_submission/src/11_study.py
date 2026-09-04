"""Robustness study: metrics on the full test set vs the 'hard' subset with
near-duplicate test items removed (cos>=0.99 or 0.999 of any train image).

Uses frozen features (dup_flags.npz) + classifier predictions:
  - probe (LogisticRegression, C=0.30) for reference
  - final model predictions from results/predictions.npz (if present)

Output results/robustness_study.json
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import N_L2, RESULTS_DIR, load_labels  # noqa: E402
from sklearn.linear_model import LogisticRegression  # noqa: E402
from sklearn.metrics import accuracy_score, f1_score  # noqa: E402


def oa_mf1(y, p):
    return (float(accuracy_score(y, p)),
            float(f1_score(y, p, average="macro", labels=list(range(N_L2)),
                           zero_division=0)))


def main():
    lab = load_labels()
    l2, split = lab["label_2"], lab["split"]
    tr, te = split == "train", split == "test"
    flags = np.load(os.path.join(RESULTS_DIR, "dup_flags.npz"))
    d099 = ~flags["test_dup_099"]
    d0999 = ~flags["test_dup_0999"]

    study = {"full_test_size": int(te.sum()),
             "n_nondup_099": int(d099.sum()),
             "n_nondup_0999": int(d0999.sum())}

    # probe
    d = np.load(os.path.join(RESULTS_DIR, "features_resnet18_224.npz"))
    feat = d["feat"]
    clf = LogisticRegression(max_iter=2000, C=0.30, n_jobs=4)
    clf.fit(feat[tr], l2[tr])
    pred = clf.predict(feat[te])
    y = l2[te]
    study["probe_full"] = dict(zip(["oa", "macro_f1"], oa_mf1(y, pred)))
    study["probe_nondup_099"] = dict(zip(["oa", "macro_f1"], oa_mf1(y[d099], pred[d099])))
    study["probe_nondup_0999"] = dict(zip(["oa", "macro_f1"], oa_mf1(y[d0999], pred[d0999])))

    # final model (if present)
    predis = os.path.join(RESULTS_DIR, "predictions.npz")
    if os.path.exists(predis):
        predd = np.load(predis)
        p2 = predd["pred2"]
        study["final_model_full"] = dict(zip(["oa", "macro_f1"],
                                             oa_mf1(y, p2)))
        study["final_model_nondup_099"] = dict(zip(["oa", "macro_f1"],
                                                   oa_mf1(y[d099], p2[d099])))
        study["final_model_nondup_0999"] = dict(zip(["oa", "macro_f1"],
                                                    oa_mf1(y[d0999], p2[d0999])))
    with open(os.path.join(RESULTS_DIR, "robustness_study.json"), "w") as fp:
        json.dump(study, fp, indent=2, default=str)
    print(json.dumps(study, indent=2, default=str))


if __name__ == "__main__":
    main()