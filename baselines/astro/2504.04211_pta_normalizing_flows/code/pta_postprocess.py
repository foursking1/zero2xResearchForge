# -*- coding: utf-8 -*-
"""Post-process PTA run outputs: robust figures + IS-based BF consistency.

The main run_pta.py writes metrics.json / evidence_table.csv but its figure
routine crashes on the degenerate importance weights (neff ~ 1, fewer non-zero
entries than the requested draw).  This script:
  1. reads results/metrics.json and code/cache_smoke/post_*.npz
  2. recomputes an IS-based Bayes-factor consistency table (NF vs MCMC)
  3. regenerates figure.svg (posterior comparison) and figure_logz.svg
     (evidence comparison using the IS estimator) robustly
  4. rewrites metrics.json with corrected protocol note + BF-consistency metrics
"""
import os
import csv
import json
import sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUTDIR = os.path.normpath(os.path.join(HERE, "..", "results"))
CACHE = os.path.join(HERE, "cache_smoke")
MODELS = ["PowerLaw", "SMBHB", "DW"]

with open(os.path.join(OUTDIR, "metrics.json")) as f:
    M = json.load(f)

pm = M["per_model"]
logZ_mcmc = {m: pm[m]["logZ_mcmc_hme"] for m in MODELS}
logZ_nf_is = {m: pm[m]["logZ_nf_is"] for m in MODELS}

# ---- IS-based Bayes-factor consistency (ln BF, PowerLaw reference) ----
bf_mcmc = {a: {b: logZ_mcmc[a] - logZ_mcmc[b] for b in MODELS} for a in MODELS}
bf_nfis = {a: {b: logZ_nf_is[a] - logZ_nf_is[b] for b in MODELS} for a in MODELS}

pairs = [(a, b) for a in MODELS for b in MODELS if a != b]
pair_diffs = {f"{a}/{b}": abs(bf_mcmc[a][b] - bf_nfis[a][b]) for a, b in pairs}
max_lnbf_diff = max(pair_diffs.values())
n_within_1 = sum(1 for v in pair_diffs.values() if v <= 1.0)
frac_within_1 = n_within_1 / len(pair_diffs)

def rank(d):
    return {m: i for i, m in enumerate(sorted(d, key=lambda x: d[x], reverse=True))}
rk_m, rk_n = rank(logZ_mcmc), rank(logZ_nf_is)
rank_consistent = all(rk_m[m] == rk_n[m] for m in MODELS)

# ---- timing ----
t_mcmc = {m: pm[m]["time_mcmc_s"] for m in MODELS}
t_nf_train = {m: pm[m]["time_train_s"] for m in MODELS}
t_nf_eval = {m: pm[m]["time_eval_s"] for m in MODELS}
t_nf_total = {m: pm[m]["time_train_s"] + pm[m]["time_eval_s"] for m in MODELS}
speedup = {m: t_mcmc[m] / t_nf_total[m] for m in MODELS}

# ---- Hellinger ----
H_direct = {m: pm[m]["Hellinger_direct_vs_mcmc"] for m in MODELS}
H_reweight = {m: pm[m]["Hellinger_reweighted_vs_mcmc"] for m in MODELS}
mean_H_direct = float(np.mean(list(H_direct.values())))
mean_H_reweight = float(np.mean(list(H_reweight.values())))

# ---- evidence_table.csv with ln-BF columns (IS estimator for NF) ----
with open(os.path.join(OUTDIR, "evidence_table.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["SGWB_model", "Hellinger_direct", "Hellinger_reweighted",
                "logZ_MCMC_HME", "logZ_NF_HME", "logZ_NF_IS",
                "lnBF_vs_PL_MCMC", "lnBF_vs_PL_NF_IS",
                "time_MCMC_s", "time_NF_train_s", "time_NF_eval_s"])
    for m in MODELS:
        r = pm[m]
        w.writerow([m, f"{r['Hellinger_direct_vs_mcmc']:.4f}",
                    f"{r['Hellinger_reweighted_vs_mcmc']:.4f}",
                    f"{r['logZ_mcmc_hme']:.3f}", f"{r['logZ_nf_hme']:.3f}",
                    f"{r['logZ_nf_is']:.3f}",
                    f"{bf_mcmc[m]['PowerLaw']:.3f}",
                    f"{bf_nfis[m]['PowerLaw']:.3f}",
                    f"{r['time_mcmc_s']:.1f}", f"{r['time_train_s']:.1f}",
                    f"{r['time_eval_s']:.1f}"])

# ---- figures ----
def robust_reweight_sample(w, n=3000, seed=0):
    """Sample indices with probability p, tolerating degenerate p."""
    rng = np.random.default_rng(seed)
    n = min(n, len(w))
    ww = np.asarray(w, dtype=float)
    if ww.sum() <= 0:
        return rng.choice(len(ww), size=n, replace=True)
    p = ww / ww.sum()
    nz = np.count_nonzero(p > 0)
    if nz >= n:
        return rng.choice(len(ww), size=n, replace=False, p=p)
    return rng.choice(len(ww), size=n, replace=True, p=p)


def make_figs():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, len(MODELS), figsize=(5.5 * len(MODELS), 4.6),
                             constrained_layout=True)
    for ax, m in zip(axes, MODELS):
        d = np.load(os.path.join(CACHE, f"post_{m}.npz"))
        mcmc_sg = d["mcmc_sg"]
        nf_sg = d["nf_sg"]
        w = d["w"]
        ax.scatter(nf_sg[::5, 0], nf_sg[::5, 1], s=2, alpha=0.15, c="tab:blue",
                   label="NF direct")
        ax.scatter(mcmc_sg[::2, 0], mcmc_sg[::2, 1], s=2, alpha=0.2, c="tab:red",
                   label="MCMC")
        idx = robust_reweight_sample(w, n=3000, seed=0)
        ax.scatter(nf_sg[idx, 0], nf_sg[idx, 1], s=2, alpha=0.4, c="tab:green",
                   label="NF reweighted")
        ax.set_xlabel("SGWB log10 A"); ax.set_ylabel("SGWB gamma")
        ax.set_title(m, fontsize=12)
        ax.legend(fontsize=7, loc="upper right")
    fig.suptitle("Posterior comparison (SGWB marginal): MCMC vs NF (frozen NG15, 10 pulsars)")
    fig.savefig(os.path.join(OUTDIR, "figure.svg"), dpi=150)
    plt.close(fig)

    # evidence comparison: MCMC (HME) vs NF (IS)
    fig, ax = plt.subplots(figsize=(4.5, 4.2))
    xs = [logZ_mcmc[m] for m in MODELS]
    ys = [logZ_nf_is[m] for m in MODELS]
    ax.plot(xs, ys, "o-")
    for i, m in enumerate(MODELS):
        ax.annotate(m, (xs[i], ys[i]))
    lo = min(xs + ys) - 1.0
    hi = max(xs + ys) + 1.0
    ax.plot([lo, hi], [lo, hi], "k--", lw=0.8)
    ax.set_xlabel("logZ MCMC (truncated HME)")
    ax.set_ylabel("logZ NF (importance sampling)")
    ax.set_title("Evidence comparison (IS estimator)")
    fig.tight_layout()
    fig.savefig(os.path.join(OUTDIR, "figure_logz.svg"), dpi=150)
    plt.close(fig)


make_figs()

# ---- update metrics.json ----
M["note"] = ("Hellinger computed on the 2-dim SGWB marginal (params dims 20,21; "
             "paper Appendix H uses the full 22-dim, mean reweighted 0.2611). "
             "NF trained at reduced scale (15000 forward sims x 40 epochs vs "
             "paper 2e5 x 50). Learned-HME evidence for the NF fails (neff~1-2/8000: "
             "proposal under-covers the target), so NF evidence is reported via the "
             "importance-sampling (IS) estimator, an equivalent evidence estimator "
             "allowed by the task. MCMC reference = emcee + truncated harmonic mean "
             "(keep highest 90% likelihood).")
M["Hellinger_mean_direct"] = mean_H_direct
M["Hellinger_mean_reweighted"] = mean_H_reweight
M["Hellinger_per_model_reweighted"] = H_reweight
M["bf_consistency_IS"] = {
    "method": "ln BF from logZ_MCMC_HME vs logZ_NF_IS (PowerLaw reference)",
    "bf_mcmc_ln": {m: bf_mcmc[m]["PowerLaw"] for m in MODELS},
    "bf_nf_is_ln": {m: bf_nfis[m]["PowerLaw"] for m in MODELS},
    "per_pair_abs_ln_diff": {k: float(v) for k, v in pair_diffs.items()},
    "max_abs_ln_diff": float(max_lnbf_diff),
    "n_pairs_within_1": int(n_within_1),
    "frac_pairs_within_1": float(frac_within_1),
    "rank_consistent_MCMC_vs_NF_IS": bool(rank_consistent),
}
M["timing"] = {
    "MCMC_s_per_model": t_mcmc,
    "NF_train_s_per_model": t_nf_train,
    "NF_eval_s_per_model": t_nf_eval,
    "NF_total_s_per_model": t_nf_total,
    "speedup_MCMC_over_NF_total": speedup,
    "note": "10-pulsar subset; paper ~20h/model (NF) vs ~10d/68-pulsar (MCMC). "
            "Our reduced MCMC (48 walkers x 1200 steps) is not the paper's full run.",
}
M["data_ntoa"] = M.get("data_ntoa", 4944)
M["data_Tobs_days"] = M.get("data_Tobs_days", 5724.3)

with open(os.path.join(OUTDIR, "metrics.json"), "w") as f:
    json.dump(M, f, indent=2, default=float)

print("PTA post-process done.")
print(f"  Hellinger reweighted: {H_reweight}")
print(f"  mean reweighted: {mean_H_reweight:.4f}")
print(f"  BF IS rank consistent: {rank_consistent}")
print(f"  max |lnBF diff|: {max_lnbf_diff:.2f}; pairs within 1: {n_within_1}/{len(pairs)}")
print(f"  speedup MCMC/NF-total: {speedup}")
