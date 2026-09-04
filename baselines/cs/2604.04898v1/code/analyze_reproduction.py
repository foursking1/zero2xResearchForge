"""Recompute evaluation metrics from the frozen reproduction output JSONL files.

Experiments available in the reproduction workspace:
  results/imo_30shot/        IMOProofBench, first 30 problems, 3 seeds (42/123/456)
  results/cross_dataset/     ProofBench, first 15 problems, 3 seeds
  results/local_proof_pilot/ IMOProofBench, first 2 problems, 1 seed
  results/local_proof_3shot/ IMOProofBench, first 3 problems, 1 seed
  results/dsm_wiring_test/   IMOProofBench, 1 problem, DSM scaffold

Judging was done with a LOCAL judge (Qwen/Qwen2.5-1.5B-Instruct) -- NOT the paper's
Gemini-3-Pro judge -- so absolute scores are not directly comparable to the paper.

Outputs (results/):
  - reproduction_metrics.json  (aggregate per-experiment statistics)
  - reproduction_tests.json    (paired statistical tests)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import repro_results, output_dir

EXPERIMENT_GROUPS = {
    "imo_30shot": ["qwen3_direct", "qed_nano_direct", "qed_nano_rc"],
    "cross_dataset": ["qwen3_direct", "qed_nano_direct"],
    "local_proof_pilot": ["qwen3_direct", "qed_nano_direct", "qed_nano_rc"],
    "local_proof_3shot": ["qwen3_direct", "qed_nano_direct", "qed_nano_rc"],
    "dsm_wiring_test": ["qed_nano_dsm"],
}


def load_experiment(group: str, exp: str) -> pd.DataFrame:
    p = repro_results() / group / f"{exp}.jsonl"
    if not p.exists():
        raise FileNotFoundError(p)
    return pd.read_json(p, lines=True)


def exp_stats(df: pd.DataFrame) -> dict:
    scores = df["candidate_score"].dropna()
    norm = df["normalized_score"].dropna()
    has_seed = "seed" in df.columns
    return {
        "n": int(len(df)),
        "n_unique_problems": int(df["question_id"].nunique()),
        "seeds": sorted(int(s) for s in df["seed"].unique()) if has_seed else [],
        "mean_score": float(scores.mean()),
        "std_score": float(scores.std(ddof=1) if len(scores) > 1 else 0.0),
        "mean_normalized_score": float(norm.mean()),
        "std_normalized_score": float(norm.std(ddof=1) if len(norm) > 1 else 0.0),
        "mean_total_tokens": float(df["total_tokens"].mean()),
        "mean_prompt_tokens": float(df["prompt_tokens"].mean()),
        "mean_completion_tokens": float(df["completion_tokens"].mean()),
        "frac_score_ge_6": float((scores >= 6).mean()),
        "frac_score_ge_5": float((scores >= 5).mean()),
        "reference_score_dist": {str(k): int(v) for k, v in df["reference_score"].value_counts().sort_index().items()},
        "per_seed_mean": {
            str(seed): float(df.loc[df["seed"] == seed, "candidate_score"].mean())
            for seed in sorted(df["seed"].unique())
        } if has_seed else {},
    }


def run_paired_tests(group: str, exps: list[str]) -> dict:
    """Paired tests on per-question mean (over seeds) between every experiment pair."""
    frames = {e: load_experiment(group, e) for e in exps}
    per_q = {e: f.groupby("question_id")["candidate_score"].mean() for e, f in frames.items()}
    common = set.intersection(*[set(v.index) for v in per_q.values()])
    common = sorted(common)
    out = {"group": group, "n_common_problems": len(common), "tests": []}
    for i, e1 in enumerate(exps):
        for e2 in exps[i + 1:]:
            a = per_q[e1].loc[common].to_numpy(dtype=float)
            b = per_q[e2].loc[common].to_numpy(dtype=float)
            t = stats.ttest_rel(a, b)
            try:
                w = stats.wilcoxon(a, b)
            except ValueError:
                w = None
            out["tests"].append(
                {
                    "experiment_a": e1,
                    "experiment_b": e2,
                    "mean_a": float(a.mean()),
                    "mean_b": float(b.mean()),
                    "mean_diff_a_minus_b": float(a.mean() - b.mean()),
                    "paired_ttest_t": float(t.statistic),
                    "paired_ttest_p": float(t.pvalue),
                    "wilcoxon_statistic": float(w.statistic) if w else None,
                    "wilcoxon_p": float(w.pvalue) if w else None,
                    "frac_a_gt_b": float((a > b).mean()),
                    "frac_b_gt_a": float((b > a).mean()),
                }
            )
    return out


def main() -> None:
    out_dir = output_dir()
    out_dir.mkdir(parents=True, exist_ok=True)

    all_stats = {}
    for group, exps in EXPERIMENT_GROUPS.items():
        all_stats[group] = {e: exp_stats(load_experiment(group, e)) for e in exps}

    out = out_dir / "reproduction_metrics.json"
    out.write_text(json.dumps(all_stats, indent=2, ensure_ascii=False), encoding="utf-8")

    tests = {}
    for group in ("imo_30shot", "cross_dataset"):
        tests[group] = run_paired_tests(group, EXPERIMENT_GROUPS[group])
    out2 = out_dir / "reproduction_tests.json"
    out2.write_text(json.dumps(tests, indent=2, ensure_ascii=False), encoding="utf-8")

    # console summary
    print("=== IMO-ProofBench (imo_30shot) ===")
    for e in EXPERIMENT_GROUPS["imo_30shot"]:
        s = all_stats["imo_30shot"][e]
        print(f"  {e:16s} n={s['n']:3d} score={s['mean_score']:.3f}+/-{s['std_score']:.3f} "
              f"norm={s['mean_normalized_score']:.3f} tokens={s['mean_total_tokens']:9.1f} "
              f"frac>=6={s['frac_score_ge_6']:.3f}")
    print("=== ProofBench (cross_dataset) ===")
    for e in EXPERIMENT_GROUPS["cross_dataset"]:
        s = all_stats["cross_dataset"][e]
        print(f"  {e:16s} n={s['n']:3d} score={s['mean_score']:.3f}+/-{s['std_score']:.3f} "
              f"tokens={s['mean_total_tokens']:7.1f} frac>=6={s['frac_score_ge_6']:.3f}")
    print("=== DSM wiring test ===")
    s = all_stats["dsm_wiring_test"]["qed_nano_dsm"]
    print(f"  qed_nano_dsm n={s['n']} score={s['mean_score']:.1f} tokens={s['mean_total_tokens']:,.0f}")
    print("\n=== Paired tests ===")
    for group, t in tests.items():
        for item in t["tests"]:
            print(f"  [{group}] {item['experiment_a']} vs {item['experiment_b']}: "
                  f"diff={item['mean_diff_a_minus_b']:+.4f}, t={item['paired_ttest_t']:.3f}, "
                  f"p={item['paired_ttest_p']:.4f}")
    print(f"\nWrote {out} and {out2}")


if __name__ == "__main__":
    main()
