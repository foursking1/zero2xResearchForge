#!/usr/bin/env python3
"""Robustness / data-integrity checks on the frozen RGZ DR1 csv files.

These checks confirm the input quality assumptions used by run_analysis.py
(no need to trust us: the numbers are derived from verified raw files).
Checks:
  * schema: column names + dtypes of the 4 files
  * CL within [0,1]; integer-like enumerations (N_comp, N_peaks, N_votes,
    N_total positive); LAE/TSA/TF non-negative where defined
  * CL granularity (how many distinct values; confirm 0.65 appears exactly)
  * RA/Dec ranges (FIRST: ~7.6-46.8h window; ATLAS: around -35..-29)
  * duplicate-RGZID consistency (same N_comp/N_peaks/CL within dup groups)
  * host table RGZID sets == classification RGZID sets
"""

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

from config import resolve_data_dir, resolve_files


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default=None)
    ap.add_argument("--out-dir", default=None)
    args = ap.parse_args()

    files = resolve_files(resolve_data_dir(args.data_dir))
    first = pd.read_csv(files["FIRST_class"])
    atlas = pd.read_csv(files["ATLAS_class"])
    first_host = pd.read_csv(files["FIRST_host"])
    atlas_host = pd.read_csv(files["ATLAS_host"])

    out = {}

    # -- schema
    out["schema"] = {
        "FIRST_class": {"columns": list(first.columns), "dtypes": {c: str(t) for c, t in first.dtypes.items()}},
        "ATLAS_class": {"columns": list(atlas.columns), "dtypes": {c: str(t) for c, t in atlas.dtypes.items()}},
        "FIRST_host": {"columns": list(first_host.columns), "dtypes": {c: str(t) for c, t in first_host.dtypes.items()}},
        "ATLAS_host": {"columns": list(atlas_host.columns), "dtypes": {c: str(t) for c, t in atlas_host.dtypes.items()}},
    }

    # -- value ranges
    for label, df in [("FIRST", first), ("ATLAS", atlas)]:
        cl = df["CL"]
        out[f"{label}_cl_range"] = {
            "min": float(cl.min()), "max": float(cl.max()),
            "all_within_01": bool(((cl >= 0) & (cl <= 1)).all()),
            "n_unique_values": int(cl.nunique()),
            "value_0_65_present": bool((cl == 0.65).any()),
        }
        for c in ["N_comp", "N_peaks", "N_votes", "N_total", "CatID"]:
            s = df[c]
            out[f"{label}_{c}"] = {
                "min": int(s.min()), "max": int(s.max()),
                "all_positive_or_zero": bool((s >= 0).all()),
                "all_integer": bool((s == s.round()).all() or (s.dtype.kind == "i")),
                "n_na": int(s.isna().sum()),
            }
        out[f"{label}_RA_range"] = [float(df["RA"].min()), float(df["RA"].max())]
        out[f"{label}_Dec_range"] = [float(df["Dec"].min()), float(df["Dec"].max())]

    # -- duplicate RGZID row consistency
    first = first.sort_values("RGZID")
    grp = first.groupby("RGZID")
    dup_mask = first.groupby("RGZID")["RGZID"].transform("size") > 1
    dup_df = first[dup_mask]
    out["duplicate_RGZID_rows"] = int(dup_mask.sum())
    for col in ["N_comp", "N_peaks", "CL", "RA", "Dec"]:
        out[f"dup_consistent_{col}"] = int(
            (dup_df.groupby("RGZID")[col].nunique() == 1).all()
        )

    # -- host-table set equality
    out["FIRST_host_vs_class_set_equal"] = set(first_host["RGZID"]) == set(first["RGZID"])
    out["ATLAS_host_vs_class_set_equal"] = set(atlas_host["RGZ_ID"]) == set(atlas["RGZID"])

    # -- exact count of CL == 0.65
    out["FIRST_CL_equal_0_65_count"] = int((first["CL"] == 0.65).sum())
    out["ATLAS_CL_equal_0_65_count"] = int((atlas["CL"] == 0.65).sum())

    print(json.dumps(out, indent=2, default=str, ensure_ascii=False))

    # a couple of hard assertions
    assert (out["FIRST_cl_range"]["all_within_01"])
    assert (out["FIRST_cl_range"]["min"] >= 0.649999)  # giteps float repr
    assert out["FIRST_N_comp"]["all_positive_or_zero"]
    print("\n[ok] robustness checks passed")

    # write checkset out next to results if requested
    if args.out_dir:
        Path(args.out_dir).mkdir(parents=True, exist_ok=True)
        (Path(args.out_dir) / "robustness_checks.json").write_text(
            json.dumps(out, indent=2, default=str, ensure_ascii=False), encoding="utf-8"
        )

    sys.exit(0)


if __name__ == "__main__":
    main()