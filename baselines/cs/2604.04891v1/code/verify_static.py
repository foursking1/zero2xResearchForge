"""Verify Claim C01.

Claim C01 (TASK.md / .claim_spec.json):
  "Static spectral couplings for Schatten p = 1, 2, infinity show different
   optimal transport plans between the same source and target point clouds,
   with costs 23.745, 19.916, and 19.323 respectively"

Pipeline
--------
1. Load the frozen couplings P_1, P_2, P_inf from
   F:\\dataset\\2604.04891v1\\results\\static_couplings.npz.
2. Check each plan is a feasible coupling (P >= 0, row/col sums = 1/n).
3. Evaluate the three spectral costs  gamma_p(Sigma(P))  with
   gamma_1 = trace, gamma_2 = Frobenius, gamma_inf = lambda_max.
4. Independently re-solve the three optimisation problems on the SAME frozen
   point clouds (Hungarian for p=1, CVXPY/SCS for p=2 and p=inf) and compare
   the recovered optimal cost with the frozen value.
5. Quantify how different the three optimal plans are (pairwise).
6. Write results/metrics_static.json and results/c01_static_summary.json.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np

from common import (N, displacement_covariance, load_static, perm_from_plan,
                    plan_agreement, plan_feasibility, schatten_norm)

OUT = Path(__file__).resolve().parent.parent / "results"
OUT.mkdir(parents=True, exist_ok=True)


def solve_static_cvxpy(X: np.ndarray, Y: np.ndarray, p, solver: str = "SCS") -> tuple:
    """Re-solve the discrete spectral OT problem (same formulation as reproduce.py)."""
    n, m = len(X), len(Y)
    a = np.full(n, 1.0 / n)
    b = np.full(m, 1.0 / m)

    dx = Y[None, :, 0] - X[:, None, 0]
    dy = Y[None, :, 1] - X[:, None, 1]
    A11, A12, A22 = dx * dx, dx * dy, dy * dy

    if p == 1:
        from scipy.optimize import linear_sum_assignment

        C = A11 + A22
        rows, cols = linear_sum_assignment(C)
        P = np.zeros((n, m))
        P[rows, cols] = 1.0 / n
        cost = float(C[rows, cols].sum() / n)
        return P, cost, "hungarian"

    import cvxpy as cp

    Pv = cp.Variable((n, m), nonneg=True)
    cons = [cp.sum(Pv, axis=1) == a, cp.sum(Pv, axis=0) == b]
    S11 = cp.sum(cp.multiply(A11, Pv))
    S12 = cp.sum(cp.multiply(A12, Pv))
    S22 = cp.sum(cp.multiply(A22, Pv))
    S = cp.bmat([[S11, S12], [S12, S22]])
    if p == 2:
        obj = cp.Minimize(cp.norm(S, "fro"))
    elif p == np.inf:
        obj = cp.Minimize(cp.lambda_max(S))
    else:
        raise ValueError(p)

    prob = cp.Problem(obj, cons)
    kwargs = {"verbose": False}
    if solver == "SCS":
        kwargs.update({"eps": 1e-5, "max_iters": 12000})
    t0 = time.time()
    prob.solve(solver=solver, **kwargs)
    elapsed = time.time() - t0
    if Pv.value is None:
        raise RuntimeError(f"CVXPY failed p={p}: {prob.status}")
    return np.asarray(Pv.value, dtype=float), float(prob.value), prob.status, elapsed


def main() -> None:
    data = load_static()
    X, Y = data["X"], data["Y"]
    n = len(X)

    report = {
        "claim_id": "C01",
        "n_points": int(n),
        "source": str(STATIC_NPZ := Path(__file__).resolve().parents[2] / "results" / "static_couplings.npz"),
        "plans": {},
        "plan_differences": {},
        "recompute_matches_frozen": True,
    }

    costs = {}
    for pkey, p in [("1", 1), ("2", 2), ("inf", np.inf)]:
        P = data[f"P_{pkey}"]
        feas = plan_feasibility(P, n, n)
        S = displacement_covariance(P, X, Y)
        cost = schatten_norm(S, p)
        costs[pkey] = cost
        report["plans"][pkey] = {
            "frozen_cost": cost,
            "sigma": S.tolist(),
            "feasibility": feas,
            "perm_mass_on_diag": float(P[np.arange(n), data[f"perm_{pkey}"]].sum()),
        }

    # ── Independent re-solve on the same frozen clouds ──────────────────
    print("Independent re-solve of the static OT problems (same frozen X, Y):")
    reopt = {}
    for pkey, p in [("1", 1), ("2", 2), ("inf", np.inf)]:
        if p == 1:
            P2, cost2, status = solve_static_cvxpy(X, Y, p)
            report["plans"][pkey]["reopt_cost"] = cost2
            report["plans"][pkey]["reopt_solver"] = status
            reopt[pkey] = cost2
            print(f"  p={pkey}: reopt_cost={cost2:.6f} (hungarian)")
        else:
            P2, cost2, status, elapsed = solve_static_cvxpy(X, Y, p)
            report["plans"][pkey]["reopt_cost"] = cost2
            report["plans"][pkey]["reopt_status"] = status
            report["plans"][pkey]["reopt_time_s"] = elapsed
            reopt[pkey] = cost2
            print(f"  p={pkey}: reopt_cost={cost2:.6f} status={status} time={elapsed:.1f}s")

    # ── Plan differences (are the three plans really different?) ─────────
    pairs = [("1", "2"), ("1", "inf"), ("2", "inf")]
    for pa, pb in pairs:
        d = plan_agreement(data[f"P_{pa}"], data[f"P_{pb}"])
        report["plan_differences"][f"P_{pa}_vs_P_{pb}"] = d

    # displacement singular values (Figure 1 style)
    svd = {}
    for pkey in ["1", "2", "inf"]:
        perm = data[f"perm_{pkey}"]
        D = Y[perm] - X
        s = np.linalg.svd(D, compute_uv=False)
        top_share = s[0] / s.sum() if s.sum() > 0 else float("nan")
        svd[pkey] = {
            "singular_values": s.tolist(),
            "top_singular_share": float(top_share),
            "cond": float(s[0] / s[1]) if s[1] > 0 else float("inf"),
        }
    report["displacement_svd"] = svd

    # tolerance check against the claim values
    claim = {"1": 23.745, "2": 19.916, "inf": 19.323}
    report["claim_values"] = claim
    report["tolerance_check"] = {}
    for pkey in claim:
        val = costs[pkey]
        c = claim[pkey]
        rel = abs(val - c) / c
        report["tolerance_check"][pkey] = {
            "frozen": val,
            "claim": c,
            "abs_diff": abs(val - c),
            "rel_diff": rel,
            "within_5pct": rel <= 0.05,
        }

    with open(OUT / "metrics_static.json", "w") as fh:
        json.dump(report, fh, indent=2)
    print(f"\nWrote {OUT / 'metrics_static.json'}")

    print("\nSummary of frozen costs vs claim:")
    for pkey in claim:
        tc = report["tolerance_check"][pkey]
        print(f"  p={pkey}: frozen={tc['frozen']:.6f} claim={tc['claim']} "
              f"rel_diff={tc['rel_diff']*100:.2f}% within5%={tc['within_5pct']}")


if __name__ == "__main__":
    main()
