"""
Verify the BetaPrime shrinkage closed form (paper Theorem 3.1 / Section 5.1):

    a(s) = 1 - gamma(p-1, s/2) / ((s/2) * gamma(p-2, s/2))

with gamma(.,.) the (regularized) lower incomplete gamma; limiting value
a(0) = 1/(p-1). Checks: (i) a(0) = 1/(p-1); (ii) monotone increasing;
(iii) bounded in (0,1); (iv) values at a few s points for the record.
"""
import json
from pathlib import Path

import numpy as np

import sys

DATA_ROOT = r"F:\dataset\2604.04673v1"
sys.path.insert(0, DATA_ROOT)
from src.shrinkage import compute_shrinkage_betaprime, validate_betaprime_shrinkage

p_list = [5, 50, 100]
s_test = [0.0, 0.5, 1.0, 2.0, 5.0, 10.0, 25.0, 100.0, 500.0, 1e4, 1e6]

out = {}
for p in p_list:
    vals = compute_shrinkage_betaprime(np.array(s_test), p)
    check = validate_betaprime_shrinkage(p)
    out[str(p)] = {
        "a_at_s": {f"{s:.6g}": float(v) for s, v in zip(s_test, vals)},
        "a0": float(vals[0]),
        "a0_expected": 1.0 / (p - 1),
        "a_at_inf": float(vals[-1]),
        "monotone_increasing": bool(check["monotonic"]),
        "bounded_in_0_1": bool(check["bounded"]),
        "issues": check["issues"],
    }
    print(f"p={p}: a0={vals[0]:.6f} (exp {1/(p-1):.6f}), "
          f"a(s=1e6)={vals[-1]:.6f}, mono_inc={check['monotonic']}, bounded={check['bounded']}")

res = Path(__file__).resolve().parent.parent / "results"
res.mkdir(parents=True, exist_ok=True)
json.dump(out, open(res / "betaprime_shrinkage_verify.json", "w"), indent=2)
print("saved:", res / "betaprime_shrinkage_verify.json")
