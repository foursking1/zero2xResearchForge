# -*- coding: utf-8 -*-
"""
run_all.py
==========
Orchestrates the full analysis of arXiv 2604.04895v1 frozen data and
assembles the two machine-readable deliverables:

  results/evidence_table.csv   (metric name, value, operational definition)
  results/metrics.json         (same metrics in nested JSON, keys consistent
                                with the evidence table)

Usage:  python run_all.py
Run from the code/ directory (paths in paper_evidence.py are absolute).
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import analyze_official_kagent
import analyze_paper_table2
import analyze_smoke_runs

OUT_DIR = Path(__file__).resolve().parent.parent / "results"


def load_json(name: str) -> dict:
    with open(OUT_DIR / name, encoding="utf-8") as fh:
        return json.load(fh)


def build_evidence_rows() -> list[dict]:
    ka = load_json("kagent_analysis.json")
    sm = load_json("smoke_analysis.json")
    pt = load_json("paper_table2_analysis.json")
    rows = []

    def add(metric, value, definition, claim, provenance):
        rows.append({
            "指标名": metric,
            "数值": value,
            "口径": definition,
            "claim": claim,
            "provenance": provenance,
        })

    # ---------------- C01: K-Agent comparable accuracy (CIFAR-10) -----------
    a = ka["accuracy"]
    add("cifar10_kagent_accuracy_mean", f"{a['mean']:.4f}",
        "Mean accuracy across all 30 K-Agent configs (paper Table 1 CIFAR-10 half)",
        "C01", "computed from frozen data/official_artifacts/k_agent.csv")
    add("cifar10_kagent_accuracy_range_pp", f"{a['range_pp']:.4f}",
        "max - min accuracy across all 30 configs (percentage points)",
        "C01", "computed from frozen k_agent.csv")
    add("cifar10_kagent_method_mean_spread_pp", f"{ka['c01_comparable_check']['method_mean_spread_pp']:.4f}",
        "Spread of between-method mean accuracy (oort/poc/random/rrobin) in pp",
        "C01", "computed from frozen k_agent.csv")
    add("cifar10_kagent_anova_method_p", f"{ka['anova_method']['p_value']:.4f}",
        "One-way ANOVA p-value of accuracy across selection methods",
        "C01", "computed from frozen k_agent.csv")
    add("cifar10_kagent_anova_prompt_p", f"{ka['anova_prompt']['p_value']:.4f}",
        "One-way ANOVA p-value of accuracy across prompt types",
        "C01", "computed from frozen k_agent.csv")
    add("cifar10_kagent_anova_model_p", f"{ka['anova_model']['p_value']:.4f}",
        "One-way ANOVA p-value of accuracy across LLM models",
        "C01", "computed from frozen k_agent.csv")
    add("cifar10_kagent_frac_within_2pp_of_mean", f"{ka['c01_comparable_check']['frac_configs_within_2pp_of_mean']:.3f}",
        "Fraction of the 30 configs with |acc - mean acc| <= 0.02",
        "C01", "computed from frozen k_agent.csv")
    for k, v in ka["pairwise_method_tests"].items():
        add(f"cifar10_t_test_{k}_p", f"{v['p_value']:.4f}",
            f"Welch t-test p-value, accuracy {k.split('_vs_')[0]} vs {k.split('_vs_')[1]}",
            "C01", "computed from frozen k_agent.csv")
    # method mean accuracies
    for m, v in ka["by_method"].items():
        add(f"cifar10_kagent_acc_mean_method_{m}", f"{v['mean_acc']:.4f}",
            f"Mean accuracy of K-Agent configs using selection method {m}",
            "C01", "computed from frozen k_agent.csv")
    # MNIST leg (paper-cited context)
    t1 = pt["table1_mnist_overall"]
    add("mnist_kagent_acc_mean_pct_paper_cited", f"{t1['mnist_acc_mean_pct']:.2f}",
        "Mean accuracy % across 27 K-Agent MNIST configs (paper Table 1 MNIST half)",
        "C01", "PAPER-CITED from frozen PDF Table 1")
    add("mnist_kagent_acc_range_pct_paper_cited",
        f"{t1['mnist_acc_max_pct'] - t1['mnist_acc_min_pct']:.2f}",
        "max - min accuracy % across MNIST configs",
        "C01", "PAPER-CITED from frozen PDF Table 1")
    # MNIST smoke baselines (frozen local reruns)
    for rec in sm["runs"]:
        add(f"mnist_smoke_final_acc_{rec['experiment']}", f"{rec['final_eval_accuracy']:.4f}",
            f"Final eval accuracy of frozen local smoke run {rec['experiment']} "
            "(5 clients, 3 rounds, MNIST, alpha=0.1)",
            "C01", "computed from frozen results/local_runs raw JSON")

    # ---------------- C02: dynamic K ----------------------------------------
    dk = ka["c02_dynamic_k"]
    add("kagent_frac_configs_dynamic_k", f"{dk['frac_dynamic']:.3f}",
        "Fraction of 30 configs with k_std > 0 (K varied across rounds)",
        "C02", "computed from frozen k_agent.csv (k_std column)")
    add("kagent_k_std_mean", f"{dk['k_std_mean']:.3f}",
        "Mean of per-config K std (rounds-to-round K variation)",
        "C02", "computed from frozen k_agent.csv")
    add("kagent_k_medio_range", f"[{dk['k_medio_min']:.1f}, {dk['k_medio_max']:.1f}]",
        "Range of mean-K across the 30 configs",
        "C02", "computed from frozen k_agent.csv")
    add("kagent_n_static_configs", str(dk["n_static_k_std_eq_0"]),
        "Number of configs with exactly static K (k_std = 0)",
        "C02", "computed from frozen k_agent.csv")
    add("kagent_static_config_list", "; ".join(dk["static_configs"]),
        "Selectors with static K",
        "C02", "computed from frozen k_agent.csv")
    add("smoke_k_per_round_oort", str(sm["per_round_k_by_run"]["mnist-oort-smoke"]),
        "Selected-client count per round (5,3,3) in frozen smoke run",
        "C02", "computed from frozen smoke raw JSON")

    # ---------------- C03: raw LLM vs ToolAgent vs random (10 clients) ------
    c3 = pt["c03_accuracy_10clients"]
    add("gpt4o_acc_10clients_llm_paper_cited", f"{c3['acc_10_llm_mean']:.4f}",
        "Raw-LLM (gpt-4o-mini) accuracy at 10 clients (paper Table 2)",
        "C03", "PAPER-CITED from frozen PDF Table 2")
    add("gpt4o_acc_10clients_tool_paper_cited", f"{c3['acc_10_tool_mean']:.4f}",
        "ToolAgent accuracy at 10 clients (paper Table 2)",
        "C03", "PAPER-CITED from frozen PDF Table 2")
    add("gpt4o_acc_10clients_llm_beats_tool_paper_cited", str(c3["acc_10_llm_beats_tool"]),
        "Whether raw-LLM accuracy exceeds ToolAgent at 10 clients per paper Table 2",
        "C03", "PAPER-CITED from frozen PDF Table 2")
    add("gpt4o_tool_minus_llm_acc_10clients_paper_cited", f"{c3['acc_gap_10_tool_minus_llm']:.4f}",
        "ToolAgent - raw-LLM accuracy gap at 10 clients (positive => Tool better)",
        "C03", "PAPER-CITED from frozen PDF Table 2")
    add("c03_fedavg_random_10clients_evidence", "missing",
        "No frozen data or paper Table value for FedAvg random at 10 clients/25 rounds",
        "C03", "no evidence in frozen set")

    # ---------------- C04: token scalability ---------------------------------
    sc = pt["c04_token_cost_scaling"]
    add("token_growth_5to50_llm_paper_cited", f"{sc['token_growth_5to50_llm']:.3f}",
        "Total-token growth factor 5->50 clients for raw LLM",
        "C04", "PAPER-CITED from frozen PDF Table 2")
    add("token_growth_5to50_tool_paper_cited", f"{sc['token_growth_5to50_tool']:.3f}",
        "Total-token growth factor 5->50 clients for ToolAgent",
        "C04", "PAPER-CITED from frozen PDF Table 2")
    add("cost_growth_5to50_llm_paper_cited", f"{sc['cost_growth_5to50_llm']:.3f}",
        "Cost growth factor 5->50 clients for raw LLM",
        "C04", "PAPER-CITED from frozen PDF Table 2")
    add("cost_growth_5to50_tool_paper_cited", f"{sc['cost_growth_5to50_tool']:.3f}",
        "Cost growth factor 5->50 clients for ToolAgent",
        "C04", "PAPER-CITED from frozen PDF Table 2")
    add("cost_50_llm_usd_paper_cited", f"{sc['cost_50_llm_usd']:.6f}",
        "Total LLM cost (USD) at 50 clients",
        "C04", "PAPER-CITED from frozen PDF Table 2")
    add("cost_50_tool_usd_paper_cited", f"{sc['cost_50_tool_usd']:.6f}",
        "Total ToolAgent cost (USD) at 50 clients",
        "C04", "PAPER-CITED from frozen PDF Table 2")
    add("cost_50_llm_exceeds_tool_paper_cited", str(sc["cost_50_llm_exceeds_tool"]),
        "Whether LLM cost exceeds ToolAgent cost at 50 clients",
        "C04", "PAPER-CITED from frozen PDF Table 2")
    add("tokens_per_client_50_llm_paper_cited", f"{sc['tokens_per_client_50_llm']:.1f}",
        "Total tokens per client at 50 clients, raw LLM",
        "C04", "PAPER-CITED from frozen PDF Table 2")
    add("tokens_per_client_50_tool_paper_cited", f"{sc['tokens_per_client_50_tool']:.1f}",
        "Total tokens per client at 50 clients, ToolAgent",
        "C04", "PAPER-CITED from frozen PDF Table 2")

    return rows


def main() -> None:
    # 1) run the three analyses (each writes its own JSON + CSVs)
    analyze_official_kagent.main()
    analyze_smoke_runs.main()
    analyze_paper_table2.main()

    # 2) assemble the unified evidence table and metrics.json
    rows = build_evidence_rows()
    with open(OUT_DIR / "evidence_table.csv", "w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=["指标名", "数值", "口径", "claim", "provenance"])
        writer.writeheader()
        writer.writerows(rows)

    metrics = {"claim": {}, "all_metrics": {r["指标名"]: r["数值"] for r in rows}}
    for r in rows:
        metrics["claim"].setdefault(r["claim"], []).append({"指标名": r["指标名"], "数值": r["数值"]})
    with open(OUT_DIR / "metrics.json", "w", encoding="utf-8") as fh:
        json.dump(metrics, fh, indent=2, ensure_ascii=False)

    print(f"\nWrote {len(rows)} evidence rows -> {OUT_DIR/'evidence_table.csv'}")
    print(f"Wrote metrics -> {OUT_DIR/'metrics.json'}")


if __name__ == "__main__":
    main()
