"""C02 - Band-pass filtered (30-200 yr) GMST shows tighter agreement across
methods with correct anomaly range and coherent warm/cold periods.

Computed on the 3 methods available in the frozen subset (CPS, PCR, PAI):
  * band-pass (30-200 yr) each ensemble member over the full 1-2000 CE series
  * ensemble-mean filtered series per method
  * between-method agreement: median across time of the cross-method spread
    (std of the 3 method means), compared with the same quantity on the
    unfiltered (raw) series
  * anomaly range of the filtered ensemble mean
  * pairwise correlations between method filtered ensemble means
"""
from __future__ import annotations

import numpy as np
import json
import os

from common import load_reconstructions, METHODS, METHOD_SLICES, bandpass_fft

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "results")


def main():
    a = load_reconstructions()
    # re-reference to 1961-1990 (consistent anomaly convention)
    ref_mean = a[1960:1990, :].mean(axis=0)
    a_ref = a - ref_mean[None, :]

    # band-pass each member
    bp = np.empty_like(a_ref)
    for j in range(a_ref.shape[1]):
        bp[:, j] = bandpass_fft(a_ref[:, j])

    # ensemble-mean filtered series per method
    bp_mean = {m: bp[:, sl].mean(axis=1) for m, sl in METHOD_SLICES.items()}
    raw_mean = {m: a_ref[:, sl].mean(axis=1) for m, sl in METHOD_SLICES.items()}

    # cross-method spread at each year
    def spread(series_dict):
        M = np.vstack([series_dict[m] for m in METHODS])
        return M.std(axis=0)

    bp_spread = spread(bp_mean)
    raw_spread = spread(raw_mean)

    # anomaly range of each method filtered ensemble mean (full period)
    bp_range = {m: [float(bp_mean[m].min()), float(bp_mean[m].max())] for m in METHODS}

    # pairwise correlations of filtered method means
    corr = {}
    for i in range(len(METHODS)):
        for j in range(i + 1, len(METHODS)):
            mi, mj = METHODS[i], METHODS[j]
            r = float(np.corrcoef(bp_mean[mi], bp_mean[mj])[0, 1])
            corr[f"{mi}-{mj}"] = r

    results = {
        "methods": METHODS,
        "filter": "FFT brick-wall band-pass, periods 30-200 yr, applied to full 1-2000 CE series",
        "between_method_spread_degC": {
            "bandpassed_median": float(np.median(bp_spread)),
            "bandpassed_mean": float(np.mean(bp_spread)),
            "raw_median": float(np.median(raw_spread)),
            "raw_mean": float(np.mean(raw_spread)),
            "ratio_median_bp_to_raw": float(np.median(bp_spread) / np.median(raw_spread)),
        },
        "bandpassed_anomaly_range_degC": bp_range,
        "overall_bandpassed_range_degC": [
            float(min(v[0] for v in bp_range.values())),
            float(max(v[1] for v in bp_range.values())),
        ],
        "cross_method_correlations_bandpassed": corr,
        "median_cross_method_correlation": float(np.median(list(corr.values()))),
        # warm/cold period coherence: correlation of filtered method means with
        # the multi-method mean
        "coherence_with_multimethod_mean": {
            m: float(np.corrcoef(bp_mean[m], np.mean([bp_mean[x] for x in METHODS], axis=0))[0, 1])
            for m in METHODS
        },
    }

    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "c02_results.json"), "w") as f:
        json.dump(results, f, indent=2)

    print("=== C02 ===")
    print("between-method spread (median): bandpassed %.4f  raw %.4f  ratio %.3f"
          % (np.median(bp_spread), np.median(raw_spread), np.median(bp_spread) / np.median(raw_spread)))
    print("bandpassed anomaly range:", results["bandpassed_anomaly_range_degC"])
    print("cross-method correlations:", {k: round(v, 3) for k, v in corr.items()})


if __name__ == "__main__":
    main()
