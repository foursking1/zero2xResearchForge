#!/usr/bin/env python3
"""Step 1 - data / schema audit of the frozen PTB-XL parquet files.

Answers TASK question 1 (samples / leads / label structure) and writes
results/data_audit.json. Runs in seconds on CPU.
"""
import hashlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common import (
    DATA_DIR,
    EXPECTED_CHECKSUMS,
    TRAIN_PATH,
    VAL_PATH,
    audit_schema,
    save_json,
)

RESULTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
os.makedirs(RESULTS_DIR, exist_ok=True)


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def main() -> None:
    print(f"DATA_DIR = {DATA_DIR}")
    checksums = {os.path.basename(p): sha256(p) for p in (TRAIN_PATH, VAL_PATH)}
    checksum_ok = {
        fn: (ch == EXPECTED_CHECKSUMS[fn]) for fn, ch in checksums.items()
    }
    print("checksums:", checksums)
    print("checksums_ok:", checksum_ok)

    audit = audit_schema()
    audit["checksums"] = checksums
    audit["checksums_ok"] = checksum_ok
    audit["data_dir"] = DATA_DIR

    save_json(audit, os.path.join(RESULTS_DIR, "data_audit.json"))
    print("wrote", os.path.join(RESULTS_DIR, "data_audit.json"))

    tr = audit["train"]
    va = audit["validation"]
    print("TRAIN rows:", tr["rows"], "leads-in-ecg_array:", tr["signal_elem_len"],
          "samples-per-lead:", tr["signal_array_shape"][1], "label-like columns:",
          tr["label_like_columns_found"])
    print("VAL  rows:", va["rows"], "leads-in-ecg_array:", va["signal_elem_len"],
          "samples-per-lead:", va["signal_array_shape"][1], "label-like columns:",
          va["label_like_columns_found"])
    print("NOTE:", audit["note"])


if __name__ == "__main__":
    main()