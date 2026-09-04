"""
Horseshoe sparsity risk experiment (paper Section 5.2).

For each dimension p and each k-sparse regime, estimate risk over r in
[0, 2.5*sqrt(p)] (6 equally spaced points) for:
  - BetaPrime rule  (radial; single curve, depends only on r)
  - Horseshoe rule  (one curve per sparsity level k)

Sparse vector construction (paper): theta_{r,k} = (r/sqrt(k), ..., r/sqrt(k), 0, ...)
with exactly k nonzero entries.

Usage:
  python 04_horseshoe_sparsity.py p  [--k k1,k2,...] [--dirs K] [--draws N] [--chains C]
Defaults:
  p=5  -> k in {1,2,5}, dirs=10, draws=20, chains=1
  p=50 -> k in {1,25,50}, dirs=5, draws=10, chains=1
  p=100-> k in {1,20,50,100}, dirs=5, draws=10, chains=1
"""
import sys, json, time, argparse
from pathlib import Path

DATA_ROOT = Path(r"F:\dataset\2604.04673v1")
sys.path.insert(0, str(DATA_ROOT))

import numpy as np

from src.config import ExperimentConfig
from src.shrinkage import compute_shrinkage_betaprime
from src.risk import compute_radial_risk_at_r
from src.horseshoe import horseshoe_posterior_mean

N_MC_BP = 5000   # BetaPrime risk draws (paper Section 5.2)
K_DIR_BP = 10
GRID_POINTS = 2500


def horseshoe_risk_at_r(r, p, k, cfg, n_mc_actual, k_dir, seed):
    """Risk of Horseshoe rule at ||theta||=r with k-sparse theta (paper 5.2)."""
    rng = np.random.default_rng(seed)
    risks = []
    for _ in range(k_dir):
        theta_sparse = np.zeros(p)
        theta_sparse[:k] = r / np.sqrt(k)
        Y = rng.standard_normal((n_mc_actual, p)) + theta_sparse
        sq_errs = []
        for i in range(n_mc_actual):
            th_hat = horseshoe_posterior_mean(Y[i], cfg, rng)
            sq_errs.append(np.sum((th_hat - theta_sparse) ** 2))
        risks.append(np.mean(sq_errs))
    return float(np.mean(risks))


def run(p, ks, k_dir, n_draws, n_chains, out_path):
    exp_cfg = ExperimentConfig(seed=42, dimensions=[p])
    # override horseshoe chain count if requested
    if n_chains:
        exp_cfg.horseshoe.n_chains = n_chains

    r_values = np.linspace(0, 2.5 * np.sqrt(p), 6)
    seed = 42

    # BetaPrime radial risk (single curve, independent of k)
    s_max = (max(r_values) + 6 * np.sqrt(p)) ** 2
    s_grid = np.linspace(0, s_max, GRID_POINTS)
    a_bp = compute_shrinkage_betaprime(s_grid, p)

    def a_bp_func(s):
        return np.interp(np.atleast_1d(np.asarray(s, dtype=np.float64)), s_grid, a_bp)

    t0 = time.time()
    bp_risks = [
        compute_radial_risk_at_r(r, p, a_bp_func, N_MC_BP, K_DIR_BP, seed + 7777)
        for r in r_values
    ]
    print(f"[p={p}] betaprime risk done in {time.time()-t0:.1f}s", flush=True)

    hs_risks = {}
    for k in ks:
        t0 = time.time()
        risks = [
            horseshoe_risk_at_r(r, p, k, exp_cfg, n_draws, k_dir, seed + k * 1000 + i)
            for i, r in enumerate(r_values)
        ]
        hs_risks[str(k)] = risks
        print(f"[p={p}] hs k={k}: {[round(x,3) for x in risks]} "
              f"max={max(risks):.3f} in {time.time()-t0:.1f}s", flush=True)

    out = {
        "p": int(p),
        "r_values": [float(x) for x in r_values],
        "mle_risk": [float(p)] * len(r_values),
        "betaprime_risk": [float(x) for x in bp_risks],
        "horseshoe_risk": hs_risks,
        "settings": {
            "k_dir": k_dir,
            "horseshoe_draws": n_draws,
            "horseshoe_chains": n_chains,
            "betaprime_n_mc": N_MC_BP,
            "horseshoe_iterations": exp_cfg.horseshoe.n_iterations,
            "horseshoe_burnin": exp_cfg.horseshoe.n_burnin,
            "horseshoe_thin": exp_cfg.horseshoe.thin,
        },
    }
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    json.dump(out, open(out_path, "w"), indent=2)
    print("SAVED", out_path, flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("p", type=int)
    ap.add_argument("--k", type=str, default="")
    ap.add_argument("--dirs", type=int, default=0)
    ap.add_argument("--draws", type=int, default=0)
    ap.add_argument("--chains", type=int, default=0)
    ap.add_argument("--out", type=str, default="")
    args = ap.parse_args()

    default_ks = {5: [1, 2, 5], 50: [1, 25, 50], 100: [1, 20, 50, 100]}
    default_dir = {5: 10, 50: 5, 100: 5}
    default_draws = {5: 20, 50: 10, 100: 10}

    ks = [int(x) for x in args.k.split(",")] if args.k else default_ks.get(args.p, [1])
    k_dir = args.dirs or default_dir.get(args.p, 5)
    n_draws = args.draws or default_draws.get(args.p, 10)
    n_chains = args.chains  # 0 -> keep config default

    out = Path(__file__).resolve().parent.parent / "results"
    fname = args.out or f"sparsity_p{args.p}_fresh.json"
    run(args.p, ks, k_dir, n_draws, n_chains, out / fname)
