#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Independent re-computation of the key 4FGL population checks requested by the
task's grading protocol.  This file deliberately uses a DIFFERENT parsing
strategy (pandas.read_fwf with ReadMe colspecs) than analyze_4fgl.py
(manual byte slicing) to cross-validate the numbers.

Verified quantities (frozen 4FGL-DR1, J/ApJS/247/33):
  1. total rows / unique Source_Name                  -> 5065
  2. CLASS1 blank (no counterpart), all sky           -> 1336
  3. |b|>10 with CLASS1 == bcu (lower case)           -> 1073
     |b|>10 with CLASS1 in {bcu,BCU}                  -> 1074

plus the paper-criteria reconstructed sample composition.

Usage:  python3 verify_checks.py [--data-dir PATH] [--outdir PATH]
"""

from __future__ import annotations

import argparse
import gzip
import json
import os
import sys

import pandas as pd

EXPECTED_SHA256_DAT = "7A01F206C24B313BCE3C2D7D162F859A8D8BC107F1B3305176B4BA37816CE49C"
README_SIZE = 70259
GZIP_SIZE = 6883415
EXPECTED_RECORDS = 5065
LRECL = 4104

# ReadMe byte-by-byte descriptions (1-based, inclusive) mapped to half-open
# pandas colspecs [(start-1, stop)].  All offsets verified against the ReadMe
# "Byte-by-byte" table and the Table-7 occurrence counts.  NOTE: the data
# file's 1-byte "gap" columns are rendered as '|' separators; the numeric and
# class fields occupy exactly their stated byte ranges.
NAMED = [
    ("Source_Name", (0, 28)),   # 1-28   (IAU name field; see note in analyze_4fgl.py)
    ("GLON",        (37, 47)),  # 38-47
    ("GLAT",        (48, 58)),  # 49-58
    ("CLASS1",      (3977, 3982)),  # 3978-3982
    ("CLASS2",      (3983, 3986)),  # 3984-3986
    ("ASSOC1",      (3987, 4015)),  # 3988-4015
]


def find_data_dir(provided, quiet=False):
    cands = []
    if provided:
        cands.append(provided)
    if os.environ.get("FROZEN_DATA_DIR"):
        cands.append(os.environ["FROZEN_DATA_DIR"])
    cands += [
        "data",
        r"F:\dataset\astro\2211.03400_fermi_4fgl_jetted_agn",
        "/mnt/f/dataset/astro/2211.03400_fermi_4fgl_jetted_agn",
        "/mnt/d/dataset/astro/2211.03400_fermi_4fgl_jetted_agn",
        os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                      "..", "..", "data")),
    ]
    seen, uniq = set(), []
    for c in cands:
        nc = os.path.abspath(c) if not c.startswith("F:") else c
        if nc not in seen:
            seen.add(nc)
            uniq.append(c)
    for c in uniq:
        dat = os.path.join(c, "4fgl.dat.gz")
        if os.path.isfile(dat) and os.path.getsize(dat) == GZIP_SIZE:
            return c
    raise FileNotFoundError("4FGL data not found; pass --data-dir")


def read_with_pandas(data_dir):
    """Independent parse via pandas.read_fwf (colspecs == ReadMe byte table)."""
    dat = os.path.join(data_dir, "4fgl.dat.gz")
    with gzip.open(dat, "rt", encoding="latin-1") as f:
        texts = [ln.rstrip("\n").rstrip("\r") for ln in f]
    texts = [t for t in texts if t.strip() != ""]
    assert len(texts) == EXPECTED_RECORDS, (len(texts), EXPECTED_RECORDS)
    cs = [(a, b) for _, (a, b) in NAMED]
    df = pd.read_fwf(pd.io.common.StringIO("\n".join(texts)), colspecs=cs,
                     names=[n for n, _ in NAMED], dtype=str, header=None)
    for col in [n for n, _ in NAMED]:
        df[col] = df[col].str.strip()
    df.fillna("", inplace=True)  # blank fixed-width fields read as NaN
    for col in ["GLON", "GLAT"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default=None)
    ap.add_argument("--outdir", default=os.getcwd())
    args = ap.parse_args()

    dd = find_data_dir(args.data_dir)
    print(f"[data] {dd}")
    df = read_with_pandas(dd)

    n_rows = len(df)
    n_uniq = df["Source_Name"].nunique()
    n_blank = int((df["CLASS1"] == "").sum())
    n_assoc1_blank = int((df["ASSOC1"] == "").sum())

    m = df["GLAT"].abs() > 10.0
    df10 = df[m]
    n10 = len(df10)
    n10_blank = int((df10["CLASS1"] == "").sum())
    n10_bcu_lower = int((df10["CLASS1"] == "bcu").sum())
    n10_bcu_BCU = int(df10["CLASS1"].isin(["bcu", "BCU"]).sum())

    excl = {"PSR", "psr", "spp", "SNR", "snr", "PWN", "pwn", "glc",
            "gal", "sbg", "SFR", "sfr", "hmb", "HMB", "lmb", "LMB"}
    samp = df10[df10["CLASS1"] != ""].loc[lambda d: ~d["CLASS1"].isin(excl)]
    n_samp = len(samp)
    comp = {
        "bll_lower": int((samp["CLASS1"] == "bll").sum()),
        "BLL": int((samp["CLASS1"] == "BLL").sum()),
        "bcu_lower": int((samp["CLASS1"] == "bcu").sum()),
        "BCU": int((samp["CLASS1"] == "BCU").sum()),
        "fsrq_lower": int((samp["CLASS1"] == "fsrq").sum()),
        "FSRQ": int((samp["CLASS1"] == "FSRQ").sum()),
        "rdg_RDG": int(samp["CLASS1"].isin(["rdg", "RDG"]).sum()),
        "nlsy1_NLSY1": int(samp["CLASS1"].isin(["nlsy1", "NLSY1"]).sum()),
        "agn_AGN": int(samp["CLASS1"].isin(["agn", "AGN"]).sum()),
        "css": int((samp["CLASS1"] == "css").sum()),
        "ssrq": int((samp["CLASS1"] == "ssrq").sum()),
    }
    res = {
        "n_rows": n_rows,
        "n_unique_source_name": n_uniq,
        "n_class1_blank_all_sky": n_blank,
        "n_assoc1_blank_all_sky": n_assoc1_blank,
        "n_absb_gt10": n10,
        "n_absb_gt10_class1_blank": n10_blank,
        "n_absb_gt10_bcu_lower": n10_bcu_lower,
        "n_absb_gt10_bcu_BCU_combined": n10_bcu_BCU,
        "agn_sample_size": n_samp,
        "agn_sample_composition": comp,
        "frac_bll_upper": round((comp["bll_lower"] + comp["BLL"]) / n_samp, 4),
        "frac_bcu_lower": round(comp["bcu_lower"] / n_samp, 4),
        "frac_fsrq_upper": round((comp["fsrq_lower"] + comp["FSRQ"]) / n_samp, 4),
        "frac_no_counterpart_absb": round(n10_blank / n10, 4),
        "frac_no_counterpart_plus_bcu_absb": round((n10_blank + n10_bcu_BCU) / n10, 4),
    }
    print(json.dumps(res, indent=2))

    # ---- assertions against the three grading checks + rubric targets ----
    checks = {
        "total_rows_eq_5065": res["n_rows"] == 5065,
        "unique_source_eq_rows": res["n_rows"] == res["n_unique_source_name"],
        "class1_blank_all_sky_eq_1336": res["n_class1_blank_all_sky"] == 1336,
        "absb_gt10_bcu_lower_eq_1073": res["n_absb_gt10_bcu_lower"] == 1073,
        "absb_gt10_bcu_BCU_eq_1074": res["n_absb_gt10_bcu_BCU_combined"] == 1074,
        "absb_gt10_no_counterpart_eq_657": res["n_absb_gt10_class1_blank"] == 657,
        "agn_sample_eq_2866": res["agn_sample_size"] == 2866,
        "bll_upper_eq_1067": (comp["bll_lower"] + comp["BLL"]) == 1067,
        "fsrq_upper_eq_658": (comp["fsrq_lower"] + comp["FSRQ"]) == 658,
    }
    ok = all(checks.values())
    for k, v in checks.items():
        print(("PASS " if v else "FAIL ") + k)
    print("ALL_CHECKS_PASS" if ok else "SOME_CHECKS_FAILED")

    os.makedirs(os.path.join(args.outdir, "results"), exist_ok=True)
    with open(os.path.join(args.outdir, "results/verify_checks.json"), "w",
              encoding="utf-8") as fh:
        json.dump({"result": res, "checks": checks, "all_passed": ok,
                   "data_dir": dd}, fh, indent=2, ensure_ascii=False)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())