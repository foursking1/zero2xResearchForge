"""
Supplementary validation for task 2509.20164_lowdim_materials_screening
=======================================================================
1. Consistency check: for entries with a valid `fcdimen_score` dict, how
   often does argmax(fcdimen_score) agree with dim_fcdimen_c1/c2/c3?
   (The three criteria aggregate the raw scores differently; the agreement
   rate characterises each criterion without re-deriving the full method.)
2. Characterise the 69 c2=2D materials in screened_materials.json that are
   NOT present in 2D_materials.json.

All numbers are computed from the frozen data.
"""

from __future__ import annotations

import ast
import collections
import csv
import json
import os

import ijson

DATA_DIR = os.environ.get(
    "FROZEN_DATA_DIR",
    r"F:\dataset\materials\2509.20164_lowdim_materials_screening",
)
SCREENED = os.path.join(DATA_DIR, "screened_materials.json")
D2 = os.path.join(DATA_DIR, "2D_materials.json")

HERE = os.path.dirname(os.path.abspath(__file__))
SOLUTION_DIR = os.path.dirname(HERE)
RESULTS_DIR = os.path.join(SOLUTION_DIR, "results")


def parse_dict(s):
    if not s or s == "None":
        return None
    try:
        return ast.literal_eval(s)
    except Exception:
        return None


def load_2d_mpids():
    with open(D2, "rb") as f:
        raw = json.load(f)
    out = {}
    for k, v in raw.items():
        if k in ("ids", "nextid"):
            continue
        kv = v["key_value_pairs"]
        out[kv["mpid"]] = kv
    return out


def stream_screened_records():
    """Yield {mpid, dim_fcdimen_*, fcdimen_score, stable, ehull, mp_gap, spacegroup}."""
    cur = None
    with open(SCREENED, "rb") as f:
        for prefix, event, value in ijson.parse(f):
            parts = prefix.split(".")
            if event == "map_key" and len(parts) == 1 and parts[0] == "":
                if value.isdigit():
                    if cur is not None:
                        yield cur
                    cur = {"mpid": value}
                else:
                    if cur is not None:
                        yield cur
                    cur = None
            elif cur is not None and event in ("string", "boolean", "number") and len(parts) == 3 and parts[1] == "key_value_pairs":
                cur[parts[2]] = float(value) if event == "number" else value
        if cur is not None:
            yield cur


def main():
    records = list(stream_screened_records())
    print("screened records:", len(records))

    # ---- 1. argmax(fcdimen_score) agreement with c1/c2/c3 ----
    agree = {"c1": 0, "c2": 0, "c3": 0}
    n = 0
    score_none = 0
    for kv in records:
        fs = parse_dict(kv.get("fcdimen_score"))
        if fs is None:
            score_none += 1
            continue
        n += 1
        argmax = max(fs, key=lambda k: fs[k])
        for crit in ("c1", "c2", "c3"):
            if kv.get(f"dim_fcdimen_{crit}") == argmax:
                agree[crit] += 1

    agreement = {
        "valid_fcdimen_score_entries": n,
        "score_none_entries": score_none,
        "c1_agreement": agree["c1"],
        "c1_agreement_frac": round(agree["c1"] / n, 4) if n else None,
        "c2_agreement": agree["c2"],
        "c2_agreement_frac": round(agree["c2"] / n, 4) if n else None,
        "c3_agreement": agree["c3"],
        "c3_agreement_frac": round(agree["c3"] / n, 4) if n else None,
    }
    print("fcdimen_score vs label agreement:", json.dumps(agreement, indent=2))

    # ---- 2. Characterise the c2=2D mpids missing from 2D_materials.json ----
    d2 = load_2d_mpids()
    screened_2d = {kv["mpid"]: kv for kv in records if kv.get("dim_fcdimen_c2") == "2D"}
    missing = {m: kv for m, kv in screened_2d.items() if m not in d2}
    present = {m: kv for m, kv in screened_2d.items() if m in d2}

    def summarize(kvs):
        ehull = [kv.get("ehull") for kv in kvs.values() if kv.get("ehull") is not None]
        gap = [kv.get("mp_gap") for kv in kvs.values() if kv.get("mp_gap") is not None]
        c1 = collections.Counter(kv.get("dim_fcdimen_c1") for kv in kvs.values())
        stable = collections.Counter(kv.get("stable") for kv in kvs.values())
        return {
            "n": len(kvs),
            "c1_dist": dict(c1),
            "stable_dist": dict(stable),
            "ehull_mean": round(sum(ehull) / len(ehull), 4) if ehull else None,
            "ehull_max": max(ehull) if ehull else None,
            "gap_mean": round(sum(gap) / len(gap), 4) if gap else None,
            "mpids": sorted(kvs.keys()),
        }

    missing_summary = summarize(missing)
    present_summary = summarize(present)
    print("missing 69 summary:", json.dumps(missing_summary, indent=2))
    present_summary_no_mpids = {k: v for k, v in present_summary.items() if k != "mpids"}
    print("present 2988 summary:", json.dumps(present_summary_no_mpids, indent=2))

    out = {
        "fcdimen_score_label_agreement": agreement,
        "c2_2d_total_in_screened": len(screened_2d),
        "c2_2d_in_2d_file": len(present),
        "c2_2d_missing_from_2d_file": len(missing),
        "missing_69": missing_summary,
        "present_2988": present_summary_no_mpids,
    }
    with open(os.path.join(RESULTS_DIR, "supplementary.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)

    with open(os.path.join(RESULTS_DIR, "c2_2d_missing_from_2d_file.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["mpid", "dim_fcdimen_c1", "stable", "ehull", "mp_gap", "spacegroup"])
        for mpid in sorted(missing.keys()):
            kv = missing[mpid]
            w.writerow([mpid, kv.get("dim_fcdimen_c1"), kv.get("stable"),
                        kv.get("ehull"), kv.get("mp_gap"), kv.get("spacegroup")])
    print("Wrote results/supplementary.json and results/c2_2d_missing_from_2d_file.csv")


if __name__ == "__main__":
    main()
