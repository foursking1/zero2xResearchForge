# -*- coding: utf-8 -*-
"""
analyze_smoke_runs.py
=====================
Independent re-derivation of the MNIST smoke results (5 clients, 3 rounds,
Dirichlet alpha=0.1, sample_size=3) directly from the frozen per-round raw
JSON files, and cross-check against results/local_baseline_comparison.csv.

These smoke runs exercise the Flower pipeline with the selection algorithms
random / oort / poc / rrobin.  They are used as *baseline* context for C01
(the established selection baselines) and as pipeline-verification for the
per-round variation of the number of selected clients (K) used in C02.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from paper_evidence import load_baseline_comparison, load_smoke_run_json, smoke_run_names

OUT_DIR = Path(__file__).resolve().parent.parent / "results"


def derive_run_frame(run_name: str) -> pd.DataFrame:
    data = load_smoke_run_json(run_name)
    round_ids = sorted(int(k) for k in data.keys() if k.isdigit())
    recs = []
    for rid in round_ids:
        p = data[str(rid)]
        recs.append({
            "round": rid,
            "selected_k": len(p.get("selected_clients", [])),
            "selection_algorithm": p.get("selection_algorithm", ""),
            "sample_time": float(p.get("sample_time", 0.0)),
            "eval_accuracy": float(p.get("agg_evaluate_metrics", {}).get("eval_accuracy", 0.0)),
            "eval_loss": float(p.get("agg_evaluate_metrics", {}).get("eval_loss", 0.0)),
            "train_accuracy": float(p.get("agg_train_metrics", {}).get("train_accuracy", 0.0)),
        })
    return pd.DataFrame(recs)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    names = smoke_run_names()
    rows = []
    per_round = []
    for name in sorted(names):
        frame = derive_run_frame(name)
        best = frame.loc[frame["eval_accuracy"].idxmax()]
        final = frame.iloc[-1]
        rows.append({
            "experiment": name,
            "rounds": int(frame["round"].max()),
            "best_round": int(best["round"]),
            "best_eval_accuracy": float(best["eval_accuracy"]),
            "final_eval_accuracy": float(final["eval_accuracy"]),
            "final_eval_loss": float(final["eval_loss"]),
            "avg_sample_time": float(frame["sample_time"].mean()),
            "avg_selected_k": float(frame["selected_k"].mean()),
        })
        for _, r in frame.iterrows():
            per_round.append({"experiment": name, **r.to_dict()})

    derived = pd.DataFrame(rows)
    official = pd.DataFrame(load_baseline_comparison())
    merged = derived.merge(
        official[["experiment", "final_eval_accuracy", "final_eval_loss", "avg_selected_k"]],
        on="experiment", suffixes=("_derived", "_official"), how="outer")

    merged["acc_match"] = (
        (merged["final_eval_accuracy_derived"] - merged["final_eval_accuracy_official"]).abs() < 1e-9
    )
    merged.to_csv(OUT_DIR / "smoke_derived_vs_official.csv", index=False)
    pd.DataFrame(per_round).to_csv(OUT_DIR / "smoke_per_round.csv", index=False)

    # clean per-run records (avoid the *_derived / *_official suffix mess)
    clean_runs = []
    for _, rec in derived.iterrows():
        off = official.loc[official["experiment"] == rec["experiment"]]
        clean_runs.append({
            "experiment": rec["experiment"],
            "rounds": int(rec["rounds"]),
            "best_round": int(rec["best_round"]),
            "best_eval_accuracy": float(rec["best_eval_accuracy"]),
            "final_eval_accuracy": float(rec["final_eval_accuracy"]),
            "final_eval_loss": float(rec["final_eval_loss"]),
            "avg_sample_time": float(rec["avg_sample_time"]),
            "avg_selected_k": float(rec["avg_selected_k"]),
            "official_final_eval_accuracy": (
                float(off.iloc[0]["final_eval_accuracy"]) if len(off) else None),
            "acc_match": bool(not off.empty and abs(
                float(rec["final_eval_accuracy"]) - float(off.iloc[0]["final_eval_accuracy"])) < 1e-9),
        })

    summary = {
        "runs": clean_runs,
        "per_round_k_by_run": {
            name: [int(x) for x in derive_run_frame(name)["selected_k"].tolist()]
            for name in sorted(names)
        },
        "all_rounds_select_all_first_round": all(
            len(load_smoke_run_json(name)["1"]["selected_clients"]) == 5 for name in names),
    }
    with open(OUT_DIR / "smoke_analysis.json", "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2, ensure_ascii=False, default=str)

    print("=== MNIST smoke runs: derived vs frozen summary ===")
    print(merged.to_string(index=False))
    print("\nPer-round selected clients:")
    for name in sorted(names):
        frame = derive_run_frame(name)
        print(f"  {name:22s} k_per_round={frame['selected_k'].tolist()} "
              f"acc_per_round={[round(v,4) for v in frame['eval_accuracy'].tolist()]}")


if __name__ == "__main__":
    main()
