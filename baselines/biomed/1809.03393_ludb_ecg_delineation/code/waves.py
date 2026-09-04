"""P/T wave detection in single-lead signal within windows relative to QRS.

Each detected wave is (onset, peak, offset) in samples (None entries allowed).
"""
import numpy as np
from common import FS, bandpass, highpass


def estimate_noise_amp(x, fs=FS):
    """Robust noise amplitude estimate from high-frequency residue (>30 Hz)."""
    hf = bandpass(x, 30.0, 100.0, fs=fs)
    return float(np.median(np.abs(hf - np.median(hf))) * 1.4826)


def _stand_peaks(seg):
    """Very small helper: centered absolute segment."""
    return seg - np.median(seg)


def wave_in_window(x, lo, hi, peak_present_thr, min_amp=None,
                   bound_frac=0.18, dsearch_s=0.080, fs=FS):
    """Detect a single dominant wave (P or T) inside [lo, hi].

    Returns (onset, peak, offset) samples within x, or None.
    Signal `x` must already be band-pass filtered (0.5-30 Hz).
    """
    lo = max(0, int(lo))
    hi = min(len(x) - 1, int(hi))
    if hi - lo < int(0.03 * fs):   # <30 ms window is unusable
        return None

    seg = x[lo:hi + 1].astype(float)
    base = np.median(seg[:max(1, int(0.02 * fs))])  # median of first 20 ms
    dev = seg - np.median(seg)

    pkin = int(np.argmax(np.abs(dev)))
    amp = float(dev[pkin])
    peak = lo + pkin
    noise = estimate_noise_amp(x)

    # presence rule: dominant deflection must clear the amplitude threshold,
    # relative to the window's own scale as well as the lead noise floor.
    half = dev.size // 2
    min_dominance = 0.0
    if noise > 0:
        min_dominance = peak_present_thr * noise

    if abs(amp) < min_dominance:
        return None
    if min_amp is not None and abs(amp) < min_amp:
        return None

    # --- boundaries via slope threshold around the peak ---
    d = np.gradient(x)
    s = int(round(dsearch_s * fs))

    # Peak-relative: start search at a point where the deviation drops to a
    # fraction of the peak value, then walk outward to the baseline.
    olo = max(lo, peak - s)
    ohi = peak
    oseg = np.abs(d[olo:ohi]) if ohi > olo else np.zeros(1)
    othr = bound_frac * (oseg.max() if oseg.size else 0.0)
    onset = peak
    if ohi - olo >= 3 and othr > 0:
        idx = np.where(oseg >= othr)[0]
        if idx.size:
            onset = olo + int(idx[0])
        while onset > olo and abs(d[onset - 1]) >= othr:
            onset -= 1

    olo = peak
    ohi = min(hi, peak + s)
    oseg = np.abs(d[olo:ohi]) if ohi > olo else np.zeros(1)
    othr = bound_frac * (oseg.max() if oseg.size else 0.0)
    offset = peak
    if ohi - olo >= 3 and othr > 0:
        idx = np.where(oseg >= othr)[0]
        if idx.size:
            offset = olo + int(idx[-1])
        while offset < ohi - 1 and abs(d[offset + 1]) >= othr:
            offset += 1

    onset = max(lo, int(onset))
    offset = min(hi, int(offset))
    if offset - onset < int(0.01 * fs):
        onset = peak
        offset = peak
    return int(onset), int(peak), int(offset)


def detect_p_wave(xf, qrs_onset, prev_qrs_offset, fs=FS,
                  search_back_ms=300.0, gap_before_qrs_ms=25.0):
    """P wave in the window [max(prev_qrs_offset+20ms, qrs_onset-search), 
    qrs_onset-gap]. `xf` is a 0.5-30 Hz filtered lead. Returns trio or None.
    """
    lo = max(0, prev_qrs_offset + int(0.02 * fs))
    hi = qrs_onset - int(gap_before_qrs_ms / 1000.0 * fs)
    lo = max(lo, qrs_onset - int(search_back_ms / 1000.0 * fs))
    if hi - lo < int(0.04 * fs):
        return None
    pthr = 3.0
    return wave_in_window(xf, lo, hi, peak_present_thr=pthr, min_amp=0.012)


def detect_t_wave(xf, qrs_offset, next_qrs_onset=5000, fs=FS,
                  search_fwd_ms=420.0, gap_after_qrs_ms=20.0):
    """T wave in the window [qrs_offset+gap, min(next_qrs_onset-gap, 
    qrs_offset+search_fwd)]. `xf` is a 0.5-30 Hz filtered lead.
    """
    lo = qrs_offset + int(gap_after_qrs_ms / 1000.0 * fs)
    hi = min(next_qrs_onset - int(gap_after_qrs_ms / 1000.0 * fs),
             qrs_offset + int(search_fwd_ms / 1000.0 * fs))
    hi = min(hi, len(xf) - 1)
    if hi - lo < int(0.05 * fs):
        return None
    thr = 2.5
    return wave_in_window(xf, lo, hi, peak_present_thr=thr, min_amp=0.02)


def per_lead_filtered(lead):
    """0.5-30 Hz band-passed lead ready for P/T analysis."""
    return bandpass(lead, 0.5, 30.0, fs=FS)