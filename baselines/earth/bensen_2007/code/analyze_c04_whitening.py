# -*- coding: utf-8 -*-
"""
C04: Spectral whitening flattens the amplitude spectrum at station HRV,
     removing microseism peaks and the ~26 s Gulf-of-Guinea signal.

Data situation
--------------
The claim concerns the *raw* amplitude spectrum recorded at station HRV.
The only HRV-labelled broadband (1 Hz, 86400 s) trace in the frozen set is
files/12mo_2004_sym.mseed.  Inspection (see explore_data.py) shows this trace is a
*band-limited, processed product* (zero spectral amplitude above ~0.14 Hz / 7 s),
consistent with the reference workflow's symmetric cross-correlation
(symmetric_xcorr/IU.HRV__II.PFO/12mo_2004_sym.mseed) rather than a raw HRV
daily record.  A raw 1-Hz record would contain energy up to Nyquist (0.5 Hz).

We therefore:
  1. Validate the whitening implementation on a real *raw* record that is
     present in the frozen set (earthquake_records/BK.CMB.LHZ.mseed).
  2. Apply the same whitening to the HRV-labelled trace and measure whether the
     (moderate) spectral features present are flattened.

Metrics
-------
  * peak prominence (P_peak / median P) for the primary microseism band (5-30 s)
    and the ~20-32 s band, before vs after whitening
  * log-amplitude flatness (std of log P) over the 7-150 s band, before vs after
"""
import json
import os
import numpy as np
from scipy.ndimage import uniform_filter1d
from scipy.signal import get_window

from obspy import read

import config as cfg


def amplitude_spectrum(d, fs):
    d = d - d.mean()
    n = len(d)
    x = d - np.polyval(np.polyfit(np.arange(n), d, 1), np.arange(n))
    xw = x * get_window("hann", n)
    X = np.fft.rfft(xw)
    freqs = np.fft.rfftfreq(n, 1.0 / fs)
    return freqs, np.abs(X)


def whitened_spectrum(freqs, amp, fw):
    df = freqs[1] - freqs[0] if len(freqs) > 1 else 1.0
    halfwin = max(1, int(round(fw / df)))
    smooth = uniform_filter1d(amp, size=2 * halfwin + 1, mode="nearest")
    smooth = np.maximum(smooth, 1e-12 * smooth.max())
    return amp / smooth, smooth


def band_prominence(freqs, P, tmin, tmax):
    m = (freqs > 1.0 / tmax) & (freqs <= 1.0 / tmin)
    if m.sum() == 0:
        return np.nan, np.nan
    Pb, fb = P[m], freqs[m]
    i = int(np.argmax(Pb))
    return 1.0 / fb[i], Pb[i] / np.median(Pb)


def band_flatness(freqs, P, flow, fhigh):
    m = (freqs >= flow) & (freqs <= fhigh)
    return float(np.std(np.log(P[m] + 1e-30)))


def analyze_record(label, trace, fs, fw_list=(0.05, 0.1, 0.2)):
    d = trace.data.astype(np.float64)
    freqs, amp = amplitude_spectrum(d, fs)
    out = {"label": label, "npts": len(d), "fs": fs,
           "original": {}, "whitened": []}
    for tmin, tmax, key in [(5, 30, "microseism_5_30s"), (20, 32, "band_20_32s")]:
        T, p = band_prominence(freqs, amp, tmin, tmax)
        out["original"][key] = {"period_s": round(float(T), 2) if T == T else None,
                                "prominence": round(float(p), 3) if p == p else None}
    out["original"]["flatness_7_150s"] = round(band_flatness(freqs, amp, 1/150, 1/7), 4)
    out["original"]["flatness_0.03_0.2Hz"] = round(band_flatness(freqs, amp, 0.03, 0.2), 4)

    for fw in fw_list:
        W, smooth = whitened_spectrum(freqs, amp, fw)
        rec = {"fw_Hz": fw}
        for tmin, tmax, key in [(5, 30, "microseism_5_30s"), (20, 32, "band_20_32s")]:
            T, p = band_prominence(freqs, W, tmin, tmax)
            rec[key] = {"period_s": round(float(T), 2) if T == T else None,
                        "prominence": round(float(p), 3) if p == p else None}
        rec["flatness_7_150s"] = round(band_flatness(freqs, W, 1/150, 1/7), 4)
        rec["flatness_0.03_0.2Hz"] = round(band_flatness(freqs, W, 0.03, 0.2), 4)
        out["whitened"].append(rec)
    return out


def main():
    # ---- validation on a real RAW record (earthquake) ----
    eq_tr = read(cfg.EARTHQUAKE_FILES["BK.CMB"]["LHZ"])[0]
    val = analyze_record("BK.CMB.LHZ (raw earthquake record)", eq_tr,
                         eq_tr.stats.sampling_rate, fw_list=(0.05,))

    # ---- application to the HRV-labelled trace ----
    hrv_tr = read(cfg.XCORR_MSEED)[0]
    app = analyze_record("IU.HRV..LHZ (12mo_2004_sym.mseed, processed xcorr product)",
                         hrv_tr, hrv_tr.stats.sampling_rate, fw_list=(0.05, 0.1, 0.2))

    result = {"validation_raw_earthquake": val, "application_hrv_trace": app}

    # ---- figure ----
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    for ax, (rec, title, path) in zip(
            axes,
            [(val, "Validation: raw BK.CMB.LHZ (earthquake record)",
              cfg.EARTHQUAKE_FILES["BK.CMB"]["LHZ"]),
             (app, "HRV-labelled trace (12mo_2004_sym.mseed)",
              cfg.XCORR_MSEED)]):
        d = read(path)[0].data.astype(np.float64)
        freqs, amp = amplitude_spectrum(d, rec["fs"])
        ax.loglog(freqs, amp, lw=0.8, color="0.35", label="original spectrum")
        for fw_rec in rec["whitened"]:
            W, _ = whitened_spectrum(freqs, amp, fw_rec["fw_Hz"])
            ax.loglog(freqs, W * np.median(amp[amp > 0]), lw=0.8,
                      label=f"whitened (fw={fw_rec['fw_Hz']:.2f} Hz)")
            break  # show first whitened only
        ax.axvline(1 / 26, color="red", ls=":", lw=1)
        ax.text(1 / 26, np.max(amp) * 0.7, "26 s", color="red", fontsize=8, rotation=90)
        ax.set_xlim(1 / 300, 0.5)
        ax.set_title(title)
        ax.set_xlabel("Frequency (Hz)")
        ax.set_ylabel("Amplitude")
        ax.legend(fontsize=8)
    fig.tight_layout()
    figpath = os.path.join(cfg.FIGURES_DIR, "c04_whitening.png")
    fig.savefig(figpath, dpi=120)
    plt.close(fig)

    out = os.path.join(cfg.RESULTS_DIR, "c04_whitening.json")
    with open(out, "w") as fh:
        json.dump(result, fh, indent=2, default=float)
    print(json.dumps(result, indent=2, default=float))
    print("saved", out)


if __name__ == "__main__":
    main()
