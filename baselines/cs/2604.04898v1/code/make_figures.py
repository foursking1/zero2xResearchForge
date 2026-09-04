"""Create summary figures for the solution report.

Figures (results/figures/):
  - fig1_dataset_composition.png   IMOProofBench category/level composition
  - fig2_score_distribution.png    Local judge score distribution by experiment (IMO-30shot)
  - fig3_tokens_by_scaffold.png    Mean tokens per scaffold (local reproduction + paper values)
  - fig4_rl_reward_distribution.png FineProofs-RL per-problem mean reward histogram
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import figure_dir

import analyze_reproduction as ar
import analyze_rewards as rwmod


def main() -> None:
    fig_dir = figure_dir()
    fig_dir.mkdir(parents=True, exist_ok=True)

    imo = pd.read_parquet(rwmod.dataset_path("IMOProofBench", "train-00000-of-00001.parquet"))

    # ---- fig1: dataset composition ----
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    imo["category"].value_counts().plot(kind="bar", ax=axes[0], title="IMOProofBench category")
    imo["level"].value_counts().plot(kind="bar", ax=axes[1], title="IMOProofBench level")
    fig.tight_layout()
    fig.savefig(fig_dir / "fig1_dataset_composition.png", dpi=120)
    plt.close(fig)

    # ---- fig2: score distribution by experiment (imo_30shot) ----
    fig, ax = plt.subplots(figsize=(8, 5))
    for exp in ["qwen3_direct", "qed_nano_direct", "qed_nano_rc"]:
        df = ar.load_experiment("imo_30shot", exp)
        counts = df["candidate_score"].value_counts().sort_index()
        ax.plot(counts.index, counts.values, marker="o", label=exp)
    ax.set_xlabel("Local judge score (0-7)")
    ax.set_ylabel("Number of examples (30 problems x 3 seeds)")
    ax.set_title("IMO-ProofBench local judge score distribution")
    ax.legend()
    fig.tight_layout()
    fig.savefig(fig_dir / "fig2_score_distribution.png", dpi=120)
    plt.close(fig)

    # ---- fig3: tokens by scaffold ----
    d = ar.exp_stats(ar.load_experiment("imo_30shot", "qed_nano_direct"))
    rc = ar.exp_stats(ar.load_experiment("imo_30shot", "qed_nano_rc"))
    dsm = ar.exp_stats(ar.load_experiment("dsm_wiring_test", "qed_nano_dsm"))
    fig, ax = plt.subplots(figsize=(7, 5))
    labels = ["Single Turn\ndirect", "Reasoning\nCache", "DeepSeek\nMath (1 ex)"]
    toks = [d["mean_total_tokens"], rc["mean_total_tokens"], dsm["mean_total_tokens"]]
    bars = ax.bar(labels, toks, color=["#4C72B0", "#DD8452", "#55A868"])
    for b, t in zip(bars, toks):
        ax.text(b.get_x() + b.get_width() / 2, b.get_height(), f"{t:,.0f}",
                ha="center", va="bottom")
    ax.set_ylabel("Mean tokens per problem")
    ax.set_title("Local reproduction: tokens per scaffold (IMO-ProofBench)")
    ax.set_yscale("log")
    fig.tight_layout()
    fig.savefig(fig_dir / "fig3_tokens_by_scaffold.png", dpi=120)
    plt.close(fig)

    # ---- fig4: RL reward distribution ----
    rl = pd.read_parquet(rwmod.dataset_path("FineProofs-RL", "train-00000-of-00001.parquet"))
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.hist(rl["reward_mean"], bins=40, color="#4C72B0", alpha=0.8)
    ax.axvline(rl["reward_mean"].mean(), color="red", linestyle="--",
               label=f"mean={rl['reward_mean'].mean():.3f}")
    ax.set_xlabel("Per-problem mean rollout reward (rubric-based)")
    ax.set_ylabel("Number of problems")
    ax.set_title("FineProofs-RL reward distribution")
    ax.legend()
    fig.tight_layout()
    fig.savefig(fig_dir / "fig4_rl_reward_distribution.png", dpi=120)
    plt.close(fig)

    print(f"Figures written to {fig_dir}")


if __name__ == "__main__":
    main()
