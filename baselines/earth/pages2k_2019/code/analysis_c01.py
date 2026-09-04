"""C01 - Reconstruction methods produce coherent 2000-year GMST reconstructions
with correct cooling rates, warmest-period fraction and reference period.

Available frozen data contains only 3 of the 7 methods (CPS, PCR, PAI).  We
therefore quantify (i) between-method coherence, (ii) pre-industrial cooling
rate, (iii) warmest 10-yr period fraction, (iv) anomaly reference period on the
available methods and clearly flag that 4 methods (OIE, M08, BHM, DA) are not
present in this bundle.
"""
from __future__ import annotations

import numpy as np
import json
import os

from common import (load_reconstructions, METHODS, METHOD_SLICES,
                    ols_trend_per_century)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "results")


def warmest_10yr_start(x: np.ndarray) -> int:
    k = 10
    cs = np.concatenate([[0.0], np.cumsum(x)])
    run = (cs[k:] - cs[:-k]) / k
    return int(np.argmax(run))


def main():
    a = load_reconstructions()                  # (2000, 3000); row i -> year i+1

    # ---- anomaly reference: per-member 1961-1990 CE (rows 1960:1990) ----
    ref_idx = slice(1960, 1990)
    raw_ref_mean = a[ref_idx, :].mean(axis=0)
    a_ref = a - raw_ref_mean[None, :]           # each member re-referenced

    results = {}

    # ---- 1. reference-period diagnostic ----
    results["reference_period_check"] = {
        "raw_data_1961_1990_ensemble_mean_C": {
            m: float(a[ref_idx, sl].mean()) for m, sl in METHOD_SLICES.items()
        },
        "note": "Raw data are NOT centered on 1961-1990 (means != 0), so the "
                "anomaly reference 1961-1990 must be applied; the paper uses "
                "1961-1990 CE.",
        "anomaly_reference_used": "1961-1990 CE (subtract per-member 1961-1990 mean)",
    }

    # ---- 2. ensemble-mean (deterministic) reconstruction per method ----
    ensmean = {m: a_ref[:, sl].mean(axis=1) for m, sl in METHOD_SLICES.items()}

    # ---- 3. pre-industrial cooling rate (degC per century, OLS) ----
    cooling = {}
    for period, sl in [("1-1800", slice(0, 1800)), ("1-1850", slice(0, 1850))]:
        cooling[period] = {m: float(ols_trend_per_century(ensmean[m][sl])) for m in METHODS}
    cooling["median_1-1800"] = float(np.median(list(cooling["1-1800"].values())))
    cooling["median_1-1850"] = float(np.median(list(cooling["1-1850"].values())))
    results["preindustrial_cooling_rate_C_per_century"] = cooling

    # ---- 4. warmest 10-yr period fraction (20th century) ----
    per_method = {}
    for m, sl in METHOD_SLICES.items():
        starts = np.array([warmest_10yr_start(x) for x in a_ref[:, sl].T])
        mid = starts + 6.5                       # midpoint year (start+1..start+10)
        per_method[m] = float(((mid >= 1901) & (mid <= 2000)).mean())
    all_starts = np.concatenate([np.array([warmest_10yr_start(x) for x in a_ref[:, sl].T])
                                 for sl in METHOD_SLICES.values()])
    all_mid = all_starts + 6.5
    results["warmest_10yr_period"] = {
        "per_method_fraction_20th_century": per_method,
        "overall_fraction_20th_century": float(((all_mid >= 1901) & (all_mid <= 2000)).mean()),
        "n_members": int(len(all_starts)),
        "definition": "fraction of ensemble members whose warmest 10-yr running mean "
                      "window has midpoint in 1901-2000 CE",
    }

    # ---- 5. between-method coherence ----
    # correlation of ensemble-mean reconstructions (raw and 30-200yr bandpass)
    from common import bandpass_fft
    bp = {m: bandpass_fft(ensmean[m]) for m in METHODS}
    raw_corr, bp_corr = {}, {}
    for i in range(len(METHODS)):
        for j in range(i + 1, len(METHODS)):
            mi, mj = METHODS[i], METHODS[j]
            raw_corr[f"{mi}-{mj}"] = float(np.corrcoef(ensmean[mi], ensmean[mj])[0, 1])
            bp_corr[f"{mi}-{mj}"] = float(np.corrcoef(bp[mi], bp[mj])[0, 1])
    results["coherence"] = {
        "raw_ensemble_mean_correlations": raw_corr,
        "bandpassed_30_200_ensemble_mean_correlations": bp_corr,
        "median_raw_correlation": float(np.median(list(raw_corr.values()))),
        "median_bandpassed_correlation": float(np.median(list(bp_corr.values()))),
    }

    # ---- 6. between-method spread ----
    preind_mean = {m: float(ensmean[m][:1800].mean()) for m in METHODS}
    c20_mean = {m: float(ensmean[m][1899:2000].mean()) for m in METHODS}
    results["between_method_spread_C"] = {
        "preindustrial_1-1800_mean_per_method": preind_mean,
        "preindustrial_warmest_minus_coldest": float(max(preind_mean.values()) - min(preind_mean.values())),
        "20th_century_mean_per_method": c20_mean,
        "20th_century_warmest_minus_coldest": float(max(c20_mean.values()) - min(c20_mean.values())),
    }

    results["methods_available"] = METHODS
    results["methods_total_paper"] = 7
    results["methods_missing"] = ["OIE", "M08", "BHM", "DA"]

    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "c01_results.json"), "w") as f:
        json.dump(results, f, indent=2)

    print("=== C01 ===")
    print("Methods available:", METHODS)
    print("Raw 1961-1990 means:", results["reference_period_check"]["raw_data_1961_1990_ensemble_mean_C"])
    print("Cooling (degC/cent):", {k: {m: round(v[m], 4) for m in METHODS} for k, v in cooling.items() if k in ("1-1800", "1-1850")})
    print("Warmest-10yr frac 20th c:", per_method, "overall", results["warmest_10yr_period"]["overall_fraction_20th_century"])
    print("Coherence raw corr:", raw_corr, "bp corr:", {k: round(v, 3) for k, v in bp_corr.items()})


if __name__ == "__main__":
    main()
