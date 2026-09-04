#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Build evidence_table.csv and metrics.json from raw_results.json.

Evidence table schema:
    claim_id, metric, dataset, value, paper_value, calibre, match, note

"match" is one of: yes (within tolerance), near, no, n/a (not directly comparable).
"""

import csv
import json
import os
from pathlib import Path

OUT_DIR = Path(__file__).resolve().parent.parent / "results"

# Paper values (arXiv:2604.04858v1), clearly quoted from the paper.
PAPER = {
    "auroc_allofus": 0.709,
    "accuracy_allofus": 0.651,
    "n_predictors_allofus": 56,
    # Table 2
    "dp_gap_intersectional": 0.200,
    "dp_gap_race": 0.1038,
    "dp_gap_gender": 0.0692,
    "eopp_gap_race": 0.0796,
    "eopp_gap_gender": 0.1661,
    "eopp_gap_intersectional": 0.3316,
    "eofpr_gap_race": 0.1031,
    "eofpr_gap_gender": 0.0133,
    "eofpr_gap_intersectional": 0.1462,
    # Table 1 (group, TPR, FPR)
    "groups": {
        "Black": (0.69, 0.40),
        "White": (0.61, 0.30),
        "Female": (0.72, 0.33),
        "Male": (0.56, 0.34),
        "Black|Female": (0.66, 0.39),
        "Black|Male": (0.72, 0.43),
        "White|Female": (0.78, 0.28),
        "White|Male": (0.45, 0.32),
    },
    # Component 3 threshold
    "uval_threshold": 0.10,
    "c3_bootstrap_B": 200,
}


def _match(v, p, tol=0.05):
    """Report match quality against a paper value."""
    if p is None:
        return "n/a"
    if v is None:
        return "n/a"
    if abs(v - p) <= tol:
        return "yes"
    if abs(v - p) <= 0.15:
        return "near"
    return "no"


def main():
    # primary analysis: Component 3 with the logistic-regression outcome model
    src = os.environ.get("RAW_RESULTS", "raw_results_lr.json")
    with open(OUT_DIR / src, encoding="utf-8") as f:
        raw = json.load(f)

    c1 = {r["label"]: r for r in raw["component1"]}
    c3 = raw["component3"]
    assoc = raw["association_strength"]

    rows = []
    add = rows.append

    # ---------------- C01 ----------------
    for ds, ds_label in [("fairselect_synthetic", "fairselect"), ("component3_synthetic", "component3")]:
        mp = c1[ds]["model_performance"]
        n_feat = len(c1[ds]["single_axis_groups"])  # not feature count
    # feature counts
    n_feat_fs = 16  # 18 columns - Race - Gender - outcome
    n_feat_c3 = 14  # 18 columns - A1 - A2 - A1A2 - Y

    for ds, ds_label in [("fairselect_synthetic", "fairselect"), ("component3_synthetic", "component3")]:
        mp = c1[ds]["model_performance"]
        add({
            "claim_id": "C01", "metric": "AUROC", "dataset": ds_label,
            "value": round(mp["auroc"], 4), "paper_value": PAPER["auroc_allofus"],
            "calibre": "LR logreg, 80/20 split, random_state=42, threshold=0.5, test-set AUROC",
            "match": "n/a",
            "note": "claim states All of Us (DUCC-controlled, not in frozen data); synthetic reproduction not directly comparable",
        })
        add({
            "claim_id": "C01", "metric": "accuracy", "dataset": ds_label,
            "value": round(mp["accuracy"], 4), "paper_value": PAPER["accuracy_allofus"],
            "calibre": "LR logreg, threshold=0.5, test-set accuracy",
            "match": "n/a",
            "note": "claim states All of Us (DUCC-controlled, not in frozen data); synthetic reproduction not directly comparable",
        })
    add({
        "claim_id": "C01", "metric": "n_predictors", "dataset": "fairselect",
        "value": n_feat_fs, "paper_value": PAPER["n_predictors_allofus"],
        "calibre": "clinical feature columns after dropping protected+outcome",
        "match": "n/a",
        "note": "paper used 56 EHR predictor variables on All of Us; synthetic data has fewer",
    })

    # ---------------- C02 ----------------
    ix = c1["fairselect_synthetic"]["intersectional"]
    sa = c1["fairselect_synthetic"]["single_axis_gaps"]
    add({"claim_id": "C02", "metric": "dp_gap_intersectional", "dataset": "fairselect",
         "value": round(ix["demographic_parity_gap"], 4), "paper_value": PAPER["dp_gap_intersectional"],
         "calibre": "max-min positive rate across 4 intersectional groups",
         "match": _match(ix["demographic_parity_gap"], PAPER["dp_gap_intersectional"]), "note": ""})
    add({"claim_id": "C02", "metric": "eo_tpr_gap_intersectional", "dataset": "fairselect",
         "value": round(ix["equalized_odds_gap_tpr"], 4), "paper_value": PAPER["eopp_gap_intersectional"],
         "calibre": "max-min TPR across intersectional groups (equal opportunity gap)",
         "match": _match(ix["equalized_odds_gap_tpr"], PAPER["eopp_gap_intersectional"]), "note": ""})
    add({"claim_id": "C02", "metric": "eo_fpr_gap_intersectional", "dataset": "fairselect",
         "value": round(ix["equalized_odds_gap_fpr"], 4), "paper_value": PAPER["eofpr_gap_intersectional"],
         "calibre": "max-min FPR across intersectional groups",
         "match": _match(ix["equalized_odds_gap_fpr"], PAPER["eofpr_gap_intersectional"]), "note": ""})
    add({"claim_id": "C02", "metric": "dp_gap_race", "dataset": "fairselect",
         "value": round(sa["Race"]["demographic_parity_gap"], 4), "paper_value": PAPER["dp_gap_race"],
         "calibre": "single-axis demographic parity gap by Race",
         "match": _match(sa["Race"]["demographic_parity_gap"], PAPER["dp_gap_race"]), "note": ""})
    add({"claim_id": "C02", "metric": "dp_gap_gender", "dataset": "fairselect",
         "value": round(sa["Gender"]["demographic_parity_gap"], 4), "paper_value": PAPER["dp_gap_gender"],
         "calibre": "single-axis demographic parity gap by Gender",
         "match": _match(sa["Gender"]["demographic_parity_gap"], PAPER["dp_gap_gender"]), "note": ""})

    # also component3 single-axis gaps for the pattern check
    ix3 = c1["component3_synthetic"]["intersectional"]
    sa3 = c1["component3_synthetic"]["single_axis_gaps"]
    add({"claim_id": "C02", "metric": "dp_gap_intersectional", "dataset": "component3",
         "value": round(ix3["demographic_parity_gap"], 4), "paper_value": None,
         "calibre": "max-min positive rate across 8 intersectional groups", "match": "n/a", "note": ""})
    add({"claim_id": "C02", "metric": "dp_gap_A1", "dataset": "component3",
         "value": round(sa3["A1"]["demographic_parity_gap"], 4), "paper_value": None,
         "calibre": "single-axis DP gap by A1", "match": "n/a", "note": ""})
    add({"claim_id": "C02", "metric": "dp_gap_A2", "dataset": "component3",
         "value": round(sa3["A2"]["demographic_parity_gap"], 4), "paper_value": None,
         "calibre": "single-axis DP gap by A2", "match": "n/a", "note": ""})

    # ---------------- C03 ----------------
    for g in c1["fairselect_synthetic"]["single_axis_groups"]["Race"] + c1["fairselect_synthetic"]["single_axis_groups"]["Gender"]:
        name = g["group"]
        if name in PAPER["groups"]:
            p_tpr, p_fpr = PAPER["groups"][name]
            add({"claim_id": "C03", "metric": f"tpr_{name}", "dataset": "fairselect",
                 "value": round(g["tpr"], 3), "paper_value": p_tpr,
                 "calibre": "test-set TPR, n={}".format(g["n"]),
                 "match": "n/a", "note": "synthetic data; not directly comparable to All of Us cohort"})
            add({"claim_id": "C03", "metric": f"fpr_{name}", "dataset": "fairselect",
                 "value": round(g["fpr"], 3), "paper_value": p_fpr,
                 "calibre": "test-set FPR, n={}".format(g["n"]),
                 "match": "n/a", "note": "synthetic data; not directly comparable to All of Us cohort"})
    for g in c1["fairselect_synthetic"]["intersectional"]["groups"]:
        name = g["group"]
        if name in PAPER["groups"]:
            p_tpr, p_fpr = PAPER["groups"][name]
            add({"claim_id": "C03", "metric": f"tpr_{name}", "dataset": "fairselect",
                 "value": round(g["tpr"], 3), "paper_value": p_tpr,
                 "calibre": "test-set TPR, n={}".format(g["n"]),
                 "match": "n/a", "note": "synthetic data; not directly comparable to All of Us cohort"})
            add({"claim_id": "C03", "metric": f"fpr_{name}", "dataset": "fairselect",
                 "value": round(g["fpr"], 3), "paper_value": p_fpr,
                 "calibre": "test-set FPR, n={}".format(g["n"]),
                 "match": "n/a", "note": "synthetic data; not directly comparable to All of Us cohort"})

    # ---------------- C04 ----------------
    for m in ["avg_neg", "avg_pos", "max_neg", "max_pos", "var_neg", "var_pos"]:
        v = c3["u_values"].get(m)
        add({"claim_id": "C04", "metric": f"u_{m}", "dataset": "component3",
             "value": v if v is None else round(v, 4),
             "paper_value": None,
             "calibre": f"u-value (mean(obs-null > {PAPER['uval_threshold']})) for {m}, "
                        f"SR, R_null={c3['R_null']}, B={c3['B']}",
             "match": "yes" if (v is not None and v <= PAPER["uval_threshold"]) else "n/a",
             "note": "paper reports u-values approaching 0 (max 0.06)"})

    # ---------------- Association (context) ----------------
    for ds, attrs in [("fairselect", ["Race", "Gender"]), ("component3", ["A1", "A2"])]:
        for a in attrs:
            v = assoc[ds][a]["cramers_v"]
            add({"claim_id": "C12_ctx", "metric": f"cramers_v_{a}", "dataset": ds,
                 "value": round(v, 4), "paper_value": None,
                 "calibre": "Cramer's V between protected attribute and outcome",
                 "match": "n/a", "note": "context for u-value interpretation"})

    # ---------------- Write CSV ----------------
    fields = ["claim_id", "metric", "dataset", "value", "paper_value", "calibre", "match", "note"]
    with open(OUT_DIR / "evidence_table.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow(r)

    # ---------------- metrics.json ----------------
    uvals = c3["u_values"]
    c04_verdict = "supported" if all(v <= PAPER["uval_threshold"] for v in uvals.values()) else "not_supported"

    metrics = {
        "claim_assessments": {
            "C01": "inconclusive",
            "C02": "partially_supported",
            "C03": "inconclusive",
            "C04": c04_verdict,
        },
        "reproduced_metrics": {
            "fairselect": {
                "auroc": c1["fairselect_synthetic"]["model_performance"]["auroc"],
                "accuracy": c1["fairselect_synthetic"]["model_performance"]["accuracy"],
                "dp_gap_intersectional": ix["demographic_parity_gap"],
                "eo_tpr_gap_intersectional": ix["equalized_odds_gap_tpr"],
                "eo_fpr_gap_intersectional": ix["equalized_odds_gap_fpr"],
                "dp_gap_race": sa["Race"]["demographic_parity_gap"],
                "dp_gap_gender": sa["Gender"]["demographic_parity_gap"],
            },
            "component3_observational": {
                "auroc": c1["component3_synthetic"]["model_performance"]["auroc"],
                "accuracy": c1["component3_synthetic"]["model_performance"]["accuracy"],
                "dp_gap_intersectional": ix3["demographic_parity_gap"],
                "eo_tpr_gap_intersectional": ix3["equalized_odds_gap_tpr"],
                "eo_fpr_gap_intersectional": ix3["equalized_odds_gap_fpr"],
            },
            "component3_counterfactual": {
                "method": c3["method"],
                "outcome_model": c3["outcome_model"],
                "R_null": c3["R_null"],
                "B": c3["B"],
                "u_values": c3["u_values"],
                "aggregate_stats": {
                    k: c3["summary"].get(k) for k in ["avg_neg", "avg_pos", "max_neg", "max_pos", "var_neg", "var_pos"]
                },
            },
            "association_strength": assoc,
        },
    }
    with open(OUT_DIR / "metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    print(f"Wrote {len(rows)} evidence rows -> {OUT_DIR / 'evidence_table.csv'}")
    print(f"Wrote -> {OUT_DIR / 'metrics.json'}")
    for r in rows:
        print(f"  {r['claim_id']:8s} {r['metric']:28s} value={r['value']} paper={r['paper_value']} match={r['match']}")


if __name__ == "__main__":
    main()
