"""
Step 1 -- Recompute 400 km Gaussian-smoothed, degree-2-excluded geoid grids
          (17 months, Apr 2002 - Dec 2003) from the raw frozen data, and
          validate against the frozen pyshtools products.

Inputs (frozen, read in place):
  data/grace_level2/GSM-2_*_GRAC_UTCSR_BA01_0600   (raw GRACE RL06 SH)
  data/gldas_sh/gldas_sh_YYYYMM.npz                 (GLDAS TWS-derived SH anomalies)
  data/grace_mean_clm.npy, grace_mean_slm.npy       (17-month mean; for validation)

Outputs:
  results/smoothed_grids/grace_geoid_400km_<tag>.npz
  results/smoothed_grids/gldas_geoid_400km_<YYYYMM>.npz
  results/smoothed_grids/validation_summary.json    (max|diff| vs frozen grids)
"""
from __future__ import annotations
import json
import numpy as np
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent))
from grace_utils import (
    DEFAULT_DATA_ROOT, load_grace_months, select_months, mean_sh,
    gaussian_weights, glq_grid, synthesize_smoothed_anomaly,
)

DATA_ROOT = Path(DEFAULT_DATA_ROOT)
OUT_ROOT = Path(__file__).resolve().parents[1] / "results"
SMOOTH_OUT = OUT_ROOT / "smoothed_grids"
SMOOTH_OUT.mkdir(parents=True, exist_ok=True)

LMAX = 60
R400 = 400.0


def main():
    # ---------------- GRACE ----------------
    print("Loading GRACE months ...")
    months = load_grace_months(DATA_ROOT)
    sel = select_months(months)
    print(f"  {len(months)} files in archive; {len(sel)} usable months selected")

    # 17-month mean (validated == frozen grace_mean_clm.npy / grace_mean_slm.npy)
    clm_mean, slm_mean = mean_sh(sel, lmax=LMAX)

    # Frozen mean for validation
    fz_mean_c = np.load(DATA_ROOT / "grace_mean_clm.npy")
    fz_mean_s = np.load(DATA_ROOT / "grace_mean_slm.npy")
    print(f"  mean vs frozen: max|dC|={np.abs(clm_mean-fz_mean_c).max():.2e}  "
          f"max|dS|={np.abs(clm_mean-fz_mean_s).max():.2e}")

    W400 = gaussian_weights(LMAX, R400)
    lats, lons = glq_grid(LMAX)

    grace_rows = []
    for m in sel:
        lu = min(m["lmax"], LMAX)
        clm_anom = m["clm"][: lu + 1, : lu + 1] - clm_mean[: lu + 1, : lu + 1]
        slm_anom = m["slm"][: lu + 1, : lu + 1] - slm_mean[: lu + 1, : lu + 1]
        g = synthesize_smoothed_anomaly(clm_anom, slm_anom, W400, lats, lons,
                                        lmax=lu, zero_deg2=True, zero_deg01=False)
        # Validation vs frozen grid
        fz = DATA_ROOT / "smoothed_grids" / f"grace_geoid_400km_{m['tag']}.npz"
        diff = None
        if fz.exists():
            diff = float(np.abs(g - np.load(fz)["geoid_mm"]).max())
        np.savez_compressed(SMOOTH_OUT / f"grace_geoid_400km_{m['tag']}.npz",
                            geoid_mm=g, lats=lats, lons=lons,
                            date_start=str(m["date_start"]))
        grace_rows.append({"tag": m["tag"], "date_start": str(m["date_start"]),
                           "min": round(float(g.min()), 3),
                           "max": round(float(g.max()), 3),
                           "max_abs_diff_vs_frozen": diff})
        print(f"  GRACE {m['tag']}: min={g.min():7.2f} max={g.max():7.2f}  "
              f"|diff|={diff}")

    # ---------------- GLDAS ----------------
    print("Loading GLDAS SH ...")
    gldas_files = sorted((DATA_ROOT / "gldas_sh").glob("gldas_sh_*.npz"))
    gldas_all = []
    for f in gldas_files:
        d = np.load(f)
        gldas_all.append({"month": str(d["month"]), "clm": d["clm"].copy(),
                          "slm": d["slm"].copy(), "lmax": int(d["lmax"])})
    gldas_mean_c = np.mean([g["clm"][: LMAX + 1, : LMAX + 1] for g in gldas_all], axis=0)
    gldas_mean_s = np.mean([g["slm"][: LMAX + 1, : LMAX + 1] for g in gldas_all], axis=0)

    gldas_rows = []
    for g in gldas_all:
        lu = min(g["lmax"], LMAX)
        clm_anom = g["clm"][: lu + 1, : lu + 1] - gldas_mean_c[: lu + 1, : lu + 1]
        slm_anom = g["slm"][: lu + 1, : lu + 1] - gldas_mean_s[: lu + 1, : lu + 1]
        gg = synthesize_smoothed_anomaly(clm_anom, slm_anom, W400, lats, lons,
                                         lmax=lu, zero_deg2=True, zero_deg01=True)
        fz = DATA_ROOT / "smoothed_grids" / f"gldas_geoid_400km_{g['month']}.npz"
        diff = None
        if fz.exists():
            diff = float(np.abs(gg - np.load(fz)["geoid_mm"]).max())
        np.savez_compressed(SMOOTH_OUT / f"gldas_geoid_400km_{g['month']}.npz",
                            geoid_mm=gg, lats=lats, lons=lons, month=g["month"])
        gldas_rows.append({"month": g["month"], "min": round(float(gg.min()), 3),
                           "max": round(float(gg.max()), 3),
                           "max_abs_diff_vs_frozen": diff})
        print(f"  GLDAS {g['month']}: min={gg.min():7.2f} max={gg.max():7.2f}  "
              f"|diff|={diff}")

    summary = {
        "n_grace": len(grace_rows),
        "n_gldas": len(gldas_rows),
        "grid": {"nlat": len(lats), "nlon": len(lons),
                 "lat_min": float(lats.min()), "lat_max": float(lats.max())},
        "smoothing_km": R400,
        "degree2_excluded": True,
        "mean": "17-month temporal mean (GRACE validated == frozen grace_mean)",
        "grace": grace_rows,
        "gldas": gldas_rows,
    }
    with open(SMOOTH_OUT / "validation_summary.json", "w") as f:
        json.dump(summary, f, indent=2, default=str)
    print(f"\nWrote {len(grace_rows) + len(gldas_rows)} grids to {SMOOTH_OUT}")
    print("Validation max|diff| across all grids:",
          max(r["max_abs_diff_vs_frozen"] or 0 for r in grace_rows + gldas_rows))


if __name__ == "__main__":
    main()
