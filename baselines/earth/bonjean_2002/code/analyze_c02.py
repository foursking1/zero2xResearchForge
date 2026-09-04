#!/usr/bin/env python3
"""C02 - Equatorial momentum balance: wind stress vs pressure gradient compensation.

Evaluates the balance at H = 70 m on the equator (mean of grid rows -0.5/+0.5):

  M_x(x) = g*z_x - (H/2)*theta_x - (1/H)*tau_x       (zonal residual)
  M_y(x) = -g*z_y + (H/2)*theta_y + (1/H)*tau_y      (meridional residual)

Term decomposition (per unit mass):
  zonal:    P_x = g*z_x                     (pressure gradient, westward where z_x<0)
            B_x = -(H/2)*theta_x            (buoyancy)
            W_x = -(1/H)*tau_x              (wind stress term)
  meridional:
            P_y = -g*z_y
            B_y = (H/2)*theta_y
            W_y = (1/H)*tau_y

Compensation metrics:
  * corr(P_x, W_x) along longitude  (approx -1 for perfect compensation)
  * |W_x|/|P_x| RMS magnitude ratio (approx 1 for perfect compensation)
  * RMS(M_x)/RMS(P_x)               (approx 0 for perfect compensation)

Two wind-stress options: Large & Pond (1981) recomputed from frozen winds
(primary) and the stored tau (documented ~2*pi weak, sensitivity).
"""
import os
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from common import (G, H_LAYER, load_dh, load_winds, load_buoyancy_gradient_mean,
                    load_stored_tau, wind_stress_large_pond, zonal_grad_1d,
                    merid_grad_2d_row)

OUT = os.path.join(os.path.dirname(__file__), "..", "results")
os.makedirs(OUT, exist_ok=True)


def rms(a):
    a = np.asarray(a, dtype=float)
    ok = np.isfinite(a)
    return np.sqrt(np.mean(a[ok] ** 2)) if ok.sum() else np.nan


def equator_terms(dh, thx, thy, tau_xm, tau_ym, lat, lon, H):
    rows = [24, 25]
    z_x = np.nanmean([zonal_grad_1d(dh[i], lat[i], lon) for i in range(dh.shape[0])], axis=0)
    # equatorial row gradient
    z_x_eq = np.nanmean([zonal_grad_1d(dh[i], lat[i], lon) for i in rows], axis=0)
    z_y_eq = np.nanmean([merid_grad_2d_row(dh, i, lat) for i in rows], axis=0)
    thx_eq = np.nanmean([thx[i] for i in rows], axis=0)
    thy_eq = np.nanmean([thy[i] for i in rows], axis=0)
    txe = np.nanmean([tau_xm[i] for i in rows], axis=0)
    tye = np.nanmean([tau_ym[i] for i in rows], axis=0)

    Px = G * z_x_eq
    Bx = -(H / 2) * thx_eq
    Wx = -(1 / H) * txe
    Mx = Px + Bx + Wx

    Py = -G * z_y_eq
    By = (H / 2) * thy_eq
    Wy = (1 / H) * tye
    My = Py + By + Wy
    return Px, Bx, Wx, Mx, Py, By, Wy, My


def compensation_metrics(P, W, M):
    ok = np.isfinite(P) & np.isfinite(W) & np.isfinite(M)
    P, W, M = P[ok], W[ok], M[ok]
    rmsP, rmsW, rmsM = rms(P), rms(W), rms(M)
    return {
        "corr_P_W": float(np.corrcoef(P, W)[0, 1]),
        "rms_P": float(rmsP),
        "rms_W": float(rmsW),
        "rms_M": float(rmsM),
        "ratio_rmsW_rmsP": float(rmsW / rmsP) if rmsP else np.nan,
        "ratio_rmsM_rmsP": float(rmsM / rmsP) if rmsP else np.nan,
        "mean_P": float(np.mean(P)),
        "mean_W": float(np.mean(W)),
        "mean_M": float(np.mean(M)),
        "ratio_meanW_absmeanP": float(np.mean(W) / abs(np.mean(P))) if np.mean(P) else np.nan,
        "ratio_absmeanM_absmeanP": float(abs(np.mean(M)) / abs(np.mean(P))) if np.mean(P) else np.nan,
        "n_valid": int(ok.sum()),
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

    H = H_LAYER

    Px, Bx, Wx, Mx, Py, By, Wy, My = equator_terms(dh, thx, thy, tau_xm, tau_ym, lat, lon, H)
    sPx, sBx, sWx, sMx, sPy, sBy, sWy, sMy = equator_terms(dh, thx, thy, stx_m, sty_m, lat, lon, H)

    zon = compensation_metrics(Px, Wx, Mx)
    mer = compensation_metrics(Py, Wy, My)
    zon_s = compensation_metrics(sPx, sWx, sMx)
    mer_s = compensation_metrics(sPy, sWy, sMy)

    # Interior (away from the eastern boundary / coastal gradients)
    int_ok = np.isfinite(Px) & np.isfinite(Wx) & np.isfinite(Mx) & (lon < 275) & (np.abs(Px) < 3e-6)
    zon_int = compensation_metrics(Px[int_ok], Wx[int_ok], Mx[int_ok])

    result = {
        "H": H,
        "equator": "mean of grid rows -0.5N and +0.5N",
        "wind_stress": "Large & Pond (1981) from frozen CCMP winds (primary)",
        "zonal": zon,
        "meridional": mer,
        "zonal_interior": zon_int,
        "zonal_stored_tau": zon_s,
        "meridional_stored_tau": mer_s,
    }
    with open(os.path.join(OUT, "c02_momentum_balance.json"), "w") as f:
        json.dump(result, f, indent=2)

    # Figure: zonal profiles along the equator
    fig, axes = plt.subplots(2, 1, figsize=(11, 7), sharex=True)
    axes[0].plot(lon, Px * 1e6, label=r"$P_x = g\,\partial_x z$", lw=1.4)
    axes[0].plot(lon, Wx * 1e6, label=r"$W_x = -\tau_x/H$", lw=1.4)
    axes[0].plot(lon, Bx * 1e6, label=r"$B_x = -(H/2)\theta_x$", lw=1.0, ls="--")
    axes[0].plot(lon, Mx * 1e6, label=r"$M_x$ residual", lw=1.8, color="k")
    axes[0].axhline(0, color="gray", lw=0.5)
    axes[0].set_ylabel(r"term (1e-6 m s$^{-2}$)")
    axes[0].set_title("Equatorial zonal momentum balance, H=70 m (Large & Pond tau)")
    axes[0].legend(fontsize=8, ncol=2)
    axes[1].plot(lon, Py * 1e6, label=r"$P_y = -g\,\partial_y z$", lw=1.4)
    axes[1].plot(lon, Wy * 1e6, label=r"$W_y = \tau_y/H$", lw=1.4)
    axes[1].plot(lon, By * 1e6, label=r"$B_y = (H/2)\theta_y$", lw=1.0, ls="--")
    axes[1].plot(lon, My * 1e6, label=r"$M_y$ residual", lw=1.8, color="k")
    axes[1].axhline(0, color="gray", lw=0.5)
    axes[1].set_xlabel("Longitude (°E)")
    axes[1].set_ylabel(r"term (1e-6 m s$^{-2}$)")
    axes[1].set_title("Equatorial meridional momentum balance, H=70 m")
    axes[1].legend(fontsize=8, ncol=2)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "c02_momentum_balance.png"), dpi=120)
    plt.close(fig)

    print("C02 results (H=70 m, Large & Pond tau):")
    print(f"  ZONAL:   corr(P_x,W_x)={zon['corr_P_W']:+.3f}  |W_x|/|P_x|={zon['ratio_rmsW_rmsP']:.3f}"
          f"  rmsM/rmsP={zon['ratio_rmsM_rmsP']:.3f}")
    print(f"           mean P_x={zon['mean_P']:.3e}  mean W_x={zon['mean_W']:.3e}  mean M_x={zon['mean_M']:.3e}"
          f"  |meanW|/|meanP|={zon['ratio_meanW_absmeanP']:.3f}  |meanM|/|meanP|={zon['ratio_absmeanM_absmeanP']:.3f}")
    print(f"  ZONAL interior: corr={zon_int['corr_P_W']:+.3f}  |W|/|P|={zon_int['ratio_rmsW_rmsP']:.3f}"
          f"  |meanW|/|meanP|={zon_int['ratio_meanW_absmeanP']:.3f}")
    print(f"  MERID:   corr(P_y,W_y)={mer['corr_P_W']:+.3f}  |W_y|/|P_y|={mer['ratio_rmsW_rmsP']:.3f}"
          f"  rmsM/rmsP={mer['ratio_rmsM_rmsP']:.3f}")
    print(f"  (stored tau) ZONAL: corr={zon_s['corr_P_W']:+.3f} ratio={zon_s['ratio_rmsW_rmsP']:.3f}")
    print("  saved: c02_momentum_balance.json, c02_momentum_balance.png")


if __name__ == "__main__":
    main()
