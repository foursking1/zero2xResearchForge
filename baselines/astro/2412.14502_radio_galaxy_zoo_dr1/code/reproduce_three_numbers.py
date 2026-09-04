#!/usr/bin/env python3
"""Standalone spot-check that reproduces the numbers used by the independent
reviewer, straight from the frozen csv files only. No other inputs.

Judge re-checks:
  1. DF1 rows in DR1_FIRST_radio_classifications.csv            -> 99,602
  2. unique RGZID count in DR1_FIRST_radio_classifications.csv  -> 99,146
  3a. CL minimum in DR1_FIRST_radio_classifications.csv         -> 0.65
  3b. (alternative) row-level N_comp>1 count                    -> 16,531

Prints every number with its derivation and exits non-zero if a spot-check
value does not match expectations.
"""

import argparse
import sys

import pandas as pd

from config import resolve_data_dir, resolve_files


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default=None)
    args = ap.parse_args()

    files = resolve_files(resolve_data_dir(args.data_dir))
    first = pd.read_csv(files["FIRST_class"])

    n_rows = len(first)
    n_unique = first["RGZID"].nunique()
    cl_min = float(first["CL"].min())
    ncomp_rows = int((first["N_comp"] > 1).sum())

    print(f"rows in DR1_FIRST_radio_classifications.csv : {n_rows}")
    print(f"unique RGZID                               : {n_unique}")
    print(f"CL min                                     : {cl_min}")
    print(f"row-level N_comp>1                         : {ncomp_rows}")
    print(f"duplicated RGZIDs                          : {int((first['RGZID'].value_counts() > 1).sum())}")
    print(f"extra duplicate rows                       : {n_rows - n_unique}")

    expect = dict(n_rows=99602, n_unique=99146, cl_min=0.65, ncomp_rows=16531)
    ok = True
    if abs(n_rows - expect["n_rows"]) > 0:
        ok = False
        print(f"[FAIL] n_rows={n_rows} != {expect['n_rows']}")
    if abs(n_unique - expect["n_unique"]) > 0:
        ok = False
        print(f"[FAIL] n_unique={n_unique} != {expect['n_unique']}")
    if abs(cl_min - expect["cl_min"]) > 1e-6:
        ok = False
        print(f"[FAIL] cl_min={cl_min} != {expect['cl_min']}")
    if abs(ncomp_rows - expect["ncomp_rows"]) > 0:
        ok = False
        print(f"[FAIL] ncomp_rows={ncomp_rows} != {expect['ncomp_rows']}")

    print("\nRESULT:", "ALL SPOT-CHECKS PASS" if ok else "MISMATCH FOUND")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()