"""k-mer shallow baseline.

Count k-mer (default 4-mer) frequencies per sequence, standardize
(row-normalize by total k-mers), then fit Logistic Regression
(and Random Forest, for a second shallow reference) on the frozen
train split and evaluate on the frozen test split.

Usage:
    python3 run_baseline.py [--k 4] [--model lr] [--data_dir <path>]
Produces results/baseline_kmer.json
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(Path(__file__).resolve().parent))
from data_utils import DATASETS, TASK_METRIC, find_data_dir, load_dataset, seq_stats  # noqa: E402
from eval_metrics import evaluate  # noqa: E402

SEED = 42
VALID_BASES = set("ACGT")


def kmer_counts(seq: str, k: int) -> Counter:
    c = Counter()
    for i in range(len(seq) - k + 1):
        c[seq[i : i + k]] += 1
    return c


class KmerVectorizer:
    """Build fixed vocabulary over training k-mers and vectorize sequences."""

    def __init__(self, k: int = 4, min_df: int = 3, max_features: int = 100000):
        self.k = k
        self.min_df = min_df
        self.max_features = max_features
        self.vocab_: list[str] = []
        self._idx: dict[str, int] = {}

    def fit(self, seqs: list[str]) -> "KmerVectorizer":
        df: Counter = Counter()
        for s in seqs:
            for km, n in kmer_counts(s, self.k).items():
                if km in df:
                    df[km] += 1
                else:
                    df[km] = 1
        candidates = sorted(
            (km for km, c in df.items() if c >= self.min_df and len(km) == self.k),
            key=lambda x: (-df[x], x),
        )
        self.vocab_ = candidates[: self.max_features]
        self._idx = {km: i for i, km in enumerate(self.vocab_)}
        return self

    def transform(self, seqs: list[str]) -> np.ndarray:
        X = np.zeros((len(seqs), len(self.vocab_)), dtype=np.float32)
        for i, s in enumerate(seqs):
            for km in kmer_counts(s, self.k):
                j = self._idx.get(km)
                if j is not None:
                    X[i, j] += 1
        return X

    def fit_transform(self, seqs: list[str]) -> np.ndarray:
        return self.fit(seqs).transform(seqs)


def run_task(dataset: str, k: int, model_name: str, data_dir: Path, subset_max: int) -> dict:
    data = load_dataset(data_dir, dataset)
    tr_seqs, tr_y = data["train"]
    te_seqs, te_y = data["test"]
    if subset_max and subset_max > 0 and len(tr_seqs) > subset_max:
        rng = np.random.RandomState(SEED)
        keep = rng.choice(len(tr_seqs), subset_max, replace=False)
        tr_seqs = [tr_seqs[i] for i in keep]
        tr_y = [tr_y[i] for i in keep]

    vec = KmerVectorizer(k=k)
    X_tr = vec.fit_transform(tr_seqs)
    X_te = vec.transform(te_seqs)
    scaler = StandardScaler(with_mean=False)
    X_tr_s = scaler.fit_transform(X_tr)
    X_te_s = scaler.transform(X_te)

    if model_name == "lr":
        clf = LogisticRegression(max_iter=2000, C=1.0, solver="lbfgs", random_state=SEED, n_jobs=-1)
    else:
        clf = RandomForestClassifier(n_estimators=300, n_jobs=-1, random_state=SEED)
    clf.fit(X_tr_s, tr_y)
    pred = clf.predict(X_te_s).astype(int).tolist()
    metric = TASK_METRIC[dataset]
    scores = evaluate(te_y, pred, metric)
    return {
        "dataset": dataset,
        "k": k,
        "model": model_name,
        "train_n": len(tr_seqs),
        "test_n": len(te_seqs),
        "vocab": len(vec.vocab_),
        "metrics": scores,
        "primary_metric": metric,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--k", type=int, default=4)
    ap.add_argument("--model", choices=["lr", "rf"], default="lr")
    ap.add_argument("--data_dir", type=str, default=None)
    ap.add_argument("--subset_max", type=int, default=0, help="cap training size (0=all)")
    ap.add_argument("--out", type=str, default="results/baseline_kmer.json")
    args = ap.parse_args()

    data_dir = Path(args.data_dir) if args.data_dir else find_data_dir()
    results = {}
    series = {}
    for ds in DATASETS:
        r = run_task(ds, args.k, args.model, data_dir, args.subset_max)
        results[ds] = r
        series[f"k{args.k}_{ds}_{args.model}"] = r["metrics"]
        print(
            f"[{ds}] train={r['train_n']} test={r['test_n']} "
            f"vocab={r['vocab']} primary={r['primary_metric']}={r['metrics'][r['primary_metric']]} "
            f"acc={r['metrics']['acc']} f1={r['metrics']['f1']} mcc={r['metrics']['mcc']}"
        )
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(series, indent=2))
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()