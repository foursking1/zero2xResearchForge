#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analysis of the reproduction-workspace results under F:/dataset/2604.04930v1/results/.

These are the frozen outputs of the reproduction pipeline (Qwen3-4B, heuristic
post-hoc CoDE-Stop simulation) over curated AIME / MATH / GPQA examples.

We recompute every aggregate metric from the raw JSON files (no paper numbers).
"""
import json
import os
import glob
import statistics as st
from pathlib import Path

REPRO = Path("F:/dataset/2604.04930v1/results")
OUT   = Path(__file__).resolve().parent.parent / "results"
OUT.mkdir(parents=True, exist_ok=True)


def load_json(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def canonical_summaries():
    """Collect the canonical (latest) baseline / codestop summaries per dataset."""
    baseline = load_json(REPRO / "baseline/summary.json")          # GPQA 10
    codestop = load_json(REPRO / "codestop/summary.json")          # GPQA 10, thr=0.95
    aime_base = load_json(REPRO / "baseline_summary.json")          # AIME 20
    aime_code = load_json(REPRO / "codestop_summary.json")          # AIME 20, thr=0.95
    agg = load_json(REPRO / "comparison/aggregate_summary.json")    # GPQA sweep
    return baseline, codestop, aime_base, aime_code, agg


def analyze_aggregate(agg):
    """Rebuild the GPQA accuracy-compute table from the aggregate sweep."""
    base = agg["baseline"]
    rows = []
    for s, red in zip(agg["codestop_sweep"], agg["token_reduction"]):
        rows.append({
            "dataset": agg["dataset"],
            "model": agg["model"],
            "method": "CoDE-Stop",
            "confidence_threshold": s["config"]["confidence_threshold"],
            "accuracy": s["accuracy"],
            "n": s["total_examples"],
            "avg_tokens": s["avg_tokens_per_example"],
            "token_reduction": red,
            "stop_reasons": s.get("stop_reasons", {}),
        })
    return {
        "dataset": agg["dataset"],
        "baseline_accuracy": base["accuracy"],
        "baseline_avg_tokens": base["avg_tokens_per_example"],
        "rows": rows,
    }


def analyze_aime():
    """AIME baseline (20) + codestop sweep (6 thresholds)."""
    # baseline
    base = load_json(REPRO / "baseline/summary_20260417_163856.json")
    base_aime = {
        "dataset": "aime",
        "model": "qwen3-4b",
        "accuracy": base["accuracy"],
        "n": base["total_examples"],
        "avg_tokens": base["avg_tokens_per_example"],
        "total_tokens": base["total_tokens"],
    }
    # codestop sweep thresholds
    thr_files = [
        (0.70, "codestop/summary_20260417_171241.json"),
        (0.75, "codestop/summary_20260417_174622.json"),
        (0.80, "codestop/summary_20260417_182127.json"),
        (0.85, "codestop/summary_20260417_185621.json"),
        (0.90, "codestop/summary_20260417_193115.json"),
        (0.95, "codestop/summary_20260417_200420.json"),
    ]
    rows = []
    for thr, f in thr_files:
        s = load_json(REPRO / f)
        rows.append({
            "dataset": "aime",
            "method": "CoDE-Stop",
            "confidence_threshold": thr,
            "accuracy": s["accuracy"],
            "n": s["total_examples"],
            "avg_tokens": s["avg_tokens_per_example"],
            "token_reduction": round(1 - s["avg_tokens_per_example"] / base["avg_tokens_per_example"], 4),
            "stop_reasons": s.get("stop_reasons", {}),
        })
    return {"baseline": base_aime, "rows": rows}


def confidence_by_correctness(detailed):
    """final_confidence vs correctness from CoDE-Stop detailed results."""
    corr, incorr = [], []
    for d in detailed:
        (corr if d["correct"] else incorr).append(d["final_confidence"])
    return {
        "correct": {"n": len(corr), "mean": round(st.mean(corr), 4) if corr else None,
                    "stdev": round(st.pstdev(corr), 4) if corr else None,
                    "values": [round(c, 3) for c in corr]},
        "incorrect": {"n": len(incorr), "mean": round(st.mean(incorr), 4) if incorr else None,
                      "stdev": round(st.pstdev(incorr), 4) if incorr else None,
                      "values": [round(c, 3) for c in incorr]},
    }


def length_by_correctness(detailed, tokens_field):
    corr, incorr = [], []
    for d in detailed:
        (corr if d["correct"] else incorr).append(d[tokens_field])
    def summ(x):
        if not x:
            return {"n": 0}
        return {"n": len(x), "mean": round(st.mean(x), 1), "median": st.median(x),
                "max": max(x), "min": min(x), "stdev": round(st.pstdev(x), 1),
                "values": x}
    return {"correct": summ(corr), "incorrect": summ(incorr)}


def main():
    baseline, codestop, aime_base, aime_code, agg = canonical_summaries()
    report = {}

    # GPQA aggregate
    gpqa = analyze_aggregate(agg)
    report["gpqa"] = gpqa

    # AIME
    aime = analyze_aime()
    report["aime"] = aime

    # token reduction ranges
    reds_gpqa = [r["token_reduction"] for r in gpqa["rows"]]
    reds_aime = [r["token_reduction"] for r in aime["rows"]]
    report["token_reduction_range_gpqa"] = {"min": min(reds_gpqa), "max": max(reds_gpqa)}
    report["token_reduction_range_aime"] = {"min": min(reds_aime), "max": max(reds_aime)}

    # Accuracy maintenance: which GPQA thresholds keep accuracy >= baseline
    report["gpqa_thresholds_accuracy_ge_baseline"] = [
        r["confidence_threshold"] for r in gpqa["rows"] if r["accuracy"] >= gpqa["baseline_accuracy"]]
    report["aime_accuracy_delta_at_thr095"] = round(
        aime["rows"][-1]["accuracy"] - aime["baseline"]["accuracy"], 3)

    # Confidence dynamics from GPQA codestop detailed (thr=0.95)
    det = load_json(REPRO / "codestop/detailed_results.json")
    report["gpqa_codestop_thr095_confidence"] = confidence_by_correctness(det)
    report["gpqa_codestop_thr095_lengths"] = length_by_correctness(det, "full_tokens")
    report["gpqa_codestop_thr095_effective_lengths"] = length_by_correctness(det, "effective_tokens")

    # Baseline GPQA detailed lengths
    det_base = load_json(REPRO / "baseline/detailed_results.json")
    report["gpqa_baseline_lengths"] = length_by_correctness(det_base, "tokens_used")

    # Collect all codestop detailed files for a larger confidence/length sample
    all_conf = {"correct": [], "incorrect": []}
    all_len = {"correct": [], "incorrect": []}
    all_eff = {"correct": [], "incorrect": []}
    for f in glob.glob(str(REPRO / "codestop/detailed_*.json")):
        for d in load_json(f):
            key = "correct" if d["correct"] else "incorrect"
            all_conf[key].append(d["final_confidence"])
            all_len[key].append(d["full_tokens"])
            all_eff[key].append(d["effective_tokens"])
    report["all_codestop_runs"] = {
        "n_correct": len(all_conf["correct"]),
        "n_incorrect": len(all_conf["incorrect"]),
        "confidence": {
            "correct": {"mean": round(st.mean(all_conf["correct"]), 4), "stdev": round(st.pstdev(all_conf["correct"]), 4)},
            "incorrect": {"mean": round(st.mean(all_conf["incorrect"]), 4), "stdev": round(st.pstdev(all_conf["incorrect"]), 4)},
        },
        "full_tokens": {
            "correct": {"mean": round(st.mean(all_len["correct"]), 1), "median": st.median(all_len["correct"])},
            "incorrect": {"mean": round(st.mean(all_len["incorrect"]), 1), "median": st.median(all_len["incorrect"])},
        },
        "effective_tokens": {
            "correct": {"mean": round(st.mean(all_eff["correct"]), 1), "median": st.median(all_eff["correct"])},
            "incorrect": {"mean": round(st.mean(all_eff["incorrect"]), 1), "median": st.median(all_eff["incorrect"])},
        },
    }

    # Compute ratio incorrect/correct for lengths
    def ratio(c, i):
        if c and i:
            return round(i / c, 3)
        return None
    report["all_codestop_runs"]["length_ratio_incorrect_over_correct"] = ratio(
        st.mean(all_len["correct"]), st.mean(all_len["incorrect"]))
    report["all_codestop_runs"]["effective_ratio_incorrect_over_correct"] = ratio(
        st.mean(all_eff["correct"]), st.mean(all_eff["incorrect"]))

    with open(OUT / "metrics_repro.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)
    print("repro analysis written to", OUT / "metrics_repro.json")

    # console summary
    print("\n=== GPQA sweep (thr, acc, avg_tok, reduction) ===")
    for r in gpqa["rows"]:
        print(f"  thr={r['confidence_threshold']:.2f}  acc={r['accuracy']:.2f}  avg_tok={r['avg_tokens']:7.1f}  red={r['token_reduction']:.3f}")
    print("  baseline: acc=%.2f avg_tok=%.1f" % (gpqa["baseline_accuracy"], gpqa["baseline_avg_tokens"]))
    print("\n=== AIME sweep ===")
    for r in aime["rows"]:
        print(f"  thr={r['confidence_threshold']:.2f}  acc={r['accuracy']:.2f}  avg_tok={r['avg_tokens']:7.1f}  red={r['token_reduction']:.3f}")
    print("  baseline: acc=%.2f avg_tok=%.1f" % (aime["baseline"]["accuracy"], aime["baseline"]["avg_tokens"]))
    print("\n=== All codestop detailed: conf correct vs incorrect ===")
    ac = report["all_codestop_runs"]
    print("  correct conf mean=%.4f stdev=%.4f (n=%d)" % (
        ac["confidence"]["correct"]["mean"], ac["confidence"]["correct"]["stdev"], ac["n_correct"]))
    print("  incorrect conf mean=%.4f stdev=%.4f (n=%d)" % (
        ac["confidence"]["incorrect"]["mean"], ac["confidence"]["incorrect"]["stdev"], ac["n_incorrect"]))
    print("  full tokens correct mean=%.1f median=%s; incorrect mean=%.1f median=%s; ratio=%.3f" % (
        ac["full_tokens"]["correct"]["mean"], ac["full_tokens"]["correct"]["median"],
        ac["full_tokens"]["incorrect"]["mean"], ac["full_tokens"]["incorrect"]["median"],
        ac["length_ratio_incorrect_over_correct"]))


if __name__ == "__main__":
    main()
