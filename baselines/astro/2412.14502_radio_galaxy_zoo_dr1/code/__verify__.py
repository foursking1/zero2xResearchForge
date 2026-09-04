#!/usr/bin/env python3
"""Verifier: recomputes the headline numbers from the raw frozen csvs and
cross-checks them against every stored artifact (metrics.json,
evidence_table.csv, probe_numbers.json, summary_table.csv).

Run:
  python __verify__.py [--data-dir <dir>] [--results-dir <dir>]

Exit code 0 if and only if:
  * recomputed numbers match expectations (rubric full-mark band)
  * stored artifacts equal the recomputed numbers
  * evidence_table.csv contains per-source rows and summary rows
"""

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

from config import resolve_data_dir, resolve_files

TOL = {
    "first_rows": 3, "atlas_rows": 2, "total_rows": 5,
    "first_unique": 10, "cl_min": 0.005, "cl_mean_lo": 0.90, "cl_mean_hi": 0.98,
    "ncomp_rows_tol": 150, "ncomp_unique_tol": 150,
}

failures = []


def check(name, condition, detail):
    status = "ok" if condition else "FAIL"
    print(f"[{status}] {name}: {detail}")
    if not condition:
        failures.append(name)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default=None)
    ap.add_argument("--results-dir", default=None)
    args = ap.parse_args()

    results_dir = Path(args.results_dir) if args.results_dir else (
        Path(__file__).resolve().parent.parent / "results"
    )

    files = resolve_files(resolve_data_dir(args.data_dir))
    first = pd.read_csv(files["FIRST_class"])
    atlas = pd.read_csv(files["ATLAS_class"])

    # ---- 1. recompute from scratch (raw csv) ------------------------------
    n_rows = len(first)
    n_atlas = len(atlas)
    n_unique = first["RGZID"].nunique()
    n_atlas_unique = atlas["RGZID"].nunique()
    total = n_rows + n_atlas
    clmin = float(first["CL"].min())
    clmean = float(first["CL"].mean())
    clmed = float(first["CL"].median())
    ncomp_rows = int((first["N_comp"] > 1).sum())
    uniq_src = first.drop_duplicates(subset="RGZID", keep="first")
    ncomp_unique = int((uniq_src["N_comp"] > 1).sum())
    npeaks_unique = int((uniq_src["N_peaks"] > 1).sum())
    atlas_ncomp = int((atlas["N_comp"] > 1).sum())
    dup_sources = int((first["RGZID"].value_counts() > 1).sum())
    cl_lt1_frac = float((first["CL"] < 1).mean())

    # ---- 2. stored json ---------------
    metrics = json.loads((results_dir / "metrics.json").read_text(encoding="utf-8"))
    probe = json.loads((results_dir / "probe_numbers.json").read_text(encoding="utf-8"))
    ev = pd.read_csv(results_dir / "evidence_table.csv")

    print("== headline numbers (recomputed) ==")
    for line in [
        f"rows={n_rows} unique={n_unique} atlas={n_atlas} total={total}",
        f"cl(min={clmin:.6f}, median={clmed}, mean={clmean:.5f})",
        f"ncomp rows={ncomp_rows} unique={ncomp_unique} npeaks unique={npeaks_unique}",
        f"atlas ncomp>1={atlas_ncomp} dup src={dup_sources} cl<1 frac={cl_lt1_frac:.4f}",
    ]:
        print("  " + line)

    # ---- admin check: rubric full-mark band ---------------------------------
    check("first_rows==99602", abs(n_rows - 99602) <= TOL["first_rows"],
          f"{n_rows}")
    check("atlas_rows==583", abs(n_atlas - 583) <= TOL["atlas_rows"], f"{n_atlas}")
    check("total_rows==100185", abs(total - 100185) <= TOL["total_rows"], f"{total}")
    check("first_unique==99146", abs(n_unique - 99146) <= TOL["first_unique"],
          f"{n_unique}")
    check("cl_min==0.65", abs(clmin - 0.65) <= TOL["cl_min"], f"{clmin}")
    check("cl_median==1.0", clmed == 1.0, f"{clmed}")
    check("cl_mean_in_[0.90,0.98]", TOL["cl_mean_lo"] <= clmean <= TOL["cl_mean_hi"],
          f"{clmean:.5f}")
    check("ncomp_row_band", abs(ncomp_rows - 16531) <= TOL["ncomp_rows_tol"],
          f"{ncomp_rows}")
    check("ncomp_unique_band", abs(ncomp_unique - 16334) <= TOL["ncomp_unique_tol"],
          f"{ncomp_unique}")

    # ---- stored vs recomputed -----------------------------------------------
    def eq(name, stored, recomputed, tol=0):
        check(f"stored_{name}", abs(float(stored) - float(recomputed)) <= max(tol, 1e-9),
              f"stored={stored} recomputed={recomputed}")

    eq("rows", probe["first_rows"], n_rows)
    eq("unique", probe["first_unique_rgzid"], n_unique)
    eq("cl_min", probe["cl_min_first"], clmin, 1e-6)
    eq("ncomp_rows", probe["first_ncomp_gt1_rows"], ncomp_rows)
    eq("ncomp_unique", probe["first_ncomp_gt1_unique"], ncomp_unique)
    eq("atlas_rows", probe["atlas_rows"], n_atlas)
    eq("total_rows", probe["total_rows"], total)

    m = metrics["Q1_scale"]
    eq("metrics.first_rows", m["first_rows"], n_rows)
    eq("metrics.atlas_rows", m["atlas_rows"], n_atlas)
    eq("metrics.total", m["total_rows_all_entries"], total)
    eq("metrics.first_unique", m["first_unique_sources"], n_unique)
    eq("metrics.dup_sources", m["first_duplicated_sources_count"], dup_sources)
    eq("metrics.extra_rows", m["first_extra_duplicate_rows"], n_rows - n_unique)
    eq("metrics.cl_min", metrics["Q2_consensus"]["cl_stats_FIRST_rows"]["min"], clmin, 1e-9)
    eq("metrics.cl_median", metrics["Q2_consensus"]["cl_stats_FIRST_rows"]["median"], clmed, 1e-9)
    eq("metrics.cl_mean", metrics["Q2_consensus"]["cl_stats_FIRST_rows"]["mean"], clmean, 1e-9)
    eq("metrics.cl_lt1_frac", metrics["Q2_consensus"]["cl_stats_FIRST_rows"]["lt_1_fraction"], cl_lt1_frac, 1e-9)
    eq("metrics.ncomp_rows", metrics["Q3_multicomponent"]["FIRST_row_level_N_comp_gt_1"], ncomp_rows)
    eq("metrics.ncomp_unique", metrics["Q3_multicomponent"]["FIRST_unique_source_level_N_comp_gt_1"], ncomp_unique)
    eq("metrics.npeaks_unique", metrics["Q3_multicomponent"]["FIRST_unique_source_level_N_peaks_gt_1"], npeaks_unique)
    eq("metrics.atlas_ncomp", metrics["Q4_ATLAS"]["N_comp_gt_1_rows"], atlas_ncomp)

    # ---- evidence table sanity ------------------------------------------------
    n_src = len(ev[ev["table"].isin(["FIRST", "ATLAS"])])
    check("evidence.per_source_rows==100185", n_src == 100185, f"{n_src}")
    n_sum = len(ev[ev["table"] == "summary"])
    check("evidence.summary_rows_present", n_sum >= 15, f"{n_sum}")
    for col in ["rgzid", "ra", "dec", "cl", "n_comp", "n_peaks", "ncomp_gt1", "npeaks_gt1"]:
        check(f"evidence.has_col_{col}", col in ev.columns, col)

    ev_first = ev[ev["table"] == "FIRST"]
    check("evidence.FIRST_rows==99602", len(ev_first) == 99602, f"{len(ev_first)}")
    check("evidence.ncomp_gt1_sum_matches",
          int(ev_first["ncomp_gt1"].sum()) == ncomp_rows, "")

    # floating-point paranoia check stored cl stats equal to recomputed to 1e-6
    ev_cl_min = float(ev[ev["rgzid"] == "cl_min_first"]["cl"].iloc[0])
    check("evidence.cl_min_row", abs(ev_cl_min - clmin) < 1e-6, f"{ev_cl_min}")

    print("\n" + ("ALL CHECKS PASSED ✔" if not failures else
                  f"{len(failures)} CHECK(S) FAILED"))
    sys.exit(0 if not failures else 1)


if __name__ == "__main__":
    main()