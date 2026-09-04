# -*- coding: utf-8 -*-
"""
C02: Comparison of time-domain normalization methods.

The paper claim: one-bit, running-absolute-mean and water-level normalization
produce high-SNR cross-correlation waveforms, while raw, clipped and event-
detection (or no) normalization leave noisy results, because energetic
earthquakes contaminate the cross-correlation.

Data situation
--------------
A direct test needs the *raw daily* two-station time series, cross-correlated
separately under each normalization.  Those raw daily records are NOT in the
frozen set: only files/iris_manifest.csv (metadata listing of the 2004 daily
records, paths on the producing machine) and the final 12-month stacked
cross-correlation are present.  The frozen set DOES contain real raw waveforms:
the Bhuj earthquake records (earthquake_records/*.mseed).

We therefore test the *mechanism* that underlies the claim on the real raw
earthquake waveforms: a good time-domain normalization must suppress the
earthquake relative to the ambient (quiet) part of the record, so that the
earthquake does not dominate the cross-correlation.  We quantify this as the
compression of the event-to-ambient RMS ratio.

This is a supporting demonstration, NOT a reproduction of the paper's
cross-correlation SNR comparison (which is impossible with the frozen data).
"""
import json
import os
import numpy as np
from scipy.ndimage import uniform_filter1d

from obspy import read

import config as cfg

EPS = 1e-12


# ---------------------------------------------------------------- methods
def norm_one_bit(x):
    return np.sign(x)


def norm_running_abs_mean(x, window_s, fs):
    w = max(1, int(round(window_s * fs)))
    if w % 2 == 0:
        w += 1
    denom = uniform_filter1d(np.abs(x), size=w, mode="nearest")
    return x / np.maximum(denom, EPS)


def norm_water_level(x, factor=2.0):
    wl = factor * np.median(np.abs(x))
    y = x.copy()
    m = np.abs(x) > wl
    y[m] = np.sign(x[m]) * wl
    return y


def norm_clipping(x, frac=0.1):
    lim = frac * np.max(np.abs(x))
    return np.clip(x, -lim, lim)


def norm_event_detection(x, factor=2.0):
    """Event detection & removal: samples above a running-median-based threshold
    are set to zero (removed), mimicking 'event detection and removal'."""
    thr = factor * np.median(np.abs(x))
    y = x.copy()
    y[np.abs(x) > thr] = 0.0
    return y


def norm_raw(x):
    return x


METHODS = {
    "raw": norm_raw,
    "one_bit": norm_one_bit,
    "running_absolute_mean": lambda x: norm_running_abs_mean(x, window_s=450, fs=1.0),
    "water_level": norm_water_level,
    "clipping": norm_clipping,
    "event_detection": norm_event_detection,
}


# ---------------------------------------------------------------- metrics
def event_ambient_ratio(d, event_frac=0.5):
    """Ratio of RMS in the largest-amplitude `event_frac` of the record to RMS
    in the smallest-amplitude `event_frac` of the record (a robust proxy for how
    much an energetic earthquake dominates the record)."""
    n = len(d)
    seg = max(1, n // 20)
    rms = np.array([np.sqrt(np.mean(d[i * seg:(i + 1) * seg] ** 2))
                    for i in range(20)])
    ne = max(1, int(round(20 * event_frac)))
    idx = np.argsort(rms)
    event_rms = rms[idx[-ne:]].mean()
    ambient_rms = rms[idx[:ne]].mean()
    return event_rms / (ambient_rms + EPS), event_rms, ambient_rms


def analyze_methods(record_path, label, fs, window_s, event_frac=0.5):
    tr = read(record_path)[0]
    d = tr.data.astype(np.float64)

    # adapt running-mean window to the record sampling rate
    methods = {
        "raw": norm_raw,
        "one_bit": norm_one_bit,
        "running_absolute_mean": lambda x: norm_running_abs_mean(x, window_s, fs),
        "water_level": norm_water_level,
        "clipping": norm_clipping,
        "event_detection": norm_event_detection,
    }

    raw_ratio, ev, amb = event_ambient_ratio(d, event_frac)
    rows = []
    for name, fn in methods.items():
        y = fn(d)
        ratio, ev_n, amb_n = event_ambient_ratio(y, event_frac)
        compression = raw_ratio / (ratio + EPS) if ratio > 0 else np.inf
        rows.append({
            "method": name,
            "event_ambient_rms_ratio": round(float(ratio), 3),
            "event_rms": round(float(ev_n), 4),
            "ambient_rms": round(float(amb_n), 6),
            "compression_vs_raw": round(float(compression), 2),
        })
    return {"record": label, "raw_event_ambient_rms_ratio": round(float(raw_ratio), 3),
            "rows": rows}


def main():
    results = {
        "note": ("Direct cross-correlation SNR comparison not possible with frozen data; "
                 "demonstrates normalization behaviour on real raw earthquake records."),
        "records": []
    }
    # 1 Hz record (matches xcorr band) and a 20 Hz record (cross-check)
    results["records"].append(analyze_methods(
        cfg.EARTHQUAKE_FILES["BK.CMB"]["LHZ"], "BK.CMB.LHZ (1 Hz, raw)",
        fs=1.0, window_s=450))
    results["records"].append(analyze_methods(
        cfg.EARTHQUAKE_FILES["BK.CMB"]["BHZ"], "BK.CMB.BHZ (20 Hz, raw)",
        fs=20.0, window_s=450))

    # ---- figure ----
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    tr = read(cfg.EARTHQUAKE_FILES["BK.CMB"]["LHZ"])[0]
    d = tr.data.astype(np.float64)
    t = np.arange(len(d)) / tr.stats.sampling_rate / 60.0
    fig, axes = plt.subplots(6, 1, figsize=(12, 11), sharex=True)
    fig.subplots_adjust(hspace=0.15)
    for ax, (name, fn) in zip(axes, [
            ("raw", norm_raw),
            ("one-bit", norm_one_bit),
            ("running absolute mean", lambda x: norm_running_abs_mean(x, 450, 1.0)),
            ("water level", norm_water_level),
            ("clipping", norm_clipping),
            ("event detection", norm_event_detection)]):
        y = fn(d)
        # normalize display to [-1,1]
        yn = y / (np.max(np.abs(y)) + EPS)
        ax.plot(t, yn, lw=0.5, color="0.2")
        ax.set_ylabel(name, fontsize=9)
        ax.set_ylim(-1.2, 1.2)
        ax.tick_params(labelsize=7)
    ax.set_xlabel("Time after record start (min)")
    fig.suptitle("C02: time-domain normalization methods applied to raw BK.CMB.LHZ "
                 "(Bhuj earthquake, 2001-10-31)", fontsize=11)
    figpath = os.path.join(cfg.FIGURES_DIR, "c02_normalization_methods.png")
    fig.savefig(figpath, dpi=120)
    plt.close(fig)

    out = os.path.join(cfg.RESULTS_DIR, "c02_normalization.json")
    with open(out, "w") as fh:
        json.dump(results, fh, indent=2, default=float)
    print(json.dumps(results, indent=2, default=float))
    print("saved", out)


if __name__ == "__main__":
    main()
