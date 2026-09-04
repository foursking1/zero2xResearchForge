"""
Step 2 -- Weighted least-squares fit of the annual cosine (winter-summer) and
          sine (spring-fall) components plus a linear trend at every grid point
          of the 17-month smoothed geoid time series (Claim C01).

Model:  geoid(t) = A_cos*cos(2*pi*t) + A_sin*sin(2*pi*t) + c*t + offset
with t in fractional years (month midpoint).

Primary weighting (mirrors the reference pipeline / paper's "weighted LSQ"):
  2002 months weight 0.25 (approx. 2x noisier than 2003), 2003 months 1.0.
A sensitivity run with equal weights is also reported.

Outputs (results/annual_fit/):
  grace_annual_fit.npz, gldas_annual_fit.npz  (cosine, sine, trend, offset, lats, lons)
  summary.json                                 (min/max/RMS for each map)
"""
from __future__ import annotations
import json
import numpy as np
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent))
from grace_utils import rms, month_fractional_year

SMOOTH_DIR = Path(__file__).resolve().parents[1] / "results" / "smoothed_grids"
OUT_DIR = Path(__file__).resolve().parents[1] / "results" / "annual_fit"
OUT_DIR.mkdir(parents=True, exist_ok=True)

PAPER = {
    "grace_cosine": {"min": -7.2, "max": 3.0, "rms": 0.9},
    "grace_sine": {"min": -6.4, "max": 8.9, "rms": 1.3},
    "gldas_cosine": {"min": -2.3, "max": 3.2, "rms": 0.4},
    "gldas_sine": {"min": -4.0, "max": 6.7, "rms": 1.0},
}


def load_grids():
    grace_files = sorted(SMOOTH_DIR.glob("grace_geoid_400km_*.npz"))
    gldas_files = sorted(SMOOTH_DIR.glob("gldas_geoid_400km_*.npz"))

    # GRACE: build month map and time tags
    grace_data = []
    for f in grace_files:
        d = np.load(f)
        ds = str(d["date_start"])          # '2002-04-05'
        yr, mo, dy = int(ds[:4]), int(ds[5:7]), int(ds[8:10])
        t = month_fractional_year(ds)
        grace_data.append({
            "file": f.name,
            "month_str": f"{yr:04d}{mo:02d}",
            "t": t,
            "geoid_mm": d["geoid_mm"],
            "lats": d["lats"],
            "lons": d["lons"],
        })
    # GLDAS by month
    gldas_by_month = {}
    for f in gldas_files:
        d = np.load(f)
        gldas_by_month[str(d["month"])] = d["geoid_mm"]

    # align GLDAS to same 17 months as GRACE
    grids_grace = [g for g in grace_data]
    grids_gldas = [gldas_by_month[g["month_str"]] for g in grace_data
                   if g["month_str"] in gldas_by_month]

    t = np.array([g["t"] for g in grids_grace])
    lats = grids_grace[0]["lats"]
    lons = grids_grace[0]["lons"]
    Y_grace = np.stack([g["geoid_mm"] for g in grids_grace], axis=0)
    Y_gldas = np.stack(grids_gldas, axis=0)
    months = [g["month_str"] for g in grids_grace]
    return t, lats, lons, Y_grace, Y_gldas, months


def annual_fit(Y, t, weights=None):
    """Weighted least-squares annual fit. Returns (cosine, sine, trend, offset)."""
    n = len(t)
    G = np.column_stack([np.cos(2 * np.pi * t), np.sin(2 * np.pi * t), t,
                         np.ones_like(t)])
    if weights is None:
        weights = np.ones(n)
    weights = np.asarray(weights, float)
    weights = weights / weights.sum() * n          # normalize: sum = n
    W = np.diag(weights)
    Y_flat = Y.reshape(n, -1)
    M = np.linalg.solve(G.T @ W @ G, G.T @ W @ Y_flat)
    nlat, nlon = Y.shape[1], Y.shape[2]
    return (M[0].reshape(nlat, nlon), M[1].reshape(nlat, nlon),
            M[2].reshape(nlat, nlon), M[3].reshape(nlat, nlon))


def compute_stats(cos, sin, lats):
    def stats(m):
        return {"min": round(float(m.min()), 3), "max": round(float(m.max()), 3),
                "rms": round(rms(m), 3)}
    return {"cosine": stats(cos), "sine": stats(sin)}


def main():
    t, lats, lons, Y_grace, Y_gldas, months = load_grids()
    print(f"Loaded {len(months)} months; t range {t.min():.3f}..{t.max():.3f}")

    # Weights: 2002 = 0.25, 2003 = 1.0
    w = np.array([0.25 if m[:4] == "2002" else 1.0 for m in months])

    print("\n--- Weighted fit (2002 w=0.25, 2003 w=1.0) ---")
    gcos, gsin, gtrend, goff = annual_fit(Y_grace, t, w)
    lcos, lsin, ltrend, loff = annual_fit(Y_gldas, t, w)
    res = {}
    res["grace"] = compute_stats(gcos, gsin, lats)
    res["gldas"] = compute_stats(lcos, lsin, lats)
    for k, v in res.items():
        print(f"  {k}: cosine {v['cosine']}  sine {v['sine']}")

    print("\n--- Equal-weight sensitivity ---")
    gcos_e, gsin_e, _, _ = annual_fit(Y_grace, t)
    lcos_e, lsin_e, _, _ = annual_fit(Y_gldas, t)
    res_eq = {"grace": compute_stats(gcos_e, gsin_e, lats),
              "gldas": compute_stats(lcos_e, lsin_e, lats)}
    for k, v in res_eq.items():
        print(f"  {k}: cosine {v['cosine']}  sine {v['sine']}")

    # Save primary weighted results
    np.savez_compressed(OUT_DIR / "grace_annual_fit.npz",
                        cosine=gcos, sine=gsin, trend=gtrend, offset=goff,
                        lats=lats, lons=lons, t=t, weights=w, months=months)
    np.savez_compressed(OUT_DIR / "gldas_annual_fit.npz",
                        cosine=lcos, sine=lsin, trend=ltrend, offset=loff,
                        lats=lats, lons=lons, t=t, weights=w, months=months)

    summary = {
        "n_months": len(months),
        "months": months,
        "method": "weighted LSQ: geoid=Acos*cos(2pi t)+Asin*sin(2pi t)+trend*t+offset",
        "weights_primary": "2002 months: 0.25; 2003 months: 1.0 (normalized sum=n)",
        "weighted": res,
        "equal_weight_sensitivity": res_eq,
        "paper_fig1": PAPER,
    }
    with open(OUT_DIR / "summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    # Quick comparison vs paper
    print("\n--- vs paper (Fig 1 caption) ---")
    for k in PAPER:
        p = PAPER[k]
        r = res["grace" if k.startswith("grace") else "gldas"]["cosine" if "cos" in k else "sine"]
        print(f"  {k}: paper {p} | computed {r}")


if __name__ == "__main__":
    main()
