#!/usr/bin/env python3
"""
01_c01_lvi_recompute.py
========================
Recompute the Lobster Vulnerability Index (LVI) per Lobster Fishing Area (LFA)
for the CM2.6 temperature-change scenario, using ONLY the frozen data provided
for task gehlen_2019.

The full exposure -> LVI chain is:

  1. 10401 survey rows (P02), each carrying a (lon, lat, LFA) label.
  2. A 100-iteration bootstrap GAM habitat-suitability prediction matrix for
     the CURRENT (observed) bottom temperature and for the CM2.6-projected
     bottom temperature (both frozen, 10401 x 100, saved as R .rds).
  3. A station is "suitable" when predicted suitability > 0.3 (paper p.8,
     Cook et al. 2017). For each (LFA, iteration) the percent change is
     (n_cm26 - n_current) / n_current * 100.
  4. The per-LFA exposure score is the MEDIAN percent change across the 100
     iterations, mapped to a 1-5 bin using Table 1 row definitions.
  5. Stock status = geometric mean of four 1-5 component scores (frozen P09
     output). Binned to an integer 1-5 for matrix lookup.
  6. LVI = Table 2 5x5 scoring-matrix cell (exposure row, stock-status col).

Outputs (written under agent_solution/results/):
  pct_change_per_lfa_cm26_recomputed.csv
  lvi_per_lfa_recomputed.csv
  lvi_per_lfa_detailed_recomputed.csv
"""

from __future__ import annotations

import math
import os
from pathlib import Path

import numpy as np
import pandas as pd
import pyreadr

# --------------------------------------------------------------------------
# Data locations (frozen data, read in place -- no copies)
# --------------------------------------------------------------------------
REPRO = Path(r"F:\dataset\gehlen_2019\reproduce")
CUR_RDS = REPRO / "P06_bootstrap" / "predictions_matrix_current.rds"
CM26_RDS = REPRO / "P06_bootstrap" / "predictions_matrix_cm26.rds"
STATIONS = REPRO / "P09_stock_status" / "stations_with_lfa.csv"
SS_CSV = REPRO / "P09_stock_status.csv"
SS_DET_CSV = REPRO / "P09_stock_status" / "P09_stock_status_detailed.csv"

OUT = Path(__file__).resolve().parents[1] / "results"
OUT.mkdir(exist_ok=True)

SUITABILITY_THRESHOLD = 0.3
N_ITER = 100
# LFAs reported in the paper's Figure 5 / Figure 6 (offshore lobster fishery)
PAPER_LFAS = ["35", "36", "37", "38", "34", "40", "41", "33"]
# LFAs explicitly stated to receive NO LVI (Fig 6 caption; no offshore fishery)
NO_LVI_LFAS = {"27", "28", "29", "30", "31A", "31B", "32"}

# Table 2 vulnerability-assessment scoring matrix (paper p. 8).
# rows = exposure bin 1..5 (1 = significant gain .. 5 = significant loss)
# cols = stock status bin 1..5 (1 = strong .. 5 = weak)
TABLE2 = np.array([
    [1.0, 1.5, 2.0, 2.5, 3.0],
    [1.5, 2.0, 2.5, 3.0, 3.5],
    [2.0, 2.5, 3.0, 3.5, 4.0],
    [2.5, 3.0, 3.5, 4.0, 4.5],
    [3.0, 3.5, 4.0, 4.5, 5.0],
])


def bin_exposure(pct: float):
    """Map percent change in suitable habitat to an exposure bin 1-5."""
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


def round_half_away(score: float):
    """Nearest-integer rounding (half away from zero) for matrix lookup."""
    if pd.isna(score):
        return np.nan
    return math.floor(score) if score - math.floor(score) < 0.5 else math.floor(score) + 1


def matrix_lookup(exp_bin, ss_bin):
    if pd.isna(exp_bin) or pd.isna(ss_bin):
        return np.nan
    return float(TABLE2[int(exp_bin) - 1, int(ss_bin) - 1])


def load_rds_matrix(path: Path) -> np.ndarray:
    res = pyreadr.read_r(str(path))
    df = next(iter(res.values()))
    return df.to_numpy(dtype=np.float64)


def main() -> None:
    print("=" * 72)
    print("C01 -- Recompute LVI per LFA (CM2.6 scenario) from frozen data")
    print("=" * 72)

    # ------------------------------------------------------------------ #
    # 1) Station-LFA mapping
    # ------------------------------------------------------------------ #
    stations = pd.read_csv(STATIONS)
    assert len(stations) == 10401, f"unexpected n stations {len(stations)}"
    print(f"[1] {len(stations)} survey rows loaded; LFA column present: "
          f"{'LFA' in stations.columns}")

    # ------------------------------------------------------------------ #
    # 2) Bootstrap prediction matrices (current & CM2.6)
    # ------------------------------------------------------------------ #
    print("[2] Loading frozen 100-iteration prediction matrices ...")
    cur = load_rds_matrix(CUR_RDS)
    cm26 = load_rds_matrix(CM26_RDS)
    print(f"    current matrix: {cur.shape}  (min {cur.min():.4f}, max {cur.max():.4f})")
    print(f"    CM2.6   matrix: {cm26.shape}  (min {cm26.min():.4f}, max {cm26.max():.4f})")
    assert cur.shape == (10401, N_ITER) and cm26.shape == (10401, N_ITER)
    assert cur.shape == cm26.shape

    # ------------------------------------------------------------------ #
    # 3) Per-LFA percent change in suitable habitat (>0.3)
    # ------------------------------------------------------------------ #
    rows_lfa = stations["LFA"].astype(str).values
    cur_suit = cur > SUITABILITY_THRESHOLD
    cm26_suit = cm26 > SUITABILITY_THRESHOLD

    summary = []
    long_rows = []
    for lfa in PAPER_LFAS:
        in_lfa = rows_lfa == lfa
        n_in = int(in_lfa.sum())
        if n_in == 0:
            print(f"    WARN LFA {lfa}: 0 stations -- skipped")
            continue
        n_cur = cur_suit[in_lfa, :].sum(axis=0).astype(float)
        n_cm26 = cm26_suit[in_lfa, :].sum(axis=0).astype(float)
        with np.errstate(divide="ignore", invalid="ignore"):
            pct = np.where(n_cur > 0, (n_cm26 - n_cur) / n_cur * 100.0, np.nan)
        n_undef = int(np.isnan(pct).sum())
        summary.append({
            "LFA": lfa,
            "n_stations_in_LFA": n_in,
            "n_iters_undefined": n_undef,
            "median_n_cur": float(np.median(n_cur)),
            "median_n_cm26": float(np.median(n_cm26)),
            "mean_pct_change": float(np.nanmean(pct)),
            "median_pct_change": float(np.nanmedian(pct)),
            "q025_pct_change": float(np.nanpercentile(pct, 2.5)),
            "q975_pct_change": float(np.nanpercentile(pct, 97.5)),
            "min_pct_change": float(np.nanmin(pct)),
            "max_pct_change": float(np.nanmax(pct)),
            "frac_iters_net_loss": float(np.nanmean(pct < 0)),  # share of iters with net loss
        })
        for i, p in enumerate(pct, start=1):
            long_rows.append({"LFA": lfa, "iter": i, "scenario": "CM2.6",
                              "n_cur": int(n_cur[i - 1]),
                              "n_cm26": int(n_cm26[i - 1]),
                              "pct_change": p})

    pct_df = pd.DataFrame(summary)
    pct_df.to_csv(OUT / "pct_change_per_lfa_cm26_recomputed.csv", index=False,
                  float_format="%.4f")
    print("\n[3] Per-LFA percent change in suitable habitat (CM2.6 vs current):")
    print(pct_df[[
        "LFA", "n_stations_in_LFA", "median_pct_change", "q025_pct_change",
        "q975_pct_change", "min_pct_change", "max_pct_change",
        "frac_iters_net_loss",
    ]].to_string(index=False))
    print(f"    -> wrote {OUT / 'pct_change_per_lfa_cm26_recomputed.csv'}")

    # ------------------------------------------------------------------ #
    # 4) Stock status (frozen P09 output)
    # ------------------------------------------------------------------ #
    ss = pd.read_csv(SS_CSV)
    ss["LFA"] = ss["LFA"].astype(str)
    ss_det = pd.read_csv(SS_DET_CSV)
    ss_det["LFA"] = ss_det["LFA"].astype(str)
    ss = ss.merge(ss_det[["LFA", "stock_status_score_loose"]], on="LFA", how="left")

    print("\n[4] Frozen stock-status components (P09):")
    print(ss[["LFA", "potential_score", "occupancy_score", "abundance_score",
              "food_trend_score", "stock_status_score", "stock_status_score_loose"]]
          .to_string(index=False))

    # ------------------------------------------------------------------ #
    # 5) LVI lookup via Table 2
    # ------------------------------------------------------------------ #
    merged = pct_df.merge(ss, on="LFA", how="outer")
    merged["paper_no_lvi"] = merged["LFA"].isin(NO_LVI_LFAS)
    merged["has_offshore_fishery"] = merged["LFA"].isin(PAPER_LFAS)

    merged["exposure_bin"] = merged["median_pct_change"].apply(bin_exposure)
    merged["stock_status_bin_strict"] = merged["stock_status_score"].apply(round_half_away)
    merged["stock_status_bin_loose"] = merged["stock_status_score_loose"].apply(round_half_away)

    merged["LVI_strict"] = merged.apply(
        lambda r: matrix_lookup(r["exposure_bin"], r["stock_status_bin_strict"]), axis=1)
    merged["LVI_loose"] = merged.apply(
        lambda r: matrix_lookup(r["exposure_bin"], r["stock_status_bin_loose"]), axis=1)

    # Final LVI: strict where all 4 components present, else loose where the
    # LFA has an offshore fishery (i.e. LFAs 37/40/41 with missing C3).
    merged["LVI"] = merged["LVI_strict"].where(
        merged["LVI_strict"].notna(),
        merged["LVI_loose"].where(merged["has_offshore_fishery"]))
    merged.loc[merged["paper_no_lvi"], "LVI"] = np.nan
    merged["LVI_source"] = np.where(
        merged["paper_no_lvi"], "no offshore fishery (paper rule)",
        np.where(merged["LVI_strict"].notna(), "strict (all 4 components)",
                 np.where(merged["LVI_loose"].notna() & merged["has_offshore_fishery"],
                          "loose (>=1 missing component)", "")))

    # order rows as Figure 5 / Figure 6
    order = ["27", "28", "29", "30", "31A", "31B", "32",
             "33", "34", "35", "36", "37", "38", "40", "41"]
    merged["LFA"] = pd.Categorical(merged["LFA"], categories=order, ordered=True)
    merged = merged.sort_values("LFA").reset_index(drop=True)
    merged["LFA"] = merged["LFA"].astype(str)

    detail_cols = [
        "LFA", "has_offshore_fishery", "paper_no_lvi",
        "median_pct_change", "mean_pct_change", "q025_pct_change", "q975_pct_change",
        "exposure_bin", "potential_score", "occupancy_score", "abundance_score",
        "food_trend_score", "stock_status_score", "stock_status_score_loose",
        "stock_status_bin_strict", "stock_status_bin_loose",
        "LVI_strict", "LVI_loose", "LVI", "LVI_source",
    ]
    merged[detail_cols].to_csv(OUT / "lvi_per_lfa_detailed_recomputed.csv",
                               index=False, float_format="%.4f")

    short_cols = ["LFA", "median_pct_change", "exposure_bin", "stock_status_score",
                  "stock_status_bin_strict", "LVI", "LVI_source"]
    short = merged[short_cols].rename(columns={"stock_status_bin_strict": "stock_status_bin"})
    short.to_csv(OUT / "lvi_per_lfa_recomputed.csv", index=False, float_format="%.4f")

    print("\n[5] Recomputed LVI per LFA (CM2.6):")
    print(short.to_string(index=False))
    print(f"    -> wrote {OUT / 'lvi_per_lfa_recomputed.csv'}")

    # ------------------------------------------------------------------ #
    # 6) Claim-specific checks
    # ------------------------------------------------------------------ #
    print("\n[6] Claim C01 checks (frozen-data recomputation):")
    offshore_lvi = merged[merged["LFA"].isin(["33", "34", "35", "36", "38", "41"])]
    lvi_range = (offshore_lvi["LVI"].min(), offshore_lvi["LVI"].max())
    print(f"    LVI range among paper Fig-6 LFAs (33,34,35,36,38,41): {lvi_range}")
    for lfa, paper_val in [("33", 2.0), ("34", 2.0), ("35", 2.5), ("36", 2.5),
                           ("38", 2.0), ("41", 2.0)]:
        ours = offshore_lvi.loc[offshore_lvi["LFA"] == lfa, "LVI"].iloc[0]
        match = "OK " if (pd.notna(ours) and abs(ours - paper_val) < 1e-9) else "MISMATCH"
        print(f"    LFA {lfa}: paper CM2.6 LVI = {paper_val:.1f}, recomputed = {ours}  [{match}]")
    print("    'none experience net loss' (median % change >= 0 for all LFAs):",
          bool((pct_df["median_pct_change"] >= 0).all()))


if __name__ == "__main__":
    main()
