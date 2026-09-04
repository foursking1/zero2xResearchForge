"""Shared utilities for the pages2k_2019 (Neukom et al. 2019) re-discovery analysis.

All data are read in place from the frozen data bundle; nothing is copied or
downloaded. This module provides:
  - data loading from the .RData bundle
  - a 30-200 yr FFT band-pass filter
  - a 30-200 yr Butterworth filtfilt band-pass filter (robustness check)
  - OLS linear-trend helper
"""
from __future__ import annotations

import os
import numpy as np
import pyreadr
from scipy import signal

# ----------------------------------------------------------------------------
# Paths (frozen data bundle, read in place)
# ----------------------------------------------------------------------------
DATA_ROOT = r"E:\scisolvebench-data\asset-data\datasets-v1\v1\pages2k_2019"
FILES = os.path.join(DATA_ROOT, "real_data_candidates", "reconstruction_model_subset_v1", "files")

RECONS_RDATA = os.path.join(FILES, "recons.PCP.ARnoise.RData")          # noise.full.ensemble (2000 x 3000)
DANDAMOD_RDATA = os.path.join(FILES, "Models_fullforced_Past1000_GMST_AprMAr.RData")  # models.ama.fullforced
CTRL_RDATA = os.path.join(FILES, "Models_ctrl_GMST_AprMar.RData")       # ctl.ama
DANDA_RDATA = os.path.join(FILES, "DandA_CESM_ens_30-200_1318.RData")   # da.* + resid + models.ctl.var

METHODS = ["PCR", "CPS", "PAI"]            # methods present in this frozen subset
METHOD_SLICES = {"PCR": slice(0, 1000), "CPS": slice(1000, 2000), "PAI": slice(2000, 3000)}
N_MEMBERS = 1000


# ----------------------------------------------------------------------------
# Data loading
# ----------------------------------------------------------------------------
def load_reconstructions() -> np.ndarray:
    """Return the (2000 x 3000) GMST reconstruction ensemble (methods stacked
    PCR -> CPS -> PAI, 1000 members each).  Row index i corresponds to year
    i+1 CE (rows 0..1999 = years 1..2000 CE)."""
    res = pyreadr.read_r(RECONS_RDATA)
    return res["noise.full.ensemble"].values.astype(np.float64)


def load_models_fullforced():
    """Return (n_years, 23) full-forced past1000 GMST (Kelvin).  Year axis is
    calibrated as year = 851 + row (rows 0..1154 = years 851..2005 CE)."""
    res = pyreadr.read_r(DANDAMOD_RDATA)
    df = res["models.ama.fullforced"]
    return df.values.astype(np.float64), list(df.columns)


def load_control_runs():
    """Return the control-run matrix ctl.ama (1198 x 29) with NaN padding."""
    res = pyreadr.read_r(CTRL_RDATA)
    df = res["ctl.ama"]
    return df.values.astype(np.float64), list(df.columns)


def load_danda():
    """Return dict with the pre-computed D&A objects."""
    res = pyreadr.read_r(DANDA_RDATA)
    out = {
        "all_ens": res["da.cesm.all.ens.14.30.200"].values.astype(np.float64),
        "volc_ens": res["da.cesm.volc.ens.14.30.200"].values.astype(np.float64),
        "resid": res["da.cesm.all.ens.14.30.200.resid"].values.ravel().astype(np.float64),
        "ctl_var": res["models.ctl.var.30.200"].values.ravel().astype(np.float64),
    }
    return out


# ----------------------------------------------------------------------------
# Band-pass filters (30-200 yr)
# ----------------------------------------------------------------------------
def bandpass_fft(x, lo=30.0, hi=200.0, dt=1.0):
    """Brick-wall FFT band-pass filter retaining periods in (lo, hi) years.

    The linear trend and all power outside the band are removed.  This is a
    zero-phase, non-causal filter (the standard approach used for these data).
    """
    x = np.asarray(x, dtype=np.float64)
    n = len(x)
    X = np.fft.rfft(x - x.mean())
    f = np.fft.rfftfreq(n, d=dt)
    mask = (f >= 1.0 / hi) & (f <= 1.0 / lo)
    X[~mask] = 0.0
    return np.fft.irfft(X, n)


def bandpass_butter(x, lo=30.0, hi=200.0, dt=1.0, order=2):
    """Zero-phase Butterworth band-pass (order = number of 2nd-order sections),
    used as a robustness check for the FFT filter."""
    x = np.asarray(x, dtype=np.float64)
    nyq = 0.5 / dt
    Wn = [1.0 / hi / nyq, 1.0 / lo / nyq]
    b, a = signal.butter(order, Wn, btype="band")
    return signal.filtfilt(b, a, x)


# ----------------------------------------------------------------------------
# Trend helper
# ----------------------------------------------------------------------------
def ols_trend(y, dt=1.0):
    """OLS slope of y vs index, in units of y per dt year."""
    x = np.arange(len(y), dtype=np.float64)
    b, a = np.polyfit(x, y, 1)
    return b  # per year


def ols_trend_per_century(y):
    return ols_trend(y) * 100.0
