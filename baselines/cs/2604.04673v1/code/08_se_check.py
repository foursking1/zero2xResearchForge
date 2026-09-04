"""
Monte Carlo standard-error check at the key claim points r=500 for p=5,50,100.

Independent-seed replicates (N_mc=50000, K_dir=10) of the risk estimate at
||theta||=500 to quantify the risk-estimation noise of the headline numbers
used in the claim verdicts.
"""
import sys, json
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

SEEDS = [101, 202, 303, 404, 505]
R = 500.0


def get_shrinkage(p):
    exp_cfg = ExperimentConfig(seed=42, dimensions=[p])
    rng = np.random.default_rng(42)
    vf = sample_v_fixed(exp_cfg, rng)
    vd = sample_v_dropout(exp_cfg, rng)
    smax = (500 + 6 * np.sqrt(p)) ** 2
    sg = np.linspace(0, smax, 2500)
    af, _ = compute_shrinkage_fixed_scale(sg, vf, p, exp_cfg)
    ad, _ = compute_shrinkage_dropout(sg, vd, p, exp_cfg)
    ab = compute_shrinkage_betaprime(sg, p)
    return (
        lambda s: np.interp(np.atleast_1d(np.asarray(s, dtype=float)), sg, af),
        lambda s: np.interp(np.atleast_1d(np.asarray(s, dtype=float)), sg, ad),
        lambda s: compute_shrinkage_betaprime(np.atleast_1d(np.asarray(s, dtype=float)), p),
    )


if __name__ == "__main__":
    out = {}
    for p in [5, 50, 100]:
        af, ad, ab = get_shrinkage(p)
        row = {}
        for est, f in [("fixed", af), ("dropout", ad), ("betaprime", ab)]:
            vals = [compute_radial_risk_at_r(R, p, f, 50000, 10, s) for s in SEEDS]
            row[est] = {
                "mean": float(np.mean(vals)),
                "se": float(np.std(vals, ddof=1)),
                "replicates": [float(v) for v in vals],
                "n_seeds": len(SEEDS),
                "n_mc": 50000,
                "k_dir": 10,
            }
            print(f"p={p} {est} r=500: mean={row[est]['mean']:.4f} "
                  f"se={row[est]['se']:.4f}", flush=True)
        out[str(p)] = row
    res = Path(__file__).resolve().parent.parent / "results"
    json.dump(out, open(res / "se_check.json", "w"), indent=2)
    print("SAVED", res / "se_check.json")
