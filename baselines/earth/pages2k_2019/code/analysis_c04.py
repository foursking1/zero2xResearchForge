"""C04 - Unforced variability from D&A residuals consistent with control
simulation variability.

Uses the authors' pre-computed D&A products in DandA_CESM_ens_30-200_1318.RData:
  * da.cesm.all.ens.14.30.200.resid  : 7000 residual-based unforced variability
                                       estimates (one per reconstruction member)
  * models.ctl.var.30.200            : 42 pre-industrial control-run variability
                                       estimates

We also cross-check against an independently computed control variance from the
raw control runs (Models_ctrl_GMST_AprMar.RData), reported separately.
"""
from __future__ import annotations

import numpy as np
import json
import os
from scipy import stats

from common import load_danda, load_control_runs, bandpass_fft

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "results")


def main():
    d = load_danda()
    resid = d["resid"]          # 7000
    ctl_var = d["ctl_var"]      # 42

    # ------- primary comparison (authors' pre-computed quantities) --------
    within = (resid >= ctl_var.min()) & (resid <= ctl_var.max())
    frac_within = float(within.mean())
    med_ratio = float(np.median(resid) / np.median(ctl_var))
    amp_ratio = float(np.sqrt(np.median(resid)) / np.sqrt(np.median(ctl_var)))
    ks = stats.ks_2samp(resid, ctl_var)

    # percentile of each residual estimate relative to the control distribution
    ctl_sorted = np.sort(ctl_var)
    pct_in_ctl = np.searchsorted(ctl_sorted, resid, side="right") / len(ctl_sorted)

    results = {
        "n_residual_estimates": int(len(resid)),
        "n_control_estimates": int(len(ctl_var)),
        "residual_variance_median": float(np.median(resid)),
        "control_variance_median": float(np.median(ctl_var)),
        "fraction_residual_within_control_range": frac_within,
        "median_ratio_resid_over_control": med_ratio,
        "amplitude_ratio_resid_over_control": amp_ratio,   # sqrt(variance) ratio
        "residual_variance_range": [float(resid.min()), float(resid.max())],
        "control_variance_range": [float(ctl_var.min()), float(ctl_var.max())],
        "ks_test": {"statistic": float(ks.statistic), "pvalue": float(ks.pvalue)},
        "residual_pct_of_control_dist": {
            "median": float(np.median(pct_in_ctl)),
            "p10": float(np.percentile(pct_in_ctl, 10)),
            "p90": float(np.percentile(pct_in_ctl, 90)),
        },
        "note": "resid and ctl_var are the authors' pre-computed 30-200 yr "
                "band-pass variance estimates (same pipeline -> same scale).",
    }

    # ------- independent cross-check on raw control runs (ctl.ama) --------
    ctl, ctl_names = load_control_runs()
    ind_var = []
    for j in range(ctl.shape[1]):
        seg = ctl[:, j]
        seg = seg[~np.isnan(seg)]
        if len(seg) < 500:
            continue
        bp = bandpass_fft(seg)
        # trim 100 yr at each edge to limit filter edge effects
        mid = bp[100:-100]
        ind_var.append(float(mid.var()))
    ind_var = np.array(ind_var)
    results["independent_control_variance_crosscheck"] = {
        "n_segments": int(len(ind_var)),
        "median": float(np.median(ind_var)) if len(ind_var) else None,
        "range": [float(ind_var.min()), float(ind_var.max())] if len(ind_var) else None,
        "note": "independently computed variance of 30-200 yr band-passed ctl.ama "
                "segments (degC**2, Kelvin data minus ~273). Different scale from "
                "authors' ctl_var (which includes a pipeline-specific scaling).",
    }

    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "c04_results.json"), "w") as f:
        json.dump(results, f, indent=2)

    print("=== C04 ===")
    print(f"n_resid={len(resid)}  n_ctl={len(ctl_var)}")
    print(f"resid median {np.median(resid):.3f}  ctl median {np.median(ctl_var):.3f}")
    print(f"fraction resid within ctl range: {frac_within:.4f}")
    print(f"median ratio resid/ctl: {med_ratio:.3f}  amplitude ratio: {amp_ratio:.3f}")
    print(f"KS p={ks.pvalue:.3f}")
    print(f"independent ctl var: n={len(ind_var)} median={np.median(ind_var):.5f}")


if __name__ == "__main__":
    main()
