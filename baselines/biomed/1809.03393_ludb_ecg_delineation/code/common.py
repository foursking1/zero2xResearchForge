"""Common utilities: config, WFDB I/O, filters, annotation parsing.

LUDB: 200 records x 12 leads x 500 Hz x 10 s (5000 samples/lead).
Annotation symbols: '(' wave onset, ')' wave offset, 'N' QRS peak,
'p' P peak, 't' T peak.
"""
import os
import numpy as np
import wfdb
from scipy.signal import butter, filtfilt

# ----------------------------------------------------------------------------
# Config / paths
# ----------------------------------------------------------------------------
_DEFAULT_DATA = "/mnt/f/dataset/biomed/1809.03393_ludb_ecg_delineation/ludb_1.0.1/data"
DATA_DIR = os.environ.get("LUDB_DATA_DIR", _DEFAULT_DATA)
FS = 500          # Hz
DURATION = 10.0   # s
NSAMP = int(FS * DURATION)          # 5000
LEADS = ["i", "ii", "iii", "avr", "avl", "avf",
         "v1", "v2", "v3", "v4", "v5", "v6"]
NLEADS = 12

# ANSI/AAMI EC57:1998 tolerance (+/-150 ms), at 500 Hz = +/-75 samples
TOL_MS = 150.0
TOL_SAMP = int(round(TOL_MS * FS / 1000.0))  # 75

# 'N' = QRS peak, 'p' = P peak, 't' = T peak
WAVE_OF_PEAK = {"N": "qrs", "p": "p", "t": "t"}
PEAK_SYM_OF_WAVE = {"qrs": "N", "p": "p", "t": "t"}

# Point-type families (for the evidence table)
POINT_TYPES = [
    "p_onset", "p_peak", "p_offset",
    "qrs_onset", "qrs_peak", "qrs_offset",
    "t_onset", "t_peak", "t_offset",
]


# ----------------------------------------------------------------------------
# Data I/O
# ----------------------------------------------------------------------------
def load_signal(record_id):
    """Return (numpy float array 5000x12, fields)."""
    sig, fields = wfdb.rdsamp(os.path.join(DATA_DIR, str(record_id)))
    return np.asarray(sig, dtype=float), fields


def load_annotations(record_id):
    """Return dict lead -> list of (sample, symbol)."""
    out = {}
    for lead in LEADS:
        ann = wfdb.rdann(os.path.join(DATA_DIR, str(record_id)), lead)
        out[lead] = list(zip(ann.sample.astype(int).tolist(), list(ann.symbol)))
    return out


def parse_waves(annotations):
    """Parse a single lead annotation stream into per-wave groups.

    Returns dict wave -> (onset, peak, offset), where onset/peak/offset are
    sample times (None if not annotated). LUDB stores waves as
    consecutive `( peak )` groups; a small fraction of waves lack the onset
    '(' (their onset is not annotated). Matching is peak-based: for each peak
    symbol (N/p/t) attach the nearest preceding '(' with no closing ')' in
    between (=> onset) and the nearest following ')' with no '(' in between
    (=> offset). Handle several malformed-group cases seen in the data.
    """
    waves = {"p": [], "qrs": [], "t": []}
    n = len(annotations)
    # Pre-extract indexes by kind
    on_idx = [i for i, (_, s) in enumerate(annotations) if s == "("]
    off_idx = [i for i, (_, s) in enumerate(annotations) if s == ")"]
    peak_pairs = [(i, s) for i, (_, s) in enumerate(annotations)
                  if s in ("N", "p", "t")]
    # match each peak
    for pi, (pos, sym) in enumerate(peak_pairs):
        wtype = WAVE_OF_PEAK[sym]
        peak_samp = int(annotations[pos][0])
        # onset: nearest '(' before this peak that is not already consumed,
        # and that has no ')' between it and the peak.
        onset = None
        for oi in sorted(on_idx, reverse=True):
            if oi >= pos:
                continue
            if any(off_idx[j] > oi and off_idx[j] < pos
                   for j in range(len(off_idx))):
                # a ')' between '(' and this peak -> belongs to previous wave
                continue
            onset = int(annotations[oi][0])
            break
        # offset: nearest ')' after this peak with no '(' between
        offset = None
        for oj in off_idx:
            if oj <= pos:
                continue
            if any(on_idx[k] > pos and on_idx[k] < oj
                   for k in range(len(on_idx))):
                # a '(' between this peak and ')' -> skip
                continue
            offset = int(annotations[oj][0])
            break
        waves[wtype].append((onset, peak_samp, offset))
    return waves


# ----------------------------------------------------------------------------
# Filters (zero-phase butterworth via filtfilt)
# ----------------------------------------------------------------------------
def _butter_ab(order, low, high, fs):
    nyq = fs / 2.0
    if low is None:
        Wn = high / nyq
        b, a = butter(order, Wn, btype="low", output="ba")
    elif high is None:
        Wn = low / nyq
        b, a = butter(order, Wn, btype="high", output="ba")
    else:
        Wn = [low / nyq, high / nyq]
        b, a = butter(order, Wn, btype="band", output="ba")
    return b, a


def bandpass(x, low, high, fs=FS, order=2):
    b, a = _butter_ab(order, low, high, fs)
    return filtfilt(b, a, x)


def highpass(x, low, fs=FS, order=2):
    b, a = _butter_ab(order, low, None, fs)
    return filtfilt(b, a, x)


def moving_average(x, win):
    if win < 1:
        return x.copy()
    csum = np.cumsum(np.insert(x, 0, 0.0))
    return (csum[win:] - csum[:-win]) / float(win)