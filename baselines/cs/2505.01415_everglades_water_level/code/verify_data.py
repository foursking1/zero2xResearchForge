"""Independent data-fact verification (judge reuse). Prints the facts the
benchmark defines and asserts them against the frozen CSV.

  python verify_data.py
"""
from __future__ import annotations

import hashlib
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common  # noqa: E402

DATA_PATH = common.DATA_PATH


def main() -> None:
    facts = {}
    with open(DATA_PATH, "rb") as f:
        sha = hashlib.sha256(f.read()).hexdigest().upper()
    facts["sha256"] = sha
    facts["sha256_expected"] = common.EXPECTED_SHA256
    facts["sha256_match"] = sha == common.EXPECTED_SHA256.upper()

    df = pd.read_csv(DATA_PATH)
    facts["n_rows_excl_header"] = int(df.shape[0])
    facts["n_cols"] = int(df.shape[1])
    facts["columns"] = list(df.columns)
    dfp = df.copy()
    dfp["date"] = pd.to_datetime(dfp["date"], format="%m/%d/%Y")
    facts["date_min"] = str(dfp["date"].min().date())
    facts["date_max"] = str(dfp["date"].max().date())
    facts["target_columns"] = common.TARGETS
    facts["n_target_missing"] = int(dfp[common.TARGETS].isna().sum().sum())
    facts["n_any_missing"] = int(dfp.isna().sum().sum())
    facts["n_duplicate_dates"] = int(dfp["date"].duplicated().sum())
    facts["split"] = {
        "train": [0, common.TRAIN - 1],
        "val": [common.VAL_LO, common.VAL_HI - 1],
        "test": [common.TEST_LO, common.TEST_HI - 1],
        "n_test": common.TEST,
    }

    assert facts["n_rows_excl_header"] == common.N_DAYS, "row count mismatch"
    assert facts["date_min"] == "2020-10-16" and facts["date_max"] == "2024-08-26"
    assert facts["n_target_missing"] == 0
    assert facts["n_any_missing"] == 0
    assert facts["sha256_match"]

    out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "evidence", "data_facts.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        json.dump(facts, f, indent=1)
    print(json.dumps(facts, indent=1))
    print("\nAll assertions PASSED.")


if __name__ == "__main__":
    main()