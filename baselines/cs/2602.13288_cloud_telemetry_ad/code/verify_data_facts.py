"""Freeze-data facts verification (B dimension of the rubric).

Recomputes directly from the frozen CSVs:
  - NAB: 58 series CSVs across 7 subgroups
  - Microsoft: 60 series CSVs across 9 domains; 225,445 rows; 4,555 Label=1
  - combined_windows.json has 58 entries
and optionally compares every file's sha256 against data/source_manifest.json.
"""

from __future__ import annotations

import glob
import hashlib
import json
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import default_data_root


def main():
    root = os.environ.get("PAPERBENCH_DATA_ROOT", default_data_root())

    nab_csvs = sorted(glob.glob(os.path.join(root, "nab", "data", "*", "*.csv")))
    nab_groups = {os.path.basename(os.path.dirname(p)) for p in nab_csvs}
    with open(os.path.join(root, "nab", "labels", "combined_windows.json")) as fh:
        labels = json.load(fh)

    ms_csvs = sorted(glob.glob(os.path.join(root, "microsoft", "data", "*", "*.csv")))
    ms_groups = {os.path.basename(os.path.dirname(p)) for p in ms_csvs}
    ms_rows = 0
    ms_label1 = 0
    for p in ms_csvs:
        for chunk in pd.read_csv(p, chunksize=65536, usecols=["Label"]):
            ms_rows += len(chunk)
            ms_label1 += int(chunk["Label"].sum())

    facts = {
        "nab_series_csv": len(nab_csvs),
        "nab_subgroups": sorted(nab_groups),
        "nab_labels_entries": len(labels),
        "microsoft_series_csv": len(ms_csvs),
        "microsoft_domains": sorted(ms_groups),
        "microsoft_total_rows": int(ms_rows),
        "microsoft_label1": int(ms_label1),
    }
    expected = {
        "nab_series_csv": 58, "nab_subgroups": ["artificialNoAnomaly",
        "artificialWithAnomaly", "realAdExchange", "realAWSCloudwatch",
        "realKnownCause", "realTraffic", "realTweets"],
        "nab_labels_entries": 58,
        "microsoft_series_csv": 60,
        "microsoft_domains": ["application-crash-rate-1", "application-crash-rate-2",
        "consumer-purchase-rate", "data-ingress-rate",
        "ecommerce-api-incoming-rps", "middle-tier-api-dependency-latency",
        "mongodb-application-rps", "mongodb-machine-rps", "service-unavailable"],
        "microsoft_total_rows": 225445, "microsoft_label1": 4555,
    }

    ok = True
    for k, v in expected.items():
        fv = facts[k]
        cmp_v = sorted(v) if isinstance(v, list) else v
        cmp_fv = sorted(fv) if isinstance(fv, list) else fv
        status = "OK" if cmp_fv == cmp_v else "MISMATCH"
        if status == "MISMATCH":
            ok = False
        print(f"[{status}] {k}: {facts[k]}  (expected {v})")

    manifest = os.path.join(root, "source_manifest.json")
    if os.path.exists(manifest):
        with open(manifest) as fh:
            files = json.load(fh)["files"]
        bad = 0
        for f in files:
            p = os.path.join(root, f["file"])
            if not os.path.exists(p):
                print(f"[MISSING] {f['file']}")
                bad += 1
                continue
            if hashlib.sha256(open(p, "rb").read()).hexdigest().upper() != f["sha256"]:
                print(f"[HASH-DIFF] {f['file']}")
                bad += 1
        print(f"[checksums] {len(files) - bad}/{len(files)} files match the frozen manifest")
        ok = ok and bad == 0

    if not ok:
        print("\nFROZEN-DATA FACTS MISMATCH")
        sys.exit(1)
    print("\nall frozen-data facts verified OK")


if __name__ == "__main__":
    main()