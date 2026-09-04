"""Heuristic margin search (random + differential evolution + CMA-ES).

Reports the minimum ``max_margin`` found over the query box (exact evaluations of
the comparative network).  ``status = unsafe`` if a point satisfying every
argmax constraint is found (a *certified* counterexample, since evaluation is
exact); otherwise ``not_found`` (no guarantee).
"""

from __future__ import annotations

import time

import numpy as np
from scipy.optimize import differential_evolution

from .verify import CompNet, reduce_net_for_box
from .queries import Query


def run_heuristic(net: CompNet, query: Query, seed: int = 0,
                  random_samples: int = 10000, de_maxiter: int = 200,
                  de_popsize: int = 15, use_cma: bool = True) -> dict:
    t0 = time.perf_counter()
    rnet, rlo, rhi = reduce_net_for_box(net, query.lower, query.upper)
    rng = np.random.default_rng(seed)

    def margin_of(u: np.ndarray) -> float:
        return query.max_margin(rnet.forward(u))

    best_margin = np.inf
    best_u = None

    def eval_point(u: np.ndarray):
        nonlocal best_margin, best_u
        m = margin_of(u)
        if m < best_margin:
            best_margin = m
            best_u = u.copy()
        return m

    # random sampling
    for _ in range(random_samples):
        u = rng.uniform(rlo, rhi)
        if eval_point(u) <= 0.0:
            return {
                "backend": "heuristic", "status": "unsafe", "best_margin": float(best_margin),
                "time_s": time.perf_counter() - t0, "method": "random", "witness": best_u.tolist(),
            }

    # differential evolution
    res = differential_evolution(
        margin_of,
        bounds=list(zip(rlo, rhi)),
        seed=seed,
        maxiter=de_maxiter,
        popsize=de_popsize,
        polish=True,
        workers=1,
        updating="deferred",
    )
    eval_point(res.x)

    # CMA-ES
    if use_cma:
        try:
            import cma
            opts = {"maxfevals": 3000, "seed": seed, "verbose": -9, "bounds": list(zip(rlo, rhi))}
            es = cma.CMAEvolutionStrategy(0.5 * (rlo + rhi).tolist(), 0.2, opts)
            while not es.stop():
                xs = es.ask()
                es.tell(xs, [margin_of(np.clip(x, rlo, rhi)) for x in xs])
            eval_point(np.clip(es.best.x, rlo, rhi))
        except Exception:
            pass

    status = "unsafe" if best_margin <= 1e-9 else "not_found"
    return {
        "backend": "heuristic", "status": status, "best_margin": float(best_margin),
        "time_s": time.perf_counter() - t0, "method": "random+de+cma", "witness": best_u.tolist(),
    }
