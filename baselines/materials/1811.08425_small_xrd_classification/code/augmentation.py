"""Physics-informed data augmentation following the paper Eqs. 1-3.

Eq. 1 (peak scaling): a periodic subset of the diffraction peaks is scaled by
       a random factor c ~ U(0.5, 1.5).
Eq. 2 (peak removal): a periodic subset of the diffraction peaks is set to zero.
Eq. 3 (pattern shift): the whole pattern is shifted along 2theta by a small
       random amount (|delta| <= 0.1 deg) and resampled to the fixed grid.

Augmented samples are generated **only from the training folds** (no leakage).
"""

import numpy as np
from scipy.signal import find_peaks

import config


def _find_peaks_norm(spec, tw, prom_frac=0.02, rel_height=0.5):
    """Peak positions using a relative prominence threshold.

    Returns peak indices and their prominence-based widths.
    """
    # prominence relative to the spectrum's dynamic range
    prom = max(prom_frac * (spec.max() - spec.min()), 1e-4)
    peaks, props = find_peaks(spec, prominence=prom)
    widths = props.get("widths", None)
    return peaks, widths


def _window_from_width(width, min_half=1, max_half=5):
    """Half-width of the peak influence window (in points)."""
    if width is None or not np.isfinite(width):
        return min_half
    half = int(np.clip(width / 2.0, min_half, max_half))
    return half


def _scale_peaks(spec, peaks, widths, rng):
    """Eq. 1: scale a periodic subset of peaks by factor c ~ U(0.5, 1.5)."""
    out = spec.copy()
    if len(peaks) == 0:
        return out
    period = max(2, int(config.SCALE_PERIOD))
    offset = rng.integers(0, period)
    sel = peaks[offset::period]
    # choose a random fraction of the selected peaks to actually scale
    n_sel = max(1, int(np.ceil(len(sel) * config.SCALE_FRAC)))
    if n_sel < len(sel):
        sel = rng.choice(sel, size=n_sel, replace=False)
    for p in sel:
        c = rng.uniform(config.SCALE_C_LO, config.SCALE_C_HI)
        w = _window_from_width(widths[np.where(peaks == p)[0][0]]
                               if widths is not None else None)
        lo = max(0, p - w)
        hi = min(len(spec), p + w + 1)
        out[lo:hi] = out[lo:hi] * c
    return out


def _remove_peaks(spec, peaks, widths, rng):
    """Eq. 2: set a periodic subset of peaks to zero."""
    out = spec.copy()
    if len(peaks) == 0:
        return out
    period = max(2, int(config.REMOVE_PERIOD))
    offset = rng.integers(0, period)
    sel = peaks[offset::period]
    n_sel = max(1, int(np.ceil(len(sel) * config.REMOVE_FRAC)))
    if n_sel < len(sel):
        sel = rng.choice(sel, size=n_sel, replace=False)
    for p in sel:
        w = _window_from_width(widths[np.where(peaks == p)[0][0]]
                               if widths is not None else None)
        lo = max(0, p - w)
        hi = min(len(spec), p + w + 1)
        out[lo:hi] = 0.0
    return out


def _shift_pattern(spec, tw, rng):
    """Eq. 3: shift the pattern along 2theta by delta ~ U(-0.1, 0.1) deg."""
    delta = rng.uniform(-config.SHIFT_MAX_DEG, config.SHIFT_MAX_DEG)
    shifted = np.interp(tw + delta, tw, spec, left=spec[0], right=spec[-1])
    return shifted


def augment_spectrum(spec, tw, rng, peaks=None, widths=None):
    """Apply one of the three physics-informed transformations at random."""
    if peaks is None:
        peaks, widths = _find_peaks_norm(spec, tw)
    k = rng.integers(0, 3)
    if k == 0:
        return _scale_peaks(spec, peaks, widths, rng)
    elif k == 1:
        return _remove_peaks(spec, peaks, widths, rng)
    else:
        return _shift_pattern(spec, tw, rng)


def make_augmented(X, tw, n_aug, rng, label=None):
    """Generate `n_aug` augmented spectra from the set X (train fold only).

    Mixes transformed copies (AUG_MIX_RATIO) with plain copies of the originals
    so the network still sees the original distribution.

    Returns (X_aug, y_aug) with y_aug = label (constant) if label given, else
    the source index repeated.
    """
    N = X.shape[0]
    out = np.empty((n_aug, X.shape[1]), dtype=np.float64)
    if label is None:
        y_out = np.empty(n_aug, dtype=np.int64)
    for i in range(n_aug):
        src = rng.integers(0, N)
        spec = X[src]
        if rng.random() < config.AUG_MIX_RATIO:
            peaks, widths = _find_peaks_norm(spec, tw)
            spec = augment_spectrum(spec, tw, rng, peaks, widths)
        out[i] = spec
        if label is None:
            y_out[i] = src
    if label is not None:
        return out, np.full(n_aug, label, dtype=np.int64)
    return out, y_out


if __name__ == "__main__":
    from data_loader import load_data
    rng = np.random.default_rng(config.AUG_SEED)
    d = load_data()
    tw = d["tw"]
    spec = d["X_exp"][0]
    peaks, widths = _find_peaks_norm(spec, tw)
    print("peaks found:", len(peaks))
    for name, fn in [("scale", lambda s, rng, p=peaks, w=widths: _scale_peaks(s, p, w, rng)),
                     ("remove", lambda s, rng, p=peaks, w=widths: _remove_peaks(s, p, w, rng)),
                     ("shift", lambda s, rng: _shift_pattern(s, tw, rng))]:
        out = fn(spec, rng)
        print(f"{name}: shape {out.shape}, max {out.max():.3f}, changed "
              f"{(np.abs(out - spec) > 1e-9).mean():.3f}")
