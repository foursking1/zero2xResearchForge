"""C04: Unforced variability from D&A residuals vs control simulations.

Reproduces the paper's D&A residual analysis (Fig. 3b; Methods
"Detection and Attribution"):

  - D&A total-forcing residuals: da.cesm.all.ens.14.30.200.resid (7000,).
  - Unforced variability estimate = sqrt(resid / 499)  (sum-of-squares
    residual / degrees of freedom; the smallest SVD eigenvalue).
  - Control-run estimates = sqrt(models.ctl.var.30.200 / 499) (42 precomputed
    slices of the piControl runs; the paper text states n2 = 43).
  - "99% of estimates based on the D&A residuals are within the 95% range of
    control simulations" (paper p. 7/8; Methods gives 98.7%, n1 = 7000).
  - Also compute the D&A scaling factors (total forcing, median ~0.89) and
    the low-forced-period (850-1100) bandpass sd for context.
"""
import json
import os
import numpy as np

from load_data import load_danda, load_recon_ensembles, load_models_fullforced, load_models_control
from filters import bandpass_tsc_na

METHODS = ["CPS", "PCR", "M08", "PAI", "OIE", "BHM", "DA"]
DOF = 499  # degrees of freedom used in the D&A residual variance estimate


def main():
    da_all, da_volc, resid, ctl_var = load_danda()
    n1 = resid.size
    n2 = ctl_var.size
    print("=== C04: D&A residual vs control unforced variability ===")
    print(f"n1 (D&A residual estimates) = {n1}   (paper: 7000, R29)")
    print(f"n2 (control run estimates)  = {n2}   (paper text: 43, R30)  <- frozen RData has {n2}")

    da_sd = np.sqrt(resid / DOF)          # (7000,)
    ctl_sd = np.sqrt(ctl_var / DOF)       # (42,)
    print(f"\nD&A residual stddev: median = {np.median(da_sd):.4f} degC, "
          f"[5-95%: {np.percentile(da_sd,5):.4f}-{np.percentile(da_sd,95):.4f}]  (paper R28: ~0.045)")
    print(f"control stddev: median = {np.median(ctl_sd):.4f} degC, "
          f"[5-95%: {np.percentile(ctl_sd,5):.4f}-{np.percentile(ctl_sd,95):.4f}]")

    # fraction of D&A residual estimates within the 5-95% range of control estimates
    lo, hi = np.percentile(ctl_sd, 5), np.percentile(ctl_sd, 95)
    frac = np.mean((da_sd >= lo) & (da_sd <= hi))
    print(f"\nR27: fraction of D&A residual estimates within control 5-95% range "
          f"[{lo:.4f}, {hi:.4f}] = {frac:.3f}   (paper: 0.99 / 98.7%)")

    # median residual per method (context, matches paper's da.cesm.30.200.resid.medians)
    resid_med = np.array([np.median(resid[k*1000:(k+1)*1000]) for k in range(7)])
    print("\nmedian D&A residual per method:", np.round(resid_med, 4))
    print("median residual sd per method:", np.round(np.sqrt(resid_med/DOF), 4))

    # D&A scaling factors (total forcing): da_all (1001, 7000)
    sf_med = np.median(da_all, axis=0)
    sf_lo, sf_hi = np.percentile(da_all, 5, axis=0), np.percentile(da_all, 95, axis=0)
    print(f"\nTotal-forcing D&A scaling factor (1001 MC samples x 7000 members):")
    print(f"  full-ensemble median = {np.median(sf_med):.3f}   (paper: 0.89)")
    # per-method medians
    for k, m in enumerate(METHODS):
        blk = da_all[:, k*1000:(k+1)*1000]
        print(f"  {m}: median = {np.median(blk):.3f}, "
              f"5-95% = [{np.percentile(blk,5):.3f}, {np.percentile(blk,95):.3f}]")

    # Low-forced-period (850-1100) bandpass sd of recons and models (Fig 3b right)
    print("\n=== Low-forced period (850-1100) bandpass sd (Fig 3b right) ===")
    recons = load_recon_ensembles()
    years = recons["CPS"][0]
    lf = (years >= 851) & (years <= 1100)
    recon_sd = []
    for k, m in enumerate(METHODS):
        d = recons[m][1]
        bp = np.full_like(d, np.nan)
        for i in range(d.shape[1]):
            bp[:, i] = bandpass_tsc_na(d[:, i], 30, 200, cut_end=False, end_m="pad")
        recon_sd.append(np.median(np.std(bp[lf], axis=0)))
    myears, mdata, mnames = load_models_fullforced()
    mwin = (myears >= 851) & (myears <= 1100)
    mod_w = mdata[mwin]
    bpm = np.full_like(mod_w, np.nan)
    for j in range(mod_w.shape[1]):
        bpm[:, j] = bandpass_tsc_na(mod_w[:, j], 30, 200, cut_end=False, end_m="pad")
    model_sd = np.array([np.nanstd(bpm[:, j]) for j in range(mod_w.shape[1])])
    print(f"median recon bandpass sd (850-1100): {np.median(recon_sd):.4f}")
    print(f"median model bandpass sd (850-1100): {np.median(model_sd):.4f}")

    # --- Save ---
    os.makedirs("results", exist_ok=True)
    out = {
        "n_da_residual": int(n1),
        "n_control": int(n2),
        "da_residual_sd_median": float(np.median(da_sd)),
        "da_residual_sd_q05": float(np.percentile(da_sd, 5)),
        "da_residual_sd_q95": float(np.percentile(da_sd, 95)),
        "control_sd_median": float(np.median(ctl_sd)),
        "control_sd_q05": float(np.percentile(ctl_sd, 5)),
        "control_sd_q95": float(np.percentile(ctl_sd, 95)),
        "frac_within_control_95": float(frac),
        "total_forcing_sf_median": float(np.median(sf_med)),
        "low_forced_recon_sd_median": float(np.median(recon_sd)),
        "low_forced_model_sd_median": float(np.median(model_sd)),
        "dof": DOF,
    }
    with open("results/c04_metrics.json", "w") as f:
        json.dump(out, f, indent=2, sort_keys=True)
    print("\nsaved results/c04_metrics.json")


if __name__ == "__main__":
    main()
