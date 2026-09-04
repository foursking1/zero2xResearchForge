"""Run the full Pensieve verification study.

For every (model, query) we run:
  - heuristic   : random + differential-evolution margin search  -> certified counterexample if found
  - mip         : MILP feasibility (HiGHS via scipy) with a wall-clock timeout
  - crown_bab   : CROWN/IBP branch-and-bound with a wall-clock timeout

Results are appended incrementally to results/analysis_results.jsonl so a long
run can be resumed/checked.  Uses only the frozen data tree at the data root.

Usage:
    python run_analysis.py [--models small,mid,big] [--props all]
                           [--mip-timeout 25] [--crown-timeout 25]
                           [--seed 0] [--max-queries 999]
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

from pensieve_verify.model import extract_relu_net
from pensieve_verify.verify import build_comparative
from pensieve_verify.queries import load_query_sets
from pensieve_verify.heuristic import run_heuristic
from pensieve_verify.mip_verify import verify_mip
from pensieve_verify.crown_bab import verify_crown_bab

DATA_ROOT = Path(r"F:\dataset\2604.04914v1\data\official")
MODELS = {
    "small": "pensieve_small_simple.onnx",
    "mid": "pensieve_mid_simple.onnx",
    "big": "pensieve_big_simple.onnx",
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", default="small,mid,big")
    ap.add_argument("--props", default="capacity_utilization,rebuffering_avoidance,robustness")
    ap.add_argument("--backends", default="heuristic,mip,crown_bab")
    ap.add_argument("--mip-timeout", type=float, default=25.0)
    ap.add_argument("--crown-timeout", type=float, default=25.0)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--max-queries", type=int, default=999)
    args = ap.parse_args()

    model_names = [m.strip() for m in args.models.split(",")]
    prop_names = [p.strip() for p in args.props.split(",")]
    backend_names = [b.strip() for b in args.backends.split(",")]

    out_path = Path(__file__).resolve().parents[1] / "results" / "analysis_results.jsonl"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    done = set()
    if out_path.exists():
        for line in out_path.read_text(encoding="utf-8").splitlines():
            try:
                r = json.loads(line)
                done.add((r["model"], r["prop"], r["query"], r["backend"]))
            except Exception:
                pass

    # preload models
    nets = {}
    for m in model_names:
        p = DATA_ROOT / "applications" / "pensieve" / "model" / "onnx" / MODELS[m]
        net = extract_relu_net(p, name=m)
        nets[m] = net
        print(f"[net] {m}: n_in={net.n_in} params={net.n_params()} "
              f"W0={net.W0.shape} W1={net.W1.shape} W2={net.W2.shape}", flush=True)

    sets = load_query_sets(DATA_ROOT)
    total = 0
    for prop in prop_names:
        for m in model_names:
            cnet = build_comparative(nets[m])
            for qi, q in enumerate(sets[prop][: args.max_queries]):
                for backend in backend_names:
                    key = (m, prop, q.name, backend)
                    if key in done:
                        continue
                    total += 1
                    t0 = time.perf_counter()
                    try:
                        if backend == "heuristic":
                            res = run_heuristic(
                                cnet, q, seed=args.seed,
                                random_samples=4000, de_maxiter=60, de_popsize=12,
                                use_cma=False,
                            )
                        elif backend == "mip":
                            res = verify_mip(cnet, q, timeout_s=args.mip_timeout)
                        else:
                            res = verify_crown_bab(cnet, q, timeout_s=args.crown_timeout,
                                                   max_nodes=200000, seed=args.seed)
                        res = dict(res)
                    except Exception as exc:
                        res = {"backend": backend, "status": "error",
                               "time_s": time.perf_counter() - t0, "error": str(exc)}
                    res.update({
                        "model": m, "prop": prop, "query": q.name,
                        "model_params": int(nets[m].n_params()),
                        "n_pairs": len(q.pairs),
                        "n_varying": int((q.upper - q.lower > 1e-12).sum()),
                    })
                    with out_path.open("a", encoding="utf-8") as f:
                        f.write(json.dumps(res) + "\n")
                    done.add(key)
                    print(f"[{res['status']:>8}] {m:>5} {prop:<22} {q.name:<26} "
                          f"{backend:<10} {res['time_s']:6.2f}s  (queue={total})", flush=True)
    print("DONE", flush=True)


if __name__ == "__main__":
    main()
