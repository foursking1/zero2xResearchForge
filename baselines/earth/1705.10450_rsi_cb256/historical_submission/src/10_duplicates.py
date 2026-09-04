"""Characterize potential train/test near-duplication in the frozen split.

Crowdsourced single-split datasets often contain multiple photographs of the
same ground object; a random 50/50 split can place near-identical scenes on both
sides. We estimate this using the frozen ResNet18 features (cosine similarity of
the 512-d embeddings):

  - for a sample of TRAIN images, distance to nearest TEST neighbor;
  - fraction of train samples whose nearest test neighbor has cosine sim >= 0.99
    (near-duplicate) vs typical within-class similarity.

Outputs results/duplicate_analysis.json (reported transparently in report.md).
"""
import json
import os
import sys

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import RESULTS_DIR, load_labels  # noqa: E402


def main():
    d = np.load(os.path.join(RESULTS_DIR, "features_resnet18_224.npz"))
    feat = d["feat"].astype(np.float32)
    lab = load_labels()
    l2, split = lab["label_2"], lab["split"]
    tr, te = split == "train", split == "test"
    ftr, fte = feat[tr], feat[te]
    ltr, lte = l2[tr], l2[te]
    rng = np.random.RandomState(0)
    idx = rng.choice(ftr.shape[0], size=min(8000, ftr.shape[0]), replace=False)
    S = cosine_similarity(ftr[idx], fte)  # [B, n_test]
    best = S.max(axis=1)
    same_class = np.zeros(len(idx), bool)
    for k, i in enumerate(idx):
        # closest test neighbor of the same label
        m = S[k, lte == ltr[i]]
        same_class[k] = bool(m.max() >= best[k]) if m.size else False
    out = {
        "checked_train_samples": int(len(idx)),
        "frac_near_dup_test_neighbor_0.99": float((best >= 0.99).mean()),
        "frac_near_dup_0.999": float((best >= 0.999).mean()),
        "median_best_cosine": float(np.median(best)),
        "p25_best_cosine": float(np.percentile(best, 25)),
        "p75_best_cosine": float(np.percentile(best, 75)),
        "note": "near-dup = best test neighbor cosine>=threshold; "
                "mirror is a single split, 50/50 split by the benchmark",
    }
    with open(os.path.join(RESULTS_DIR, "duplicate_analysis.json"), "w") as fp:
        json.dump(out, fp, indent=2)
    # save per-test-image "near-dup of some train image" flag (scan ALL train features)
    S2 = cosine_similarity(fte, ftr)
    test_dup_099 = (S2.max(axis=1) >= 0.99)
    test_dup_0999 = (S2.max(axis=1) >= 0.999)
    np.savez_compressed(os.path.join(RESULTS_DIR, "dup_flags.npz"),
                        test_dup_099=test_dup_099, test_dup_0999=test_dup_0999)
    out.update({
        "test_frac_dup_099": float(test_dup_099.mean()),
        "test_frac_dup_0999": float(test_dup_0999.mean()),
    })
    with open(os.path.join(RESULTS_DIR, "duplicate_analysis.json"), "w") as fp:
        json.dump(out, fp, indent=2)
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()