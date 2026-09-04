"""Shared data-loading utilities for the TJH COVID-19 EHR benchmark replication.

Data: frozen TJH (Tongji Hospital) cohort from arXiv:2209.07805's referenced
public dataset (HAIRLAB/Pre_Surv_COVID_19). 375 train + 110 test patients of
longitudinal EHR measurements.

Critical dataset caveat (must be handled transparently):
  * The frozen TEST set (time_series_test_110_preprocess[_en].xlsx) only
    contains 3 of the 74 laboratory features:
        - Lactate dehydrogenase (LDH)
        - High sensitivity C-reactive protein (hsCRP)
        - (%)lymphocyte  (lymphocyte percentage)
    plus timestamps / admission / discharge / outcome.  Age and gender are NOT
    present in the test file.  We therefore evaluate ALL models on the 3
    features that are shared between the train and test files, and document
    this as a subset-calibre deviation from the paper's full-feature pipeline.
"""
from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Paths / file resolution
# ---------------------------------------------------------------------------
# The frozen data may live either in the task's data/ dir or in the physical
# archive (see data/DATA_LOCATION.md).  Search common locations.
_DATA_CANDIDATES = [
    Path(__file__).resolve().parents[2] / "data",                 # task data/
    Path(__file__).resolve().parents[2],                          # task root
    Path("/mnt/f/dataset/biomed/2209.07805_covid_ehr_bench"),     # physical archive (WSL)
]

TRAIN_FNAME = "time_series_375_prerpocess_en.xlsx"
TEST_FNAME = "time_series_test_110_preprocess_en.xlsx"

# 3 features shared by train & test (English header names).
SHARED_FEATURES = [
    "Lactate dehydrogenase",                 # 乳酸脱氢酶 (LDH)
    "High sensitivity C-reactive protein",   # 超敏C反应蛋白 (hsCRP)
    "(%)lymphocyte",                         # 淋巴细胞(%) (lymphocyte %)
]

OUTCOME_COL = "outcome"            # 0 = survived/discharged, 1 = died
TIME_COL = "RE_DATE"               # measurement timestamp
ADMIT_COL = "Admission time"       # 入院时间
DISC_COL = "Discharge time"        # 出院时间
PID_COL = "PATIENT_ID"             # patient id (only present on first row)


def resolve_data_dir() -> Path:
    for cand in _DATA_CANDIDATES:
        if (cand / TRAIN_FNAME).exists() and (cand / TEST_FNAME).exists():
            return cand
    raise FileNotFoundError(
        f"Could not locate frozen data files {TRAIN_FNAME}/{TEST_FNAME} "
        f"in any of {_DATA_CANDIDATES}"
    )


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------
def load_raw() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (train_df, test_df) in long-format with a per-patient 'pid'.

    'pid' is recovered by forward-filling PATIENT_ID (the frozen files only
    spell the patient id on the first row of each block).
    """
    ddir = resolve_data_dir()
    train = pd.read_excel(ddir / TRAIN_FNAME)
    test = pd.read_excel(ddir / TEST_FNAME)
    for df in (train, test):
        df[PID_COL] = df[PID_COL].ffill()
        df["pid"] = df[PID_COL].astype(int)
        df[TIME_COL] = pd.to_datetime(df[TIME_COL])
        df[ADMIT_COL] = pd.to_datetime(df[ADMIT_COL])
        df[DISC_COL] = pd.to_datetime(df[DISC_COL])
        df["hour"] = (
            df[TIME_COL] - df.groupby("pid")[ADMIT_COL].transform("first")
        ).dt.total_seconds() / 3600.0
        df["outcome"] = df[OUTCOME_COL].astype(int)
        df = df.sort_values(["pid", TIME_COL], kind="mergesort").reset_index(drop=True)
        df = load_replace(df)
    return train, test


def load_replace(df: pd.DataFrame) -> pd.DataFrame:
    """(hooked separately so tests can inject customised frames)"""
    return df


def usable_patients(df: pd.DataFrame) -> pd.DataFrame:
    """Drop patients that have no measurement rows at all (no RE_DATE).

    In the frozen TJH train file, 14 of the 375 published patients only carry
    placeholder rows (PATIENT_ID / outcome, but no timestamps and no values).
    They carry zero information and are excluded from modelling.
    """
    ok = df.groupby("pid")["hour"].apply(lambda s: s.notna().any())
    keep = ok[ok].index
    return df[df["pid"].isin(keep)].copy()


def early_window(df: pd.DataFrame, w_hours: float) -> pd.DataFrame:
    """Patients + rows restricted to the first `w_hours` of the admission.

    Every patient keeps at least one *row* (clipped to their available data)
    so that no patient is lost from the evaluation cohort purely because their
    stay was shorter than the window.
    """
    df = df.copy()
    edf = df[df["hour"] <= w_hours]
    # Patients with no row within window still produce their earliest row
    # (window clipped to available data).
    missing = df.loc[~df["pid"].isin(edf["pid"].unique())]
    if len(missing):
        earliest = missing.sort_values("hour").groupby("pid").head(1)
        edf = pd.concat([edf, earliest], ignore_index=True)
    return edf.sort_values(["pid", "hour"]).reset_index(drop=True)


# ---------------------------------------------------------------------------
# Dataset statistics helpers
# ---------------------------------------------------------------------------
def missing_rate(pids: pd.Series, feats: list[str], pdf: pd.DataFrame) -> dict:
    """Patient-level missing rate of each feature over a (windowed) frame."""
    out = {}
    for f in feats:
        if f not in pdf.columns:
            out[f] = 1.0
            continue
        obs = pdf.groupby("pid")[f].apply(lambda s: s.notna().any())
        if len(obs) == 0:
            out[f] = float("nan")
        else:
            out[f] = 1.0 - obs.mean()
    return out