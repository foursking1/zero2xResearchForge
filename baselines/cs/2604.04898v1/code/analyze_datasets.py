"""Analyze the four frozen benchmark / training datasets shipped with the task.

Datasets (HuggingFace snapshot):
  - lm-provers/IMOProofBench            (60 proof problems)
  - lm-provers/ProofBench               (145 problems; splits 24_25=70, other=75)
  - lm-provers/FineProofs-SFT           (4281 supervised fine-tuning examples)
  - lm-provers/FineProofs-RL            (5227 RL prompt rows w/ rubric-based rewards)

Outputs (written to results/):
  - dataset_overview.json
  - printed summary table
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import dataset_path, hf_root, output_dir


def load(name: str, fname: str) -> pd.DataFrame:
    p = dataset_path(name, fname)
    return pd.read_parquet(p)


def main() -> None:
    hf = hf_root()
    out_dir = output_dir()
    out_dir.mkdir(parents=True, exist_ok=True)

    overview = {}

    # ---------------- IMOProofBench ----------------
    imo = load("IMOProofBench", "train-00000-of-00001.parquet")
    overview["IMOProofBench"] = {
        "n_problems": int(len(imo)),
        "categories": imo["category"].value_counts().to_dict(),
        "levels": imo["level"].value_counts().to_dict(),
        "n_novel_problems": int((imo["source"].str.contains("Novel Problem")).sum()),
        "n_modified_olympiad": int((imo["source"].str.contains("Modified|mod", regex=True)).sum()),
        "mean_problem_len_chars": float(imo["problem"].str.len().mean()),
        "mean_solution_len_chars": float(imo["solution"].str.len().mean()),
        "has_answer_field": bool(imo["answer"].notna().any()),
        "has_grading_guidelines": bool(imo["grading_guidelines"].notna().all()),
    }
    # category x level crosstab (useful for judging coverage of the 30-problem subset)
    overview["IMOProofBench"]["cat_level_crosstab"] = (
        imo.groupby(["category", "level"]).size().unstack(fill_value=0).astype(int).to_dict()
    )

    # ---------------- ProofBench ----------------
    pb_all = load("ProofBench", "all-00000-of-00001.parquet")
    pb_2425 = load("ProofBench", "24_25-00000-of-00001.parquet")
    pb_other = load("ProofBench", "other-00000-of-00001.parquet")
    pb_train = load("ProofBench", "train-00000-of-00001.parquet")
    ids_all = set(pb_all["problem_id"])
    ids_2425 = set(pb_2425["problem_id"])
    ids_other = set(pb_other["problem_id"])
    overview["ProofBench"] = {
        "n_all": int(len(pb_all)),
        "n_24_25": int(len(pb_2425)),
        "n_other": int(len(pb_other)),
        "n_train": int(len(pb_train)),
        "2425_plus_other_equals_all": bool(len(pb_2425) + len(pb_other) == len(pb_all)),
        "2425_other_disjoint": bool(ids_2425.isdisjoint(ids_other)),
        "all_is_union": bool(ids_all == (ids_2425 | ids_other)),
        "train_subset_of_all": bool(set(pb_train["problem_id"]).issubset(ids_all)),
        "mean_problem_len_chars": float(pb_all["problem"].str.len().mean()),
        "mean_solution_len_chars": float(pb_all["solution"].str.len().mean()),
    }

    # ---------------- FineProofs-SFT ----------------
    sft0 = load("FineProofs-SFT", "train-00000-of-00002.parquet")
    sft1 = load("FineProofs-SFT", "train-00001-of-00002.parquet")
    sft = pd.concat([sft0, sft1], ignore_index=True)
    grade_dist = sft["gemini-3-pro-grade"].value_counts().sort_index()
    overview["FineProofs-SFT"] = {
        "n_examples": int(len(sft)),
        "n_shards": 2,
        "gemini3_pro_grade_dist": {str(k): int(v) for k, v in grade_dist.items()},
        "grade_mean": float(sft["gemini-3-pro-grade"].mean()),
        "grade_7_fraction": float((sft["gemini-3-pro-grade"] == 7).mean()),
        "reward128_mean": float(sft["qwen3-4b-thinking-reward@128"].mean()),
        "reward128_median": float(sft["qwen3-4b-thinking-reward@128"].median()),
        "n_missing_category": int(sft["category"].isna().sum()),
        "n_missing_competition": int(sft["competition"].isna().sum()),
        "competitions": {k: int(v) for k, v in sft["competition"].value_counts().head(10).items()},
    }
    # category column contains a few spurious long strings; report the clean ones only
    clean_cat = sft[sft["category"].str.len() < 80]["category"].value_counts()
    overview["FineProofs-SFT"]["category_dist_clean"] = {k: int(v) for k, v in clean_cat.items()}

    # ---------------- FineProofs-RL ----------------
    rl = load("FineProofs-RL", "train-00000-of-00001.parquet")
    rl_rewards = rl["rewards"]
    n_rewards = rl["rewards"].map(len)
    overview["FineProofs-RL"] = {
        "n_rows": int(len(rl)),
        "rewards_per_row": {
            "min": int(n_rewards.min()),
            "median": int(n_rewards.median()),
            "max": int(n_rewards.max()),
        },
        "num_rewards_field_counts": {str(k): int(v) for k, v in rl["num_rewards"].value_counts().head(5).items()},
        "reward_mean": {
            "mean": float(rl["reward_mean"].mean()),
            "std": float(rl["reward_mean"].std()),
            "min": float(rl["reward_mean"].min()),
            "q25": float(rl["reward_mean"].quantile(0.25)),
            "median": float(rl["reward_mean"].median()),
            "q75": float(rl["reward_mean"].quantile(0.75)),
            "max": float(rl["reward_mean"].max()),
            "frac_nonzero": float((rl["reward_mean"] > 0).mean()),
        },
        "reward_std_mean": float(rl["reward_std"].mean()),
        "source_counts_top": {k: int(v) for k, v in rl["source"].value_counts().head(10).items()},
        "has_rubrics": bool(rl["rubrics"].notna().all()),
        "mean_rubric_len_chars": float(rl["rubrics"].str.len().mean()),
    }

    out = out_dir / "dataset_overview.json"
    out.write_text(json.dumps(overview, indent=2, ensure_ascii=False), encoding="utf-8")

    # ---------------- console summary ----------------
    print(f"HuggingFace snapshot root: {hf}")
    print(f"IMOProofBench problems : {overview['IMOProofBench']['n_problems']}")
    print(f"  categories            : {overview['IMOProofBench']['categories']}")
    print(f"  levels                : {overview['IMOProofBench']['levels']}")
    print(f"ProofBench (all)        : {overview['ProofBench']['n_all']} "
          f"(24_25={overview['ProofBench']['n_24_25']}, other={overview['ProofBench']['n_other']})")
    print(f"  partition consistent  : {overview['ProofBench']['all_is_union']} "
          f"(disjoint={overview['ProofBench']['2425_other_disjoint']})")
    print(f"FineProofs-SFT examples : {overview['FineProofs-SFT']['n_examples']}")
    print(f"  gemini-3-pro grade=7  : {overview['FineProofs-SFT']['grade_7_fraction']:.3f} "
          f"(mean={overview['FineProofs-SFT']['grade_mean']:.2f})")
    print(f"FineProofs-RL rows      : {overview['FineProofs-RL']['n_rows']}")
    print(f"  reward_mean           : mean={overview['FineProofs-RL']['reward_mean']['mean']:.4f} "
          f"median={overview['FineProofs-RL']['reward_mean']['median']:.4f}")
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
