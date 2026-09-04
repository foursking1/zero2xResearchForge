"""R-compatible Butterworth filters for the PAGES2k 2019 GMST analysis.

Implements the exact filtering routines from the authors' R code
(R-functions_gmst.R):

- tsfilt(x, width, "bw"): 2nd-order Butterworth low-pass at period `width`,
  padding nx = width*2 samples with the mean of the first/last `width`
  values, filtfilt, trim pad.  (R code: butterfilt.na)
- bandpass.tsc.na(x, tsc.low, tsc.up, end.m="pad"): 2nd-order Butterworth
  band-pass with pass band periods [tsc.low, tsc.up], padding nx = tsc.up*2
  samples with the mean of the first/last tsc.low values, filtfilt, trim pad.

R's signal::butter normalises frequencies to Nyquist = 1.  scipy is used with
fs = 2 so that Wn = [1/tsc.up, 1/tsc.low] is expressed in the same units.
"""
import numpy as np
from scipy.signal import butter, filtfilt


def _butter_filtfilt(y, Wn, btype, pad_fac, pad_len):
    """2nd-order Butterworth zero-phase filter with mean-value edge padding.

    Parameters
    ----------
    y : np.ndarray
        Input series (finite values; NAs trimmed by caller).
    Wn : float or (float, float)
        Cutoff period(s) in Nyquist-normalised frequency units (fs=2).
    btype : str
        'low' or 'pass'.
    pad_fac : int
        nx = pad_fac * (filter scale)  -> matches R `nx <- tsc*order` (lowpass)
        or `nx <- tsc.up*2` (bandpass).
    pad_len : int
        number of edge values used for the mean pad.
    """
    nx = pad_fac
    nx2 = pad_len
    x = y.copy()
    mx = np.mean(x[:nx2])
    xpad = np.concatenate([np.full(nx, np.mean(x[:nx2])),
                           x,
                           np.full(nx, np.mean(x[-nx2:]))])
    # R: butter(order=2, W, type) then filtfilt
    b, a = butter(2, Wn, btype=btype, fs=2)
    b1 = filtfilt(b, a, xpad)
    b1 = b1[nx:len(b1) - nx]
    return b1


def butterfilt_na(y, tsc):
    """31-yr low-pass equivalent of R butterfilt.na(y, tsc) used by tsfilt(...,'bw').

    R pads with nx = tsc*order = tsc*2 values, pad length tsc.
    """
    sy = np.where(~np.isnan(y))[0]
    ey = np.where(~np.isnan(y))[0]
    sy, ey = sy.min(), ey.max()
    x = y[sy:ey + 1]
    mx = np.mean(x)
    x = x - mx
    nx = tsc * 2
    nx2 = tsc
    x2 = np.concatenate([np.full(nx, np.mean(x[:nx2])),
                         x,
                         np.full(nx, np.mean(x[-nx2:]))])
    b, a = butter(2, 1.0 / tsc, btype='low', fs=2)
    b1 = filtfilt(b, a, x2)
    b1 = b1[nx:len(b1) - nx]
    b1 = b1 + mx
    z = y.copy()
    z[sy:ey + 1] = b1
    return z


def bandpass_tsc_na(y, tsc_low, tsc_up, cut_end=False, end_m="pad"):
    """30-200 yr bandpass equivalent of R bandpass.tsc.na(y, tsc.low, tsc.up,
    cut.end, end.m='pad')."""
    idx = np.where(~np.isnan(y))[0]
    sy, ey = idx.min(), idx.max()
    x = y[sy:ey + 1].copy()

    if end_m == "pad":
        nx = tsc_up * 2
        nx2 = tsc_low
        x = np.concatenate([np.full(nx, np.mean(x[:nx2])),
                            x,
                            np.full(nx, np.mean(x[-nx2:]))])
    b, a = butter(2, [1.0 / tsc_up, 1.0 / tsc_low], btype='pass', fs=2)
    b1 = filtfilt(b, a, x)
    if end_m == "pad":
        b1 = b1[nx:len(b1) - nx]
    if cut_end:
        b1[:int(np.floor(tsc_up / 2.0))] = np.nan
        b1[len(b1) - int(np.floor((tsc_up - 0.5) / 2.0) + 1):] = np.nan
    z = y.copy()
    z[sy:ey + 1] = b1
    return z


def tsfilt_bw(y, width=31):
    """tsfilt(x, width, 'bw') with cut.end=T (used for the 31-yr low-pass of
    medians / instrumental target in Fig. 1a)."""
    z = butterfilt_na(y, width)
    # cut.end == T in tsfilt: set edge window to NA
    sx = 1 + int(np.floor(width / 2.0) - 1)
    ex = len(y) - int(np.floor((width - 0.5) / 2.0)) + 1
    z[:sx] = np.nan
    z[ex:] = np.nan
    return z
