#!/usr/bin/env python3
"""Assemble results/metrics.json summarizing the verification vs the paper.

Outputs one JSON containing: dataset statistics, per-model (mean over seeds)
test/valid ROC-AUC, comparison against the paper anchors (PAPER_ANCHOR.md),
and the four-way claim label.
"""

import json
import os

import config

RESULTS = config.results_dir()

# Paper anchors (Table 15 of arXiv:2005.00687v2), mean ± std in %.
PAPER = {
    "gcn":    {"te": 74.18, "va": 77.34},
    "gin":    {"te": 75.20, "va": 76.20},
    "gin+vn": {"te": 77.07, "va": 79.04},
    "gcn+vn": {"te": 76.14, "va": 78.90},
}
RANDOM = 50.0


def mean_std(vals):
    vals = list(vals)
    return round(float(sum(vals) / len(vals)), 4), round(float(_sd(vals)), 4)


def _sd(vals):
    m = sum(vals) / len(vals)
    return (sum((v - m) ** 2 for v in vals) / (len(vals) - 1)) ** 0.5 if len(vals) > 1 else 0.0


def main():
    with open(os.path.join(RESULTS, "data_statistics.json")) as f:
        stats = json.load(f)
    with open(os.path.join(RESULTS, "model_results.json")) as f:
        detail = json.load(f)

    # aggregate GNN per model name
    gnn = {}
    for rec in detail["gnn"]:
        gnn.setdefault(rec["model"], []).append(rec)

    models = {}
    for name, recs in gnn.items():
        te_vals = [r["test_roc_auc"] for r in recs]
        va_vals = [r["valid_roc_auc"] for r in recs]
        m_te, s_te = mean_std(te_vals)
        m_va, s_va = mean_std(va_vals)
        paper_key = name.replace("-vn", "+vn")  # 'gin-vn' -> 'gin+vn' (paper Table 15 row)
        paper = PAPER.get(paper_key)
        within = None
        if paper:
            within = abs(m_te * 100 - paper["te"]) <= 3.0  # +-3pp tolerance
        models[name] = {
            "test_roc_auc_mean": m_te, "test_roc_auc_std": s_te,
            "valid_roc_auc_mean": m_va, "valid_roc_auc_std": s_va,
            "n_seeds": len(recs),
            "paper_test_%": paper["te"] if paper else None,
            "within_3pp_of_paper": within,
            "per_seed": recs,
        }

    baselines = {}
    for rec in detail["baselines"]:
        baselines.setdefault(rec["model"], rec)

    # summary comparison table row order
    order = ["gin", "gin-vn", "gcn", "gcn-vn"]
    table = []
    for name in order:
        if name in models:
            m = models[name]
            table.append([name, m["test_roc_auc_mean"], m["test_roc_auc_std"]])

    # ---- four-way judgement ----
    def auc(name):
        return models[name]["test_roc_auc_mean"]

    checks = {
        "dataset_size_and_split": (stats["total_graphs"] == 41127
                                   and stats["split"]["train"]["n_graphs"] == 32901
                                   and stats["split"]["valid"]["n_graphs"] == 4113
                                   and stats["split"]["test"]["n_graphs"] == 4113),
        "pos_rate_approx_3.5pct": (0.03 <= stats["overall_pos_rate"] <= 0.04),
        "gnn_in_70_80_range":
            all(0.70 <= auc(n) <= 0.80 for n in ("gin", "gin-vn", "gcn")),
        "within_3pp_of_paper": all(models[n]["within_3pp_of_paper"]
                                   for n in ("gin", "gcn", "gin-vn")),
        "virtual_node_helps_gin":
            auc("gin-vn") >= auc("gin") + 0.005,
        "gnn_beats_mean9_mlp":
            (min(auc(n) for n in ("gin", "gcn")) >
             baselines["mlp-mean9"]["test_roc_auc"]),
    }

    strong_mlp = baselines["mlp-ext"]["test_roc_auc"] if "mlp-ext" in baselines else 0
    checks["gnn_beats_strong_mlp"] = (
        min(auc(n) for n in ("gin", "gin-vn")) > strong_mlp)

    if (checks["dataset_size_and_split"] and checks["gnn_in_70_80_range"]
            and checks["within_3pp_of_paper"] and checks["virtual_node_helps_gin"]
            and checks["gnn_beats_mean9_mlp"]):
        label = "supported"
    elif (checks["dataset_size_and_split"] and checks["gnn_in_70_80_range"]
          and checks["within_3pp_of_paper"]):
        label = "partially_supported"
    elif (not checks["gnn_in_70_80_range"] and not checks["within_3pp_of_paper"]):
        label = "contradicted"
    else:
        label = "inconclusive"

    out = {
        "task_id": "2005.00687_ogb_molhiv",
        "conclusion_label": label,
        "dataset": stats,
        "models": models,
        "baselines": baselines,
        "comparison_vs_paper": {
            "paper_random_auc_pct": RANDOM,
            "paper_table_15": PAPER,
            "notes": ("Paper values are mean±std over 5 runs (Table 15). "
                      "Our values are mean±std over the seed set in one run; "
                      "+-3pp tolerance used for 'close to paper'."),
        },
        "checks": checks,
        "summary_table": table,
    }
    with open(os.path.join(RESULTS, "metrics.json"), "w") as f:
        json.dump(out, f, indent=2)
    print(json.dumps({k: v for k, v in out.items()
                      if k not in ("dataset", "models", "baselines")}, indent=2))


if __name__ == "__main__":
    main()