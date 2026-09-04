"""C02: 30-200 yr bandpass-filtered GMST: tighter cross-method agreement.

Reproduces the paper's Fig. 1b analysis:

  - 30-200 yr bandpass Butterworth filter (R bandpass.tsc.na, cut.end=F,
    end.m="pad") applied to each method's ensemble median.
  - Removing the centennial-scale trend reveals coherent multi-decadal
    variability with *narrower* inter-method spread than the raw anomalies.
  - Bandpass-filtered anomalies have an amplitude of roughly +/- 0.3 degC.
  - Warm anomalies around 1320, 1420, 1560, 1780 and cold anomalies around
    1260, 1450, 1820 appear coherently across methods.
"""
import json
import os
import numpy as np

from load_data import load_recon_ensembles
from filters import bandpass_tsc_na

METHODS = ["CPS", "PCR", "M08", "PAI", "OIE", "BHM", "DA"]

# (year, label) events from the paper results section
WARM_EVENTS = [(1320, "1320"), (1420, "1420"), (1560, "1560"), (1780, "1780")]
COLD_EVENTS = [(1260, "1260"), (1450, "1450"), (1820, "1820")]


def main():
    recons = load_recon_ensembles()
    years = recons["CPS"][0]
    meds = np.column_stack([np.median(recons[m][1], axis=1) for m in METHODS])

    # bandpass filter each method median (30-200 yr)
    bp = np.full_like(meds, np.nan)
    for k in range(meds.shape[1]):
        bp[:, k] = bandpass_tsc_na(meds[:, k], 30, 200, cut_end=False, end_m="pad")

    # --- Anomaly amplitude ---
    print("=== Bandpass-filtered (30-200 yr) GMST anomaly amplitude ===")
    bp_flat = bp[np.isfinite(bp)]
    print(f"overall min/max: {bp_flat.min():.3f} / {bp_flat.max():.3f} degC")
    per_method = {m: (np.nanmin(bp[:, k]), np.nanmax(bp[:, k]))
                  for k, m in enumerate(METHODS)}
    for m in METHODS:
        print(f"{m}: min = {per_method[m][0]:.3f}, max = {per_method[m][1]:.3f}")

    # --- Inter-method agreement: spread before vs after filtering ---
    print("\n=== Inter-method agreement (spread across the 7 medians) ===")
    # inter-method std (across the 7 methods) at each year
    raw_std = np.nanstd(meds, axis=1)
    bp_std = np.nanstd(bp, axis=1)
    full = np.isfinite(raw_std) & np.isfinite(bp_std)
    print(f"inter-method std, raw anomalies: median = {np.median(raw_std[full]):.3f} degC")
    print(f"inter-method std, bandpass 30-200: median = {np.median(bp_std[full]):.3f} degC")
    print(f"ratio bandpass/raw of inter-method std: {np.median(bp_std[full])/np.median(raw_std[full]):.3f}")
    print("(ratio < 1 -> bandpass-filtered methods agree more tightly)")

    # pairwise correlation of medians on bandpass data
    corr = np.corrcoef(bp.T)
    np.fill_diagonal(corr, np.nan)
    print(f"\npairwise correlation of bandpass medians: median = {np.nanmedian(corr):.3f}, "
          f"range = {np.nanmin(corr):.3f}-{np.nanmax(corr):.3f}")
    corr_raw = np.corrcoef(meds.T)
    np.fill_diagonal(corr_raw, np.nan)
    print(f"pairwise correlation of raw medians: median = {np.nanmedian(corr_raw):.3f}")

    # --- Coherent warm/cold periods ---
    print("\n=== Coherent warm/cold anomaly periods (ensemble-median average) ===")
    mean_bp = np.nanmean(bp, axis=1)   # mean across methods
    for yr, lab in WARM_EVENTS:
        s = (years >= yr - 15) & (years <= yr + 15)
        print(f"warm ~{lab}: mean over {yr-15}-{yr+15} = {np.nanmean(mean_bp[s]):+.3f} degC")
    for yr, lab in COLD_EVENTS:
        s = (years >= yr - 15) & (years <= yr + 15)
        print(f"cold ~{lab}: mean over {yr-15}-{yr+15} = {np.nanmean(mean_bp[s]):+.3f} degC")
    # local extrema of the mean bandpass series (to characterise event timing)
    grad = np.sign(np.gradient(np.nan_to_num(mean_bp)))
    ext = np.where(np.diff(grad) != 0)[0] + 1
    ext_years = years[ext]
    ext_vals = mean_bp[ext]
    print("\nlocal maxima (warm) of the cross-method mean, 1200-1900:")
    for i in np.argsort(-ext_vals):
        if 1200 <= ext_years[i] <= 1900 and ext_vals[i] > 0.03:
            print(f"  year {ext_years[i]}: +{ext_vals[i]:.3f}")
    print("local minima (cold) of the cross-method mean, 1200-1900:")
    for i in np.argsort(ext_vals):
        if 1200 <= ext_years[i] <= 1900 and ext_vals[i] < -0.03:
            print(f"  year {ext_years[i]}: {ext_vals[i]:+.3f}")

    # --- Save compact metrics ---
    os.makedirs("results", exist_ok=True)
    out = {
        "bp_anomaly_min": float(bp_flat.min()),
        "bp_anomaly_max": float(bp_flat.max()),
        "bp_anomaly_range": float(bp_flat.max() - bp_flat.min()),
        "inter_method_std_raw_median": float(np.median(raw_std[full])),
        "inter_method_std_bandpass_median": float(np.median(bp_std[full])),
        "inter_method_std_ratio": float(np.median(bp_std[full]) / np.median(raw_std[full])),
        "pairwise_corr_bandpass_median": float(np.nanmedian(corr)),
        "pairwise_corr_raw_median": float(np.nanmedian(corr_raw)),
        "warm_events_mean_anomaly": {lab: float(np.nanmean(mean_bp[(years >= yr - 10) & (years <= yr + 10)]))
                                     for yr, lab in WARM_EVENTS},
        "cold_events_mean_anomaly": {lab: float(np.nanmean(mean_bp[(years >= yr - 10) & (years <= yr + 10)]))
                                     for yr, lab in COLD_EVENTS},
        "per_method_bp_range": {m: [float(v[0]), float(v[1])] for m, v in per_method.items()},
    }
    with open("results/c02_metrics.json", "w") as f:
        json.dump(out, f, indent=2, sort_keys=True)
    print("\nsaved results/c02_metrics.json")


if __name__ == "__main__":
    main()
