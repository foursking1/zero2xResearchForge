# -*- coding: utf-8 -*-
"""
C01: Broad-band symmetric-component cross-correlation (12 months, 2004)
     -> test for clear Rayleigh-wave signals across six passbands.

Data: files/12mo_2004_sym.mseed  (source bundle path: symmetric_xcorr/IU.HRV__II.PFO/12mo_2004_sym.mseed)
Layout: 86400 samples @ 1 Hz ; zero lag at sample 0 ; lags 0 .. 86399 s.
Interpretation note: the file is stored under IU.HRV but the bundle-manifest source
path identifies the pair as IU.HRV -- II.PFO.  The paper claim (C01) names ANMO-HRV;
the frozen data provides the HRV-PFO pair.  We test the physics (broad-band Rayleigh
wave in a 12-month stack) on the data that actually exists and flag the station-pair
difference explicitly.

Metrics reported:
  - per-passband arrival time, peak/RMS SNR, group velocity
  - consistency with continental Rayleigh-wave dispersion
"""
import json
import os
import numpy as np
from scipy.signal import hilbert

from obspy import read
from obspy.geodetics import gps2dist_azimuth
from obspy.signal.filter import bandpass

import config as cfg

rng = np.random.default_rng(0)


def load_xcorr():
    st = read(cfg.XCORR_MSEED)
    assert len(st) == 1, "expected a single trace"
    tr = st[0]
    d = tr.data.astype(np.float64)
    return tr, d


def envelope(x):
    return np.abs(hilbert(x))


def band_envelope(d, fmin, fmax, fs=1.0):
    f = bandpass(d, fmin, fmax, fs, corners=4, zerophase=True)
    return f, envelope(f)


def main():
    tr, d = load_xcorr()
    fs = tr.stats.sampling_rate
    n = len(d)
    lag = np.arange(n) * tr.stats.delta  # zero lag at sample 0

    # ---- station pair distance (great-circle) ----
    hrv = cfg.STATION_COORDS["IU.HRV"]
    pfo = cfg.STATION_COORDS["II.PFO"]
    dist_m, az, baz = gps2dist_azimuth(hrv[0], hrv[1], pfo[0], pfo[1])
    dist_km = dist_m / 1000.0

    # ---- per-band analysis ----
    # noise windows for SNR
    noise_near = (lag >= 5_000) & (lag < 20_000)   # conservative: just after the arrival
    noise_tail = (lag >= 60_000) & (lag < 86_000)  # far tail of the record
    # physically reasonable signal search window for a ~4000 km path
    sig_mask = (lag >= 300) & (lag < 4000)

    rows = []
    for name, (t1, t2) in cfg.PASSBANDS.items():
        fb, env = band_envelope(d, 1.0 / t2, 1.0 / t1, fs)
        # arrival = max envelope within the signal window
        sig_env = env[sig_mask]
        sig_lag = lag[sig_mask]
        ipk = int(np.argmax(sig_env))
        t_arr = float(sig_lag[ipk])
        amp_peak = float(sig_env[ipk])
        # noise level in the far-tail and near windows
        noise_tail_rms = float(np.sqrt(np.mean(env[noise_tail] ** 2)))
        noise_near_rms = float(np.sqrt(np.mean(env[noise_near] ** 2)))
        snr_tail = amp_peak / noise_tail_rms if noise_tail_rms > 0 else np.nan
        snr_near = amp_peak / noise_near_rms if noise_near_rms > 0 else np.nan
        vg = dist_km / t_arr if t_arr > 0 else np.nan
        rows.append({
            "passband": name,
            "Tmin_s": t1,
            "Tmax_s": t2,
            "arrival_time_s": round(t_arr, 1),
            "peak_amp": amp_peak,
            "noise_rms_tail": noise_tail_rms,
            "noise_rms_near": noise_near_rms,
            "snr_tail": round(snr_tail, 2),
            "snr_near": round(snr_near, 2),
            "group_velocity_kms": round(vg, 3),
        })

    # ---- summary statistics ----
    snrs_tail = np.array([r["snr_tail"] for r in rows])
    snrs_near = np.array([r["snr_near"] for r in rows])
    vgs = np.array([r["group_velocity_kms"] for r in rows])

    result = {
        "data_file": os.path.basename(cfg.XCORR_MSEED),
        "pair": "IU.HRV--II.PFO",
        "claim_pair": "ANMO-HRV (claim) vs HRV-PFO (data)",
        "distance_km": round(dist_km, 1),
        "npts": n,
        "sampling_rate": fs,
        "zero_lag_at_sample0": True,
        "per_band": rows,
        "summary": {
            "min_snr_tail": float(np.min(snrs_tail)),
            "max_snr_tail": float(np.max(snrs_tail)),
            "mean_snr_tail": float(np.mean(snrs_tail)),
            "min_snr_near": float(np.min(snrs_near)),
            "max_snr_near": float(np.max(snrs_near)),
            "mean_snr_near": float(np.mean(snrs_near)),
            "group_velocity_7_25s_kms": vgs[list(cfg.PASSBANDS).index("7-25s")],
            "group_velocity_20_50s_kms": vgs[list(cfg.PASSBANDS).index("20-50s")],
            "group_velocity_70_150s_kms": vgs[list(cfg.PASSBANDS).index("70-150s")],
        },
    }

    # ---- figure: six passbands ----
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.gridspec import GridSpec

    fig, axes = plt.subplots(6, 1, figsize=(11, 12), sharex=True)
    fig.subplots_adjust(hspace=0.35, right=0.97, left=0.09, top=0.96, bottom=0.06)
    for ax, (name, (t1, t2)), row in zip(axes, cfg.PASSBANDS.items(), rows):
        fb, env = band_envelope(d, 1.0 / t2, 1.0 / t1, fs)
        # normalize for display
        fbn = fb / (np.max(np.abs(fb)) + 1e-30)
        ax.plot(lag / 60.0, fbn, lw=0.6, color="0.25")
        ax.axvline(row["arrival_time_s"] / 60.0, color="C3", ls="--", lw=1.0)
        ax.set_xlim(0, 120)
        ax.set_ylabel(f"{name}\nSNR={row['snr_tail']:.0f}\nVg={row['group_velocity_kms']:.2f} km/s",
                      fontsize=9)
        ax.tick_params(labelsize=8)
    ax.set_xlabel("Lag time (min)")
    fig.suptitle(f"C01: 12-month cross-correlation {result['pair']} "
                 f"(dist={dist_km:.0f} km) -- six passbands", fontsize=12)
    figpath = os.path.join(cfg.FIGURES_DIR, "c01_six_passbands.png")
    fig.savefig(figpath, dpi=120)
    plt.close(fig)

    # ---- figure: dispersion curve ----
    fig2, ax2 = plt.subplots(figsize=(6, 4.5))
    periods = np.array([r["Tmax_s"] for r in rows])  # use long-period corner as representative T
    ax2.plot(periods, vgs, "o-", lw=1.5)
    ax2.set_xlabel("Representative period (s)")
    ax2.set_ylabel("Group velocity (km/s)")
    ax2.set_title("Group velocity vs period (HRV-PFO, 12-month stack)")
    ax2.set_xscale("log")
    ax2.grid(alpha=0.3)
    figpath2 = os.path.join(cfg.FIGURES_DIR, "c01_dispersion_curve.png")
    fig2.savefig(figpath2, dpi=120)
    plt.close(fig2)

    # ---- save metrics ----
    out = os.path.join(cfg.RESULTS_DIR, "c01_passbands.json")
    with open(out, "w") as fh:
        json.dump(result, fh, indent=2, default=float)
    print(json.dumps(result, indent=2, default=float))
    print("saved", out)


if __name__ == "__main__":
    main()
