"""
Analysis of frozen data for task 2509.20164_lowdim_materials_screening
=====================================================================
Paper: Bagheri et al., "Massive Discovery of Low-Dimensional Materials
from Universal Computational Strategy", arXiv:2509.20164 (2026).

Frozen data (from Zenodo 17035156, databases.zip):
  - screened_materials.json (~197 MB): ASE JSON db, 35,689 entries
  - 2D_materials.json      (~13 MB) : ASE JSON db, 2,988 entries
  - README.txt

The files are ASE database JSON exports. Each material entry carries the
material properties in `key_value_pairs` (mpid, dimen_larsen, fcdimen_score,
dim_fcdimen_c1/c2/c3, stable, ehull, theoretical, magnetic_order,
spacegroup, mp_gap, and for the 2D file also E_exf, robocrys, c2db,
matpedia, mc2d, rae, topo, DBBs).

This script streams screened_materials.json with ijson (it is too large to
need full materialisation for the statistics we need) and loads
2D_materials.json in full. All statistics are computed from the frozen data;
no paper numbers are injected.

Outputs:
  results/evidence_table.csv
  results/metrics.json
  results/screened_c2_distribution.csv
  results/2d_exf_distribution.csv
"""

from __future__ import annotations

import ast
import collections
import csv
import json
import os
import statistics
from decimal import Decimal

import ijson

# ----------------------------------------------------------------------------
# Paths
# ----------------------------------------------------------------------------
DATA_DIR = os.environ.get(
    "FROZEN_DATA_DIR",
    r"F:\dataset\materials\2509.20164_lowdim_materials_screening",
)
SCREENED = os.path.join(DATA_DIR, "screened_materials.json")
D2 = os.path.join(DATA_DIR, "2D_materials.json")

HERE = os.path.dirname(os.path.abspath(__file__))
SOLUTION_DIR = os.path.dirname(HERE)
RESULTS_DIR = os.path.join(SOLUTION_DIR, "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

RANDOM_SEED = 42  # fixed seed (analysis is deterministic; seed kept for audit)


def num_to_float(v):
    if isinstance(v, Decimal):
        return float(v)
    return v


def parse_dim_dict(s: str) -> dict | None:
    """Parse a string like "{'2D': 0.45, '3D': 0.37}" into a dict, or None."""
    if not s or s == "None":
        return None
    try:
        return ast.literal_eval(s)
    except Exception:
        return None


# ----------------------------------------------------------------------------
# 1. Stream screened_materials.json and extract per-entry key_value_pairs
# ----------------------------------------------------------------------------
def stream_screened(path: str):
    """Yield a dict of key_value_pairs per entry using ijson.

    Skips the ASE-db metadata keys ``ids`` and ``nextid`` at the top level.
    """
    cur: dict | None = None
    with open(path, "rb") as f:
        for prefix, event, value in ijson.parse(f):
            parts = prefix.split(".")
            if event == "map_key" and len(parts) == 1 and parts[0] == "":
                # new top-level entry key; only integer keys are material entries
                if value.isdigit():
                    if cur is not None:
                        yield cur
                    cur = {}
                else:
                    # metadata key (ids/nextid): flush and ignore
                    if cur is not None:
                        yield cur
                    cur = None
            elif event in ("string", "boolean", "number") and len(parts) == 3:
                if cur is not None and parts[1] == "key_value_pairs":
                    cur[parts[2]] = num_to_float(value) if event == "number" else value
        if cur is not None:
            yield cur


def load_2d(path: str) -> list[dict]:
    """Load 2D_materials.json fully (small file), returning key_value_pairs per entry."""
    with open(path, "rb") as f:
        raw = json.load(f)
    out = []
    for k, v in raw.items():
        if k in ("ids", "nextid"):
            continue
        out.append(v["key_value_pairs"])
    return out


# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------
DIM_KEYS = ("0D", "1D", "2D", "3D")
MIXED_KEYS = ("01D", "02D", "03D", "12D", "13D", "23D", "012D", "013D", "023D", "123D")


def summarize_dims(counter: collections.Counter) -> dict:
    pure = {k: counter.get(k, 0) for k in DIM_KEYS}
    mixed = {k: counter.get(k, 0) for k in MIXED_KEYS if counter.get(k, 0) > 0}
    total_pure = sum(pure.values())
    total_mixed = sum(mixed.values())
    return {
        "pure": pure,
        "mixed": mixed,
        "total_pure": total_pure,
        "total_mixed": total_mixed,
        "total_classified": total_pure + total_mixed,
        "counts": dict(counter),
    }


def dim_of_larsen(score_str: str) -> str | None:
    """Return the dimension label with the largest Larsen score (or None)."""
    d = parse_dim_dict(score_str)
    if not d:
        return None
    return max(d, key=lambda k: d[k])


# ----------------------------------------------------------------------------
# 2. Analyse screened_materials.json
# ----------------------------------------------------------------------------
def analyse_screened():
    c1 = collections.Counter()
    c2 = collections.Counter()
    c3 = collections.Counter()
    stable_counter = collections.Counter()
    fcdimen_none = 0
    fcdimen_ok = 0
    total = 0
    larsen_dim_for_lowdim = collections.Counter()  # Larsen dim among c2-lowdim
    larsen_dim_all = collections.Counter()
    larsen_parse_fail = 0
    mpid_to_c2 = {}
    ehull_missing = 0

    for kv in stream_screened(SCREENED):
        total += 1
        c1[kv.get("dim_fcdimen_c1")] += 1
        c2[kv.get("dim_fcdimen_c2")] += 1
        c3[kv.get("dim_fcdimen_c3")] += 1
        stable_counter[kv.get("stable")] += 1

        fs = kv.get("fcdimen_score")
        if fs is None or fs == "None":
            fcdimen_none += 1
        else:
            fcdimen_ok += 1

        mpid = kv.get("mpid")
        c2label = kv.get("dim_fcdimen_c2")
        if mpid is not None:
            mpid_to_c2[mpid] = c2label

        # Larsen dimensionality relationship
        ldim = dim_of_larsen(kv.get("dimen_larsen"))
        if ldim is None:
            larsen_parse_fail += 1
        else:
            larsen_dim_all[ldim] += 1
            if c2label not in ("3D", "None"):
                larsen_dim_for_lowdim[ldim] += 1

    c2sum = summarize_dims(c2)
    # lowdim (paper claim) = all classified (non-None) minus pure 3D
    lowdim_total = c2sum["total_classified"] - c2.get("3D", 0)

    return {
        "total": total,
        "stable_counts": dict(stable_counter),
        "fcdimen_score_none": fcdimen_none,
        "fcdimen_score_ok": fcdimen_ok,
        "c1": summarize_dims(c1),
        "c2": c2sum,
        "c3": summarize_dims(c3),
        "lowdim_c2": lowdim_total,
        "larsen_dim_all": dict(larsen_dim_all),
        "larsen_dim_for_lowdim": dict(larsen_dim_for_lowdim),
        "larsen_parse_fail": larsen_parse_fail,
        "mpid_to_c2": mpid_to_c2,
    }


# ----------------------------------------------------------------------------
# 3. Analyse 2D_materials.json
# ----------------------------------------------------------------------------
def analyse_2d():
    entries = load_2d(D2)

    c1 = collections.Counter()
    c2 = collections.Counter()
    c3 = collections.Counter()
    known_flags = collections.Counter()
    exf = []
    ehull = []
    mp_gap = []
    stable_counter = collections.Counter()
    mpids = []
    novel_count = 0
    novel_exf = []

    for kv in entries:
        c1[kv.get("dim_fcdimen_c1")] += 1
        c2[kv.get("dim_fcdimen_c2")] += 1
        c3[kv.get("dim_fcdimen_c3")] += 1
        stable_counter[kv.get("stable")] += 1
        e = kv.get("E_exf")
        if e is not None:
            exf.append(float(e))
        if kv.get("ehull") is not None:
            ehull.append(float(kv["ehull"]))
        if kv.get("mp_gap") is not None:
            mp_gap.append(float(kv["mp_gap"]))
        for flag in ("c2db", "matpedia", "mc2d", "rae", "topo", "DBBs", "robocrys"):
            if kv.get(flag):
                known_flags[flag] += 1
        any_known = any(kv.get(f) for f in ("c2db", "matpedia", "mc2d", "rae", "topo", "DBBs", "robocrys"))
        if not any_known:
            novel_count += 1
            if e is not None:
                novel_exf.append(float(e))
        mpids.append(kv.get("mpid"))

    # E_exf threshold analysis (paper: easy <=35, potential 35-125, strong >125 meV/A^2)
    easy = [e for e in exf if e <= 35.0]
    potential = [e for e in exf if 35.0 < e < 125.0]
    strong = [e for e in exf if e >= 125.0]

    # Novel subset within exfoliable classes
    def classify(e):
        if e <= 35.0:
            return "easy"
        if e < 125.0:
            return "potential"
        return "strong"

    exf_novel_class = collections.Counter()
    for kv, e in [(kv, kv.get("E_exf")) for kv in entries if kv.get("E_exf") is not None]:
        any_known = any(kv.get(f) for f in ("c2db", "matpedia", "mc2d", "rae", "topo", "DBBs", "robocrys"))
        if not any_known:
            exf_novel_class[classify(float(e))] += 1

    def stats(vals):
        if not vals:
            return None
        s = sorted(vals)
        n = len(s)
        q1 = s[n // 4] if n else None
        q3 = s[3 * n // 4] if n else None
        return {
            "n": n,
            "min": s[0],
            "q1": q1,
            "median": s[n // 2] if n else None,
            "mean": sum(s) / n,
            "q3": q3,
            "max": s[-1],
        }

    return {
        "total": len(entries),
        "unique_mpids": len(set(mpids)),
        "stable_counts": dict(stable_counter),
        "c1": summarize_dims(c1),
        "c2": summarize_dims(c2),
        "c3": summarize_dims(c3),
        "E_exf": stats(exf),
        "E_exf_thresholds": {
            "easy_le35": len(easy),
            "potential_35_125": len(potential),
            "strong_ge125": len(strong),
            "easy_plus_potential": len(easy) + len(potential),
        },
        "known_flags": dict(known_flags),
        "novel_total": novel_count,
        "novel_E_exf": stats(novel_exf),
        "exf_novel_class": dict(exf_novel_class),
        "ehull": stats(ehull),
        "mp_gap": stats(mp_gap),
        "mpids": mpids,
        "exf_raw": exf,
    }


# ----------------------------------------------------------------------------
# 4. Cross-checks
# ----------------------------------------------------------------------------
def cross_check(screened_stats, d2_stats):
    # All 2D-file mpids should be among screened c2==2D mpids
    screened_2d_mpids = {m for m, c in screened_stats["mpid_to_c2"].items() if c == "2D"}
    d2_mpids = set(d2_stats["mpids"])
    in_both = d2_mpids & screened_2d_mpids
    only_2d_file = d2_mpids - screened_2d_mpids
    only_screened = screened_2d_mpids - d2_mpids
    return {
        "screened_c2_2d_mpids": len(screened_2d_mpids),
        "2d_file_mpids": len(d2_mpids),
        "2d_file_mpids_in_screened_c2_2d": len(in_both),
        "2d_file_mpids_not_in_screened_c2_2d": sorted(only_2d_file),
        "screened_c2_2d_mpids_not_in_2d_file": len(only_screened),
    }


# ----------------------------------------------------------------------------
# 5. Write outputs
# ----------------------------------------------------------------------------
def write_evidence_table(screened, d2, cross):
    rows = []

    def add(dataset, group, metric, value):
        rows.append({"dataset": dataset, "group": group, "metric": metric, "value": value})

    # Screened database
    add("screened_materials.json", "count", "total_entries", screened["total"])
    add("screened_materials.json", "count", "stable", screened["stable_counts"].get(True, 0))
    add("screened_materials.json", "count", "unstable", screened["stable_counts"].get(False, 0))
    add("screened_materials.json", "count", "fcdimen_score_none", screened["fcdimen_score_none"])
    add("screened_materials.json", "count", "fcdimen_score_ok", screened["fcdimen_score_ok"])
    for crit in ("c1", "c2", "c3"):
        for dim, cnt in screened[crit]["counts"].items():
            add("screened_materials.json", f"dim_fcdimen_{crit}", dim, cnt)
    add("screened_materials.json", "fcdimen_c2", "total_lowdim_non3D", screened["lowdim_c2"])
    add("screened_materials.json", "fcdimen_c2", "pure_0D", screened["c2"]["pure"]["0D"])
    add("screened_materials.json", "fcdimen_c2", "pure_1D", screened["c2"]["pure"]["1D"])
    add("screened_materials.json", "fcdimen_c2", "pure_2D", screened["c2"]["pure"]["2D"])
    add("screened_materials.json", "fcdimen_c2", "pure_3D", screened["c2"]["pure"]["3D"])
    add("screened_materials.json", "fcdimen_c2", "mixed_total", screened["c2"]["total_mixed"])
    add("screened_materials.json", "larsen", "larsen_3D_among_c2_lowdim",
        screened["larsen_dim_for_lowdim"].get("3D", 0))
    add("screened_materials.json", "larsen", "larsen_parse_fail", screened["larsen_parse_fail"])

    # 2D database
    add("2D_materials.json", "count", "total_entries", d2["total"])
    add("2D_materials.json", "count", "unique_mpids", d2["unique_mpids"])
    for crit in ("c1", "c2", "c3"):
        for dim, cnt in d2[crit]["counts"].items():
            add("2D_materials.json", f"dim_fcdimen_{crit}", dim, cnt)
    for stat_name in ("n", "min", "q1", "median", "mean", "q3", "max"):
        add("2D_materials.json", "E_exf", stat_name, d2["E_exf"][stat_name])
    for k, v in d2["E_exf_thresholds"].items():
        add("2D_materials.json", "E_exf_thresholds", k, v)
    for flag, cnt in d2["known_flags"].items():
        add("2D_materials.json", "known_flags", flag, cnt)
    add("2D_materials.json", "known_flags", "novel_total", d2["novel_total"])
    for cls, cnt in d2["exf_novel_class"].items():
        add("2D_materials.json", "exf_novel_class", cls, cnt)
    for stat_name in ("n", "min", "q1", "median", "mean", "q3", "max"):
        if d2["ehull"]:
            add("2D_materials.json", "ehull", stat_name, d2["ehull"][stat_name])
    for stat_name in ("n", "min", "q1", "median", "mean", "q3", "max"):
        if d2["mp_gap"]:
            add("2D_materials.json", "mp_gap", stat_name, d2["mp_gap"][stat_name])

    # Cross-checks
    add("cross_check", "mpid_overlap", "screened_c2_2d_mpids", cross["screened_c2_2d_mpids"])
    add("cross_check", "mpid_overlap", "2d_file_mpids", cross["2d_file_mpids"])
    add("cross_check", "mpid_overlap", "2d_file_mpids_in_screened_c2_2d", cross["2d_file_mpids_in_screened_c2_2d"])
    add("cross_check", "mpid_overlap", "screened_c2_2d_mpids_not_in_2d_file", cross["screened_c2_2d_mpids_not_in_2d_file"])

    with open(os.path.join(RESULTS_DIR, "evidence_table.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["dataset", "group", "metric", "value"])
        writer.writeheader()
        writer.writerows(rows)

    return rows


def write_distributions(screened, d2):
    # Screened c2 distribution CSV
    with open(os.path.join(RESULTS_DIR, "screened_c2_distribution.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["dim_fcdimen_c2", "count"])
        for dim, cnt in sorted(screened["c2"]["counts"].items(), key=lambda x: -x[1]):
            writer.writerow([dim, cnt])

    # 2D E_exf distribution histogram (binned) from raw values
    if d2.get("exf_raw"):
        bins = [0, 20, 35, 50, 75, 100, 125, 150, 200, 300, 500, 1000, 2000]
        hist = collections.Counter()
        for e in d2["exf_raw"]:
            placed = False
            for i in range(len(bins) - 1):
                if bins[i] <= e < bins[i + 1]:
                    hist[i] += 1
                    placed = True
                    break
            if not placed:
                hist[len(bins) - 2] += 1  # tail bin >= last edge
        with open(os.path.join(RESULTS_DIR, "2d_exf_distribution.csv"), "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["bin_lower_meV_per_Ang2", "bin_upper_meV_per_Ang2", "count"])
            for i in sorted(hist):
                writer.writerow([bins[i], bins[i + 1], hist[i]])


def main():
    print("Analysing screened_materials.json ...")
    screened = analyse_screened()
    print(f"  total entries: {screened['total']}")
    print(f"  c2 low-dim (non-3D): {screened['lowdim_c2']}")

    print("Analysing 2D_materials.json ...")
    d2 = analyse_2d()
    print(f"  total entries: {d2['total']}")

    print("Cross-checks ...")
    cross = cross_check(screened, d2)
    print(f"  screened c2-2D mpids: {cross['screened_c2_2d_mpids']}, "
          f"2D file mpids in screened c2-2D: {cross['2d_file_mpids_in_screened_c2_2d']}")

    # Histogram CSVs
    write_distributions(screened, d2)
    # remove bulky fields before serialisation
    d2.pop("mpids", None)
    d2.pop("exf_raw", None)

    # Build metrics.json (drop bulky key_value collections)
    metrics = {
        "task_id": "2509.20164_lowdim_materials_screening",
        "frozen_data_dir": DATA_DIR,
        "random_seed": RANDOM_SEED,
        "device": "cpu",
        "screened_materials.json": {
            "total_entries": screened["total"],
            "stable_counts": screened["stable_counts"],
            "fcdimen_score_none": screened["fcdimen_score_none"],
            "fcdimen_score_ok": screened["fcdimen_score_ok"],
            "dim_fcdimen_c1_counts": screened["c1"]["counts"],
            "dim_fcdimen_c2_counts": screened["c2"]["counts"],
            "dim_fcdimen_c3_counts": screened["c3"]["counts"],
            "fcdimen_c2_pure": screened["c2"]["pure"],
            "fcdimen_c2_mixed": screened["c2"]["mixed"],
            "fcdimen_c2_total_lowdim_non3D": screened["lowdim_c2"],
            "larsen_dim_all": screened["larsen_dim_all"],
            "larsen_dim_for_c2_lowdim": screened["larsen_dim_for_lowdim"],
            "larsen_parse_fail": screened["larsen_parse_fail"],
        },
        "2D_materials.json": {
            "total_entries": d2["total"],
            "unique_mpids": d2["unique_mpids"],
            "stable_counts": d2["stable_counts"],
            "dim_fcdimen_c1_counts": d2["c1"]["counts"],
            "dim_fcdimen_c2_counts": d2["c2"]["counts"],
            "dim_fcdimen_c3_counts": d2["c3"]["counts"],
            "E_exf": d2["E_exf"],
            "E_exf_thresholds": d2["E_exf_thresholds"],
            "known_flags": d2["known_flags"],
            "novel_total": d2["novel_total"],
            "exf_novel_class": d2["exf_novel_class"],
            "ehull_stats": d2["ehull"],
            "mp_gap_stats": d2["mp_gap"],
        },
        "cross_check": cross,
        "paper_anchor_comparison": {
            "paper_screened_pool_153234": 153234,
            "frozen_screened_entries": screened["total"],
            "paper_benchmark_35689": 35689,
            "paper_lowdim_total_9139": 9139,
            "frozen_lowdim_c2": screened["lowdim_c2"],
            "paper_2d_count_3057": 3057,
            "frozen_c2_2d_count": screened["c2"]["pure"]["2D"],
            "paper_exfoliable_novel_887": 887,
            "frozen_exfoliable_novel": d2["exf_novel_class"]["easy"] + d2["exf_novel_class"]["potential"],
        },
    }

    with open(os.path.join(RESULTS_DIR, "metrics.json"), "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, default=str)

    rows = write_evidence_table(screened, d2, cross)
    print(f"Wrote {len(rows)} evidence rows.")
    print("Done.")


if __name__ == "__main__":
    main()
