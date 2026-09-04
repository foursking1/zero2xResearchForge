"""C01: Coherent 2000-year GMST reconstructions from seven methods.

Implements the paper's key quantitative results (Methods "Pre-industrial
trends"; results section; Table 1):

  - Anomaly reference period 1961-1990 CE (R05).
  - Pre-industrial cooling rate: linear trend over 1-1850 CE in degC per
    thousand years (degC/ka), per ensemble member, grouped by proxy
    resolution: lower-than-annual {OIE, M08, PAI} vs annual-only
    {CPS, PCR, BHM, DA} (paper: -0.23 and -0.09 degC/ka).
  - Warmest 10-year period: running 10-yr mean of each member; fraction of
    ensemble members whose warmest decade falls in the second half of the
    20th century (1950-2000) (paper: 0.94).
  - DA minus BHM temperature difference around 1600 CE (paper: ~0.5 degC).
  - Inter-method coherence: correlations of the 7 ensemble medians.
"""
import json
import os
import numpy as np

from load_data import load_recon_ensembles

METHODS = ["CPS", "PCR", "M08", "PAI", "OIE", "BHM", "DA"]
LOW_RES = ["OIE", "M08", "PAI"]          # lower-than-annual proxy resolution
ANN_RES = ["CPS", "PCR", "BHM", "DA"]    # annual-or-higher resolution only
REF_START, REF_END = 1961, 1990
TREND_END = 1850                          # pre-industrial trend period 1-1850
WARMEST_WIN = (1950, 2000)                # "second half of the 20th century"


def linfit_trend_k(a, years):
    """Least-squares slope of a on years, in degC per 1000 years."""
    x = years - years.mean()
    y = a - a.mean()
    slope = np.sum(x * y) / np.sum(x * x)   # degC / year
    return slope * 1000.0                   # degC / ka


def main():
    recons = load_recon_ensembles()
    years = recons["CPS"][0]
    ref_ok = (years >= REF_START) & (years <= REF_END)

    # --- R05: reference period ---
    print("=== Reference period ===")
    print(f"anomaly reference period used: {REF_START}-{REF_END} CE")
    # ensemble median anomaly at the reference period mean is ~0 by construction
    med = np.median(recons["CPS"][1], axis=1)
    ref_mean = np.mean(med[ref_ok])
    print(f"mean of CPS ensemble median over {REF_START}-{REF_END}: {ref_mean:.2e} (-> ~0, centred)")

    # --- Pre-industrial cooling rates (degC/ka), 1-1850 ---
    print("\n=== Pre-industrial cooling rate (1-1850 CE), degC/ka ===")
    trend_sel = (years >= 1) & (years <= TREND_END)
    tyears = years[trend_sel]
    rates = {}
    for m in METHODS:
        d = recons[m][1][trend_sel]
        tr = np.array([linfit_trend_k(d[:, i], tyears) for i in range(d.shape[1])])
        rates[m] = tr
        q = np.percentile(tr, [2.5, 50, 97.5])
        print(f"{m}: median = {q[1]:.3f}  [2.5-97.5: {q[0]:.3f}-{q[2]:.3f}] degC/ka")
    lo = np.concatenate([rates[m] for m in LOW_RES])
    ann = np.concatenate([rates[m] for m in ANN_RES])
    lo_q = np.percentile(lo, [2.5, 50, 97.5])
    ann_q = np.percentile(ann, [2.5, 50, 97.5])
    print(f"lower-than-annual methods {LOW_RES}: median = {lo_q[1]:.3f}  [{lo_q[0]:.3f}, {lo_q[2]:.3f}]  (paper: -0.23 [-0.31,-0.11])")
    print(f"annual-only methods {ANN_RES}:      median = {ann_q[1]:.3f}  [{ann_q[0]:.3f}, {ann_q[2]:.3f}]  (paper: -0.09 [-0.27, 0.02])")

    # --- Warmest 10-year period ---
    print("\n=== Warmest 10-year period (centred 10-yr running mean) ===")
    n = len(years)
    frac_warmest = {}
    for m in METHODS:
        d = recons[m][1]
        # centred running mean of window k=10
        k = 10
        run = np.full((n, d.shape[1]), np.nan)
        for t in range(n):
            a = max(0, t - k // 2)
            b = min(n, t + k // 2 + 1)
            if b - a >= k:
                run[t] = np.nanmean(d[a:b], axis=0)
        maxi = np.nanargmax(run, axis=0)
        warm_year = years[maxi]
        frac = np.mean((warm_year >= WARMEST_WIN[0]) & (warm_year <= WARMEST_WIN[1]))
        frac_warmest[m] = frac
        print(f"{m}: fraction with warmest 10-yr in {WARMEST_WIN} = {frac:.3f}")
    all_frac = np.mean(list(frac_warmest.values()))
    print(f"mean across methods: {all_frac:.3f}   (paper: 0.94)")

    # --- DA vs BHM around 1600 CE ---
    print("\n=== DA vs BHM temperature difference around 1600 CE ===")
    from filters import tsfilt_bw
    da_lp = tsfilt_bw(np.median(recons["DA"][1], axis=1), 31)
    bhm_lp = tsfilt_bw(np.median(recons["BHM"][1], axis=1), 31)
    diff = da_lp - bhm_lp
    # gap between the warmest (DA) and coldest (BHM) low-pass estimates around 1600
    w = (years >= 1500) & (years <= 1700)
    da_max = np.nanmax(da_lp[w])
    bhm_min = np.nanmin(bhm_lp[w])
    gap = da_max - bhm_min
    print(f"DA max - BHM min over 1500-1700 (31-yr low-pass): {gap:.3f} degC  (paper: ~0.5)")
    print(f"DA - BHM at year 1600 (low-pass): {diff[years==1600][0]:.3f} degC")

    # --- Inter-method coherence ---
    print("\n=== Inter-method coherence (correlation of ensemble medians, 1-2000) ===")
    meds = np.column_stack([np.median(recons[m][1], axis=1) for m in METHODS])
    corr = np.corrcoef(meds.T)
    np.fill_diagonal(corr, np.nan)
    print("pairwise correlation range of medians:",
          round(float(np.nanmin(corr)), 3), "-", round(float(np.nanmax(corr)), 3))
    print("median pairwise correlation:", round(float(np.nanmedian(corr)), 3))

    # --- Save compact metrics ---
    os.makedirs("results", exist_ok=True)
    out = {
        "reference_period": [REF_START, REF_END],
        "cooling_rate_lower_than_annual_median": float(lo_q[1]),
        "cooling_rate_lower_than_annual_q025": float(lo_q[0]),
        "cooling_rate_lower_than_annual_q975": float(lo_q[2]),
        "cooling_rate_annual_only_median": float(ann_q[1]),
        "cooling_rate_annual_only_q025": float(ann_q[0]),
        "cooling_rate_annual_only_q975": float(ann_q[2]),
        "cooling_rate_per_method": {m: float(np.median(rates[m])) for m in METHODS},
        "warmest_10yr_fraction": {m: float(v) for m, v in frac_warmest.items()},
        "warmest_10yr_fraction_mean": float(all_frac),
        "DA_minus_BHM_1500_1700_gap": float(gap),
        "DA_minus_BHM_at_1600_lowpass": float(diff[years == 1600][0]),
        "median_pairwise_corr": float(np.nanmedian(corr)),
        "corr_range": [float(np.nanmin(corr)), float(np.nanmax(corr))],
    }
    with open("results/c01_metrics.json", "w") as f:
        json.dump(out, f, indent=2, sort_keys=True)
    print("\nsaved results/c01_metrics.json")


if __name__ == "__main__":
    main()
