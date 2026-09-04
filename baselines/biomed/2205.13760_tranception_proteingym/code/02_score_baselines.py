"""Non-LM baseline scorers for ProteinGym substitutions.

Baselines (all zero-shot; never see DMS scores, no training):
  1. BLOSUM62          - site-independent substitution log-odds score:
                         score = sum_i BLOSUM62[wt_i, mut_i].
  2. BLOSUM62_norm     - per-position normalised version (z-score over the 20
                         AA exchanges at each position) to test robustness of
                         the simple baseline.
  3. null_uniform      - fixed-seed uniform noise (sanity floor; Spearman ~ 0).

Usage:  python 02_score_baselines.py
"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common import AA20, AA_TO_IDX, ASSAYS, BLOSUM62, ROOT, load_assay

rng = np.random.default_rng(seed=1234)


def blosum62_scores(df):
    out = np.empty(len(df), dtype=np.float64)
    for i, subs in enumerate(df["subs"]):
        out[i] = sum(BLOSUM62[wt + mut] for _, wt, mut in subs)
    return out


def blosum62_norm_scores(df):
    """Per-position normalised BLOSUM62: at each position z-score the 20
    exchange scores (mean/std over AA at that position), sum over positions."""
    out = np.empty(len(df), dtype=np.float64)
    # precompute per-residue mean/std over target AA of all 20 exchanges
    exchange = {}
    for wt in AA20:
        vals = [BLOSUM62[wt + mut] for mut in AA20]
        exchange[wt] = (float(np.mean(vals)), float(np.std(vals)))
    for i, subs in enumerate(df["subs"]):
        s = 0.0
        for _, wt, mut in subs:
            m, sd = exchange[wt]
            s += (BLOSUM62[wt + mut] - m) / sd if sd > 0 else 0.0
        out[i] = s
    return out


def null_scores(df):
    return rng.uniform(0, 1, size=len(df))


METHODS = {
    "baseline_blosum62": blosum62_scores,
    "baseline_blosum62_norm": blosum62_norm_scores,
    "baseline_null": null_scores,
}


def main():
    out_dir = os.path.join(ROOT, "results", "baseline_scores")
    os.makedirs(out_dir, exist_ok=True)
    for fid in ASSAYS:
        df = load_assay(fid)
        for name, fn in METHODS.items():
            df["score"] = fn(df)
            df[["mutant", "DMS_score", "DMS_score_bin", "score"]].to_csv(
                os.path.join(out_dir, f"{name}__{fid}.csv"), index=False
            )
        print(f"{fid}: baselines written")


if __name__ == "__main__":
    main()