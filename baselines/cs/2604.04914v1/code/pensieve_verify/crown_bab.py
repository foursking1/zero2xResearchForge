"""CROWN-style verification backend.

Sound branch-and-bound over the input box:
  - neuron bounds by interval bound propagation (IBP),
  - output-functional bounds by linear relaxation (CROWN),
  - input-box splitting to tighten the relaxation until a proof of safety
    (every sub-box provably cannot satisfy all argmax constraints) or a
    certified counterexample is found,
  - a per-query wall-clock timeout -> unknown.

The label ``crown_bab`` reflects that this is a CROWN/α-CROWN-style linear
relaxation + branching verifier, *not* the paper's own Alpha-Beta-CROWN build.
"""

from __future__ import annotations

import time

import numpy as np

from .verify import CompNet, ibp_bounds, crown_bound, reduce_net_for_box
from .queries import Query


def _margin_vec(net: CompNet, query: Query) -> np.ndarray:
    """Matrix C (12,) -> margins: C has +1 at lhs, -1 at rhs per constraint."""
    c = np.zeros(net.n_out)
    for lhs, rhs in query.pairs:
        c[lhs] += 1.0
        c[rhs] -= 1.0
    return c


def verify_crown_bab(net: CompNet, query: Query, timeout_s: float = 120.0,
                     max_nodes: int = 200000, seed: int = 0) -> dict:
    t0 = time.perf_counter()
    rnet, rlo, rhi = reduce_net_for_box(net, query.lower, query.upper)
    n_in = rnet.n_in

    # Fast pre-check: concrete counterexample via (bounded) local search on the box.
    # Real BaB verifiers (e.g. Alpha-Beta-CROWN) also attack the box with an
    # adversarial search before branching; any witness is certified by exact eval.
    rng = np.random.default_rng(seed)
    best_margin = np.inf
    best_u = None

    def eval_point(u):
        nonlocal best_margin, best_u
        out = rnet.forward(u)
        m = query.max_margin(out)
        if m < best_margin:
            best_margin = m
            best_u = u.copy()
        return m

    def report_unsafe(u, reason):
        out = rnet.forward(u)
        return {
            "backend": "crown_bab", "status": "unsafe", "time_s": time.perf_counter() - t0,
            "reason": reason, "best_margin": query.max_margin(out), "nodes": 0, "witness": u.tolist(),
        }

    cands = [rlo.copy(), rhi.copy(), 0.5 * (rlo + rhi)]
    for _ in range(256):
        cands.append(rng.uniform(rlo, rhi))
    for u in cands:
        out = rnet.forward(u)
        if query.satisfied(out):
            return report_unsafe(u, "counterexample")
        m = query.max_margin(out)
        if m < best_margin:
            best_margin = m
            best_u = u.copy()

    # brief differential-evolution attack on the box
    try:
        from scipy.optimize import differential_evolution
        res = differential_evolution(
            eval_point,
            bounds=list(zip(rlo, rhi)),
            seed=seed,
            maxiter=30,
            popsize=10,
            polish=True,
            workers=1,
            updating="deferred",
            x0=best_u if best_u is not None else None,
        )
        out = rnet.forward(res.x)
        if query.satisfied(out):
            return report_unsafe(res.x, "counterexample(de)")
    except Exception:
        pass

    # margin matrix: for each pair we need a lower bound of (y_lhs - y_rhs).
    margin_vectors = []
    for lhs, rhs in query.pairs:
        c = np.zeros(rnet.n_out)
        c[lhs] = 1.0
        c[rhs] = -1.0
        margin_vectors.append(c)

    nodes = 0
    stack = [(rlo, rhi)]
    while stack and time.perf_counter() - t0 < timeout_s and nodes < max_nodes:
        lo, hi = stack.pop()
        nodes += 1

        # CROWN lower bounds of every margin; if any lower bound > 0 the
        # corresponding argmax constraint can never hold -> sub-box is safe.
        provable_safe = False
        for cvec in margin_vectors:
            lb, _ = crown_bound(rnet, lo, hi, cvec)
            if lb > 1e-9:
                provable_safe = True
                break
        if provable_safe:
            continue

        # try to certify unsafe in this sub-box: if IBP upper bounds show all
        # margins can be <= 0 simultaneously?  We cannot conjure simultaneity from
        # per-margin intervals, so we split and rely on concrete evaluation.
        mid = 0.5 * (lo + hi)
        out = rnet.forward(mid)
        if query.satisfied(out):
            return {
                "backend": "crown_bab", "status": "unsafe", "time_s": time.perf_counter() - t0,
                "reason": "counterexample(bisection)", "best_margin": query.max_margin(out),
                "nodes": nodes, "witness": mid.tolist(),
            }

        # split on widest varying dimension
        width = hi - lo
        dim = int(np.argmax(width))
        if width[dim] <= 1e-12:
            # no volume left -> numerically degenerate, treat as safe
            continue
        lo1, hi1 = lo.copy(), hi.copy()
        lo2, hi2 = lo.copy(), hi.copy()
        hi1[dim] = mid[dim]
        lo2[dim] = mid[dim]
        # push larger first (heuristic)
        stack.append((lo1, hi1))
        stack.append((lo2, hi2))

    status = "safe" if nodes < max_nodes and time.perf_counter() - t0 < timeout_s else "unknown"
    return {
        "backend": "crown_bab", "status": status, "time_s": time.perf_counter() - t0,
        "reason": "exhausted" if status == "safe" else "timeout/nodes",
        "best_margin": float(best_margin), "nodes": nodes, "witness": None,
        "input_dim_red": n_in,
    }
