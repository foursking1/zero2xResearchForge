"""Spot-check / verification script (judge evidence).

Recomputes two fields from the frozen data:
  1. Record 1, lead ii: annotated symbol counts and their distribution
     (recomputed with wfdb.rdann).
  2. Multi-lead method QRS onset (and QRS peak) Se/PPV from
     results/evidence_table.csv.

Run:  python3 code/spot_check.py
"""
import os
import sys
import csv
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)

from common import DATA_DIR, LEADS, parse_waves
import wfdb


def check_annotation_counts():
    print("=" * 60)
    print("SPOT-CHECK 1: record 1 lead ii annotation counts (via wfdb.rdann)")
    ann = wfdb.rdann(os.path.join(DATA_DIR, "1"), "ii")
    counts = Counter(ann.symbol)
    print("  total symbols:", len(ann.sample))
    print("  symbol counts:", dict(counts))
    waves = parse_waves(list(zip(ann.sample, ann.symbol)))
    print("  parsed waves:  P=%d QRS=%d T=%d (onsets/peaks/offsets per wave)"
          % (len(waves["p"]), len(waves["qrs"]), len(waves["t"])))
    print("  expected:      P peaks=5, QRS peaks(N)=6, T peaks=5, then"
          " onset/offset counts 16 each")
    print("  (paper/manifest: LUDB total P=16797 / QRS=21965 / T=19661)")
    return counts


def check_evidence_table():
    print("=" * 60)
    print("SPOT-CHECK 2: multilead QRS onset / QRS peak Se/PPV "
          "(from results/evidence_table.csv)")
    path = os.path.join(ROOT, "results", "evidence_table.csv")
    with open(path) as fo:
        rows = list(csv.DictReader(fo))
    for pt in ("qrs_onset", "qrs_peak"):
        for r in rows:
            if r["method"] == "multilead" and r["point_type"] == pt:
                print(f"  {pt}: Se={r['se']}% PPV={r['ppv']}% "
                      f"(TP={r['tp']} FP={r['fp']} FN={r['fn']}, "
                      f"m={r['mean_err_ms']}ms sd={r['std_err_ms']}ms)")
    print("  (paper anchor multilead: QRS onset Se=99.61% PPV=99.87%)")


if __name__ == "__main__":
    check_annotation_counts()
    check_evidence_table()