# -*- coding: utf-8 -*-
"""
make_figures.py
===============
Supplementary visualizations written to results/figures/.

  fig1_kagent_accuracy_by_factor.png : K-Agent CIFAR-10 accuracy vs
      selection method / prompt / LLM model (from frozen k_agent.csv)
  fig2_dynamic_k.png                  : per-config k_medio vs k_std scatter,
      with static-K configs highlighted (C02)
  fig3_token_scaling.png              : paper-cited Table 2 total tokens vs
      client count for raw-LLM vs Tool-Agent (C04)
"""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from paper_evidence import TABLE2_RAW, load_k_agent_csv

FIG_DIR = Path(__file__).resolve().parent.parent / "results" / "figures"


def main() -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    rows = load_k_agent_csv()
    df = pd.DataFrame(rows)
    order = ("oort", "poc", "random", "round_robin")

    # ---- Fig 1: accuracy by factor -----------------------------------------
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.2), sharey=True)
    for ax, key, title in (
        (axes[0], "method", "by selection method"),
        (axes[1], "prompt", "by prompt type"),
        (axes[2], "model", "by LLM model"),
    ):
        data = []
        labels = []
        for v in sorted(df[key].unique(), key=lambda x: x if key != "method" else order.index(x)):
            data.append(df.loc[df[key] == v, "accuracy"].values)
            labels.append(v)
        try:
            ax.boxplot(data, tick_labels=labels, showmeans=True)
        except TypeError:  # older matplotlib
            ax.boxplot(data, labels=labels, showmeans=True)
        ax.set_title(title)
        ax.set_ylabel("accuracy")
        ax.tick_params(axis="x", rotation=20)
    fig.suptitle("K-Agent CIFAR-10 accuracy by factor (frozen official artifacts)")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig1_kagent_accuracy_by_factor.png", dpi=130)
    plt.close(fig)

    # ---- Fig 2: dynamic K (C02) --------------------------------------------
    fig, ax = plt.subplots(1, 1, figsize=(7.5, 5))
    dynamic = df[df["k_std"] > 0]
    static = df[df["k_std"] == 0]
    ax.scatter(dynamic["k_medio"], dynamic["k_std"], s=45, alpha=0.75,
               label=f"dynamic K (k_std>0, n={len(dynamic)})")
    ax.scatter(static["k_medio"], static["k_std"], marker="x", s=70, color="crimson",
               label=f"static K (k_std=0, n={len(static)})")
    for _, r in static.iterrows():
        ax.annotate(r["sel"].replace("-chain-of-thought", " CoT")
                    .replace("description-only-", "DO-"), (r["k_medio"], r["k_std"]),
                    textcoords="offset points", xytext=(6, -8), fontsize=7, color="crimson")
    ax.axhline(0, color="grey", lw=0.8)
    ax.set_xlabel("mean K across rounds (k_medio)")
    ax.set_ylabel("std of K across rounds (k_std)")
    ax.set_title("C02: K-Agent dynamically varies K across rounds")
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig2_dynamic_k.png", dpi=130)
    plt.close(fig)

    # ---- Fig 3: paper-cited token scaling (C04) ----------------------------
    t2 = pd.DataFrame(TABLE2_RAW, columns=["n_clients", "approach", "completion_mean",
                                           "completion_std", "prompt_mean", "prompt_std",
                                           "cost_mean", "cost_std", "total_tokens_mean",
                                           "total_tokens_std", "acc_mean", "acc_std"])
    fig, ax = plt.subplots(1, 1, figsize=(7.5, 5))
    for approach, color, marker in (("llm", "tab:blue", "o"), ("tool", "tab:orange", "s")):
        sub = t2[t2["approach"] == approach]
        ax.errorbar(sub["n_clients"], sub["total_tokens_mean"], yerr=sub["total_tokens_std"],
                    marker=marker, capsize=4, color=color, label=f"{approach}")
    ax.set_xlabel("number of clients")
    ax.set_ylabel("total tokens (mean +- std)")
    ax.set_title("C04: token scalability raw-LLM vs Tool-Agent\n(paper-cited Table 2)")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig3_token_scaling.png", dpi=130)
    plt.close(fig)

    print("Figures written to", FIG_DIR)


if __name__ == "__main__":
    main()
