"""QRS detection: Pan-Tompkins-style adaptive detector on a single lead.

Returns, per detected complex, the R peak sample plus onset/offset
estimated from a wider-band filtered signal.

Detection chain: bandpass(5-15 Hz) -> derivative -> square ->
moving-window integration (~150 ms) -> adaptive threshold + local maxima
with a ~200 ms refractory period (no post-hoc duplicate searchback needed).
"""
import numpy as np
from scipy.signal import find_peaks

from common import FS, bandpass


class QRSDetector:
    """Pan-Tompkins-style single-lead QRS detection."""

    def __init__(self, fs=FS,
                 band_low=5.0, band_high=15.0,
                 int_win_s=0.150, refractory_s=0.200,
                 spk_perc=97.0, npk_perc=15.0, thr_frac=0.25):
        self.fs = fs
        self.band_low = band_low
        self.band_high = band_high
        self.int_win = max(1, int(round(int_win_s * fs)))
        self.refractory = int(round(refractory_s * fs))
        self.spk_perc = spk_perc
        self.npk_perc = npk_perc
        self.thr_frac = thr_frac

    def preprocess(self, x):
        bp = bandpass(x, self.band_low, self.band_high, fs=self.fs)
        d = np.diff(bp)
        d = np.concatenate([np.zeros(1), d])
        sq = d ** 2
        csum = np.cumsum(np.insert(sq, 0, 0.0))
        y = (csum[self.int_win:] - csum[:-self.int_win]) / self.int_win
        y = np.concatenate([np.zeros(self.int_win - 1), y])
        return y

    def detect(self, x):
        """Return numpy array of R-peak sample indices (sorted, unique)."""
        y = self.preprocess(x)
        n = len(y)
        if n < self.refractory + 2 or y.max() <= 0:
            return np.array([], dtype=int)

        # Pan-Tompkins style adaptive threshold (SPK/NPK)
        spk = float(np.percentile(y, self.spk_perc))
        npk = float(np.percentile(y, self.npk_perc))
        thr = npk + self.thr_frac * (spk - npk)

        d = int(self.refractory)
        local_max = np.asarray(find_peaks(y, distance=d)[0], dtype=int)
        # the moving-average integration delays the peak by ~int_win/2;
        # shift detections back to the undelayed energy centre
        shift = self.int_win // 2
        cands = [int(k) - shift for k in local_max if y[k] >= thr]

        # Non-maximum suppression + adaptive level refinement
        out = []
        for k in cands:
            if out and (k - out[-1]) < d:
                continue
            out.append(k)
            spk = 0.125 * y[k] + 0.875 * spk
            npk = 0.125 * y[k] * 0.2 + 0.875 * npk
            thr = npk + self.thr_frac * (spk - npk)
        return np.array(sorted(int(k) for k in out), dtype=int)


def refine_r_peak(x, peaks, window_s=0.040):
    """Move each candidate R location to the max-|bandpass| sample around it."""
    bp = bandpass(x, 1.0, 30.0, fs=FS)
    w = int(round(window_s * FS))
    out = []
    for p in peaks:
        lo, hi = max(0, p - w), min(len(x), p + w + 1)
        if lo >= hi:
            out.append(p)
            continue
        out.append(int(np.argmax(np.abs(bp[lo:hi])) + lo))
    return np.array(out, dtype=int)


def qrs_onset_offset(x, rpeak, filter_low=1.0, filter_high=30.0,
                     search_s=0.100, slope_frac=0.10):
    """Estimate QRS onset/offset around an R peak using a wide-band filtered
    derivative (slope) threshold method. Returns (onset, offset) samples.
    """
    n = len(x)
    f = bandpass(x, filter_low, filter_high, fs=FS)
    d = np.gradient(f)
    s = int(round(search_s * FS))

    # --- onset: search left from R ---
    lo, hi = max(0, rpeak - s), rpeak
    if hi - lo < 3:
        onset = rpeak
    else:
        seg = np.abs(d[lo:hi])
        thr = slope_frac * (seg.max() if seg.size else 0.0)
        idx = np.where(seg >= thr)[0]
        onset = lo + (idx[0] if idx.size else 0)
        while onset > 0 and abs(d[onset - 1]) >= thr:
            onset -= 1

    # --- offset: search right from R ---
    lo, hi = rpeak, min(n, rpeak + s)
    if hi - lo < 3:
        offset = rpeak
    else:
        seg = np.abs(d[lo:hi])
        thr = slope_frac * (seg.max() if seg.size else 0.0)
        idx = np.where(seg >= thr)[0]
        offset = lo + (idx[-1] if idx.size else 0)
        while offset < n - 1 and abs(d[offset + 1]) >= thr:
            offset += 1

    return int(max(0, onset)), int(min(n - 1, offset))