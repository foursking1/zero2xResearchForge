# -*- coding: utf-8 -*-
"""
analyze_paper_table2.py
=======================
Analysis for claims C03 and C04, which concern the appendix experiment
"Compare single LLM vs Agent" (paper Sec. A.2):

  - raw-LLM  = gpt-4o-mini sees ALL client descriptions in context
  - ToolAgent = ReAct architecture querying client info via tools
  - FedAvg random selection as baseline
  Dataset: MNIST (DNN), Non-IID; Experiment 1 uses 10 clients / 25 rounds.

IMPORTANT PROVENANCE
--------------------
No machine-readable file for this experiment is present in the frozen data
set (confirmed by artifacts/collect_report.json rules R08-R15 -> no_evidence,
and by full directory listing).  The only numbers available are those printed
in Table 2 of the frozen PDF and the qualitative statement about Figure 4.
All numbers used here are therefore tagged PAPER-CITED and MUST NOT be
presented as independently reproduced.

We still perform the arithmetic that the claims require (token-growth ratios,
cost comparison at 50 clients, accuracy comparison at 10 clients) using the
paper-reported means, and we flag exactly what is / is not verifiable.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from paper_evidence import TABLE2_RAW, TABLE1_MNIST, PAPER_CITED_TABLE2, PAPER_CITED_TABLE1_MNIST

OUT_DIR = Path(__file__).resolve().parent.parent / "results"


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # ---------------- Table 2 (paper-cited) --------------------------------
    cols = ["n_clients", "approach", "completion_mean", "completion_std",
            "prompt_mean", "prompt_std", "cost_mean", "cost_std",
            "total_tokens_mean", "total_tokens_std", "acc_mean", "acc_std"]
    t2 = pd.DataFrame(TABLE2_RAW, columns=cols)
    t2["provenance"] = "PAPER-CITED (frozen PDF Table 2)"
    t2.to_csv(OUT_DIR / "paper_table2_llm_vs_tool.csv", index=False)

    piv = t2.pivot(index="n_clients", columns="approach")
    token_llm = piv[("total_tokens_mean", "llm")]
    token_tool = piv[("total_tokens_mean", "tool")]
    cost_llm = piv[("cost_mean", "llm")]
    cost_tool = piv[("cost_mean", "tool")]
    acc_llm = piv[("acc_mean", "llm")]
    acc_tool = piv[("acc_mean", "tool")]

    # ---- C04: token / cost scaling 5 -> 50 clients ------------------------
    scaling = {
        "token_growth_5to50_llm": float(token_llm.loc[50] / token_llm.loc[5]),
        "token_growth_5to50_tool": float(token_tool.loc[50] / token_tool.loc[5]),
        "cost_growth_5to50_llm": float(cost_llm.loc[50] / cost_llm.loc[5]),
        "cost_growth_5to50_tool": float(cost_tool.loc[50] / cost_tool.loc[5]),
        "tokens_per_client_5_llm": float(token_llm.loc[5] / 5),
        "tokens_per_client_50_llm": float(token_llm.loc[50] / 50),
        "tokens_per_client_5_tool": float(token_tool.loc[5] / 5),
        "tokens_per_client_50_tool": float(token_tool.loc[50] / 50),
    }
    # cost at 50 clients
    scaling["cost_50_llm_usd"] = float(cost_llm.loc[50])
    scaling["cost_50_tool_usd"] = float(cost_tool.loc[50])
    scaling["cost_50_llm_exceeds_tool"] = bool(cost_llm.loc[50] > cost_tool.loc[50])
    # sign flip: at 5 clients tool is more expensive; at 50 LLM is more expensive
    scaling["cost_5_llm_exceeds_tool"] = bool(cost_llm.loc[5] > cost_tool.loc[5])
    scaling["token_50_llm_exceeds_tool"] = bool(token_llm.loc[50] > token_tool.loc[50])

    # ---- C03: accuracy at 10 clients (paper-cited Table 2) -----------------
    acc_10 = {
        "acc_10_llm_mean": float(acc_llm.loc[10]),
        "acc_10_tool_mean": float(acc_tool.loc[10]),
        "acc_10_llm_beats_tool": bool(acc_llm.loc[10] > acc_tool.loc[10]),
        "acc_gap_10_tool_minus_llm": float(acc_tool.loc[10] - acc_llm.loc[10]),
    }
    # FedAvg random accuracy at 10 clients / 25 rounds: NOT reported in Table 2.
    # Local MNIST smoke (random=0.4805, oort=0.626, poc=0.626, 5 clients/3 rounds)
    # is a different configuration and only directional context.

    # ---- Table 1 MNIST (paper-cited) for C01 context ------------------------
    t1 = pd.DataFrame(TABLE1_MNIST, columns=["prompt", "model", "method",
                                             "k_mean", "k_std", "acc_mean_pct",
                                             "acc_std_pct", "st_s"])
    t1["provenance"] = "PAPER-CITED (frozen PDF Table 1, MNIST half)"
    t1.to_csv(OUT_DIR / "paper_table1_mnist.csv", index=False)
    t1_by_method = t1.groupby("method")["acc_mean_pct"].agg(["mean", "min", "max", "count"])
    t1_overall = {
        "mnist_acc_mean_pct": float(t1["acc_mean_pct"].mean()),
        "mnist_acc_min_pct": float(t1["acc_mean_pct"].min()),
        "mnist_acc_max_pct": float(t1["acc_mean_pct"].max()),
        "mnist_n_configs": int(len(t1)),
    }

    out = {
        "PAPER_CITED_note": ("All values in this analysis are transcribed from the frozen "
                             "paper PDF (Table 2 and Table 1 MNIST half). No machine-readable "
                             "data for the gpt-4o-mini experiments exists in the frozen set."),
        "table2": t2.to_dict(orient="records"),
        "c04_token_cost_scaling": scaling,
        "c03_accuracy_10clients": acc_10,
        "table1_mnist_overall": t1_overall,
        "table1_mnist_by_method": {
            k: {"mean_pct": float(v["mean"]), "min_pct": float(v["min"]),
                "max_pct": float(v["max"]), "n": int(v["count"])}
            for k, v in t1_by_method.iterrows()},
    }
    with open(OUT_DIR / "paper_table2_analysis.json", "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, ensure_ascii=False, default=str)

    print("=== C04: token/cost scaling (paper-cited Table 2) ===")
    print(f"total-token growth 5->50: LLM x{scaling['token_growth_5to50_llm']:.2f}, "
          f"Tool x{scaling['token_growth_5to50_tool']:.2f}")
    print(f"cost growth 5->50: LLM x{scaling['cost_growth_5to50_llm']:.2f}, "
          f"Tool x{scaling['cost_growth_5to50_tool']:.2f}")
    print(f"at 50 clients: cost LLM=${cost_llm.loc[50]:.6f} vs Tool=${cost_tool.loc[50]:.6f} "
          f"-> LLM exceeds Tool: {scaling['cost_50_llm_exceeds_tool']}")
    print(f"at 5 clients: cost LLM=${cost_llm.loc[5]:.6f} vs Tool=${cost_tool.loc[5]:.6f} "
          f"-> LLM exceeds Tool: {scaling['cost_5_llm_exceeds_tool']}")
    print()
    print("=== C03: accuracy at 10 clients (paper-cited Table 2) ===")
    print(f"LLM acc={acc_10['acc_10_llm_mean']:.4f} vs Tool acc={acc_10['acc_10_tool_mean']:.4f} "
          f"-> LLM beats Tool: {acc_10['acc_10_llm_beats_tool']}")
    print()
    print("=== C01 context: Table 1 MNIST half (paper-cited) ===")
    print(f"acc mean={t1_overall['mnist_acc_mean_pct']:.2f}% "
          f"range=[{t1_overall['mnist_acc_min_pct']:.2f}%,{t1_overall['mnist_acc_max_pct']:.2f}%]")


if __name__ == "__main__":
    main()
