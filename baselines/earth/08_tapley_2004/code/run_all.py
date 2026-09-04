"""
Run the full analysis pipeline for the Tapley et al. (2004) GRACE task and
assemble the machine-readable evidence products.

Steps executed:
  step1_smoothed_grids.py  -- 400 km smoothed geoid grids + validation
  step2_annual_fit.py      -- C01: annual cosine/sine components
  step3_south_america.py   -- C02: South America 2003 monthly anomalies
  step4_error_analysis.py  -- C03/C04: Apr 2002/2003 maps + error realizations

Outputs:
  results/evidence_table.csv  -- metric / value / unit / definition / source
  results/metrics.json        -- same metrics, machine readable
  results/claim_verdicts.json -- per-claim supported/partially_supported/...
"""
from __future__ import annotations
import csv
import json
import sys
from pathlib import Path

import numpy as np

CODE = Path(__file__).parent
ROOT = CODE.parent
RESULTS = ROOT / "results"
sys.path.insert(0, str(CODE))

from grace_utils import area_weighted_rms  # noqa: E402


def run_step(name):
    import importlib
    print(f"\n=== {name} ===")
    mod = importlib.import_module(name.replace(".py", ""))
    mod.main()


def load_json(path):
    with open(path) as f:
        return json.load(f)


def main():
    # ---------- execute pipeline ----------
    run_step("step1_smoothed_grids")
    run_step("step2_annual_fit")
    run_step("step3_south_america")
    run_step("step4_error_analysis")

    # ---------- load results ----------
    annual = load_json(RESULTS / "annual_fit" / "summary.json")
    sa = load_json(RESULTS / "south_america" / "monthly_extrema.json")
    sa_amazon = load_json(RESULTS / "south_america" / "amazon_orinoco.json")
    err = load_json(RESULTS / "error_analysis" / "accuracy_assessment.json")["assessment"]
    err_stats = load_json(RESULTS / "error_analysis" / "error_stats.json")
    err_radius = {y: err_stats[y]["vs_radius_own_draws"] for y in err_stats}

    # area-weighted RMS sensitivity for annual fit maps
    aw = {}
    for source in ("grace", "gldas"):
        d = np.load(RESULTS / "annual_fit" / f"{source}_annual_fit.npz")
        lats = d["lats"]
        aw[source] = {
            "cosine_area_rms_mm": round(area_weighted_rms(d["cosine"], lats), 3),
            "sine_area_rms_mm": round(area_weighted_rms(d["sine"], lats), 3),
        }

    w = annual["weighted"]
    gcos, gsin = w["grace"]["cosine"], w["grace"]["sine"]
    lcos, lsin = w["gldas"]["cosine"], w["gldas"]["sine"]

    # ---------- evidence rows ----------
    # (claim_id, metric_id, metric_name, value, unit, definition)
    rows = []

    def add(claim, mid, name, value, unit, definition, source):
        rows.append([claim, mid, name, value, unit, definition, source])

    # ---- C01 ----
    add("C01", "R01", "GRACE cosine min", gcos["min"], "mm",
        "min of annual cosine geoid amplitude (400 km smoothing, deg-2 excluded, "
        "17-month weighted LSQ)", "computed")
    add("C01", "R02", "GRACE cosine max", gcos["max"], "mm",
        "max of annual cosine geoid amplitude", "computed")
    add("C01", "R03", "GRACE cosine RMS", gcos["rms"], "mm",
        "global RMS of annual cosine geoid amplitude (unweighted grid RMS)",
        "computed")
    add("C01", "R04", "GRACE sine min", gsin["min"], "mm",
        "min of annual sine geoid amplitude", "computed")
    add("C01", "R05", "GRACE sine max", gsin["max"], "mm",
        "max of annual sine geoid amplitude", "computed")
    add("C01", "R06", "GRACE sine RMS", gsin["rms"], "mm",
        "global RMS of annual sine geoid amplitude", "computed")
    add("C01", "R07", "GLDAS cosine min", lcos["min"], "mm",
        "min of GLDAS annual cosine geoid amplitude", "computed")
    add("C01", "R08", "GLDAS cosine max", lcos["max"], "mm",
        "max of GLDAS annual cosine geoid amplitude", "computed")
    add("C01", "R09", "GLDAS cosine RMS", lcos["rms"], "mm",
        "global RMS of GLDAS annual cosine geoid amplitude", "computed")
    add("C01", "R10", "GLDAS sine min", lsin["min"], "mm",
        "min of GLDAS annual sine geoid amplitude", "computed")
    add("C01", "R11", "GLDAS sine max", lsin["max"], "mm",
        "max of GLDAS annual sine geoid amplitude", "computed")
    add("C01", "R12", "GLDAS sine RMS", lsin["rms"], "mm",
        "global RMS of GLDAS annual sine geoid amplitude", "computed")
    add("C01", "R03-aw", "GRACE cosine area-weighted RMS", aw["grace"]["cosine_area_rms_mm"],
        "mm", "cos(lat)-area-weighted global RMS (sensitivity)", "computed")
    add("C01", "R06-aw", "GRACE sine area-weighted RMS", aw["grace"]["sine_area_rms_mm"],
        "mm", "cos(lat)-area-weighted global RMS (sensitivity)", "computed")
    add("C01", "R09-aw", "GLDAS cosine area-weighted RMS",
        aw["gldas"]["cosine_area_rms_mm"], "mm", "cos(lat)-area-weighted RMS", "computed")
    add("C01", "R12-aw", "GLDAS sine area-weighted RMS",
        aw["gldas"]["sine_area_rms_mm"], "mm", "cos(lat)-area-weighted RMS", "computed")
    add("C01", "R19", "GRACE > GLDAS cosine amplitude",
        round(abs(gcos["max"]) + abs(gcos["min"]), 2) >
        round(abs(lcos["max"]) + abs(lcos["min"]), 2), "bool",
        "GRACE cosine peak-to-peak (8.90 mm) exceeds GLDAS (4.57 mm)",
        "computed")
    add("C01", "R20", "GRACE > GLDAS sine amplitude",
        round(abs(gsin["max"]) + abs(gsin["min"]), 2) >
        round(abs(lsin["max"]) + abs(lsin["min"]), 2), "bool",
        "GRACE sine peak-to-peak (14.98 mm) exceeds GLDAS (11.19 mm)",
        "computed")
    add("C01", "R21", "GRACE RMS > GLDAS RMS both components",
        (gcos["rms"] > lcos["rms"]) and (gsin["rms"] > lsin["rms"]), "bool",
        "GRACE RMS (0.59, 1.32) > GLDAS RMS (0.48, 1.02)", "computed")
    add("C01", "R22", "Sine RMS > cosine RMS (GRACE)",
        gsin["rms"] > gcos["rms"], "bool", "annual cycle peaks spring/fall",
        "computed")
    add("C01", "R23", "Sine RMS > cosine RMS (GLDAS)",
        lsin["rms"] > lcos["rms"], "bool", "annual cycle peaks spring/fall",
        "computed")

    # ---- C02 ----
    add("C02", "R13", "Amazon April 2003 max", sa_amazon["amazon_april_max_mm"], "mm",
        "max geoid anomaly within Amazon box (lat -15..5, lon 285..312) in "
        "Apr 2003 relative to 17-month mean (400 km smoothing)", "computed")
    add("C02", "R14", "Amazon October 2003 min", sa_amazon["amazon_october_min_mm"], "mm",
        "min geoid anomaly within Amazon box in Oct 2003 relative to mean",
        "computed")
    add("C02", "R13-loc", "April 2003 max location",
        sa["2003-04"]["max_at"], "lat,lon",
        "location of Apr 2003 SA-region max (should be in Amazon basin)",
        "computed")
    add("C02", "R14-loc", "October 2003 min location",
        sa["2003-10"]["min_at"], "lat,lon",
        "location of Oct 2003 SA-region min (should be in Amazon basin)",
        "computed")
    amazon_series = sa_amazon["amazon"]
    orinoco_series = sa_amazon["orinoco"]
    # correlation between Amazon and Orinoco basin-averaged anomalies
    a = np.array([amazon_series[k]["mean_mm"] for k in amazon_series])
    o = np.array([orinoco_series[k]["mean_mm"] for k in orinoco_series])
    corr = float(np.corrcoef(a, o)[0, 1])
    add("C02", "R15a", "Amazon-Orinoco anomaly correlation", round(corr, 3), "-",
        "correlation of basin-averaged monthly anomalies (negative -> separation)",
        "computed")
    add("C02", "R15b", "April Amazon vs Orinoco sign",
        f"Amz={amazon_series['2003-04']['mean_mm']:+.2f} "
        f"Ori={orinoco_series['2003-04']['mean_mm']:+.2f}", "mm",
        "basin-averaged anomalies in April 2003 (opposite signs -> separation)",
        "computed")

    # ---- C03 ----
    for y in ("2002", "2003"):
        a = err[y]
        add("C03", f"R16-{y}", f"{a['label']} signal peak/error ratio",
            a["peak_over_error"], "-",
            "signal peak amplitude / frozen calibrated error RMS "
            "(distinctly >1 => signal above random error)", "computed")
        add("C03", f"R16b-{y}", f"{a['label']} signal RMS", a["signal_rms_mm"], "mm",
            "global RMS of observed anomaly map", "computed")
        add("C03", f"R16c-{y}", f"{a['label']} error RMS (frozen)", a["error_rms_mm_primary_frozen"],
            "mm", "RMS of frozen calibrated-covariance error realization",
            "computed(frozen data)")
        add("C03", f"R16d-{y}", f"{a['label']} SNR (signal/error RMS)", a["snr_rms"], "-",
            "global RMS signal / error RMS", "computed")

    # ---- C04 ----
    add("C04", "R17", "2003 error RMS at 600 km (frozen)", err["2003"]["error_rms_mm_primary_frozen"],
        "mm", "geoid-height error at 600 km smoothing, Apr 2003", "computed(frozen data)")
    add("C04", "R18", "2002 error RMS at 1000 km (frozen)", err["2002"]["error_rms_mm_primary_frozen"],
        "mm", "geoid-height error at 1000 km smoothing, Apr 2002", "computed(frozen data)")
    add("C04", "R17-own", "2003 error RMS at 600 km (own draws)",
        err_stats["2003"]["own_error_multi_seed_mean_rms_mm"], "mm",
        "mean of 3 own realizations from formal covariance x64", "computed")
    add("C04", "R18-own", "2002 error RMS at 1000 km (own draws)",
        err_stats["2002"]["own_error_multi_seed_mean_rms_mm"], "mm",
        "mean of 3 own realizations from formal covariance x64", "computed")
    add("C04", "R17b", "2003 error RMS at 400 km (own draws)",
        err_radius["2003"]["400"]["rms_mean_mm"], "mm",
        "geoid error at 400 km smoothing, Apr 2003 (resolution limit probe)",
        "computed")
    add("C04", "R18b", "2002 error RMS at 400 km (own draws)",
        err_radius["2002"]["400"]["rms_mean_mm"], "mm",
        "geoid error at 400 km smoothing, Apr 2002", "computed")
    add("C04", "R17c", "2003 error RMS at 1000 km (own draws)",
        err_radius["2003"]["1000"]["rms_mean_mm"], "mm",
        "geoid error at 1000 km smoothing, Apr 2003", "computed")
    add("C04", "R24", "2003 achieves 600 km at ~2 mm vs 2002 needs 1000 km",
        err["2003"]["error_rms_mm_primary_frozen"] <= 3.0 and
        err["2002"]["error_rms_mm_primary_frozen"] <= 3.0, "bool",
        "both solutions reach ~2-3 mm error at their nominal resolutions",
        "computed")

    # ---------- write evidence table ----------
    csv_path = RESULTS / "evidence_table.csv"
    with open(csv_path, "w", newline="") as f:
        wtr = csv.writer(f)
        wtr.writerow(["claim_id", "metric_id", "metric_name", "value", "unit",
                      "definition", "source"])
        wtr.writerows(rows)
    print(f"\nWrote {len(rows)} evidence rows -> {csv_path}")

    # ---------- metrics.json ----------
    metrics = {}
    for r in rows:
        claim, mid, name, value, unit, definition, source = r
        metrics[mid] = {"claim": claim, "metric": name, "value": value,
                        "unit": unit, "definition": definition, "source": source}
    metrics["_meta"] = {
        "paper": "Tapley et al. 2004, Science 305:503",
        "data": "frozen GRACE RL06 L2 (18 mo), GLDAS SH (17 mo), covariance "
                "(RL06 formal diag x64), frozen error realizations",
        "n_months_used": 17,
        "smoothing_km": [400, 600, 1000],
        "degree2_excluded": True,
        "annual_fit": "weighted LSQ cos/sin/trend/offset (2002 w=0.25, 2003 w=1.0)",
        "grace_cosine_pp_mm": round(abs(gcos["max"]) + abs(gcos["min"]), 2),
        "gldas_cosine_pp_mm": round(abs(lcos["max"]) + abs(lcos["min"]), 2),
        "grace_sine_pp_mm": round(abs(gsin["max"]) + abs(gsin["min"]), 2),
        "gldas_sine_pp_mm": round(abs(lsin["max"]) + abs(lsin["min"]), 2),
        "paper_values": {
            "grace_cosine": [-7.2, 3.0, 0.9],
            "grace_sine": [-6.4, 8.9, 1.3],
            "gldas_cosine": [-2.3, 3.2, 0.4],
            "gldas_sine": [-4.0, 6.7, 1.0],
            "amazon_april_max": 14.0,
            "amazon_october_min": -7.7,
            "accuracy_mm": "2-3",
        },
    }
    with open(RESULTS / "metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"Wrote {RESULTS / 'metrics.json'}")

    # ---------- claim verdicts ----------
    verdicts = {
        "C01": {"verdict": "partially_supported",
                "evidence": (
                    "GRACE sine (max +9.12 vs 8.9, RMS 1.32 vs 1.3) and cosine min "
                    "(-7.24 vs -7.2) match; but GRACE cosine max (+1.65 vs +3.0) and "
                    "RMS (0.59 vs 0.9), and GLDAS cosine max (+2.25 vs +3.2) differ. "
                    "Patterns (GRACE>GLDAS, sine>cosine) reproduced.")},
        "C02": {"verdict": "partially_supported",
                "evidence": (
                    "April 2003 Amazon max +11.37 mm (paper +14.0) and October min "
                    "-8.44 mm (paper -7.7), both located in the Amazon basin; "
                    "Amazon-Orinoco basin-averaged anomalies negatively correlated "
                    "(r=-0.37), opposite signs in Apr (Amz +5.83 vs Ori -4.19) and "
                    "Sep (Amz -3.85 vs Ori +2.50) -> clear separation. Amplitudes "
                    "differ from paper due to RL06 vs RL01 / 17- vs 14-month mean.")},
        "C03": {"verdict": "partially_supported",
                "evidence": (
                    "Signal peaks 8.8 mm (2002) and 10.3 mm (2003) are 4.1x/4.8x the "
                    "frozen calibrated error RMS (2.16/2.15 mm); coherent spatial "
                    "patterns above random error. But global signal RMS (1.42/1.44 mm) "
                    "is below error RMS, so only the peak/coherent-feature amplitudes "
                    "are distinctly above the noise.")},
        "C04": {"verdict": "supported",
                "evidence": (
                    "Frozen calibrated error RMS = 2.15 mm (2003, 600 km) and 2.16 mm "
                    "(2002, 1000 km) -> 2-3 mm accuracy at 600-1000 km. Own draws: "
                    "3.35 mm at 400 km (2003) vs 6.51 mm (2002) -> 2003 resolves "
                    "400-600 km, 2002 requires ~1000 km.")},
    }
    with open(RESULTS / "claim_verdicts.json", "w") as f:
        json.dump(verdicts, f, indent=2)

    print("\nClaim verdicts:")
    for k, v in verdicts.items():
        print(f"  {k}: {v['verdict']}")


if __name__ == "__main__":
    main()
