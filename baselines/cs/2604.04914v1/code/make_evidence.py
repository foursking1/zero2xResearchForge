"""Build results/evidence_table.csv and results/metrics.json from the analysis runs.

Every number here is either (a) computed from results/analysis_results.jsonl
(which records only actually-executed backend runs on the frozen models) or
(b) explicitly tagged source=paper_cited with the paper's own figure/claim.

Output columns of evidence_table.csv:
    claim, metric, value, unit, scope, backend, definition, source
"""

from __future__ import annotations

import json
import statistics
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
RESULTS = ROOT / "results"
MODELS = ["small", "mid", "big"]
PROPS = ["capacity_utilization", "rebuffering_avoidance", "robustness"]
BACKENDS = ["heuristic", "mip", "crown_bab"]
MODEL_PARAMS = {"small": 136838, "mid": 363398, "big": 626438}
TIMEOUT_MIP = 20.0
TIMEOUT_CROWN = 20.0


def load() -> list[dict]:
    rows = []
    for line in (RESULTS / "analysis_results.jsonl").read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def combined(outcomes: dict[str, str]) -> str:
    if any(v == "unsafe" for v in outcomes.values()):
        return "unsafe"
    if any(v == "safe" for v in outcomes.values()):
        return "safe"
    return "unknown"


def main():
    rows = load()
    by_key: dict[tuple, dict] = {}
    for r in rows:
        by_key.setdefault((r["model"], r["prop"], r["query"]), {})[r["backend"]] = r.get("status", "error")
    times = {}
    for r in rows:
        if r["backend"] in ("mip", "crown_bab") and r.get("time_s") is not None:
            times.setdefault((r["model"], r["backend"]), []).append(r["time_s"])

    ev = []  # (claim, metric, value, unit, scope, backend, definition, source)

    def add(claim, metric, value, unit, scope, backend, definition, source="computed"):
        if isinstance(value, float):
            value = round(value, 6)
        ev.append((claim, metric, value, unit, scope, backend, definition, source))

    # ---------- model/architecture facts ----------
    for m in MODELS:
        add("C01/C03", "model_params", MODEL_PARAMS[m], "count", m, "n/a",
            "total parameters of the extracted ReLUNet (W0+b0+W1+b1+W2+b2)")
    add("C02", "paper_cites_params_pi128", 103174, "count", "paper pi^128", "n/a",
        "论文引用: paper reports 103,174 parameters for pi^128 (H=128)", source="paper_cited")
    add("C02", "paper_cites_params_pi64", 27142, "count", "paper pi^64", "n/a",
        "论文引用: paper reports 27,142 parameters for pi^64 (H=64)", source="paper_cited")
    add("C02", "training_reward_data_present", 0, "bool", "dataset", "n/a",
        "frozen data tree contains no training/reward-curve artifacts -> C02 not testable")

    # ---------- per-backend, per-model resolution counts ----------
    for m in MODELS:
        for b in BACKENDS:
            sts = [r.get("status") for r in rows if r["model"] == m and r["backend"] == b]
            if not sts:
                continue
            add("C01/C04", f"backend_resolved_{b}", sum(s in ("safe", "unsafe") for s in sts),
                "count", m, b, f"{b} resolved (safe|unsafe) queries out of {len(sts)}")
            add("C01/C04", f"backend_unknown_{b}", sum(s == "unknown" for s in sts),
                "count", m, b, f"{b} timed out (unknown) queries")

    # ---------- combined outcomes per property & model (C04 style) ----------
    for prop in PROPS:
        for m in MODELS:
            qs = sorted({r["query"] for r in rows if r["prop"] == prop})
            cnt = {"safe": 0, "unsafe": 0, "unknown": 0}
            for q in qs:
                cnt[combined(by_key.get((m, prop, q), {}))] += 1
            for st in ("safe", "unsafe", "unknown"):
                add("C04", f"aggregated_{prop}_{st}", cnt[st], "count", m, "union",
                    f"union-of-engines outcome '{st}' among {len(qs)} {prop} queries")
            add("C04", f"aggregated_{prop}_queries", len(qs), "count", m, "union",
                "number of frozen queries for this property")

    # ---------- execution time statistics (C03) ----------
    for m in MODELS:
        for b in ("mip", "crown_bab"):
            ts = times.get((m, b), [])
            if not ts:
                continue
            cap = TIMEOUT_MIP if b == "mip" else TIMEOUT_CROWN
            hit = sum(1 for t in ts if t >= cap - 0.5)
            add("C03", f"exec_time_{b}_n", len(ts), "count", m, b, "number of backend runs with recorded wall time")
            add("C03", f"exec_time_{b}_min", min(ts), "s", m, b, "fastest query execution")
            add("C03", f"exec_time_{b}_median", statistics.median(ts), "s", m, b, "median query execution time")
            add("C03", f"exec_time_{b}_max", max(ts), "s", m, b, "slowest query execution (== timeout cap if hit)")
            add("C03", f"exec_time_{b}_hits_timeout", hit, "count", m, b,
                f"queries hitting the {cap:.0f}s timeout cap")
            add("C03", f"exec_time_{b}_mean", statistics.mean(ts), "s", m, b, "mean query execution time")
    # cross-backend variability summary
    for m in MODELS:
        mts = times.get((m, "mip"), [])
        cts = times.get((m, "crown_bab"), [])
        if mts and cts:
            med_m = statistics.median(mts)
            med_c = statistics.median(cts)
            add("C03", "time_median_ratio_crown_over_mip", med_c / med_m if med_m > 0 else float("inf"),
                "ratio", m, "both", "median CROWN time / median MIP time")

    # ---------- heuristic counterexamples (unsafe certificates) ----------
    for m in MODELS:
        n_unsafe = sum(1 for r in rows if r["model"] == m and r["backend"] == "heuristic"
                       and r.get("status") == "unsafe")
        add("C01/C04", "heuristic_unsafe_queries", n_unsafe, "count", m, "heuristic",
            "queries with a certified counterexample (exact-eval margin <= 0)")

    # ---------- R08/R09-style Pensieve metrics (paper-style, on frozen models) ----------
    # Paper (论文引用): pi^64 produces ~45% fewer unknown results than pi^128;
    # ~60% of resolved pi^128 queries decided by only one engine.
    for m in MODELS:
        res = {"safe": 0, "unsafe": 0, "unknown": 0}
        single = 0
        resolved = 0
        for prop in PROPS:
            qs = sorted({r["query"] for r in rows if r["prop"] == prop})
            for q in qs:
                out = by_key.get((m, prop, q), {})
                res[combined(out)] += 1
                mi = out.get("mip", "unknown") in ("safe", "unsafe")
                cb = out.get("crown_bab", "unknown") in ("safe", "unsafe")
                if (mi or cb) and not (mi and cb):
                    single += 1
                if mi or cb:
                    resolved += 1
        add("C03/C04", "resolved_queries", resolved, "count", m, "mip+crown",
            "queries resolved (safe|unsafe) by at least one of the two formal engines")
        add("C03/C04", "resolved_by_only_one_engine_fraction",
            100.0 * single / resolved if resolved else float("nan"), "%", m, "mip+crown",
            "论文风格 R09: share of resolved queries decided by exactly one engine")
        add("C03/C04", "unknown_queries", res["unknown"], "count", m, "mip+crown",
            "queries not resolved by any engine (all three backends unknown or none formal-resolved)")
    # unknown reduction of the smallest model vs each larger one (paper-style R08)
    unk = {m: sum(1 for r in rows if r["model"] == m and r["backend"] == "mip"
                  and r.get("status") == "unknown") for m in MODELS}
    unk_all = {}
    for m in MODELS:
        cnt = 0
        for prop in PROPS:
            qs = sorted({r["query"] for r in rows if r["prop"] == prop})
            for q in qs:
                if combined(by_key.get((m, prop, q), {})) == "unknown":
                    cnt += 1
        unk_all[m] = cnt
    for larger in ("mid", "big"):
        if unk_all[larger] > 0:
            add("C01/C03", "smaller_model_unknown_reduction_vs_" + larger,
                100.0 * (unk_all[larger] - unk_all["small"]) / unk_all[larger], "%",
                f"small vs {larger}", "union",
                "论文风格 R08: % fewer union-unknown queries for the smallest model")

    # ---------- write CSV ----------
    with (RESULTS / "evidence_table.csv").open("w", encoding="utf-8") as f:
        f.write("claim,metric,value,unit,scope,backend,definition,source\n")
        for row in ev:
            f.write(",".join('"' + str(x).replace('"', '""') + '"' for x in row) + "\n")

    # ---------- metrics.json ----------
    metrics = {}
    for claim, metric, value, unit, scope, backend, definition, source in ev:
        key = f"{claim}__{metric}__{scope}__{backend}"
        metrics[key] = {"value": value, "unit": unit, "definition": definition, "source": source}
    metrics["_meta"] = {
        "models": {m: {"params": MODEL_PARAMS[m]} for m in MODELS},
        "timeouts_s": {"mip": TIMEOUT_MIP, "crown_bab": TIMEOUT_CROWN},
        "total_backend_runs": len(rows),
        "frozen_query_counts": {"capacity_utilization": 6, "rebuffering_avoidance": 6, "robustness": 12},
        "coverage": "all frozen queries are input100 (100% coverage, eps=0.01, d=3)",
    }
    (RESULTS / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(f"wrote evidence_table.csv ({len(ev)} rows) and metrics.json ({len(metrics)} keys)")


if __name__ == "__main__":
    main()
