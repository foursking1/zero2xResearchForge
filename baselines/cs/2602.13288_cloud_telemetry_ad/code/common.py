"""Data loading, time-based 70/30 split, validation-from-train windowing and
anomaly-window extraction for the frozen NAB + Microsoft datasets.

Protocol (mirrors the reference paper, Table III / §IV-A):

  * per series, an ordered time split: first 70% -> train, last 30% -> test;
  * the last 10% of the training period -> validation (early stopping and
    likelihood-calibration selection are done here – strictly train-only);
  * ground-truth anomaly windows are intersected with the test period; only
    windows overlapping the test period are used for scoring.

All index arithmetic is done on the *point index* domain of each series, so no
calendar/timestamp handling is ever needed downstream.

Leakage guard: nothing in this module exposes test-period labels or statistics
during fit/validation; labels are only read back for scoring (via
:func:`build_windows` on the detections the model produces on the test slice).
"""

from __future__ import annotations

import glob
import json
import os
import re

import numpy as np
import pandas as pd

NAN_TOKENS = {"None", "null", "NaN", "nan"}

# ---------------------------------------------------------------------------
# paths
# ---------------------------------------------------------------------------

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))

def default_data_root():
    """Return the frozen-data root.  Prefers the task-local ``data/``
    directory when the CSV payload is actually present, else the physical
    frozen location (see DATA_LOCATION.md), else a user override via the
    env var ``PAPERBENCH_DATA_ROOT``."""

    def _healthy(root):
        if not os.path.isdir(root):
            return False
        n_csv = 0
        for ds in ("nab", "microsoft"):
            n_csv += len(glob.glob(os.path.join(root, ds, "data", "*", "*.csv")))
        with_labels = os.path.isfile(
            os.path.join(root, "nab", "labels", "combined_windows.json"))
        return n_csv >= 110 and with_labels

    override = os.environ.get("PAPERBENCH_DATA_ROOT")
    if override and _healthy(override):
        return override
    here = REPO_ROOT
    local = os.path.join(here, "..", "..", "data")
    if _healthy(local):
        return os.path.abspath(local)
    alt = "/mnt/f/dataset/cs/2602.13288_cloud_telemetry_ad"
    if _healthy(alt):
        return alt
    if override and os.path.isdir(override):
        return override
    raise FileNotFoundError(
        "cannot locate a healthy frozen-data root (nab/microsoft CSV trees "
        "+ combined_windows.json); set PAPERBENCH_DATA_ROOT")


# ---------------------------------------------------------------------------
# NAB dataset
# ---------------------------------------------------------------------------

NAB_GROUPS = ["artificialNoAnomaly", "artificialWithAnomaly", "realAdExchange",
              "realAWSCloudwatch", "realKnownCause", "realTraffic", "realTweets"]


def load_nab_series(root=None):
    root = root or default_data_root()
    base = os.path.join(root, "nab", "data")
    out = []
    for group in NAB_GROUPS:
        gdir = os.path.join(base, group)
        for csv_file in sorted(glob.glob(os.path.join(gdir, "*.csv"))):
            rel = os.path.relpath(csv_file, base).replace("\\", "/")
            out.append({
                "dataset": "nab",
                "subgroup": group,
                "file": os.path.relpath(csv_file, base).replace("\\", "/"),
                "relpath": rel,
            })
    return out


def load_nab_windows(root=None):
    root = root or default_data_root()
    with open(os.path.join(root, "nab", "labels", "combined_windows.json")) as fh:
        data = json.load(fh)
    out = {}
    for relpath, win in data.items():
        out[relpath.replace("\\", "/").lstrip("/")] = win
    return out


def load_nab_series_values(series, root=None):
    """Return (timestamps:np.ndarray, values:np.ndarray, key:matching label key)"""
    root = root or default_data_root()
    path = os.path.join(root, "nab", "data", series["file"])
    df = pd.read_csv(path)
    ts = pd.to_datetime(df["timestamp"])
    vals = df["value"].to_numpy(dtype=np.float64)
    label_key = series["relpath"]
    return ts.to_numpy(), vals, label_key


NAB_WINDOW_CACHE = {}


def get_windows_for(label_key):
    if label_key not in NAB_WINDOW_CACHE:
        NAB_WINDOW_CACHE[label_key] = []
        root = default_data_root()
        with open(os.path.join(root, "nab", "labels", "combined_windows.json")) as fh:
            allw = json.load(fh)
            for relpath, win in allw.items():
                key = relpath.replace("\\", "/").lstrip("/")
                NAB_WINDOW_CACHE[key] = win
    return NAB_WINDOW_CACHE[label_key]


# ---------------------------------------------------------------------------
# Microsoft dataset
# ---------------------------------------------------------------------------

MS_GROUPS = ["application-crash-rate-1", "application-crash-rate-2",
             "consumer-purchase-rate", "data-ingress-rate",
             "ecommerce-api-incoming-rps", "middle-tier-api-dependency-latency",
             "mongodb-application-rps", "mongodb-machine-rps",
             "service-unavailable"]

MS_POINT_GAP = 2  # merge consecutive labelled points closer than this into one window


def load_microsoft_series(root=None):
    root = root or default_data_root()
    base = os.path.join(root, "microsoft", "data")
    out = []
    for group in MS_GROUPS:
        gdir = os.path.join(base, group)
        for csv_file in sorted(glob.glob(os.path.join(gdir, "*.csv"))):
            out.append({
                "dataset": "microsoft",
                "subgroup": group,
                "file": os.path.relpath(csv_file, base).replace("\\", "/"),
                "relpath": os.path.relpath(csv_file, base).replace("\\", "/"),
            })
    return out


def load_microsoft_series_values(series, root=None):
    root = root or default_data_root()
    path = os.path.join(root, "microsoft", "data", series["file"])
    df = pd.read_csv(path)
    ts = pd.to_datetime(df["TimeStamp"])
    vals = df["Value"].to_numpy(dtype=np.float64)
    labels = df["Label"].to_numpy(dtype=np.int64)
    return ts.to_numpy(), vals, labels


# ---------------------------------------------------------------------------
# shared split/window helpers
# ---------------------------------------------------------------------------

def time_split(n, train_frac=0.7, val_frac_of_train=0.1):
    """Return (train, val, test) index ranges on the point-axis.

    train : [0, train_end)
    val   : [train_end - val_len, train_end)   (last 10% of the 70%)
    test  : [train_end, n)
    """
    train_end = int(round(n * train_frac))
    if train_end < 1:
        train_end = 1
    val_len = int(round(train_end * val_frac_of_train))
    val_len = max(1, min(val_len, train_end))
    val_start = train_end - val_len
    return (0, train_end), (val_start, train_end), (train_end, n)


def split_ranges_as_slices(n, train_frac=0.7, val_frac_of_train=0.1):
    (a, b), (c, d), (e, f) = time_split(n, train_frac, val_frac_of_train)
    return {"train": slice(a, b), "val": slice(c, d), "test": slice(e, f)}


def windows_to_test_indices(ts, windows, test_start_idx, n):
    """Convert list of ISO-timestamp or [] windows to point-index ranges
    restricted to [test_start_idx, n).  Returns list[(s_idx, e_idx)]."""
    if windows is None or len(windows) == 0:
        return []
    tvals = np.asarray(ts)
    result = []
    for (w0, w1) in windows:
        w0 = pd.Timestamp(w0); w1 = pd.Timestamp(w1)
        if w1 < pd.Timestamp(tvals[test_start_idx]):
            continue  # fully before test period
        if w0 > pd.Timestamp(tvals[n - 1]):
            continue  # fully after test period
        wins = tvals >= np.datetime64(w0)
        win_e = tvals <= np.datetime64(w1)
        s = int(np.argmax(wins)) if wins.any() else test_start_idx
        e = int(n - 1 - np.argmax(win_e[::-1])) if win_e.any() else n - 1
        s = max(s, test_start_idx)
        e = min(e, n - 1)
        if e >= s:
            result.append((s, e))
    return result


def microsoft_labels_to_windows(labels, gap=MS_POINT_GAP):
    """Cluster labelled points into contiguous windows.  Windows are stored
    back in the *entire-series* index domain (later clipped to the test
    period when scoring)."""
    idx = np.nonzero(labels)[0]
    if len(idx) == 0:
        return []
    windows = []
    cur_start = idx[0]
    prev = idx[0]
    for i in idx[1:]:
        if i - prev > gap:
            windows.append((int(cur_start), int(prev)))
            cur_start = i
        prev = i
    windows.append((int(cur_start), int(prev)))
    return windows


def prepare_series(series, runs_dir=None, root=None):
    """Load one series and return a dict with:

      values      : float array (raw)
      ts          : datetime array
      ranges      : {"train": slice, "val": slice, "test": slice}
      test_windows: list[(int,int)] point-index windows on the test period
      has_anomaly_in_test : bool
      n_test      : int
    """
    if series["dataset"] == "microsoft":
        ts, vals, labels = load_microsoft_series_values(series, root)
        all_windows = microsoft_labels_to_windows(labels)
    else:
        ts, vals, _ = load_nab_series_values(series, root)
        label_key = series["relpath"]
        raw_windows = get_windows_for(label_key)
        all_windows = [(pd.Timestamp(a).to_pydatetime(), pd.Timestamp(b).to_pydatetime())
                       for (a, b) in raw_windows] if raw_windows else []

    n = len(vals)
    (a, b), (c, d), (e, f) = time_split(n)
    test_start, test_end = e, f

    if series["dataset"] == "microsoft":
        # all_windows are index-based windows -> clip to test period in index space
        test_windows = [(max(s, test_start), min(t, test_end - 1))
                        for (s, t) in all_windows
                        if t >= test_start and s <= test_end - 1]
        test_windows = [(s_, t_) for (s_, t_) in test_windows if t_ >= s_]
    else:
        test_windows = windows_to_test_indices(ts, all_windows, test_start, test_end)

    return {
        "values": vals,
        "ts": ts,
        "train": slice(a, b),
        "val": slice(c, d),
        "test": slice(e, f),
        "test_windows": test_windows,
        "has_anomaly_in_test": len(test_windows) > 0,
        "n_test": test_end - test_start,
        "n": n,
        "meta": series,
    }


def zscore_fit(x):
    mu = float(np.nanmean(x))
    sd = float(np.nanstd(x))
    if sd < 1e-12:
        sd = 1.0
    return mu, sd


def zscore_apply(x, mu, sd):
    return (np.asarray(x, dtype=np.float64) - mu) / sd


def sliding_windows(x, wlen, step=1):
    """Return (n_windows, wlen) array of sliding windows over 1-D x."""
    x = np.asarray(x, dtype=np.float32)
    if x.ndim == 1:
        x = x[:, None]
    n = x.shape[0]
    if n < wlen:
        x = np.pad(x, ((0, wlen - n), (0, 0)), mode="edge")
        n = wlen
    idx = np.arange(wlen)[None, :] + np.arange(0, n - wlen + 1, step)[:, None]
    return x[idx]


def center_offsets(wlen):
    """Offset of each window position's anchor (its centre) w.r.t. window start."""
    return np.arange(wlen)  # every position is reconstructed