# -*- coding: utf-8 -*-
"""
analyze_official_kagent.py
==========================
Analysis of the official K-Agent artifact CSV (CIFAR-10 half of paper Table 1).

Claims targeted:
  C01  K-Agent (different LLMs / prompt techniques) achieves COMPARABLE accuracy
       to the established selection baselines (PoC, Random, Oort).
  C02  K-Agent dynamically adapts its K value across communication rounds.

The CSV stores, per configuration 'prompt-method-model' (n=30, 3 runs averaged):
  accuracy        mean accuracy (paper reports ~35-39% for CIFAR-10)
  std_accuracy    std across runs
  k_medio         mean K (number of selected clients) across rounds
  k_std           std of K across rounds   <- direct probe of C02
  download_mb     total download traffic = K * per-client model download
  sample_time     selection time (LLM inference + algorithm)

Statistical tests use scipy.stats (system python has numpy/pandas/scipy).
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

from paper_evidence import load_k_agent_csv

OUT_DIR = Path(__file__).resolve().parent.parent / "results"


def _group_mean(rows, key):
    g = defaultdict(list)
    for r in rows:
        g[r[key]].append(r["accuracy"])
    return {k: (float(np.mean(v)), float(np.std(v, ddof=1)) if len(v) > 1 else 0.0, len(v))
            for k, v in sorted(g.items())}


def anova_table(group_accs: dict[str, list[float]]) -> dict:
    """One-way ANOVA over groups; returns summary or None if <2 groups."""
    groups = [g for g in group_accs.values() if len(g) >= 1]
    if len(groups) < 2:
        return None
    f, p = stats.f_oneway(*groups)
    return {"f_stat": float(f), "p_value": float(p)}


def main() -> None:
    rows = load_k_agent_csv()
    df = pd.DataFrame(rows)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    report = {"n_configs": len(df)}
    acc = df["accuracy"]

    # ---- Overall accuracy distribution (CIFAR-10) --------------------------
    report["accuracy"] = {
        "mean": float(acc.mean()),
        "std": float(acc.std(ddof=1)),
        "min": float(acc.min()),
        "max": float(acc.max()),
        "range_pp": float(acc.max() - acc.min()),   # percentage points
        "median": float(acc.median()),
    }

    # ---- Aggregates by method / prompt / model -----------------------------
    for key in ("method", "prompt", "model"):
        agg = _group_mean(rows, key)
        report[f"by_{key}"] = {k: {"mean_acc": m, "std_acc": s, "n": n}
                               for k, (m, s, n) in agg.items()}

    # ---- ANOVA: does method / prompt / model choice change accuracy? -------
    for key in ("method", "prompt", "model"):
        groups = defaultdict(list)
        for r in rows:
            groups[r[key]].append(r["accuracy"])
        at = anova_table(groups)
        report[f"anova_{key}"] = at if at else None

    # ---- Welch t-tests between method aggregates (unpaired) ----------------
    methods = ("oort", "poc", "random")
    pair_tests = {}
    for i, a in enumerate(methods):
        for b in methods[i + 1:]:
            va = df.loc[df["method"] == a, "accuracy"]
            vb = df.loc[df["method"] == b, "accuracy"]
            t, p = stats.ttest_ind(va, vb, equal_var=False)
            pair_tests[f"{a}_vs_{b}"] = {
                "mean_diff": float(va.mean() - vb.mean()),
                "t_stat": float(t),
                "p_value": float(p),
            }
    report["pairwise_method_tests"] = pair_tests

    # ---- "Comparable" operational check (C01) -------------------------------
    # Criterion A: max between-method mean-accuracy spread
    method_means = {k: v["mean_acc"] for k, v in report["by_method"].items()}
    spread_method = max(method_means.values()) - min(method_means.values())
    report["c01_comparable_check"] = {
        "method_mean_spread_pp": float(spread_method),
        "max_pairwise_method_diff_pp": float(max(
            abs(method_means[a] - method_means[b])
            for a in method_means for b in method_means if a < b)),
        # Criterion B: fraction of the 30 configs inside mean +/- 2 pct pts
        "frac_configs_within_2pp_of_mean": float(
            np.mean(np.abs(acc - acc.mean()) <= 0.02)),
        # Criterion C: overall range
        "overall_range_pp": float(acc.max() - acc.min()),
    }

    # ---- C02: dynamic K -----------------------------------------------------
    k_std = df["k_std"]
    static_configs = df.loc[k_std == 0, "sel"].tolist()
    report["c02_dynamic_k"] = {
        "n_configs": int(len(df)),
        "n_static_k_std_eq_0": int((k_std == 0).sum()),
        "n_dynamic_k_std_gt_0": int((k_std > 0).sum()),
        "frac_dynamic": float((k_std > 0).mean()),
        "k_medio_mean": float(df["k_medio"].mean()),
        "k_medio_min": float(df["k_medio"].min()),
        "k_medio_max": float(df["k_medio"].max()),
        "k_std_mean": float(k_std.mean()),
        "k_std_median": float(k_std.median()),
        "k_std_max": float(k_std.max()),
        "static_configs": static_configs,
    }

    # ---- C01 context: implied per-client download MB ------------------------
    df["implied_mb_per_client"] = df["download_mb"] / df["k_medio"]
    report["download"] = {
        "download_mb_total_mean": float(df["download_mb"].mean()),
        "implied_mb_per_client_mean": float(df["implied_mb_per_client"].mean()),
    }

    # ---- Full config table for evidence_table.csv --------------------------
    df_out = df.copy()
    df_out["accuracy_pct"] = df_out["accuracy"] * 100
    df_out["std_accuracy_pct"] = df_out["std_accuracy"] * 100
    df_out["is_dynamic_k"] = (df_out["k_std"] > 0)
    df_out.to_csv(OUT_DIR / "k_agent_cifar10_configs.csv", index=False)

    with open(OUT_DIR / "kagent_analysis.json", "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, ensure_ascii=False, default=str)

    # ---- Console summary ------------------------------------------------------
    print("=== C01: K-Agent comparable accuracy (CIFAR-10 official artifacts) ===")
    print(f"n = {report['n_configs']}; accuracy mean={acc.mean():.4f} "
          f"range=[{acc.min():.4f},{acc.max():.4f}] "
          f"spread={acc.max()-acc.min():.4f} pp")
    print("by method (mean acc):", {k: round(v['mean_acc'], 4) for k, v in report["by_method"].items()})
    print("by prompt (mean acc):", {k: round(v['mean_acc'], 4) for k, v in report["by_prompt"].items()})
    print("by model  (mean acc):", {k: round(v['mean_acc'], 4) for k, v in report["by_model"].items()})
    print("ANOVA method p=", report["anova_method"]["p_value"] if report["anova_method"] else None,
          "| prompt p=", report["anova_prompt"]["p_value"] if report["anova_prompt"] else None,
          "| model p=", report["anova_model"]["p_value"] if report["anova_model"] else None)
    print("pairwise method t-tests:", {k: round(v["p_value"], 4) for k, v in pair_tests.items()})
    print("method mean spread (pp):", round(report["c01_comparable_check"]["method_mean_spread_pp"], 4))
    print("frac configs within 2pp of mean:", round(report["c01_comparable_check"]["frac_configs_within_2pp_of_mean"], 3))
    print()
    print("=== C02: Dynamic K ===")
    print(f"dynamic (k_std>0): {report['c02_dynamic_k']['n_dynamic_k_std_gt_0']}/"
          f"{report['c02_dynamic_k']['n_configs']} = {report['c02_dynamic_k']['frac_dynamic']:.1%}")
    print(f"k_medio mean={report['c02_dynamic_k']['k_medio_mean']:.2f} "
          f"range=[{report['c02_dynamic_k']['k_medio_min']:.1f}, "
          f"{report['c02_dynamic_k']['k_medio_max']:.1f}]")
    print(f"k_std mean={report['c02_dynamic_k']['k_std_mean']:.2f} "
          f"median={report['c02_dynamic_k']['k_std_median']:.2f} "
          f"max={report['c02_dynamic_k']['k_std_max']:.2f}")
    print("static configs:", report["c02_dynamic_k"]["static_configs"])
    print(f"implied MB per client (download/k): {report['download']['implied_mb_per_client_mean']:.2f}")


if __name__ == "__main__":
    main()
