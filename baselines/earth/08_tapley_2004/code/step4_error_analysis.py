"""
Step 4 -- April 2002 / April 2003 geoid anomaly maps + random error
          realizations from the calibrated diagonal covariance (C03 & C04).

Two independent estimates of the GRACE geoid-height error are used:

  (1) PRIMARY -- the frozen calibrated-covariance error realizations shipped
      in data/fig3_error_realizations/ (RL06 formal diagonal covariance
      scaled by 64x to approximate the RL01 calibrated errors, per the
      embedded metadata note).  These are the "calibrated covariance" random
      error maps the paper's Fig. 3 refers to.

  (2) CROSS-CHECK -- our own realizations drawn directly from the frozen
      covariance diagonals (data/grace_covariance) with the same cal_factor
      and several seeds, to demonstrate the error level is robust to the
      random draw.

Signal maps (observed anomalies relative to the 17-month mean) are computed
for April 2002 smoothed at 1000 km and April 2003 smoothed at 600 km, and
compared against the error maps (spatial-pattern/amplitude separation, C03)
and an error-vs-smoothing-radius table (accuracy/resolution, C04).

Outputs (results/error_analysis/):
  signal_maps.json, error_stats.json, accuracy_assessment.json
  error_realization_<year>_<radius>km.npz   (own draws, cross-check)
"""
from __future__ import annotations
import json
import numpy as np
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent))
from grace_utils import (
    DEFAULT_DATA_ROOT, parse_grace_gsm, gaussian_weights, glq_grid,
    synthesize_geoid, mean_sh, load_grace_months, select_months, rms,
)

DATA_ROOT = Path(DEFAULT_DATA_ROOT)
OUT_DIR = Path(__file__).resolve().parents[1] / "results" / "error_analysis"
OUT_DIR.mkdir(parents=True, exist_ok=True)

LMAX = 60
CAL_FACTOR = 64.0          # RL06 formal sigma -> RL01 calibrated approx.
SEED_REF = 42              # seed used in the frozen error-realization products

TARGETS = {
    "2002": {"gsm": "GSM-2_2002095-2002120_GRAC_UTCSR_BA01_0600",
             "cov": "COV-diag_2002095-2002120_GRAC_UTCSR_BA01_0600",
             "frozen": DATA_ROOT / "fig3_error_realizations" /
                       "error_realization_2002_1000km.npz",
             "radius_km": 1000.0, "label": "Apr 2002 (1000 km)"},
    "2003": {"gsm": "GSM-2_2003091-2003120_GRAC_UTCSR_BA01_0600",
             "cov": "COV-diag_2003091-2003120_GRAC_UTCSR_BA01_0600",
             "frozen": DATA_ROOT / "fig3_error_realizations" /
                       "error_realization_2003_600km.npz",
             "radius_km": 600.0, "label": "Apr 2003 (600 km)"},
}


def load_covariance(tag):
    var = np.load(DATA_ROOT / "grace_covariance" / f"{tag}.npy")
    idx = json.load(open(DATA_ROOT / "grace_covariance" / f"{tag}_idx.json"))
    return var, idx


def random_realization(var, idx, seed, lmax=LMAX):
    """Draw one Gaussian SH error realization: delta ~ N(0,(cal*sigma)^2)."""
    rng = np.random.default_rng(seed)
    draws = rng.standard_normal(len(var))
    clm_d = np.zeros((lmax + 1, lmax + 1))
    slm_d = np.zeros((lmax + 1, lmax + 1))
    for (typ, l, m), v, z in zip(idx, var, draws):
        s = CAL_FACTOR * float(np.sqrt(v))
        if typ == "C":
            clm_d[l, m] = s * z
        else:
            slm_d[l, m] = s * z
    return clm_d, slm_d


def synth_error(var, idx, seed, radius_km, lats, lons):
    clm_d, slm_d = random_realization(var, idx, seed)
    W = gaussian_weights(LMAX, radius_km)
    for l in range(LMAX + 1):
        clm_d[l, :] *= W[l]
        slm_d[l, :] *= W[l]
    return synthesize_geoid(clm_d, slm_d, lats, lons)


def signal_map(gsm_name, clm_mean, slm_mean, radius_km, lats, lons):
    clm, slm, lmax, ds = parse_grace_gsm(DATA_ROOT / "grace_level2" / gsm_name)
    lu = min(lmax, LMAX)
    clm_anom = clm[: lu + 1, : lu + 1] - clm_mean[: lu + 1, : lu + 1]
    slm_anom = slm[: lu + 1, : lu + 1] - slm_mean[: lu + 1, : lu + 1]
    clm_anom[2, :] = 0.0
    slm_anom[2, :] = 0.0
    W = gaussian_weights(lu, radius_km)
    for l in range(lu + 1):
        clm_anom[l, :] *= W[l]
        slm_anom[l, :] *= W[l]
    return synthesize_geoid(clm_anom, slm_anom, lats, lons)


def main():
    lats, lons = glq_grid(LMAX)
    months = load_grace_months(DATA_ROOT)
    sel = select_months(months)
    clm_mean, slm_mean = mean_sh(sel, lmax=LMAX)

    signal_maps, error_stats, assessment = {}, {}, {}

    for year, tgt in TARGETS.items():
        # ----- signal -----
        sig = signal_map(tgt["gsm"], clm_mean, slm_mean, tgt["radius_km"],
                         lats, lons)
        signal_maps[year] = {"radius_km": tgt["radius_km"],
                             "min": round(float(sig.min()), 3),
                             "max": round(float(sig.max()), 3),
                             "rms": round(rms(sig), 3),
                             "peak_abs": round(max(abs(sig.min()), abs(sig.max())), 3)}

        # ----- primary error: frozen calibrated-covariance realization -----
        fz = np.load(tgt["frozen"])
        err_frozen = fz["geoid_mm"]
        err_frozen_rms = rms(err_frozen)

        # ----- cross-check: our own realizations (seed 42 + multi-seed) -----
        var, idx = load_covariance(tgt["cov"])
        err_own_42 = synth_error(var, idx, SEED_REF, tgt["radius_km"], lats, lons)
        np.savez_compressed(
            OUT_DIR / f"error_realization_{year}_{int(tgt['radius_km'])}km.npz",
            geoid_mm=err_own_42, lats=lats, lons=lons,
            smooth_km=tgt["radius_km"], cal_factor=CAL_FACTOR,
            random_seed=SEED_REF,
            note="Our draw from frozen RL06 formal diagonal covariance scaled 64x")

        radii = [400.0, 600.0, 1000.0]
        seeds = [0, 42, 2026]
        vs_radius = {}
        for r in radii:
            rms_list = [rms(synth_error(var, idx, s, r, lats, lons)) for s in seeds]
            vs_radius[str(int(r))] = {"rms_mean_mm": round(float(np.mean(rms_list)), 3),
                                      "rms_std_mm": round(float(np.std(rms_list)), 3)}
        err_own_mean = vs_radius[str(int(tgt["radius_km"]))]["rms_mean_mm"]

        error_stats[year] = {
            "radius_km": tgt["radius_km"],
            "frozen_error_rms_mm": round(err_frozen_rms, 3),
            "frozen_error_min": round(float(err_frozen.min()), 3),
            "frozen_error_max": round(float(err_frozen.max()), 3),
            "own_error_seed42_rms_mm": round(rms(err_own_42), 3),
            "own_error_multi_seed_mean_rms_mm": err_own_mean,
            "vs_radius_own_draws": vs_radius,
            "cal_factor": CAL_FACTOR,
        }

        assessment[year] = {
            "label": tgt["label"],
            "smoothing_km": tgt["radius_km"],
            "signal_rms_mm": signal_maps[year]["rms"],
            "signal_peak_abs_mm": signal_maps[year]["peak_abs"],
            "error_rms_mm_primary_frozen": round(err_frozen_rms, 3),
            "snr_rms": round(signal_maps[year]["rms"] / err_frozen_rms, 3),
            "peak_over_error": round(signal_maps[year]["peak_abs"] / err_frozen_rms, 2),
        }
        print(f"{tgt['label']}: signal rms={signal_maps[year]['rms']} mm, "
              f"peak={signal_maps[year]['peak_abs']} mm | "
              f"error(frozen) rms={err_frozen_rms:.3f} mm, "
              f"error(own,seed42)={rms(err_own_42):.3f} mm, "
              f"error(own,mean3)={err_own_mean:.3f} mm")
        print(f"    error RMS vs smoothing radius (own draws): "
              f"{ {k: v['rms_mean_mm'] for k, v in vs_radius.items()} }")

    with open(OUT_DIR / "signal_maps.json", "w") as f:
        json.dump(signal_maps, f, indent=2)
    with open(OUT_DIR / "error_stats.json", "w") as f:
        json.dump(error_stats, f, indent=2)
    with open(OUT_DIR / "accuracy_assessment.json", "w") as f:
        json.dump({"assessment": assessment,
                   "paper_claim": "2-3 mm geoid accuracy at 400-1000 km; "
                                  "2002 ~1000 km, 2003 ~400-600 km",
                   "method": "frozen calibrated-covariance realizations "
                             "(primary) + own draws (cross-check)",
                   "cal_factor": CAL_FACTOR}, f, indent=2)

    print("\nAccuracy assessment (primary = frozen calibrated error):")
    for year, a in assessment.items():
        print(f"  {a['label']}: signal RMS {a['signal_rms_mm']} mm, "
              f"error RMS {a['error_rms_mm_primary_frozen']} mm, "
              f"SNR {a['snr_rms']}, peak/error {a['peak_over_error']}")


if __name__ == "__main__":
    main()
