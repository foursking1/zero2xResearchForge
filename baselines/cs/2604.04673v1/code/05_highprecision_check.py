"""
High-precision risk check at large ||theta|| (r in {400,450,500}) for p=50,100.

The full-grid runs show the p=50/p=100 exceedances are tiny (0.02-0.13 on a
scale of 50/100). This script re-estimates the risk at the largest r values
with a much larger MC budget (N_mc=200000, K_dir=30) to determine whether the
fixed/dropout rules actually exceed the minimax level p at large ||theta||.

Also assesses shrinkage-function sensitivity to M_v (200k vs 2M samples) to
quantify the impact of importance-sampling ESS collapse at large s.
"""
import sys, json, time
from pathlib import Path

DATA_ROOT = Path(r"F:\dataset\2604.04673v1")
sys.path.insert(0, str(DATA_ROOT))

import numpy as np

from src.config import ExperimentConfig
from src.priors import sample_v_fixed, sample_v_dropout
from src.shrinkage import (
    compute_shrinkage_betaprime,
    compute_shrinkage_fixed_scale,
    compute_shrinkage_dropout,
)
from src.risk import compute_radial_risk_at_r


def shrinkage_for(p, seed=42, m_v=200_000):
    exp_cfg = ExperimentConfig(seed=seed, dimensions=[p])
    exp_cfg.mc.M_v = m_v
    rng = np.random.default_rng(seed)
    v_fixed = sample_v_fixed(exp_cfg, rng)
    v_dropout = sample_v_dropout(exp_cfg, rng)
    s_max = (500 + 6 * np.sqrt(p)) ** 2
    s_grid = np.linspace(0, s_max, 2500)
    a_fixed, ess_f = compute_shrinkage_fixed_scale(s_grid, v_fixed, p, exp_cfg)
    a_dropout, ess_d = compute_shrinkage_dropout(s_grid, v_dropout, p, exp_cfg)
    a_bp = compute_shrinkage_betaprime(s_grid, p)
    return (
        lambda s: np.interp(np.atleast_1d(np.asarray(s, dtype=float)), s_grid, a_fixed),
        lambda s: np.interp(np.atleast_1d(np.asarray(s, dtype=float)), s_grid, a_dropout),
        lambda s: compute_shrinkage_betaprime(np.atleast_1d(np.asarray(s, dtype=float)), p),
        ess_f, ess_d,
    )


def risk_at(p, r, a_func, n_mc=200_000, k_dir=30, seed=12345):
    risks = [
        compute_radial_risk_at_r(r, p, a_func, n_mc, k_dir, seed + i) for i in range(1)
    ]
    return float(np.mean(risks))


if __name__ == "__main__":
    out_dir = Path(__file__).resolve().parent.parent / "results"
    report = {}

    for p in [50, 100]:
        a_f, a_d, a_b, ess_f, ess_d = shrinkage_for(p)
        row = {}
        for r in [400.0, 450.0, 500.0]:
            row[str(r)] = {
                "fixed": risk_at(p, r, a_f),
                "dropout": risk_at(p, r, a_d),
                "betaprime": risk_at(p, r, a_b),
            }
            print(f"p={p} r={r}: fixed={row[str(r)]['fixed']:.4f} "
                  f"dropout={row[str(r)]['dropout']:.4f} betaprime={row[str(r)]['betaprime']:.4f}",
                  flush=True)
        report[f"p{p}"] = row

    # shrinkage sensitivity to M_v at p=5 (largest ESS-collapse effect)
    s_check = [100.0, 1000.0, 1e4, 5e4, 1e5, 2.5e5]
    sens = {}
    for m_v in [200_000, 2_000_000]:
        a_f, a_d, a_b, ess_f, ess_d = shrinkage_for(5, m_v=m_v)
        sens[str(m_v)] = {
            "s": s_check,
            "a_fixed": [float(a_f(np.array([s]))[0]) for s in s_check],
            "a_dropout": [float(a_d(np.array([s]))[0]) for s in s_check],
        }
    report["shrinkage_mv_sensitivity_p5"] = sens

    out_dir.mkdir(parents=True, exist_ok=True)
    json.dump(report, open(out_dir / "highprecision_check.json", "w"), indent=2)
    print("SAVED", out_dir / "highprecision_check.json")
