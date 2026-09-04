#!/usr/bin/env python3
"""
02_c02_temperature_compare.py
=============================
Characterise the bottom-temperature projection data for claim C02:

  "BNAM and CM2.6 bottom temperature projections show similar spatial
   patterns but different magnitudes"

Using ONLY the frozen data bundle (bnam_cm26_input_subset_v1):

  CM2.6_bottom_temperature_change.nc  -> CM2.6 bottom-temperature change
                                          (one_percent - control, annual mean)
  BNAM_TSUV_AllDepths.zip / Bottom_TSUV.nc
                                       -> BNAM monthly bottom-temperature
                                          climatology (present day, 1990-2015)
  coords.npz                           -> CM2.6 grid coordinates

What is actually possible with the frozen data:
  * fully characterise the CM2.6 projected change field (magnitude + pattern);
  * characterise the BNAM present-day bottom-temperature climatology;
  * quantify present-day model agreement (CM2.6 control vs BNAM) over the
    overlapping domain;
  * DOCUMENT that no BNAM 2055 RCP8.5 (future) field exists in the frozen set,
    so the BNAM *projection* (and therefore the direct BNAM-vs-CM2.6 change
    comparison) cannot be computed.

Outputs (agent_solution/results/):
  cm26_temp_change_stats.csv
  bnam_present_temp_stats.csv
  cm26_vs_bnam_present_comparison.csv
  figures/cm26_bottom_temp_change.png
  figures/bnam_present_bottom_temp.png
"""

from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pandas as pd
import netCDF4

# --------------------------------------------------------------------------
# Data locations
# --------------------------------------------------------------------------
BUNDLE = Path(r"E:\scisolvebench-data\asset-data\datasets-v1\v1\gehlen_2019"
              r"\real_data_candidates\bnam_cm26_input_subset_v1\files")
CM26_NC = BUNDLE / "CM2.6_bottom_temperature_change.nc"
COORDS_NPZ = BUNDLE / "coords.npz"
# BNAM bottom climatology: extracted copy in the frozen reproduce workspace
# (identical to the entry inside BNAM_TSUV_AllDepths.zip; verified by size).
BNAM_BOTTOM_NC = Path(r"F:\dataset\gehlen_2019\reproduce\BNAM\Bottom_TSUV.nc")

OUT = Path(__file__).resolve().parents[1] / "results"
FIG = OUT / "figures"
OUT.mkdir(exist_ok=True)
FIG.mkdir(exist_ok=True)


def area_weight_1d(lat_deg):
    """cos(lat) area weights for a regular lat-lon grid (per latitude row)."""
    return np.cos(np.deg2rad(lat_deg))


def main() -> None:
    print("=" * 72)
    print("C02 -- Bottom temperature projections: CM2.6 (available), BNAM (present only)")
    print("=" * 72)

    # ------------------------------------------------------------------ #
    # 1) CM2.6 projection change field
    # ------------------------------------------------------------------ #
    ds = netCDF4.Dataset(str(CM26_NC))
    xt = np.asarray(ds["xt_ocean"][:])
    yt = np.asarray(ds["yt_ocean"][:])
    chg = np.ma.filled(ds["bottom_temp_change"][:], np.nan).astype(np.float64)
    ctrl = np.ma.filled(ds["bottom_temp_control"][:], np.nan).astype(np.float64)
    proj = np.ma.filled(ds["bottom_temp_projection"][:], np.nan).astype(np.float64)
    ds.close()

    # coords.npz must match the nc grid
    c = np.load(COORDS_NPZ)
    assert np.allclose(c["xt"], xt) and np.allclose(c["yt"], yt)

    valid = ~np.isnan(chg)
    n_valid = int(valid.sum())
    lat_2d = np.broadcast_to(yt[:, None], chg.shape)
    w = np.where(valid, np.cos(np.deg2rad(lat_2d)), np.nan)

    chg_v = chg[valid]
    w_v = w[valid]

    def wmean(a):
        return float(np.nansum(a * w_v) / np.nansum(w_v))

    stats = {
        "n_valid_cells": n_valid,
        "n_total_cells": int(chg.size),
        "pct_domain_covered": 100.0 * n_valid / chg.size,
        "mean": float(np.nanmean(chg_v)),
        "area_weighted_mean": wmean(chg_v),
        "median": float(np.nanmedian(chg_v)),
        "std": float(np.nanstd(chg_v)),
        "p05": float(np.nanpercentile(chg_v, 5)),
        "p25": float(np.nanpercentile(chg_v, 25)),
        "p75": float(np.nanpercentile(chg_v, 75)),
        "p95": float(np.nanpercentile(chg_v, 95)),
        "min": float(np.nanmin(chg_v)),
        "max": float(np.nanmax(chg_v)),
        "frac_warming_gt_0": float(np.nanmean(chg_v > 0)),
        "frac_cooling_lt_0": float(np.nanmean(chg_v < 0)),
        "frac_gt_1C": float(np.nanmean(chg_v > 1)),
        "frac_gt_2C": float(np.nanmean(chg_v > 2)),
        "frac_gt_3C": float(np.nanmean(chg_v > 3)),
        "frac_gt_4C": float(np.nanmean(chg_v > 4)),
    }
    # location of maximum warming
    max_idx = np.nanargmax(chg)
    max_ij = np.unravel_index(max_idx, chg.shape)
    stats["max_change_lon"] = float(xt[max_ij[1]])
    stats["max_change_lat"] = float(yt[max_ij[0]])
    pdf = pd.DataFrame([stats])
    pdf.to_csv(OUT / "cm26_temp_change_stats.csv", index=False)
    print("\n[1] CM2.6 annual-mean bottom-temperature change (projection - control):")
    for k, v in stats.items():
        print(f"    {k:24s} {v:.6g}")

    # spatial pattern: subregion means
    sub = {
        "Gulf of Maine (lon -71..-66, lat 42..45)": (
            (xt >= -71) & (xt <= -66) & (yt[:, None] >= 42) & (yt[:, None] <= 45)),
        "Scotian Shelf (lon -65..-59, lat 42..46)": (
            (xt >= -65) & (xt <= -59) & (yt[:, None] >= 42) & (yt[:, None] <= 46)),
        "Bay of Fundy (lon -67..-65, lat 44.5..45.8)": (
            (xt >= -67) & (xt <= -65) & (yt[:, None] >= 44.5) & (yt[:, None] <= 45.8)),
        "Georges Bank (lon -68..-66, lat 41..42.5)": (
            (xt >= -68) & (xt <= -66) & (yt[:, None] >= 41) & (yt[:, None] <= 42.5)),
        "NE US Shelf (lon -73..-69, lat 39..42)": (
            (xt >= -73) & (xt <= -69) & (yt[:, None] >= 39) & (yt[:, None] <= 42)),
    }
    print(f"\n    Location of maximum change: lon={xt[max_ij[1]]:.2f}, "
          f"lat={yt[max_ij[0]]:.2f}, change={chg[max_ij]:.2f} C")
    sub_rows = []
    for name, mask in sub.items():
        m = mask & valid
        if m.sum() == 0:
            continue
        sub_rows.append({"subregion": name, "n_cells": int(m.sum()),
                         "mean_change": float(np.nanmean(chg[m])),
                         "max_change": float(np.nanmax(chg[m]))})
    subdf = pd.DataFrame(sub_rows)
    subdf.to_csv(OUT / "cm26_temp_change_subregions.csv", index=False)
    print("    Subregion mean change (C):")
    print(subdf.to_string(index=False))

    # ------------------------------------------------------------------ #
    # 2) BNAM present-day bottom-temperature climatology
    # ------------------------------------------------------------------ #
    db = netCDF4.Dataset(str(BNAM_BOTTOM_NC))
    lon_b = db["lon"][:].astype(np.float64)
    lat_b = db["lat"][:].astype(np.float64)
    temper = db["temper"][:].astype(np.float64)  # (12, y, x)
    db.close()
    months = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]

    ann_mean = np.nanmean(temper, axis=0)  # (y, x)
    winter = np.nanmean(temper[[0, 1, 2]], axis=0)   # JFM
    summer = np.nanmean(temper[[6, 7, 8]], axis=0)   # JAS

    # Restrict to the CM2.6 domain overlap so stats are comparable
    overlap = ((lon_b >= -77.95) & (lon_b <= -50.05) &
               (lat_b >= 38.01) & (lat_b <= 49.96) &
               ~np.isnan(ann_mean))
    n_ov = int(overlap.sum())
    b_stats = {
        "grid_y": int(lon_b.shape[0]), "grid_x": int(lon_b.shape[1]),
        "n_valid_cells_full": int((~np.isnan(ann_mean)).sum()),
        "n_cells_in_cm26_domain": n_ov,
        "annual_mean_full_domain": float(np.nanmean(ann_mean)),
        "annual_mean_in_cm26_domain": float(np.nanmean(ann_mean[overlap])),
        "summer_mean_JAS_in_cm26_domain": float(np.nanmean(summer[overlap])),
        "winter_mean_JFM_in_cm26_domain": float(np.nanmean(winter[overlap])),
        "min_annual": float(np.nanmin(ann_mean)),
        "max_annual": float(np.nanmax(ann_mean)),
    }
    bpdf = pd.DataFrame([b_stats])
    bpdf.to_csv(OUT / "bnam_present_temp_stats.csv", index=False)
    print("\n[2] BNAM present-day bottom-temperature climatology (1990-2015):")
    for k, v in b_stats.items():
        print(f"    {k:32s} {v:.6g}")

    # ------------------------------------------------------------------ #
    # 3) Present-day model agreement: CM2.6 control vs BNAM
    #    (context only -- this is NOT a projection comparison)
    # ------------------------------------------------------------------ #
    # Sample CM2.6 control onto the BNAM grid by nearest-neighbour.
    # (CM2.6 grid is 47k nodes; BNAM overlap is ~43k cells -> KDTree is cheap.)
    from scipy.spatial import cKDTree
    ctrl_valid = ~np.isnan(ctrl)
    yy, xx = np.meshgrid(yt, xt, indexing="ij")
    tree = cKDTree(np.column_stack([yy[ctrl_valid], xx[ctrl_valid]]))
    q_pts = np.column_stack([lat_b.ravel(), lon_b.ravel()])
    dist, idx = tree.query(q_pts, k=1)
    idx2 = np.where(np.isfinite(idx), idx, 0)
    ctrl_flat = ctrl[ctrl_valid].ravel()[idx2]
    ctrl_b = ctrl_flat.reshape(lat_b.shape)
    ctrl_b[~np.isfinite(idx).reshape(lat_b.shape)] = np.nan

    both = overlap & ~np.isnan(ctrl_b)
    a = ctrl_b[both]            # CM2.6 control sampled to BNAM grid
    b = ann_mean[both]          # BNAM annual mean
    n_both = int(both.sum())
    pearson = float(np.corrcoef(a, b)[0, 1])
    bias = float(np.nanmean(b - a))          # BNAM - CM2.6 control
    rmse = float(np.sqrt(np.nanmean((b - a) ** 2)))
    comp = {
        "n_overlap_cells": n_both,
        "spatial_corr_present": pearson,
        "mean_bias_BNAM_minus_CM26_control": bias,
        "rmse": rmse,
        "note": "present-day comparison only; BNAM future field absent",
    }
    cpdf = pd.DataFrame([comp])
    cpdf.to_csv(OUT / "cm26_vs_bnam_present_comparison.csv", index=False)
    print("\n[3] Present-day model agreement (CM2.6 control vs BNAM, overlap cells):")
    for k, v in comp.items():
        print(f"    {k:34s} {v:.6g}" if isinstance(v, float) else f"    {k:34s} {v}")

    # ------------------------------------------------------------------ #
    # 4) Explicit data-availability statement for the projection comparison
    # ------------------------------------------------------------------ #
    print("\n[4] BNAM projection availability:")
    print("    The frozen bundle contains the BNAM present-day climatology only.")
    print("    The BNAM 2055 RCP8.5 (2046-2065) monthly bottom-temperature field")
    print("    used by the paper is NOT part of the frozen data (P03/P17 reports),")
    print("    therefore the BNAM projected CHANGE field cannot be computed and the")
    print("    direct BNAM-vs-CM2.6 projection comparison is not possible.")

    # ------------------------------------------------------------------ #
    # 5) Figures
    # ------------------------------------------------------------------ #
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib.colors import TwoSlopeNorm

        fig, ax = plt.subplots(1, 1, figsize=(9, 6))
        norm = TwoSlopeNorm(vmin=0, vcenter=1.5, vmax=np.nanmax(chg))
        pm = ax.pcolormesh(xt, yt, chg, shading="auto", cmap="RdBu_r", norm=norm)
        cb = fig.colorbar(pm, ax=ax, extend="max")
        cb.set_label("CM2.6 bottom-temp change (degC)")
        ax.set_xlabel("lon"); ax.set_ylabel("lat")
        ax.set_title("CM2.6 bottom temperature change (one_percent - control)")
        fig.tight_layout()
        fig.savefig(FIG / "cm26_bottom_temp_change.png", dpi=150)
        plt.close(fig)

        fig, ax = plt.subplots(1, 1, figsize=(9, 6))
        pm = ax.pcolormesh(lon_b, lat_b, ann_mean, shading="auto", cmap="viridis")
        cb = fig.colorbar(pm, ax=ax)
        cb.set_label("BNAM present-day bottom temp (degC)")
        ax.set_xlabel("lon"); ax.set_ylabel("lat")
        ax.set_title("BNAM present-day climatology annual-mean bottom temperature")
        fig.tight_layout()
        fig.savefig(FIG / "bnam_present_bottom_temp.png", dpi=150)
        plt.close(fig)
        print("\n[5] Figures written to", FIG)
    except Exception as e:  # plotting must never block the numeric results
        print(f"\n[5] Figure generation skipped: {e}")


if __name__ == "__main__":
    main()
