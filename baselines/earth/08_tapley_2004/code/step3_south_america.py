"""
Step 3 -- Month-to-month geoid anomalies for equatorial South America during
          2003 (Claim C02).

The 400 km-smoothed GRACE grids from Step 1 are anomalies relative to the
17-month mean.  We subset to the South America domain (35S..20N, 270..340E),
compute monthly extrema, and assess the Amazon vs Orinoco watershed behaviour:

  * Amazon basin box:  lat [-15, 5],  lon [285, 312]  (48W..75W)
  * Orinoco basin box: lat [ 2, 10],  lon [290, 300]  (60W..70W)

Paper (Fig. 2 text): Amazon basin local maximum +14.0 mm in April 2003 and
local minimum -7.7 mm in October 2003, relative to the mean, with a clear
separation between the Amazon and Orinoco watersheds.

Outputs (results/south_america/):
  monthly_extrema.json     (per-month min/max over the full SA region)
  amazon_orinoco.json      (box-averaged time series + April max / Oct min)
  south_america_geoid_YYYYMM.npz (saved sub-region grids)
"""
from __future__ import annotations
import json
import numpy as np
from pathlib import Path

SMOOTH_DIR = Path(__file__).resolve().parents[1] / "results" / "smoothed_grids"
OUT_DIR = Path(__file__).resolve().parents[1] / "results" / "south_america"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# South America domain (matches reference Fig. 2 subset)
LAT_MIN, LAT_MAX = -35.0, 20.0
LON_MIN, LON_MAX = 270.0, 340.0

AMAZON = {"name": "Amazon", "lat": (-15.0, 5.0), "lon": (285.0, 312.0)}
ORINOCO = {"name": "Orinoco", "lat": (2.0, 10.0), "lon": (290.0, 300.0)}

# 10 GRACE months in 2003 available in the frozen data
MONTH_TAGS = {
    "2003032-2003059": "2003-02",
    "2003060-2003090": "2003-03",
    "2003091-2003120": "2003-04",
    "2003121-2003141": "2003-05",
    "2003182-2003212": "2003-07",
    "2003213-2003243": "2003-08",
    "2003244-2003273": "2003-09",
    "2003274-2003304": "2003-10",
    "2003305-2003334": "2003-11",
    "2003335-2003365": "2003-12",
}


def box_average(grid, lats, lons, box):
    lat_lo, lat_hi = box["lat"]
    lon_lo, lon_hi = box["lon"]
    m = (lats >= lat_lo) & (lats <= lat_hi)
    n = (lons >= lon_lo) & (lons <= lon_hi)
    sub = grid[np.ix_(m, n)]
    return float(sub.mean()), sub.max(), sub.min()


def main():
    extrema = {}
    amazon_series = {}
    orinoco_series = {}

    for tag, label in MONTH_TAGS.items():
        f = SMOOTH_DIR / f"grace_geoid_400km_{tag}.npz"
        if not f.exists():
            continue
        d = np.load(f)
        lats, lons, g = d["lats"], d["lons"], d["geoid_mm"]

        m = (lats >= LAT_MIN) & (lats <= LAT_MAX)
        n = (lons >= LON_MIN) & (lons <= LON_MAX)
        sub = g[np.ix_(m, n)]
        sub_lats, sub_lons = lats[m], lons[n]

        np.savez_compressed(OUT_DIR / f"south_america_geoid_{label.replace('-', '')}.npz",
                            geoid_mm=sub, lats=sub_lats, lons=sub_lons, month=label)

        i, j = np.unravel_index(np.nanargmax(sub), sub.shape)
        im, jm = np.unravel_index(np.nanargmin(sub), sub.shape)
        extrema[label] = {
            "min_mm": round(float(sub.min()), 3),
            "max_mm": round(float(sub.max()), 3),
            "max_at": [round(float(sub_lats[i]), 2), round(float(sub_lons[j]), 2)],
            "min_at": [round(float(sub_lats[im]), 2), round(float(sub_lons[jm]), 2)],
        }

        a_mean, a_max, a_min = box_average(g, lats, lons, AMAZON)
        o_mean, o_max, o_min = box_average(g, lats, lons, ORINOCO)
        amazon_series[label] = {"mean_mm": round(a_mean, 3), "max_mm": round(a_max, 3),
                                "min_mm": round(a_min, 3)}
        orinoco_series[label] = {"mean_mm": round(o_mean, 3), "max_mm": round(o_max, 3),
                                 "min_mm": round(o_min, 3)}
        print(f"{label}: SA max={sub.max():+7.2f} @ {extrema[label]['max_at']}  "
              f"SA min={sub.min():+7.2f} @ {extrema[label]['min_at']}  "
              f"| Amazon mean={a_mean:+6.2f}  Orinoco mean={o_mean:+6.2f}")

    april_max = extrema.get("2003-04", {}).get("max_mm")
    oct_min = extrema.get("2003-10", {}).get("min_mm")
    print(f"\nApril 2003 SA-region max: {april_max} mm (paper: +14.0 mm)")
    print(f"October 2003 SA-region min: {oct_min} mm (paper: -7.7 mm)")

    # Amazon-box extrema (the paper's claim is specifically about the Amazon basin)
    amazon_april_max = amazon_series["2003-04"]["max_mm"]
    amazon_oct_min = amazon_series["2003-10"]["min_mm"]
    print(f"Amazon box April 2003 max: {amazon_april_max} mm")
    print(f"Amazon box October 2003 min: {amazon_oct_min} mm")

    with open(OUT_DIR / "monthly_extrema.json", "w") as f:
        json.dump(extrema, f, indent=2)
    with open(OUT_DIR / "amazon_orinoco.json", "w") as f:
        json.dump({"amazon": amazon_series, "orinoco": orinoco_series,
                   "amazon_april_max_mm": amazon_april_max,
                   "amazon_october_min_mm": amazon_oct_min,
                   "paper_april_max_mm": 14.0, "paper_october_min_mm": -7.7},
                  f, indent=2)
    print(f"\nWrote results to {OUT_DIR}")


if __name__ == "__main__":
    main()
