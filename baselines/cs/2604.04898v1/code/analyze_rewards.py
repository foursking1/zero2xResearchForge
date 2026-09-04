"""Analyze the FineProofs-RL / FineProofs-SFT reward signals.

C04 in TASK.md asks whether RL training with rubric-based rewards shows *increasing*
training reward and corresponding evaluation-score increases over ~350 optimization steps
(paper Fig. 3).  The frozen snapshot contains the *reward datasets* (cross-sectional
per-problem reward arrays) but no step-by-step training log, so the temporal trend cannot
be reproduced directly.  This script therefore characterises:
  1. the rubric-based reward distribution in FineProofs-RL,
  2. how many distinct problems carry non-trivial rewards,
  3. the SFT grade distribution that feeds the reward model,
and records explicitly that no training-step time series exists in the frozen data.

Outputs (results/): fineproofs_rewards.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import dataset_path, output_dir


def main() -> None:
    out_dir = output_dir()
    out_dir.mkdir(parents=True, exist_ok=True)

    rl = pd.read_parquet(dataset_path("FineProofs-RL", "train-00000-of-00001.parquet"))
    sft0 = pd.read_parquet(dataset_path("FineProofs-SFT", "train-00000-of-00002.parquet"))
    sft1 = pd.read_parquet(dataset_path("FineProofs-SFT", "train-00001-of-00002.parquet"))
    sft = pd.concat([sft0, sft1], ignore_index=True)

    n_r = rl["rewards"].map(len)
    flat_rewards = np.concatenate(rl["rewards"].tolist())

    report = {
        "FineProofs-RL": {
            "n_rows": int(len(rl)),
            "total_rollout_rewards": int(len(flat_rewards)),
            "rewards_per_problem": {
                "min": int(n_r.min()),
                "median": int(n_r.median()),
                "max": int(n_r.max()),
            },
            "flat_reward_distribution": {
                "mean": float(flat_rewards.mean()),
                "std": float(flat_rewards.std()),
                "min": float(flat_rewards.min()),
                "q25": float(np.quantile(flat_rewards, 0.25)),
                "median": float(np.quantile(flat_rewards, 0.50)),
                "q75": float(np.quantile(flat_rewards, 0.75)),
                "max": float(flat_rewards.max()),
                "frac_zero": float((flat_rewards == 0).mean()),
            },
            "per_problem_reward_mean_distribution": {
                "mean": float(rl["reward_mean"].mean()),
                "std": float(rl["reward_mean"].std()),
                "min": float(rl["reward_mean"].min()),
                "q25": float(rl["reward_mean"].quantile(0.25)),
                "median": float(rl["reward_mean"].median()),
                "q75": float(rl["reward_mean"].quantile(0.75)),
                "max": float(rl["reward_mean"].max()),
            },
            "frac_problems_with_positive_mean_reward": float((rl["reward_mean"] > 0).mean()),
            "frac_problems_with_max_rollout_reward": float((rl["reward_mean"] == 1.0).mean()),
            "rubric_coverage": bool(rl["rubrics"].notna().all()),
            "mean_rubric_len_chars": float(rl["rubrics"].str.len().mean()),
        },
        "FineProofs-SFT": {
            "n_examples": int(len(sft)),
            "gemini3_pro_grade": {
                "mean": float(sft["gemini-3-pro-grade"].mean()),
                "median": float(sft["gemini-3-pro-grade"].median()),
                "dist": {str(k): int(v) for k, v in sft["gemini-3-pro-grade"].value_counts().sort_index().items()},
                "frac_grade_7": float((sft["gemini-3-pro-grade"] == 7).mean()),
            },
            "qwen3_4b_reward_at_128": {
                "mean": float(sft["qwen3-4b-thinking-reward@128"].mean()),
                "median": float(sft["qwen3-4b-thinking-reward@128"].median()),
                "frac_zero": float((sft["qwen3-4b-thinking-reward@128"] == 0).mean()),
                "frac_one": float((sft["qwen3-4b-thinking-reward@128"] == 1.0).mean()),
            },
        },
        "temporal_training_curve": {
            "available_in_frozen_data": False,
            "reason": ("No step-level RL training log (reward vs optimization step) is present "
                       "in the frozen snapshot; only the cross-sectional FineProofs-RL reward "
                       "dataset and the reproduction evaluation JSONL files are provided. "
                       "The paper's Fig. 3 curve therefore cannot be recomputed from frozen data."),
        },
    }

    out = out_dir / "fineproofs_rewards.json"
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    print("=== FineProofs-RL (rubric-based reward dataset) ===")
    rl_d = report["FineProofs-RL"]
    print(f"  rows={rl_d['n_rows']}, total rollout rewards={rl_d['total_rollout_rewards']}")
    print(f"  flat reward mean={rl_d['flat_reward_distribution']['mean']:.4f} "
          f"median={rl_d['flat_reward_distribution']['median']:.4f} "
          f"frac_zero={rl_d['flat_reward_distribution']['frac_zero']:.4f}")
    print(f"  per-problem reward_mean mean={rl_d['per_problem_reward_mean_distribution']['mean']:.4f} "
          f"median={rl_d['per_problem_reward_mean_distribution']['median']:.4f}")
    print(f"  problems with positive mean reward: {rl_d['frac_problems_with_positive_mean_reward']:.4f}")
    print(f"  rubrics present on all rows: {rl_d['rubric_coverage']}")
    print("=== FineProofs-SFT ===")
    sft_d = report["FineProofs-SFT"]
    print(f"  n={sft_d['n_examples']}, gemini grade mean={sft_d['gemini3_pro_grade']['mean']:.2f}, "
          f"frac grade 7={sft_d['gemini3_pro_grade']['frac_grade_7']:.3f}")
    print("=== Temporal training curve ===")
    print(f"  available in frozen data: {report['temporal_training_curve']['available_in_frozen_data']}")
    print(f"  reason: {report['temporal_training_curve']['reason']}")
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
