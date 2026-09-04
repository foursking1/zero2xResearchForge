#!/usr/bin/env python3
"""
04_sensitivity_lvi.py
=====================
Sensitivity analysis for the C01 LVI recomputation.

The paper leaves two small implementation details unspecified:
  1. how the continuous geometric-mean stock-status score (real in [1,5]) is
     mapped to the integer bins used for the Table 2 matrix lookup
     (round / floor / ceil);
  2. which per-LFA exposure summary drives the exposure bin
     (median vs mean of the 100-iteration percent-change distribution).

We recompute the LVI for all combinations and report which LFAs match or
mismatch the paper-reported CM2.6 values (33=2, 34=2, 35=2.5, 36=2.5,
38=2, 41=2).  This establishes whether the C01 mismatch is robust.

Output: results/lvi_sensitivity.csv
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parents[1] / "results"

TABLE2 = np.array([
    [1.0, 1.5, 2.0, 2.5, 3.0],
    [1.5, 2.0, 2.5, 3.0, 3.5],
    [2.0, 2.5, 3.0, 3.5, 4.0],
    [2.5, 3.0, 3.5, 4.0, 4.5],
    [3.0, 3.5, 4.0, 4.5, 5.0],
])

PAPER_CM26 = {"33": 2.0, "34": 2.0, "35": 2.5, "36": 2.5, "38": 2.0, "41": 2.0}


def bin_exposure(pct):
    if pd.isna(pct):
        return np.nan
    if pct > 25.0:
        return 1
    if pct >= 5.0:
        return 2
    if pct >= -5.0:
        return 3
    if pct >= -25.0:
        return 4
    return 5


def bin_ss(score, mode):
    if pd.isna(score):
        return np.nan
    if mode == "floor":
        return math.floor(score)
    if mode == "ceil":
        return math.ceil(score)
    # round half away from zero
    return math.floor(score) if score - math.floor(score) < 0.5 else math.floor(score) + 1


def lookup(exp, ss):
    if pd.isna(exp) or pd.isna(ss):
        return np.nan
    return TABLE2[int(exp) - 1, int(ss) - 1]


def main() -> None:
    pct = pd.read_csv(OUT / "pct_change_per_lfa_cm26_recomputed.csv")
    pct["LFA"] = pct["LFA"].astype(str)
    lvi = pd.read_csv(OUT / "lvi_per_lfa_detailed_recomputed.csv")
    lvi["LFA"] = lvi["LFA"].astype(str)

    rows = []
    for mode in ["round", "floor", "ceil"]:
        for exp_metric in ["median_pct_change", "mean_pct_change"]:
            row = {"stock_status_bin_mode": mode, "exposure_metric": exp_metric}
            for lfa in ["33", "34", "35", "36", "38", "41"]:
                p = pct.loc[pct["LFA"] == lfa, exp_metric].iloc[0]
                ss = lvi.loc[lvi["LFA"] == lfa, "stock_status_score_loose"].iloc[0]
                exp_bin = bin_exposure(p)
                ss_bin = bin_ss(ss, mode)
                v = lookup(exp_bin, ss_bin)
                row[f"LVI_{lfa}"] = v
                row[f"match_{lfa}"] = (
                    pd.notna(v) and abs(v - PAPER_CM26[lfa]) < 1e-9)
            row["n_matches"] = sum(row[f"match_{lfa}"] for lfa in PAPER_CM26)
            row["n_mismatches"] = 6 - row["n_matches"]
            rows.append(row)

    sens = pd.DataFrame(rows)
    sens.to_csv(OUT / "lvi_sensitivity.csv", index=False, float_format="%.2f")

    print("Sensitivity of CM2.6 LVI recomputation to binning choices")
    print("(paper CM2.6 LVI: 33=2, 34=2, 35=2.5, 36=2.5, 38=2, 41=2)\n")
    show = [c for c in sens.columns if c.startswith(("stock", "exposure", "LVI_"))]
    print(sens[show].to_string(index=False))

    # strict stock-status version for LFAs that have all 4 components
    print("\nStrict-composite version (LFAs with all 4 stock-status components):")
    for mode in ["round", "floor", "ceil"]:
        vals = []
        for lfa in ["33", "34", "35", "36", "38"]:
            ss = lvi.loc[lvi["LFA"] == lfa, "stock_status_score"].iloc[0]
            p = pct.loc[pct["LFA"] == lfa, "median_pct_change"].iloc[0]
            v = lookup(bin_exposure(p), bin_ss(ss, mode))
            vals.append(f"{lfa}={v}")
        print(f"  {mode:6s}: " + ", ".join(vals))


if __name__ == "__main__":
    main()
