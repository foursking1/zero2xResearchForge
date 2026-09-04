"""Shared configuration and data-path resolution for the CTO reproduction scripts.

Task: Automatically Labeling Clinical Trial Outcomes (arXiv:2406.10292)
L1 critical-claim verification.

The frozen data package's files were migrated to a shared dataset store
(see data/DATA_LOCATION.md). This module locates the frozen CSVs across the
usual candidate paths or via the CTO_DATA_DIR environment variable.
"""

import os
from pathlib import Path

DATA_FILES = {
    "phase1": "phase1_CTO_rf.csv",
    "phase2": "phase2_CTO_rf.csv",
    "phase3": "phase3_CTO_rf.csv",
    "human": "human_labels_2020_2024.csv",
    "tickers": "labels_and_tickers.csv",
}

EXPECTED_SHA256 = {
    "phase1_CTO_rf.csv": "81963ED27F7FE0F1A87095222F97A9AE774C902CE54BCE8D9C7CC0E38681679F",
    "phase2_CTO_rf.csv": "968850AC8C622A218F658E6505F332867C52580B1F9D15E0EA6076CBEE563BFA",
    "phase3_CTO_rf.csv": "3061A2CF41051787EACA0324EF2CA80BEB90975E20BF740A4A5D4BF9DF6B3FBC",
    "human_labels_2020_2024.csv": "C51B9C455DE8C0BEFC07BC3EC58BA4B09DA35767FD7F0D9F2ECB048CDB51FC47",
    "labels_and_tickers.csv": "83C20DC302B981B33EB3686288080D1D4B9848A7846485636E5D902024C5B058",
}

_HERE = Path(__file__).resolve().parent
_TASK_DIR = _HERE.parent.parent.parent  # agent_solution/code -> task dir

# Phase-group mapping: which CTORF phase model covers which human phase labels.
# These counts replicate the paper's reported matched sizes
# (Phase I = 3,239 / Phase II = 5,060 / Phase III = 2,823).
PHASE_GROUPS = {
    "I": ["PHASE1", "PHASE1/PHASE2", "EARLY_PHASE1"],
    "II": ["PHASE2", "PHASE1/PHASE2", "PHASE2/PHASE3"],
    "III": ["PHASE3", "PHASE2/PHASE3"],
}

CANDIDATE_DATA_DIRS = [
    os.environ.get("CTO_DATA_DIR", ""),
    str(_HERE.parent.parent / "data"),                 # agent_solution/data
    str(_TASK_DIR / "data"),                           # task_dir/data
    "/mnt/f/dataset/biomed/2406.10292_cto_trial_outcomes",
    "/mnt/d/dataset/biomed/2406.10292_cto_trial_outcomes",
    "F:/dataset/biomed/2406.10292_cto_trial_outcomes",
]


def find_data_dir() -> Path:
    for p in CANDIDATE_DATA_DIRS:
        if not p:
            continue
        d = Path(p)
        if (d / "phase1_CTO_rf.csv").exists() and (d / "human_labels_2020_2024.csv").exists():
            return d
    raise FileNotFoundError(
        "Could not locate frozen data directory. Set CTO_DATA_DIR or place the "
        "5 CSVs in one of the candidate paths:\n  "
        + "\n  ".join(CANDIDATE_DATA_DIRS)
    )


def data_path(file_key: str) -> Path:
    d = find_data_dir()
    return d / DATA_FILES[file_key]


def results_dir() -> Path:
    out = _HERE.parent / "results"
    out.mkdir(parents=True, exist_ok=True)
    return out