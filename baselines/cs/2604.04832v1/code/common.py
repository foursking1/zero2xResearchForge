"""Shared configuration, data loading and feature extraction.

All data is read in-place from the frozen dataset root
(``F:/dataset/2604.04832v1``).  No large files are copied.
"""
from __future__ import annotations

import os
from pathlib import Path

import numpy as np

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
DATA_ROOT = Path(os.environ.get(
    "ROSHAMBO_DATA_ROOT",
    r"F:/dataset/2604.04832v1",
))

RAW_DIR = DATA_ROOT / "data" / "raw"
PROCESSED_PATH = DATA_ROOT / "data" / "processed" / "roshambo_combined.npz"
FEATURES_RAW_PATH = DATA_ROOT / "data" / "features" / "features_raw.npz"
FEATURES_NORM_PATH = DATA_ROOT / "data" / "features" / "features_normalized.npz"

NUM_SENSORS = 8
WINDOW = 400
NUM_FEATURES_PER_SENSOR = 9
FEATURE_DIM = NUM_SENSORS * NUM_FEATURES_PER_SENSOR

CLASS_NAMES = {0: "rock", 1: "paper", 2: "scissors"}
# Paper labels sensors S1..S8; the array uses 0-based indices 0..7.
SENSOR_LABEL_1BASED = [f"S{i+1}" for i in range(NUM_SENSORS)]
SENSOR_LABEL_0BASED = [f"sensor_{i}" for i in range(NUM_SENSORS)]

FEATURE_NAMES = [
    "shannon_entropy",
    "sample_entropy",
    "zero_crossings",
    "waveform_length",
    "rms",
    "slope_sign_changes",
    "median_frequency",
    "wavelet_energy",
    "fractal_dimension",
]


def full_feature_names() -> list[str]:
    """72 names: <feature>_s<sensor0based> (column = sensor*9 + feat_idx)."""
    names = []
    for s in range(NUM_SENSORS):
        for fn in FEATURE_NAMES:
            names.append(f"{fn}_s{s}")
    return names


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------
def load_processed() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return (X (N,8,400), Y (N,), participant_ids (N,))."""
    d = np.load(PROCESSED_PATH, allow_pickle=True)
    X = np.asarray(d["X"], dtype=float)
    Y = np.asarray(d["Y"], dtype=int)
    pids = np.asarray(d["participant_ids"], dtype=int)
    return X, Y, pids


def load_features() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return frozen feature matrix (N,72), Y, participant_ids."""
    d = np.load(FEATURES_RAW_PATH, allow_pickle=True)
    F = np.asarray(d["X"], dtype=float)
    Y = np.asarray(d["Y"], dtype=int)
    pids = np.asarray(d["participant_ids"], dtype=int)
    return F, Y, pids


# ---------------------------------------------------------------------------
# 9 sEMG features (implemented with the same libraries as the frozen data)
# ---------------------------------------------------------------------------
def shannon_entropy(signal: np.ndarray) -> float:
    """Shannon entropy of the signal amplitude distribution.

    antropy 0.2.x has no top-level ``shannon_entropy``, so we use the
    histogram-based estimator (identical to the frozen reproduction).
    """
    try:
        import antropy
        return float(antropy.shannon_entropy(signal))
    except Exception:
        hist, _ = np.histogram(signal, bins="fd", density=True)
        hist = hist[hist > 0]
        return float(-np.sum(hist * np.log(hist + 1e-300)))


def sample_entropy(signal: np.ndarray) -> float:
    import antropy
    return float(antropy.sample_entropy(signal, order=2, tolerance=0.2 * np.std(signal)))


def zero_crossings(signal: np.ndarray) -> float:
    return float(np.sum(np.diff(np.sign(signal)) != 0))


def waveform_length(signal: np.ndarray) -> float:
    return float(np.sum(np.abs(np.diff(signal))))


def rms(signal: np.ndarray) -> float:
    return float(np.sqrt(np.mean(signal ** 2)))


def slope_sign_changes(signal: np.ndarray) -> float:
    deriv = np.diff(signal)
    return float(np.sum(np.diff(np.sign(deriv)) != 0))


def median_frequency(signal: np.ndarray, fs: float = 200.0) -> float:
    from scipy.signal import welch
    freqs, psd = welch(signal, fs=fs, nperseg=min(len(signal), 256))
    cum = np.cumsum(psd)
    total = cum[-1]
    if total == 0:
        return 0.0
    idx = np.searchsorted(cum, total * 0.5)
    return float(freqs[min(idx, len(freqs) - 1)])


def wavelet_energy(signal: np.ndarray) -> float:
    import pywt
    coeffs = pywt.wavedec(signal, "db4", level=3)
    return float(sum(np.sum(c ** 2) for c in coeffs))


def _higuchi_fd(signal: np.ndarray, kmax: int = 10) -> float:
    """Higuchi fractal dimension (from-scratch; nolds 0.6.x exposes no
    top-level ``higuchi_fd``, so this matches the frozen reproduction)."""
    N = len(signal)
    if N < 10:
        return 1.0
    l_all, k_vals = [], []
    for k in range(1, kmax + 1):
        lmk = 0.0
        for m in range(1, k + 1):
            lm = 0.0
            for i in range(1, int((N - m) / k) + 1):
                lm += abs(signal[m + i * k - 1] - signal[m + (i - 1) * k - 1])
            if ((N - m) // k * k) != 0:
                lm = lm * (N - 1) / ((N - m) // k * k)
            lmk += lm
        l_all.append(lmk / k)
        k_vals.append(k)
    x = np.log(1.0 / np.array(k_vals))
    y = np.log(np.array(l_all) + 1e-300)
    if np.std(x) < 1e-10:
        return 1.0
    return float(np.polyfit(x, y, 1)[0])


def fractal_dimension(signal: np.ndarray) -> float:
    try:
        import nolds
        if hasattr(nolds, "higuchi_fd"):
            return float(nolds.higuchi_fd(signal))
    except Exception:
        pass
    return _higuchi_fd(signal)


FEATURE_FUNCTIONS = [
    shannon_entropy,
    sample_entropy,
    zero_crossings,
    waveform_length,
    rms,
    slope_sign_changes,
    median_frequency,
    wavelet_energy,
    fractal_dimension,
]


def extract_sample_features(X: np.ndarray) -> np.ndarray:
    """Extract (N, 8*9) features from raw signals X of shape (N, 8, 400).

    A feature that cannot be computed (exception / non-finite) is set to 0.0,
    matching the frozen reproduction pipeline.
    """
    N, num_sensors, _ = X.shape
    F = np.zeros((N, num_sensors * len(FEATURE_FUNCTIONS)))
    for i in range(N):
        for s in range(num_sensors):
            sig = X[i, s, :]
            for f_idx, func in enumerate(FEATURE_FUNCTIONS):
                try:
                    v = func(sig)
                    F[i, s * len(FEATURE_FUNCTIONS) + f_idx] = float(v) if np.isfinite(v) else 0.0
                except Exception:
                    F[i, s * len(FEATURE_FUNCTIONS) + f_idx] = 0.0
    return F


def verify_features_match_frozen(tol: float = 1e-6) -> bool:
    """Check that our feature extraction reproduces the frozen feature file."""
    X, _, _ = load_processed()
    mine = extract_sample_features(X)
    frozen, _, _ = load_features()
    diff = np.abs(mine - frozen)
    ok = bool(np.nanmax(diff) < tol)
    print(f"[verify] feature recomputation max|diff| = {np.nanmax(diff):.3e} "
          f"({'MATCH' if ok else 'MISMATCH'})")
    return ok
