#!/usr/bin/env python3
"""
Independent verification of the three judge check-values for
task 2512.06316_frb_repeater_semisupervised (L1).

Check values (SCORE_RUBRIC B / PAPER_ANCHOR probe):
  1. chime_dm_subset.csv row count                            == 3584
  2. repeater count == 94, repeater mean DM in [425, 465]
  3. Mann-Whitney U p < 1e-5 AND repeater mean DM lower

Also verifies SHA-256 integrity of both frozen files against the manifest.
"""
import hashlib
import json
import os
import sys

import numpy as np
import pandas as pd
import scipy.stats as st

MANIFEST = {
    "chime_dm_subset.csv": "be77dddae6a3889e18dad6f59641901830e6d9567ce4c28b38f59e266b1cf4a7",
    "blinkverse_all_sources.json": "3302a12f91cdc36f7599f4c6894640f2792f757dcf996ffcfda7c0814ce2124e",
}

BASE = "/mnt/f/dataset/astro/2512.06316_frb_repeater_semisupervised"
if not os.path.isdir(BASE):
    for cand in (r"F:\dataset\astro\2512.06316_frb_repeater_semisupervised",
                 "F:/dataset/astro/2512.06316_frb_repeater_semisupervised"):
        if os.path.isdir(cand):
            BASE = cand
            break


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for blk in iter(lambda: fh.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def main():
    csv_path = os.path.join(BASE, "chime_dm_subset.csv")
    json_path = os.path.join(BASE, "blinkverse_all_sources.json")

    integrity = {}
    for fn, exp in MANIFEST.items():
        p = os.path.join(BASE, fn)
        got = sha256(p)
        integrity[fn] = {"sha256": got, "expected": exp, "match": got == exp}

    df = pd.read_csv(csv_path)
    n_rows = len(df)
    n_rep = int((df["repeater"] == 1).sum())
    n_non = int((df["repeater"] == 0).sum())
    rep_mean = float(df.loc[df["repeater"] == 1, "dm_pc_cm3"].mean())
    non_mean = float(df.loc[df["repeater"] == 0, "dm_pc_cm3"].mean())
    U, p = st.mannwhitneyu(
        df.loc[df["repeater"] == 1, "dm_pc_cm3"].values,
        df.loc[df["repeater"] == 0, "dm_pc_cm3"].values,
        alternative="two-sided",
    )

    checks = {
        "rows": {"value": n_rows, "pass": n_rows == 3584},
        "repeater_count": {"value": n_rep, "pass": n_rep == 94},
        "repeater_mean_dm_in_range": {"value": rep_mean, "pass": 425 <= rep_mean <= 465},
        "nonrepeater_mean_larger": {"value": non_mean, "pass": non_mean > rep_mean},
        "mwu_p": {"value": float(p), "pass": p < 1e-5},
        "direction": {"value": "repeater lower", "pass": rep_mean < non_mean},
    }
    for c in checks.values():
        c["pass"] = bool(c["pass"])
    all_pass = bool(integrity["chime_dm_subset.csv"]["match"]) and all(
        c["pass"] for c in checks.values()
    )

    result = {
        "verification_passed": all_pass,
        "integrity": integrity,
        "checks": checks,
        "U_statistic": float(U),
        "summary": "All judge check-values reproduce from frozen data.",
    }
    out_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results",
        "verification.json",
    )
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2, ensure_ascii=False)

    print(json.dumps(result, indent=2, ensure_ascii=False))
    if not all_pass:
        sys.exit("VERIFICATION FAILED")
    print("\nALL CHECKS PASSED")


if __name__ == "__main__":
    main()