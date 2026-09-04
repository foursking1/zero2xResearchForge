# -*- coding: utf-8 -*-
"""
Characterization of every waveform file in the frozen bensen_2007 bundle.
Used to establish exactly what real data is available for the four claims.
"""
import glob
import json
import os

import numpy as np

from obspy import read, read_inventory

import config as cfg


def main():
    report = {"xcorr_trace": {}, "earthquake_records": {}, "manifest": {},
              "stations": []}

    # ---- 12-month cross-correlation / HRV-labelled trace ----
    tr = read(cfg.XCORR_MSEED)[0]
    d = tr.data.astype(np.float64)
    n = len(d)
    report["xcorr_trace"] = {
        "file": os.path.basename(cfg.XCORR_MSEED),
        "network.station.channel": f"{tr.stats.network}.{tr.stats.station}.{tr.stats.channel}",
        "npts": n,
        "sampling_rate": tr.stats.sampling_rate,
        "duration_s": n / tr.stats.sampling_rate,
        "rms": float(np.sqrt(np.mean(d ** 2))),
        "max_abs": float(np.max(np.abs(d))),
        "nyquist_Hz": 0.5 * tr.stats.sampling_rate,
    }
    # energy above 0.14 Hz
    X = np.fft.rfft(d - d.mean())
    P = np.abs(X) ** 2
    freqs = np.fft.rfftfreq(n, 1.0 / tr.stats.sampling_rate)
    mask = freqs > 0.14
    report["xcorr_trace"]["energy_frac_above_0.14Hz"] = (
        float(P[mask].sum() / P.sum()) if P.sum() > 0 else 0.0
    )

    # ---- earthquake records ----
    eq = {}
    for key, chs in cfg.EARTHQUAKE_FILES.items():
        for cha, path in chs.items():
            t = read(path)[0]
            dd = t.data.astype(np.float64)
            eq[f"{key}.{cha}"] = {
                "npts": t.stats.npts,
                "sampling_rate": t.stats.sampling_rate,
                "start": str(t.stats.starttime),
                "rms": float(np.sqrt(np.mean(dd ** 2))),
                "max_abs": float(np.max(np.abs(dd))),
            }
    report["earthquake_records"] = eq

    # ---- manifest summary ----
    import pandas as pd
    df = pd.read_csv(cfg.IRIS_MANIFEST)
    report["manifest"] = {
        "n_files": int(len(df)),
        "n_stations": int(df["sta"].nunique()),
        "networks": sorted(df["net"].unique().tolist()),
        "stations": sorted(df["sta"].unique().tolist()),
        "channels": sorted(df["cha"].unique().tolist()),
        "mean_coverage_frac": float(df["coverage_frac"].mean()),
        "total_size_bytes": int(df["size_bytes"].sum()),
    }

    # ---- stations in priority-12 XML ----
    inv = read_inventory(cfg.STATIONS_XML)
    report["stations"] = [
        {"network": n.code, "station": s.code,
         "lat": float(s.latitude), "lon": float(s.longitude)}
        for n in inv for s in n
    ]

    out = os.path.join(cfg.RESULTS_DIR, "data_inventory.json")
    with open(out, "w") as fh:
        json.dump(report, fh, indent=2, default=str)
    print(json.dumps(report, indent=2, default=str))
    print("saved", out)


if __name__ == "__main__":
    main()
