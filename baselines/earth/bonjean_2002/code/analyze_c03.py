#!/usr/bin/env python3
"""C03 - Mean diagnostic velocity vs drifter mean field.

Reproduces the standard deviation of the difference (STDD) between the time-mean
diagnostic model velocity (0-30 m layer average) and the drifter mean surface
current field.

Steps (following P15 report):
  1. Time-mean of layer_averaged_velocity_30m.nc after filtering outliers
     (|u|,|v| > 3 m/s removed).
  2. Regrid the 1-deg model mean field onto the 0.5-deg drifter grid (linear
     interpolation).
  3. delta = u_model - u_drifter over valid ocean points.
  4. STDD = spatial std of (delta - mean(delta)); also report RMS and mean bias.

The paper claims STDD = 8 cm/s (zonal) and 3 cm/s (meridional).
"""
import os
import json
import numpy as np
import scipy.interpolate as si
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from common import path, load_layer_velocity, load_drifter_05

OUT = os.path.join(os.path.dirname(__file__), "..", "results")
os.makedirs(OUT, exist_ok=True)

OUTLIER_MPS = 3.0   # m/s threshold (P16 convention)


def stdd(a):
    a = np.asarray(a, dtype=float)
    a = a[np.isfinite(a)]
    if a.size == 0:
        return np.nan
    dm = a - np.mean(a)
    return np.sqrt(np.mean(dm ** 2)), np.sqrt(np.mean(a ** 2)), np.mean(a)


def regrid_to_drifter(u_mod, v_mod, mlat, mlon, dlat, dlon):
    """Bilinear interpolation of (lat,lon) model field onto drifter grid."""
    interp_u = si.RegularGridInterpolator((mlat, mlon), u_mod, bounds_error=False, fill_value=np.nan)
    interp_v = si.RegularGridInterpolator((mlat, mlon), v_mod, bounds_error=False, fill_value=np.nan)
    LON, LAT = np.meshgrid(dlon, dlat)
    pts = np.column_stack([LAT.ravel(), LON.ravel()])
    u_out = interp_u(pts).reshape(LAT.shape)
    v_out = interp_v(pts).reshape(LAT.shape)
    return u_out, v_out


def main():
    u, v, t, mlat, mlon = load_layer_velocity()

    # Outlier filtering then time mean
    u = np.where(np.abs(u) > OUTLIER_MPS, np.nan, u)
    v = np.where(np.abs(v) > OUTLIER_MPS, np.nan, v)
    u_mod_mean = np.nanmean(u, axis=0)
    v_mod_mean = np.nanmean(v, axis=0)

    # Drifter 0.5 deg (u, v stored as lon x lat)
    du, dv, dlat, dlon = load_drifter_05()
    u_drift = du.T   # -> (lat, lon)
    v_drift = dv.T

    # Regrid model to drifter grid
    u_mod_rg, v_mod_rg = regrid_to_drifter(u_mod_mean, v_mod_mean, mlat, mlon, dlat, dlon)

    # Compute differences
    du_ = u_mod_rg - u_drift
    dv_ = v_mod_rg - v_drift

    # Full domain (all valid points)
    stdd_u, rms_u, bias_u = stdd(du_)
    stdd_v, rms_v, bias_v = stdd(dv_)

    # Restricted domain 20S-20N (P15 secondary metric)
    mask = (dlat[:, None] >= -20) & (dlat[:, None] <= 20) & np.isfinite(du_) & np.isfinite(dv_)
    stdd_u20, rms_u20, bias_u20 = stdd(du_[mask])
    stdd_v20, rms_v20, bias_v20 = stdd(dv_[mask])

    # Southern-hemisphere-only metric (P15 closest match to paper)
    mask_s = (dlat[:, None] <= 0) & np.isfinite(du_) & np.isfinite(dv_)
    stdd_us, rms_us, bias_us = stdd(du_[mask_s])
    stdd_vs, rms_vs, bias_vs = stdd(dv_[mask_s])

    # Spatial correlation between model and drifter mean fields (qualitative agreement)
    okc = np.isfinite(u_mod_rg) & np.isfinite(u_drift) & np.isfinite(v_mod_rg) & np.isfinite(v_drift)
    corr_u = float(np.corrcoef(u_mod_rg[okc], u_drift[okc])[0, 1])
    corr_v = float(np.corrcoef(v_mod_rg[okc], v_drift[okc])[0, 1])
    # Equatorial zonal velocity profile (mean over 2S-2N)
    eq_mask = (np.abs(dlat) <= 2)
    u_mod_eq = np.nanmean(u_mod_rg[eq_mask], axis=0)
    u_drift_eq = np.nanmean(u_drift[eq_mask], axis=0)

    n_valid = int(np.isfinite(du_).sum())

    result = {
        "outlier_threshold_mps": OUTLIER_MPS,
        "domain": "full tropical Pacific on 0.5-deg drifter grid",
        "stdd_u_cm_s": stdd_u * 100,
        "stdd_v_cm_s": stdd_v * 100,
        "rms_u_cm_s": rms_u * 100,
        "rms_v_cm_s": rms_v * 100,
        "mean_bias_u_cm_s": bias_u * 100,
        "mean_bias_v_cm_s": bias_v * 100,
        "n_valid": n_valid,
        "stdd_u_20S_20N_cm_s": stdd_u20 * 100,
        "stdd_v_20S_20N_cm_s": stdd_v20 * 100,
        "stdd_u_SHemisphere_cm_s": stdd_us * 100,
        "stdd_v_SHemisphere_cm_s": stdd_vs * 100,
        "model_mean_u": float(np.nanmean(u_mod_mean)),
        "model_mean_v": float(np.nanmean(v_mod_mean)),
        "drifter_mean_u": float(np.nanmean(u_drift)),
        "drifter_mean_v": float(np.nanmean(v_drift)),
        "spatial_corr_u": corr_u,
        "spatial_corr_v": corr_v,
    }
    with open(os.path.join(OUT, "c03_stdd.json"), "w") as f:
        json.dump(result, f, indent=2)

    # Figure: mean zonal velocity maps (model, drifter, difference)
    fig, axes = plt.subplots(1, 3, figsize=(16, 4.2))
    vmin, vmax = -0.6, 0.6
    im0 = axes[0].pcolormesh(mlon, mlat, u_mod_mean, vmin=vmin, vmax=vmax, cmap="RdBu_r")
    axes[0].set_title("Model mean u (m/s)")
    im1 = axes[1].pcolormesh(dlon, dlat, u_drift, vmin=vmin, vmax=vmax, cmap="RdBu_r")
    axes[1].set_title("Drifter mean u (m/s)")
    im2 = axes[2].pcolormesh(dlon, dlat, du_, vmin=-0.4, vmax=0.4, cmap="RdBu_r")
    axes[2].set_title("u_model - u_drifter (m/s)")
    for ax in axes:
        ax.set_xlabel("Longitude (°E)")
        ax.set_ylabel("Latitude (°N)")
    fig.colorbar(im2, ax=axes[2], shrink=0.8)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "c03_mean_u_maps.png"), dpi=120)
    plt.close(fig)

    print("C03 results (full domain, 0.5-deg drifter grid):")
    print(f"  spatial corr(model,drifter): u={corr_u:.3f}, v={corr_v:.3f}")
    print(f"  STDD u = {stdd_u*100:.2f} cm/s,  STDD v = {stdd_v*100:.2f} cm/s   (paper: 8, 3)")
    print(f"  RMS  u = {rms_u*100:.2f} cm/s,  RMS  v = {rms_v*100:.2f} cm/s")
    print(f"  mean bias u = {bias_u*100:.2f} cm/s, v = {bias_v*100:.2f} cm/s")
    print(f"  20S-20N: STDD u={stdd_u20*100:.2f}, v={stdd_v20*100:.2f}")
    print(f"  S-hemi:  STDD u={stdd_us*100:.2f}, v={stdd_vs*100:.2f}")
    print(f"  n_valid = {n_valid}")
    print("  saved: c03_stdd.json, c03_mean_u_maps.png")


if __name__ == "__main__":
    main()
