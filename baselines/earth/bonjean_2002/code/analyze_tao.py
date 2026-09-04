#!/usr/bin/env python3
"""Supplementary: TAO mooring validation of the diagnostic model.

Pearson correlation and mean bias of the model 0-30 m layer velocity against
the four equatorial TAO 10 m current meters (165E, 170W, 140W, 110W), using the
frozen model_tao_comparison.nc (model bilinearly interpolated to the equator).

Context for C03: how well does the diagnostic velocity track the observed
equatorial currents?  (Paper reports r ~ 0.62-0.76 at these sites.)
"""
import os
import json
import numpy as np
import netCDF4 as nc4
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from common import path

OUT = os.path.join(os.path.dirname(__file__), "..", "results")
os.makedirs(OUT, exist_ok=True)


def main():
    ds = nc4.Dataset(path("model_tao_comparison.nc"))
    u_model = ds.variables["u_model"][:]
    v_model = ds.variables["v_model"][:]
    u_obs = ds.variables["u_obs"][:]
    v_obs = ds.variables["v_obs"][:]
    site = ds.variables["site"][:]
    ds.close()

    names = [str(s) for s in site]
    out = {"site": names}
    for i, name in enumerate(names):
        um = u_model[:, i]
        uo = u_obs[:, i]
        vm = v_model[:, i]
        vo = v_obs[:, i]
        ok = np.isfinite(um) & np.isfinite(uo)
        r = float(np.corrcoef(um[ok], uo[ok])[0, 1]) if ok.sum() > 2 else np.nan
        bias = float(np.nanmean(um - uo))
        rms = float(np.sqrt(np.nanmean((um[ok] - uo[ok]) ** 2)))
        okv = np.isfinite(vm) & np.isfinite(vo)
        rv = float(np.corrcoef(vm[okv], vo[okv])[0, 1]) if okv.sum() > 2 else np.nan
        out[f"u_corr_{name}"] = r
        out[f"v_corr_{name}"] = rv
        out[f"u_bias_{name}_m_s"] = bias
        out[f"u_rms_{name}_m_s"] = rms
        out[f"n_{name}"] = int(ok.sum())

    with open(os.path.join(OUT, "tao_validation.json"), "w") as f:
        json.dump(out, f, indent=2)

    fig, axes = plt.subplots(4, 1, figsize=(10, 9), sharex=True)
    t = np.arange(u_model.shape[0])
    for i, name in enumerate(names):
        axes[i].plot(t, u_model[:, i], "b-", lw=0.8, label="model (0-30m)")
        axes[i].plot(t, u_obs[:, i], "r-", lw=0.8, alpha=0.8, label="TAO 10m")
        axes[i].set_ylabel(name)
        axes[i].legend(fontsize=7, loc="upper right")
    axes[-1].set_xlabel("10-day time step (Oct 1992 - Jul 2000)")
    axes[0].set_title("Zonal velocity: diagnostic model vs TAO moorings")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "tao_validation.png"), dpi=110)
    plt.close(fig)

    print("TAO validation (model 0-30m vs TAO 10m):")
    for i, name in enumerate(names):
        print(f"  {name}: r_u={out[f'u_corr_{name}']:.3f}  r_v={out[f'v_corr_{name}']:.3f}  "
              f"bias_u={out[f'u_bias_{name}_m_s']:.3f} m/s  rms_u={out[f'u_rms_{name}_m_s']:.3f} m/s  "
              f"n={out[f'n_{name}']}")
    print("  saved: tao_validation.json, tao_validation.png")


if __name__ == "__main__":
    main()
