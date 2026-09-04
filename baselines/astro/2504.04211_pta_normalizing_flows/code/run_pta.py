# -*- coding: utf-8 -*-
"""End-to-end PTA NF-vs-MCMC verification (arXiv:2504.04211).

Pipeline (forward-simulation / amortised-inference protocol, paper Sec.III):
  1. Load the real NG15 ToA grid + white-noise levels + sky positions
     (frozen data, 10 pulsars, 4944 active ToAs).
  2. Build the 22-dim Gaussian joint likelihood (marginalised Fourier
     coefficients, Woodbury) for 3 SGWB spectral models (PowerLaw, SMBHB, DW).
  3. Draw ONE reference realisation r0 under a PowerLaw injection theta_true.
  4. MCMC reference (emcee) for each model on r0.
  5. Train a conditional RealNVP for each model on forward-simulated
     (theta, summary=(b,c)) pairs; summary = exact sufficient statistics.
  6. Evaluate on r0:
       - direct NF posterior samples   (amortised)
       - reweighted NF samples (self-normalised IS, paper Eq.G1)
       - Hellinger distance vs MCMC on the 2-dim SGWB marginal
       - evidence via truncated harmonic mean (keep highest 90% likelihood)
         for both MCMC and NF  -> Bayes factors
  7. Timing (train+inference per model) + hardware report.

All random numbers are seeded; intermediate chains/models are cached to disk.
"""
import os
import sys
import csv
import json
import time
import argparse
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import pta_data
import pta_likelihood as pl
import pta_nf
import pta_hellinger as ph

MODELS = ["PowerLaw", "SMBHB", "DW"]
INJECT = {"logA_gw": -15.0, "gamma_gw": 5.0}
RED_A = -15.5
RED_GAMMA = 4.0


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--nwalkers", type=int, default=48)
    p.add_argument("--nsteps", type=int, default=1200)
    p.add_argument("--burn", type=int, default=300)
    p.add_argument("--n_train", type=int, default=50000)
    p.add_argument("--n_epochs", type=int, default=30)
    p.add_argument("--n_eval", type=int, default=12000)
    p.add_argument("--batch", type=int, default=256)
    p.add_argument("--seed", type=int, default=20250817)
    p.add_argument("--models", type=str, default="PowerLaw,SMBHB,DW")
    p.add_argument("--outdir", type=str, default=os.path.normpath(os.path.join(HERE, "..", "results")))
    p.add_argument("--cache", type=str, default=os.path.join(HERE, "cache"))
    p.add_argument("--skip_mcmc", action="store_true", help="load cached MCMC chains if present")
    return p.parse_args()


# ----------------------------------------------------------------------------
# helpers
# ----------------------------------------------------------------------------
def theta_true(model_name):
    lo, hi = pl.PTAJointLikelihood.prior_ranges(model_name)
    th = np.zeros(22)
    th[0:10] = RED_A
    th[10:20] = RED_GAMMA
    th[20] = INJECT["logA_gw"]
    th[21] = INJECT["gamma_gw"]
    return np.clip(th, lo, hi)


def scale01(theta, lo, hi):
    return (theta - lo) / (hi - lo)


def unscale01(theta_u, lo, hi):
    return lo + theta_u * (hi - lo)


def make_logpost(lik, precomp, lo, hi):
    def lp(theta):
        if np.any(theta < lo) or np.any(theta > hi):
            return -np.inf
        ll = lik.loglike(theta, precomputed=precomp)
        if not np.isfinite(ll):
            return -np.inf
        return ll + lik.prior_logp(theta, lo, hi)
    return lp


def build_context(lik, r):
    d = lik.prepare_data(r)
    return np.concatenate([d["b"], [d["c"]]]).astype(np.float32)


def logsumexp(x):
    m = np.max(x)
    return m + np.log(np.sum(np.exp(x - m)))


def truncated_hme_logz(loglike, frac_discard=0.10):
    ll = np.asarray(loglike, dtype=float)
    ll = ll[np.isfinite(ll)]
    if len(ll) == 0:
        return -np.inf
    n_keep = int(np.round((1.0 - frac_discard) * len(ll)))
    n_keep = max(n_keep, 1)
    ll = np.sort(ll)[-n_keep:]
    return -logsumexp(-ll) + np.log(n_keep)


def is_logz(loglike, logprior, logq, jac_const):
    ll = np.asarray(loglike, dtype=float)
    lp = np.asarray(logprior, dtype=float)
    lq = np.asarray(logq, dtype=float)
    ok = np.isfinite(ll) & np.isfinite(lp) & np.isfinite(lq)
    if ok.sum() == 0:
        return -np.inf
    return logsumexp(ll[ok] + lp[ok] - lq[ok]) - np.log(ok.sum()) + jac_const


def effective_n(w):
    s = w.sum()
    return float(s * s / np.sum(w * w))


# ----------------------------------------------------------------------------
# MCMC
# ----------------------------------------------------------------------------
def run_mcmc(lik, precomp, lo, hi, model_name, args, cache_path):
    import emcee
    from scipy.optimize import minimize

    if args.skip_mcmc and os.path.exists(cache_path):
        data = np.load(cache_path)
        print(f"  [mcmc] loading cached chain {cache_path}")
        return data["chain"], data["loglike"], data["t_mcmc"], data["accept"]

    logpost = make_logpost(lik, precomp, lo, hi)

    def nll(th):
        v = logpost(th)
        return -v if np.isfinite(v) else 1e20

    x0 = np.clip(0.5 * (lo + hi), lo + 1e-6, hi - 1e-6)
    res = minimize(nll, x0, method="Nelder-Mead",
                   options={"maxiter": 500, "xatol": 1e-3, "fatol": 1e-3})
    xbest = np.clip(res.x, lo + 1e-6, hi - 1e-6)
    print(f"  [mcmc] opt logpost {logpost(x0):.1f} -> {logpost(xbest):.1f}")

    rng = np.random.default_rng(args.seed)
    ndim = 22
    # spread walkers by a fraction of the prior width per dimension so the
    # initial ensemble covariance is well-conditioned (emcee requirement)
    scale = np.maximum(0.01 * (hi - lo), 1e-3)
    x0s = np.clip(xbest + scale[None, :] * rng.standard_normal((args.nwalkers, ndim)),
                  lo + 1e-6, hi - 1e-6)

    sampler = emcee.EnsembleSampler(args.nwalkers, ndim, logpost)
    t0 = time.time()
    sampler.run_mcmc(x0s, args.nsteps, progress=False)
    t_mcmc = time.time() - t0

    chain = sampler.get_chain()
    logp = sampler.get_log_prob()
    # loglike = logpost - prior_logp (free, no extra likelihood evals)
    loglike = np.empty_like(logp)
    for i in range(args.nwalkers):
        for j in range(args.nsteps):
            th = chain[j, i]
            loglike[j, i] = logp[j, i] - lik.prior_logp(th, lo, hi)
    accept = float(np.mean(sampler.acceptance_fraction))

    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    np.savez(cache_path, chain=chain, logp=logp, loglike=loglike, t_mcmc=t_mcmc, accept=accept)
    print(f"  [mcmc] {model_name}: {args.nsteps} steps x {args.nwalkers} walkers "
          f"in {t_mcmc:.1f}s; acceptance={accept:.2f}")
    return chain, loglike, t_mcmc, accept


# ----------------------------------------------------------------------------
# main
# ----------------------------------------------------------------------------
def main():
    args = parse_args()
    models = [m for m in args.models.split(",") if m]
    rng = np.random.default_rng(args.seed)
    np.random.seed(args.seed)
    import torch
    torch.manual_seed(args.seed)
    # tiny MLPs: single-thread avoids thread-thrash under shared-machine load
    torch.set_num_threads(1)

    os.makedirs(args.outdir, exist_ok=True)
    os.makedirs(args.cache, exist_ok=True)

    # ---- 1. data ----
    times, sigma, ra, dec, psrs = pta_data.load_toas()
    ntoa = sum(len(t) for t in times)
    print(f"[data] {len(psrs)} pulsars, {ntoa} active ToAs, "
          f"sigma avg {np.mean([np.mean(s) for s in sigma])*1e6:.2f} us")
    T_obs = max(t.max() for t in times) / 86400.0
    print(f"[data] T_obs = {T_obs:.0f} days, Nfreq = 14")

    # ---- 2. likelihoods ----
    liks = {m: pl.PTAJointLikelihood(times, sigma, ra, dec, nfreq=14, model_name=m)
            for m in models}
    los = {m: lik.prior_ranges(m)[0] for m, lik in liks.items()}
    his = {m: lik.prior_ranges(m)[1] for m, lik in liks.items()}

    # ---- 3. reference realisation (PowerLaw injection) ----
    ref_model = "PowerLaw"
    th_true = theta_true(ref_model)
    r0 = liks[ref_model].simulate(th_true, rng=rng)
    precomp = liks[ref_model].prepare_data(r0)
    ctx0_raw = np.concatenate([precomp["b"], [precomp["c"]]]).astype(np.float32)
    print(f"[inject] loglike(true) = {liks[ref_model].loglike(th_true, precomputed=precomp):.2f}")

    # ---- per model ----
    results = {}
    for m in models:
        print(f"\n===== model {m} =====")
        lik = liks[m]
        lo, hi = los[m], his[m]

        # ---------- 4. MCMC ----------
        cache_chain = os.path.join(args.cache, f"mcmc_{m}.npz")
        chain, loglike, t_mcmc, accept = run_mcmc(lik, precomp, lo, hi, m, args, cache_chain)
        flat_th = chain[args.burn:].reshape(-1, 22)
        flat_ll = loglike[args.burn:].reshape(-1)
        # convergence diagnostics (autocorrelation time, only if enough samples)
        try:
            import emcee as _emcee
            tau = float(np.mean(_emcee.autocorr.integrated_time(chain, quiet=True)))
        except Exception:
            tau = float("nan")

        logZ_mcmc = truncated_hme_logz(flat_ll)
        print(f"  [mcmc] n_eff={len(flat_th)}  logZ_HME = {logZ_mcmc:.2f}  tau~{tau:.0f}")

        # ---------- 5. NF training ----------
        n_train = args.n_train
        th_tr = lo + (hi - lo) * rng.random((n_train, 22))
        ctx_tr = np.zeros((n_train, 281), dtype=np.float32)
        t0 = time.time()
        for i in range(n_train):
            r = lik.simulate(th_tr[i], rng=rng)
            ctx_tr[i] = build_context(lik, r)
        t_sim = time.time() - t0
        print(f"  [sim] {n_train} forward sims in {t_sim:.1f}s")

        # whiten context
        mu_c = ctx_tr.mean(axis=0)
        sd_c = ctx_tr.std(axis=0)
        sd_c = np.where(sd_c < 1e-12, 1.0, sd_c)
        ctx_tr_w = ((ctx_tr - mu_c) / sd_c).astype(np.float32)
        ctx0_w = ((ctx0_raw - mu_c) / sd_c).astype(np.float32)
        jac_const = float(np.sum(np.log(hi - lo)))

        th_tr_u = scale01(th_tr, lo, hi).astype(np.float32)
        t0 = time.time()
        nf_model, hist = pta_nf.train_nf(
            th_tr_u, ctx_tr_w, n_epochs=args.n_epochs, batch_size=args.batch,
            context_dim=281, dim=22, seed=args.seed)
        t_train = time.time() - t0
        print(f"  [nf] training {n_train} x {args.n_epochs} epochs in {t_train:.1f}s; "
              f"loss {hist[0]:.2f} -> {hist[-1]:.2f}")

        # ---------- 6. evaluation on r0 ----------
        n_eval = args.n_eval
        ctx0_exp = np.repeat(ctx0_w[None, :], n_eval, axis=0)
        t0 = time.time()
        th_u = nf_model.sample(n_eval, torch.from_numpy(ctx0_exp))
        t_samp = time.time() - t0
        th_eval = unscale01(th_u, lo, hi)

        t0 = time.time()
        lq = nf_model.log_prob(torch.from_numpy(th_u), torch.from_numpy(ctx0_exp)).detach().numpy()
        lp = np.array([lik.prior_logp(th_eval[i], lo, hi) for i in range(n_eval)])
        ll_nf = np.array([lik.loglike(th_eval[i], precomputed=precomp) for i in range(n_eval)])
        t_eval = time.time() - t0
        print(f"  [nf] sampled {n_eval} in {t_samp:.1f}s; reweight+loglike in {t_eval:.1f}s")

        # importance weights (Eq.G1), self-normalised (jac_const cancels)
        lw = ll_nf + lp - lq
        w = np.exp(lw - lw.max())
        w = w / w.sum()
        neff = effective_n(w)
        print(f"  [nf] effective sample size for reweighting = {neff:.0f} / {n_eval}")

        logZ_nf_hme = truncated_hme_logz(ll_nf)
        logZ_nf_is = is_logz(ll_nf, lp, lq, jac_const)
        print(f"  [nf] logZ_HME = {logZ_nf_hme:.2f}   logZ_IS = {logZ_nf_is:.2f}")

        # ---------- Hellinger (2-dim SGWB marginal) ----------
        sg = (20, 21)
        mcmc_sg = flat_th[:, sg]
        nf_sg = th_eval[:, sg]
        H_direct, _ = ph.hellinger_2d(mcmc_sg, nf_sg)
        H_reweight, _ = ph.hellinger_2d(mcmc_sg, nf_sg, w2=w)
        H1_direct = [ph.hellinger_1d(mcmc_sg[:, 0], nf_sg[:, 0]),
                     ph.hellinger_1d(mcmc_sg[:, 1], nf_sg[:, 1])]
        H1_reweight = [ph.hellinger_1d(mcmc_sg[:, 0], nf_sg[:, 0], w2=w),
                       ph.hellinger_1d(mcmc_sg[:, 1], nf_sg[:, 1], w2=w)]
        print(f"  [hellinger] direct={H_direct:.4f}  reweighted={H_reweight:.4f} "
              f"(1d d=[{H1_direct[0]:.3f},{H1_direct[1]:.3f}] "
              f"r=[{H1_reweight[0]:.3f},{H1_reweight[1]:.3f}])")

        results[m] = {
            "model": m,
            "Hellinger_direct_vs_mcmc": H_direct,
            "Hellinger_reweighted_vs_mcmc": H_reweight,
            "H1_direct": H1_direct,
            "H1_reweighted": H1_reweight,
            "logZ_mcmc_hme": logZ_mcmc,
            "logZ_nf_hme": logZ_nf_hme,
            "logZ_nf_is": logZ_nf_is,
            "time_mcmc_s": t_mcmc,
            "time_train_s": t_train,
            "time_eval_s": t_eval,
            "time_sim_s": t_sim,
            "time_sample_s": t_samp,
            "loss_first": hist[0],
            "loss_last": hist[-1],
            "n_train": n_train,
            "n_eval": n_eval,
            "n_mcmc": len(flat_th),
            "mcmc_accept": accept,
            "autocorr_tau": tau,
            "neff_reweight": neff,
        }
        np.savez(os.path.join(args.cache, f"post_{m}.npz"),
                 mcmc_sg=mcmc_sg, nf_sg=nf_sg, w=w, th_eval=th_eval, flat_th=flat_th)

    # ---------- 7. Bayes factors & timing ----------
    logZ_m = {m: results[m]["logZ_mcmc_hme"] for m in models}
    logZ_n = {m: results[m]["logZ_nf_hme"] for m in models}
    bf_mcmc = {a: {b: logZ_m[a] - logZ_m[b] for b in models} for a in models}
    bf_nf = {a: {b: logZ_n[a] - logZ_n[b] for b in models} for a in models}

    def rank(d):
        return {m: i for i, m in enumerate(sorted(d, key=lambda x: d[x], reverse=True))}
    rk_m, rk_n = rank(logZ_m), rank(logZ_n)
    rank_consistent = all(rk_m[m] == rk_n[m] for m in models)

    max_logbf_diff = 0.0
    for a in models:
        for b in models:
            if a != b:
                max_logbf_diff = max(max_logbf_diff, abs(bf_mcmc[a][b] - bf_nf[a][b]))

    print("\n===== log10 evidence =====")
    for m in models:
        print(f"  {m:10s} MCMC={logZ_m[m]:.2f}  NF_HME={logZ_n[m]:.2f}  "
              f"NF_IS={results[m]['logZ_nf_is']:.2f}")
    print(f"  ranking MCMC {rk_m}  NF {rk_n}  consistent={rank_consistent}")
    print(f"  max |logBF_mcmc - logBF_nf| = {max_logbf_diff:.2f}")

    # ---------- 8. outputs ----------
    out = {
        "task": "2504.04211_pta_normalizing_flows",
        "device": "CPU",
        "hardware": {"cpu": os.cpu_count(), "python": sys.version.split()[0]},
        "data_ntoa": int(ntoa),
        "data_Tobs_days": float(T_obs),
        "reference_injection": {"model": ref_model, **INJECT,
                                "logA_red": RED_A, "gamma_red": RED_GAMMA},
        "seed": args.seed,
        "n_train_per_model": args.n_train,
        "n_epochs": args.n_epochs,
        "n_eval_per_model": args.n_eval,
        "mcmc": {"nwalkers": args.nwalkers, "nsteps": args.nsteps, "burn": args.burn},
        "hellinger_dim": "2-dim SGWB marginal (params dims 20,21)",
        "evidence_method": "truncated harmonic mean (discard lowest 10% likelihood)",
        "per_model": results,
        "logZ_mcmc": logZ_m,
        "logZ_nf_hme": logZ_n,
        "logZ_nf_is": {m: results[m]["logZ_nf_is"] for m in models},
        "bf_mcmc_log": bf_mcmc,
        "bf_nf_log": bf_nf,
        "rank_consistent": bool(rank_consistent),
        "max_logbf_diff": float(max_logbf_diff),
        "Hellinger_mean_direct": float(np.mean([results[m]["Hellinger_direct_vs_mcmc"] for m in models])),
        "Hellinger_mean_reweighted": float(np.mean([results[m]["Hellinger_reweighted_vs_mcmc"] for m in models])),
        "note": ("Hellinger computed on the 2-dim SGWB marginal (numerically stable); "
                 "paper Appendix H uses the full 22-dim (mean reweighted 0.2611). "
                 "Evidence via truncated harmonic mean (keep highest 90% L). "
                 "NF trained at reduced scale (50k sims x 30 epochs vs paper 2e5 x 50)."),
    }
    with open(os.path.join(args.outdir, "metrics.json"), "w") as f:
        json.dump(out, f, indent=2, default=float)

    with open(os.path.join(args.outdir, "evidence_table.csv"), "w", newline="") as f:
        wcsv = csv.writer(f)
        wcsv.writerow(["SGWB_model", "Hellinger_direct", "Hellinger_reweighted",
                       "logZ_MCMC_HME", "logZ_NF_HME", "logZ_NF_IS",
                       "time_MCMC_s", "time_train_s", "time_eval_s"])
        for m in models:
            r = results[m]
            wcsv.writerow([m, f"{r['Hellinger_direct_vs_mcmc']:.4f}",
                           f"{r['Hellinger_reweighted_vs_mcmc']:.4f}",
                           f"{r['logZ_mcmc_hme']:.3f}", f"{r['logZ_nf_hme']:.3f}",
                           f"{r['logZ_nf_is']:.3f}",
                           f"{r['time_mcmc_s']:.1f}", f"{r['time_train_s']:.1f}",
                           f"{r['time_eval_s']:.1f}"])

    try:
        make_figures(results, models, args.outdir, args.cache, logZ_m, logZ_n)
    except Exception as e:
        print("figure failed:", e)

    print("\nDONE. results written to", args.outdir)


def make_figures(results, models, outdir, cachedir, logZ_m, logZ_n):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, len(models), figsize=(5.5 * len(models), 4.6),
                             constrained_layout=True)
    if len(models) == 1:
        axes = [axes]
    for ax, m in zip(axes, models):
        d = np.load(os.path.join(cachedir, f"post_{m}.npz"))
        mcmc_sg = d["mcmc_sg"]
        nf_sg = d["nf_sg"]
        w = d["w"]
        ax.scatter(nf_sg[::5, 0], nf_sg[::5, 1], s=2, alpha=0.15, c="tab:blue",
                   label="NF direct")
        ax.scatter(mcmc_sg[::2, 0], mcmc_sg[::2, 1], s=2, alpha=0.2, c="tab:red",
                   label="MCMC")
        rng = np.random.default_rng(0)
        idx = rng.choice(len(w), size=min(3000, len(w)), replace=False, p=w / w.sum())
        ax.scatter(nf_sg[idx, 0], nf_sg[idx, 1], s=2, alpha=0.4, c="tab:green",
                   label="NF reweighted")
        ax.set_xlabel("SGWB param 1"); ax.set_ylabel("SGWB param 2")
        ax.set_title(m, fontsize=12)
        ax.legend(fontsize=7, loc="upper right")
    fig.suptitle("Posterior comparison (SGWB marginal): MCMC vs NF")
    fig.savefig(os.path.join(outdir, "figure.svg"), dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(4.5, 4.2))
    xs = [logZ_m[m] for m in models]
    ys = [logZ_n[m] for m in models]
    ax.plot(xs, ys, "o-")
    for i, m in enumerate(models):
        ax.annotate(m, (xs[i], ys[i]))
    lo = min(xs + ys) - 1.0
    hi = max(xs + ys) + 1.0
    ax.plot([lo, hi], [lo, hi], "k--", lw=0.8)
    ax.set_xlabel("logZ MCMC (HME)")
    ax.set_ylabel("logZ NF (HME)")
    ax.set_title("Evidence comparison")
    fig.tight_layout()
    fig.savefig(os.path.join(outdir, "figure_logz.svg"), dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    main()
