"""
Fresh radial risk computation for p=5,50,100 on the paper's grid r=0..500.

Uses the frozen reproduction source code (F:/dataset/2604.04673v1/src) for
V-sampling, shrinkage functions (fixed/dropout importance sampling + BetaPrime
closed form) and MC risk estimation, exactly matching paper Section 5.1:
  d=3, n1=n2=20, sigma1=sigma2=sigma3=1, ||x||=1, dropout q1=q2=0.8,
  M_v=200000, N_mc=50000, K_dir=10, grid r=0,1,...,500,
  shrinkage grid 2500 points on [0,(500+6*sqrt(p))^2].
"""
import sys, json, time
from pathlib import Path

DATA_ROOT = Path(r"F:\dataset\2604.04673v1")
sys.path.insert(0, str(DATA_ROOT))

import numpy as np
from joblib import Parallel, delayed

from src.config import ExperimentConfig
from src.priors import sample_v_fixed, sample_v_dropout
from src.shrinkage import (
    compute_shrinkage_betaprime,
    compute_shrinkage_fixed_scale,
    compute_shrinkage_dropout,
)
from src.risk import compute_radial_risk_at_r

N_MC = 50000
K_DIR = 10
GRID_POINTS = 2500
R_MAX = 500


def compute_estimator_risk(p, r_values, seed=42):
    """Return dict with risk curves + ESS diagnostics for one dimension."""
    exp_cfg = ExperimentConfig(seed=seed, dimensions=[p])
    rng = np.random.default_rng(seed)

    v_fixed = sample_v_fixed(exp_cfg, rng)
    v_dropout = sample_v_dropout(exp_cfg, rng)

    s_max = (max(r_values) + 6 * np.sqrt(p)) ** 2
    s_grid = np.linspace(0, s_max, GRID_POINTS)

    t0 = time.time()
    a_fixed, ess_f = compute_shrinkage_fixed_scale(s_grid, v_fixed, p, exp_cfg)
    a_dropout, ess_d = compute_shrinkage_dropout(s_grid, v_dropout, p, exp_cfg)
    a_bp = compute_shrinkage_betaprime(s_grid, p)
    print(f"[p={p}] shrinkage computed in {time.time()-t0:.1f}s", flush=True)

    def a_fixed_func(s):
        return np.interp(np.atleast_1d(np.asarray(s, dtype=np.float64)), s_grid, a_fixed)

    def a_bp_func(s):
        return compute_shrinkage_betaprime(np.atleast_1d(np.asarray(s, dtype=np.float64)), p)

    def a_dropout_func(s):
        return np.interp(np.atleast_1d(np.asarray(s, dtype=np.float64)), s_grid, a_dropout)

    results = {
        "p": int(p),
        "r_values": [float(r) for r in r_values],
        "mle_risk": [float(p)] * len(r_values),
        "ess_fixed_min": float(ess_f.min()),
        "ess_fixed_max": float(ess_f.max()),
        "ess_dropout_min": float(ess_d.min()),
        "ess_dropout_max": float(ess_d.max()),
        "v_fixed_mean": float(v_fixed.mean()),
        "v_dropout_mean": float(v_dropout.mean()),
        "v_dropout_frac_zero": float((v_dropout == 0).mean()),
        "shrinkage_notes": (
            "fixed/dropout a(s) from MC importance sampling with M_v=200000; "
            "ESS collapses for large s (see ess_*_min)"
        ),
    }

    for name, a_func in [
        ("fixed", a_fixed_func),
        ("betaprime", a_bp_func),
        ("dropout", a_dropout_func),
    ]:
        t0 = time.time()
        seed_est = seed + hash(name) % 10000
        risks = Parallel(n_jobs=-1)(
            delayed(compute_radial_risk_at_r)(r, p, a_func, N_MC, K_DIR, seed_est)
            for r in r_values
        )
        results[f"{name}_risk"] = [float(x) for x in risks]
        print(
            f"[p={p}] {name} risk: {len(risks)} pts in {time.time()-t0:.1f}s "
            f"max={max(risks):.4f} min={min(risks):.4f}",
            flush=True,
        )
    return results


if __name__ == "__main__":
    dims = [int(x) for x in sys.argv[1:]] or [5, 50, 100]
    out_dir = Path(__file__).resolve().parent.parent / "results"
    out_dir.mkdir(parents=True, exist_ok=True)

    for p in dims:
        r_values = list(range(0, R_MAX + 1))
        res = compute_estimator_risk(p, r_values)
        outpath = out_dir / f"radial_risk_p{p}_full.json"
        with open(outpath, "w") as f:
            json.dump(res, f, indent=2)
        print(f"SAVED {outpath}", flush=True)
