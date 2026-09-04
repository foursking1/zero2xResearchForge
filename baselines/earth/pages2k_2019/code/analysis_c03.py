"""C03 - Model/data variance ratios and correlations (band-pass 30-200 yr,
1000-2000 CE).

Two reconstruction representations are used:
  A) each ensemble member (1000 members x 3 methods), all (model, member) pairs
  B) deterministic ensemble-mean reconstruction per method

Both are compared to each of the 23 full-forced past1000 model runs.
The paper's reported medians are listed alongside for reference (marked as
paper values).  Because only 3 of 7 methods are in the frozen bundle, the
"all 7 methods" claim cannot be fully checked.
"""
from __future__ import annotations

import numpy as np
import json
import os

from common import (load_reconstructions, load_models_fullforced, METHODS,
                    METHOD_SLICES, bandpass_fft)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "results")

MODEL_YR0 = 851
# paper values (Neukom et al. 2019, Fig. 2) - clearly marked as citations
PAPER_VAR_RATIO = {"CPS": 0.96, "PCR": 1.01, "PAI": 0.63}
PAPER_CORR = {"CPS": 0.64, "PCR": 0.60, "PAI": 0.63}


def main():
    a = load_reconstructions()
    models, model_names = load_models_fullforced()

    recon_sl = slice(999, 2000)                                # 1000-2000 CE
    model_sl = slice(1000 - MODEL_YR0, 2000 - MODEL_YR0 + 1)   # rows 149..1149

    bp_members = np.empty_like(a)
    for j in range(a.shape[1]):
        bp_members[:, j] = bandpass_fft(a[:, j])
    recon_bp = bp_members[recon_sl, :]                          # (1001, 3000)

    model_bp = np.empty_like(models)
    for j in range(models.shape[1]):
        col = models[:, j]
        if np.isnan(col).any():
            col = np.nan_to_num(col, nan=np.nanmean(col))
        model_bp[:, j] = bandpass_fft(col)
    model_bp_win = model_bp[model_sl, :]
    ok = ~np.isnan(models[model_sl, :]).any(axis=0)
    model_bp_win = model_bp_win[:, ok]
    n_mod = int(ok.sum())

    model_var = model_bp_win.var(axis=0)                        # (n_mod,)

    results = {"methods_available": METHODS, "period": "1000-2000 CE",
               "filter": "FFT brick-wall band-pass 30-200 yr applied to full series"}

    # ---- representation A: all (model, member) pairs ----
    A = {}
    all_ratios, all_corrs = [], []
    for m, sl in METHOD_SLICES.items():
        members = recon_bp[:, sl]                               # (1001, 1000)
        mvar = members.var(axis=0)
        ratios = model_var[:, None] / mvar[None, :]
        ratios_flat = ratios.ravel()
        corrs = np.zeros((n_mod, 1000))
        for i in range(n_mod):
            xi = model_bp_win[:, i]
            for j in range(1000):
                corrs[i, j] = np.corrcoef(xi, members[:, j])[0, 1]
        corrs_flat = corrs.ravel()
        all_ratios.append(ratios_flat)
        all_corrs.append(corrs_flat)
        A[m] = {
            "variance_ratio_median": float(np.median(ratios_flat)),
            "variance_ratio_p25": float(np.percentile(ratios_flat, 25)),
            "variance_ratio_p75": float(np.percentile(ratios_flat, 75)),
            "correlation_median": float(np.median(corrs_flat)),
            "correlation_p5": float(np.percentile(corrs_flat, 5)),
            "correlation_p95": float(np.percentile(corrs_flat, 95)),
            "n_pairs": int(len(ratios_flat)),
            "paper_variance_ratio_median": PAPER_VAR_RATIO[m],
            "paper_correlation_median": PAPER_CORR[m],
        }
    results["per_member_pairs"] = A
    results["per_member_pairs"]["overall_variance_ratio_median"] = float(np.median(np.concatenate(all_ratios)))
    results["per_member_pairs"]["overall_correlation_median"] = float(np.median(np.concatenate(all_corrs)))
    results["per_member_pairs"]["paper_overall_variance_ratio_median"] = 1.01
    results["per_member_pairs"]["n_model_runs_used"] = int(n_mod)

    # ---- representation B: deterministic ensemble-mean reconstruction ----
    B = {}
    for m, sl in METHOD_SLICES.items():
        s = recon_bp[:, sl].mean(axis=1)                        # ensemble mean
        corrs = np.array([np.corrcoef(model_bp_win[:, i], s)[0, 1] for i in range(n_mod)])
        ratios = model_var / s.var()
        B[m] = {
            "variance_ratio_median": float(np.median(ratios)),
            "correlation_median": float(np.median(corrs)),
            "recon_signal_variance": float(s.var()),
        }
    results["deterministic_ensemble_mean"] = B

    # ---- significance fraction: naive 95% threshold |r|>0.19 (see note) ----
    all_corrs_all = np.concatenate(all_corrs)
    for m in METHODS:
        sl = METHOD_SLICES[m]
        corrs_m = np.concatenate(all_corrs)[:0]  # placeholder, replaced below
    # recompute per-method correlation arrays for the fraction
    for m, sl in METHOD_SLICES.items():
        members = recon_bp[:, sl]
        cvals = np.array([np.corrcoef(model_bp_win[:, i], members[:, j])[0, 1]
                          for i in range(n_mod) for j in range(1000)])
        A[m]["fraction_pairs_abs_corr_gt_0.19"] = float((np.abs(cvals) > 0.19).mean())
    results["significance_note"] = ("naive |r|>0.19 approximates the 95% level only for "
                                    "~25 independent (effective) degrees of freedom; "
                                    "band-passed series are autocorrelated so true dof are "
                                    "much lower.")

    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "c03_results.json"), "w") as f:
        json.dump(results, f, indent=2)

    print("=== C03 (member-pair medians) ===")
    for m in METHODS:
        r = A[m]
        print(f"{m}: ratio {r['variance_ratio_median']:.3f} [paper {r['paper_variance_ratio_median']}]  "
              f"corr {r['correlation_median']:.3f} [paper {r['paper_correlation_median']}]")
    print("overall ratio:", round(results["per_member_pairs"]["overall_variance_ratio_median"], 3),
          "[paper 1.01]")
    print("=== C03 (deterministic ensemble mean) ===")
    for m in METHODS:
        print(f"{m}: ratio {B[m]['variance_ratio_median']:.3f}  corr {B[m]['correlation_median']:.3f}")


if __name__ == "__main__":
    main()
