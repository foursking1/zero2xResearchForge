#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Independent verification of the two evidence spot-checks used by the scorer
(B dimension of SCORE_RUBRIC.md), recomputed from the frozen data and the
same protocol as `impute_bench.py`:

  1. test masked-points total for seed=42  == 2385
  2. Linear test MAE for seed=42           == 0.2033249300539183
     (also optional: LOCF == 0.3023943111..., test windows == 72)

This script is intentionally self-contained (it embeds the mask/imputation
logic, identical to impute_bench.py) so a judge can re-run it directly.
Exit code is non-zero if any check fails.

Usage: python verify_anchor.py [--data /path/to/ETT-h1.csv]
"""
import argparse
import json
import os
import sys

import numpy as np
import pandas as pd

WINDOW = 48
RATE = 0.1
FEAT_COLS = ["HUFL", "HULL", "MUFL", "MULL", "LUFL", "LULL", "OT"]

EXPECTED = {
    "n_test_windows": 72,
    "n_test_masked_seed42": 2385,
    "linear_mae_seed42": 0.2033249300539183,
    "locf_mae_seed42": 0.3023943111054866,
    "mean_mae_seed42": 0.8712812162171027,
    "median_mae_seed42": 0.8588405536279224,
}
RTOL = 1e-6

_DATA_PATHS = [
    "/mnt/f/dataset/cs/2406.12747_tsibench/ETT-h1.csv",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "ETT-h1.csv"),
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data", "ETT-h1.csv"),
    "ETT-h1.csv",
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=None)
    args = ap.parse_args()
    data_path = args.data
    if data_path is None:
        for p in _DATA_PATHS:
            if os.path.isfile(p):
                data_path = p
                break
    if data_path is None or not os.path.isfile(data_path):
        print("ERROR: could not locate ETT-h1.csv", file=sys.stderr)
        sys.exit(2)

    df = pd.read_csv(data_path)
    df["date"] = pd.to_datetime(df["date"])
    tr = (df["date"] < pd.Timestamp("2017-09-01")).to_numpy()
    va = ((df["date"] >= pd.Timestamp("2017-09-01"))
          & (df["date"] < pd.Timestamp("2018-02-01"))).to_numpy()
    te = (df["date"] >= pd.Timestamp("2018-02-01")).to_numpy()
    X = df[FEAT_COLS].to_numpy(dtype=float)
    mu = X[tr].mean(axis=0)
    sd = X[tr].std(axis=0)
    Z = (X - mu) / sd

    def nw(idx):
        return int(len(np.where(idx)[0]) // WINDOW)

    n_tr, n_va, n_te = nw(tr), nw(va), nw(te)

    def wins(arr, start, n):
        return np.stack([arr[start + i * WINDOW: start + (i + 1) * WINDOW]
                         for i in range(n)])

    te_w = wins(Z, (n_tr + n_va) * WINDOW, n_te)

    rng = np.random.default_rng(42)
    masks = []
    for n_win in (n_tr, n_va, n_te):
        masks.append(np.stack([rng.random((WINDOW, Z.shape[1])) < RATE
                               for _ in range(n_win)]))
    M_te = masks[2]

    def metric(imp, mask, kind):
        d = np.abs(imp[mask] - te_w[mask]) if kind == "mae" else \
            (imp[mask] - te_w[mask]) ** 2
        return float(d.mean())

    def linear_impute(Win, M):
        out = Win.copy()
        for w in range(Win.shape[0]):
            for f in range(Win.shape[2]):
                col = out[w, :, f].copy()
                col[M[w, :, f]] = np.nan
                out[w, :, f] = pd.Series(col).interpolate(
                    method="linear", limit_direction="both").to_numpy()
        return out

    def locf_impute(Win, M):
        out = Win.copy()
        for w in range(Win.shape[0]):
            for f in range(Win.shape[2]):
                col = out[w, :, f].copy()
                col[M[w, :, f]] = np.nan
                out[w, :, f] = pd.Series(col).ffill().bfill().to_numpy()
        return out

    def const_impute(Win, M, val):
        out = Win.copy()
        for w in range(Win.shape[0]):
            for f in range(Win.shape[2]):
                out[w, M[w, :, f], f] = val[f]
        return out

    train_cells = Z[: n_tr * WINDOW]
    fmean = train_cells.mean(axis=0)
    fmed = np.median(train_cells, axis=0)

    got = {
        "n_test_windows": int(n_te),
        "n_test_masked_seed42": int(M_te.sum()),
        "linear_mae_seed42": metric(linear_impute(te_w, M_te), M_te, "mae"),
        "locf_mae_seed42": metric(locf_impute(te_w, M_te), M_te, "mae"),
        "mean_mae_seed42": metric(const_impute(te_w, M_te, fmean), M_te, "mae"),
        "median_mae_seed42": metric(const_impute(te_w, M_te, fmed), M_te, "mae"),
    }

    ok = True
    for k, exp in EXPECTED.items():
        g = got[k]
        diff = abs(g - exp)
        relative = diff / abs(exp) if exp else diff
        pass_ = (isinstance(exp, int) and g == exp) or (isinstance(exp, float) and relative <= RTOL)
        if k.startswith("n_"):
            pass_ = (g == exp)
        ok &= pass_
        rel_str = "n/a" if isinstance(g, int) else f"{relative:.2e}"
        print(f"[{'PASS' if pass_ else 'FAIL'}] {k:>22} = {g!r}  "
              f"(expected {exp!r}, rel.diff {rel_str})")

    print("train/val/test windows:", n_tr, n_va, n_te)
    print("ALL CHECKS:", "PASS" if ok else "FAIL")
    evout = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "evidence")
    os.makedirs(evout, exist_ok=True)
    with open(os.path.join(evout, "verify_anchor_output.json"), "w") as f:
        json.dump({"got": got, "expected": EXPECTED, "all_pass": ok}, f, indent=2)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()