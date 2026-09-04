"""Seed/logit ensembling over saved per-row scores.

Usage:
  python3 -m code.ensemble "concat_regress_*" --out results/ensemble.json
Combines scores from all results/eval_scores_<wildcard>.pkl files
(majority/binary via averaged logits, count via averaged regression value or
binned-logit average) and reports the accuracy against the stored targets.
"""
import argparse
import glob
import json
import os
import pickle

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(HERE, "results")


def load_scores(pattern):
    files = sorted(glob.glob(os.path.join(RESULTS, f"eval_scores_{pattern}.pkl")))
    assert files, f"no score files for {pattern}"
    items = []
    for f in files:
        with open(f, "rb") as fh:
            d = pickle.load(fh)
        items.append((os.path.basename(f), d))
    return items


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pattern")
    ap.add_argument("--out", default=None)
    ap.add_argument("--mode", default="scores", choices=["scores", "vote"])
    args = ap.parse_args()

    items = load_scores(args.pattern)
    qtypes = items[0][1]["qtypes"]
    targets = items[0][1]["targets"]
    n = len(targets)
    n_files = len(items)

    def qtype(i):
        # 3 == count else binary/rural
        return "count" if qtypes[i] == 3 else "binary"

    # ensemble: average yn logits; average regr log1p; for hybrid average bin logits
    ens_cnt_reg = np.zeros(n)
    ens_cnt_bin = None
    ens_yn = np.zeros((n, 2))
    have_reg = np.zeros(n, dtype=bool)
    votes = []  # per-model integer predictions (for majority voting)
    for _, d in items:
        s = d["scores"]
        ens_yn += np.stack([x["yn"] for x in s])
        v = np.zeros(n, dtype=np.int64)
        for i in range(n):
            c = s[i]["cnt"]
            if c.shape[0] == 1:
                ens_cnt_reg[i] += c[0]
                have_reg[i] = True
            else:
                if ens_cnt_bin is None:
                    ens_cnt_bin = np.zeros((n, c.shape[0]))
                ens_cnt_bin[i] += c
            if qtypes[i] == 3:
                v[i] = int(c.argmax()) if c.shape[0] > 1 else int(max(0, round(np.expm1(c[0]))))
            else:
                v[i] = int(s[i]["yn"].argmax())
        votes.append(v)
    ens_yn /= n_files
    votes = np.stack(votes)

    preds = np.zeros(n, dtype=np.int64)
    for i in range(n):
        if qtypes[i] == 3:
            if args.mode == "vote":
                uv, cc = np.unique(votes[:, i], return_counts=True)
                preds[i] = uv[cc.argmax()]
            elif ens_cnt_bin is not None:
                top = ens_cnt_bin.shape[1] - 1
                b = int(ens_cnt_bin[i].argmax())
                preds[i] = b if b < top else int(max(0, round(np.expm1(ens_cnt_reg[i] / n_files))))
            else:
                preds[i] = int(max(0, round(np.expm1(ens_cnt_reg[i] / n_files))))
        else:
            if args.mode == "vote":
                uv, cc = np.unique(votes[:, i], return_counts=True)
                preds[i] = uv[cc.argmax()]
            else:
                preds[i] = int(ens_yn[i].argmax())

    correct = preds == targets
    by_type = {
        "count": round(float(correct[qtypes == 3].mean()), 5),
        "binary": round(float(correct[qtypes != 3].mean()), 5),
    }

    res = {"n_models": n_files, "overall_accuracy": round(float(correct.mean()), 5),
           "accuracy_count": by_type["count"], "accuracy_binary": by_type["binary"]}
    print(json.dumps(res, indent=2))
    if args.out:
        os.makedirs(os.path.dirname(os.path.join(RESULTS, args.out)), exist_ok=True)
        with open(os.path.join(RESULTS, args.out), "w") as f:
            json.dump(res, f, indent=2)
    return res


if __name__ == "__main__":
    main()