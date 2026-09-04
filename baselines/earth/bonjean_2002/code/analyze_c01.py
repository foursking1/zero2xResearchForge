#!/usr/bin/env python3
"""C01 - Optimal depth-scale parameter H.

Recompute the equatorial momentum-balance residual (Eq. 11a/b of Bonjean &
Lagerloef 2002, as transcribed in the P07 report):

    M_x(x, H) =  g * z_x - (H/2) * theta_x - (1/H) * tau_x        (11a)
    M_y(x, H) = -g * z_y + (H/2) * theta_y + (1/H) * tau_y        (11b)
    ||M_i||   = sqrt( (1/N_x) sum_x M_i(x,H)^2 )

using only time-mean frozen fields:
  z      = WOA94 mean dynamic height
  theta  = mean SST buoyancy gradient  (g*chi_T*SST)
  tau    = mean wind stress

Two wind-stress choices are reported:
  (a) Large & Pond (1981) recomputed from the frozen CCMP winds (primary; the
      method documented in the P05 report), and
  (b) the tau stored in wind_stress_tropical_pacific_10day.nc, which is ~2*pi
      too weak relative to (a) (documented frozen-data inconsistency).

Robustness: the equatorial balance is evaluated at lat=0 obtained either as the
mean of the two bracketing grid rows (-0.5, +0.5) or as each row alone.

Outputs (JSON + CSV + figure) are written to ../results/.
"""
import os
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from common import (DATA_ROOT, G, H_LAYER, path, load_dh, load_winds,
                    load_buoyancy_gradient_mean, load_stored_tau,
                    wind_stress_large_pond, zonal_grad_1d, merid_grad_2d_row)

OUT = os.path.join(os.path.dirname(__file__), "..", "results")
os.makedirs(OUT, exist_ok=True)


def rms(a):
    a = np.asarray(a, dtype=float)
    ok = np.isfinite(a)
    return np.sqrt(np.mean(a[ok] ** 2)) if ok.sum() else np.nan


def h_sweep(dh, thx, thy, tau_xm, tau_ym, lat, lon, Hvals, eq_rows):
    """eq_rows: list of row indices to average for the equatorial latitude."""
    if isinstance(eq_rows, int):
        eq_rows = [eq_rows]
    def eq(field2d):
        return np.nanmean([field2d[i] for i in eq_rows], axis=0)

    z_x = eq(np.stack([zonal_grad_1d(dh[i], lat[i], lon) for i in range(dh.shape[0])]))
    z_y = np.nanmean([merid_grad_2d_row(dh, i, lat) for i in eq_rows], axis=0)
    thx_eq = eq(thx)
    thy_eq = eq(thy)
    txe = eq(tau_xm)
    tye = eq(tau_ym)

    Mx = np.full(len(Hvals), np.nan)
    My = np.full(len(Hvals), np.nan)
    for i, H in enumerate(Hvals):
        Mx[i] = rms(G * z_x - (H / 2) * thx_eq - (1 / H) * txe)
        My[i] = rms(-G * z_y + (H / 2) * thy_eq + (1 / H) * tye)
    dMx = np.gradient(Mx, Hvals)
    dMy = np.gradient(My, Hvals)
    return Mx, My, dMx, dMy


def summarize(Hvals, Mx, dMx):
    """Flatness / knee metrics."""
    i70 = int(np.where(Hvals == H_LAYER)[0][0])
    i_min = int(np.nanargmin(Mx))
    # smallest H where |dMx/dH| <= 1% of its maximum magnitude
    dmax = np.nanmax(np.abs(dMx))
    small = [H for H, d in zip(Hvals, dMx) if abs(d) <= 0.01 * dmax]
    H_flat = small[0] if small else None
    # relative change from H=70 to H=100
    rel70 = (Mx[i70] - Mx[-1]) / Mx[i70] * 100.0
    return {
        "H_argmin": float(Hvals[i_min]),
        "Mx_argmin": float(Mx[i_min]),
        "H_flat_1pct_d": H_flat,
        "Mx_rel_change_70_to_100_pct": float(rel70),
        "dMx_dH_at70": float(dMx[i70]),
        "Mx_at70": float(Mx[i70]),
        "My_at70": float(np.interp(H_LAYER, Hvals, My_home if False else Mx)),  # placeholder replaced below
    }


def main():
    dh, lat, lon = load_dh()
    thx, thy, _, _ = load_buoyancy_gradient_mean()
    uw, vw, _, _, _ = load_winds()

    tau_x, tau_y = wind_stress_large_pond(uw, vw)
    tau_xm = np.nanmean(tau_x, axis=0)
    tau_ym = np.nanmean(tau_y, axis=0)
    stx, sty = load_stored_tau()
    stx_m = np.nanmean(stx, axis=0)
    sty_m = np.nanmean(sty, axis=0)

    Hvals = np.arange(10, 101, 5, dtype=float)

    # Primary: equator = mean of rows 24 (-0.5) and 25 (+0.5), Large & Pond tau
    Mx, My, dMx, dMy = h_sweep(dh, thx, thy, tau_xm, tau_ym, lat, lon, Hvals, [24, 25])
    sMx, sMy, sdMx, sdMy = h_sweep(dh, thx, thy, stx_m, sty_m, lat, lon, Hvals, [24, 25])

    # Sensitivity: single-row equator sampling, LP tau
    sens = {}
    for rows, name in [([24], "row24_lat-0.5"), ([25], "row25_lat+0.5"), ([24, 25], "mean_rows24_25")]:
        M, _, dM, _ = h_sweep(dh, thx, thy, tau_xm, tau_ym, lat, lon, Hvals, rows)
        i70 = int(np.where(Hvals == H_LAYER)[0][0])
        sens[name] = {"argmin_H": float(Hvals[int(np.nanargmin(M))]),
                      "Mx_at70": float(M[i70]),
                      "dMx_dH_at70": float(dM[i70])}

    i70 = int(np.where(Hvals == H_LAYER)[0][0])
    dmax = np.nanmax(np.abs(dMx))
    H_flat = [float(H) for H, d in zip(Hvals, dMx) if abs(d) <= 0.01 * dmax]
    H_flat = H_flat[0] if H_flat else None

    result = {
        "method": "Equatorial momentum residual Eq.11a/b on time-mean fields; "
                  "equator=mean of rows -0.5N/+0.5N; wind stress = Large&Pond from frozen winds",
        "H_vals": Hvals.tolist(),
        "Mx_rms_LP": Mx.tolist(),
        "My_rms_LP": My.tolist(),
        "dMx_dH_LP": dMx.tolist(),
        "dMy_dH_LP": dMy.tolist(),
        "Mx_rms_stored_tau": sMx.tolist(),
        "My_rms_stored_tau": sMy.tolist(),
        "H_argmin_Mx_LP": float(Hvals[int(np.nanargmin(Mx))]),
        "Mx_argmin_LP": float(np.nanmin(Mx)),
        "H_flat_1pct_dMx_LP": H_flat,
        "Mx_at_H70_LP": float(Mx[i70]),
        "My_at_H70_LP": float(My[i70]),
        "dMx_dH_at_H70_LP": float(dMx[i70]),
        "dMy_dH_at_H70_LP": float(dMy[i70]),
        "Mx_rel_change_70_to_100_pct": float((Mx[i70] - Mx[-1]) / Mx[i70] * 100.0),
        "My_rel_change_70_to_100_pct": float((My[i70] - My[-1]) / My[i70] * 100.0),
        "sensitivity_equator_sampling": sens,
    }
    with open(os.path.join(OUT, "c01_H_sweep.json"), "w") as f:
        json.dump(result, f, indent=2)

    # CSV table
    with open(os.path.join(OUT, "c01_H_sweep.csv"), "w") as f:
        f.write("H_m,Mx_rms_LP_ms2,My_rms_LP_ms2,dMx_dH_LP,dMy_dH_LP,Mx_rms_stored_tau_ms2\n")
        for i, H in enumerate(Hvals):
            f.write(f"{H},{Mx[i]:.6e},{My[i]:.6e},{dMx[i]:.6e},{dMy[i]:.6e},{sMx[i]:.6e}\n")

    # Figure
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    axes[0].plot(Hvals, Mx * 1e6, "o-", label="Mx (Large & Pond tau)")
    axes[0].plot(Hvals, My * 1e6, "s--", label="My (Large & Pond tau)")
    axes[0].plot(Hvals, sMx * 1e6, "o:", color="gray", label="Mx (stored tau, ~2pi weak)")
    axes[0].axvline(70, color="r", ls=":", label="H=70 m")
    axes[0].set_xlabel("H (m)")
    axes[0].set_ylabel("RMS residual (1e-6 m s^-2)")
    axes[0].set_title("Equatorial momentum residual vs H")
    axes[0].legend(fontsize=8)
    axes[1].plot(Hvals, dMx * 1e10, "o-", label="dMx/dH (LP tau)")
    axes[1].plot(Hvals, dMy * 1e10, "s--", label="dMy/dH (LP tau)")
    axes[1].axhline(0, color="k", lw=0.5)
    axes[1].axvline(70, color="r", ls=":", label="H=70 m")
    axes[1].set_xlabel("H (m)")
    axes[1].set_ylabel("d(RMS)/dH (1e-10 m^-1 s^-2)")
    axes[1].set_title("Derivative of residual w.r.t. H")
    axes[1].legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "c01_H_sweep.png"), dpi=120)
    plt.close(fig)

    print("C01 results (Large & Pond tau, equator=mean rows -0.5/+0.5):")
    print("  argmin H for ||Mx||:", result["H_argmin_Mx_LP"])
    print("  smallest H with |d||Mx||/dH|<=1% of max:", H_flat)
    print(f"  ||Mx||(H=70) = {result['Mx_at_H70_LP']:.3e}, ||My||(H=70) = {result['My_at_H70_LP']:.3e}")
    print(f"  d||Mx||/dH(H=70) = {result['dMx_dH_at_H70_LP']:.3e}")
    print(f"  ||Mx|| change H70->H100 = {result['Mx_rel_change_70_to_100_pct']:.2f}%")
    print("  equator sampling sensitivity:", sens)
    print("  saved: c01_H_sweep.json, c01_H_sweep.csv, c01_H_sweep.png")


if __name__ == "__main__":
    main()
