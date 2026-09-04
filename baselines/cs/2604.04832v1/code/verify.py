"""Standalone verification of the analysis pipeline and the paper's claims.

Two kinds of checks are reported:

* *infrastructure checks* (data integrity, shapes, folds, expected output
  keys) - these must all pass; the process exit code depends only on them.
* *claim checks* (does the real data support the paper's falsifiable
  claims) - printed as PASS/FAIL but *informational*: a FAIL here is a
  legitimate scientific finding (a claim the data contradicts), not a
  pipeline error.

Loads the result JSONs produced by stage1/2/3.  Exits 0 if all
infrastructure checks pass, 1 otherwise.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

import common

RESULTS = Path(__file__).resolve().parents[1] / "results"


def load(name: str) -> dict:
    with open(RESULTS / name) as fh:
        return json.load(fh)


def main() -> int:
    infra, claims = [], []

    # ---- infrastructure: data / feature sanity ---------------------------
    X, Y, pids = common.load_processed()
    F, _, _ = common.load_features()
    infra.append(("data shape (900,8,400)", X.shape == (900, 8, 400), X.shape))
    counts = {int(c): int((Y == c).sum()) for c in np.unique(Y)}
    infra.append(("class balance 300/class", all(v == 300 for v in counts.values()), counts))
    infra.append(("feature shape (900,72)", F.shape == (900, 72), F.shape))
    infra.append(("features finite", bool(np.isfinite(F).all()), None))
    infra.append(("10 participants", len(np.unique(pids)) == 10, sorted(np.unique(pids))))

    # ---- C01 FDR ----------------------------------------------------------
    s1 = load("stage1_fdr_results.json")
    raw = s1["pairwise_fdr_max_raw"]
    norm = s1["fdr_normalized_divide_max"]
    order_ok = raw["paper_vs_scissors"] < raw["rock_vs_paper"] < raw["rock_vs_scissors"]
    claims.append(("C01 FDR ordering PvS < RvP < RvS", order_ok, raw))
    ratio = s1["difficulty_ratio_vs_paper_scissors"]["rock_vs_paper"]
    claims.append(("C01 paper-vs-scissors >10x harder (RvP/PvS)", ratio > 10.0, ratio))

    # per-participant consistency
    pp = s1["per_participant_fdr_max"]
    consistent = all(
        pp["paper_vs_scissors"][str(p)] < pp["rock_vs_paper"][str(p)]
        for p in range(10)
    )
    claims.append(("C01 PvS lowest per participant (all 10)", bool(consistent), None))

    # ---- C02 MLP ----------------------------------------------------------
    s2 = load("mlp_architecture_sweep.json")
    best = s2["best_architecture"]
    claims.append(("C02 best architecture is (64,)", best == "(64,)", best))
    mcc = s2["best_results"]["mean_pairwise_mcc"]
    tol = {"paper_vs_scissors": 0.05, "rock_vs_paper": 0.02, "rock_vs_scissors": 0.02}
    papers = {"paper_vs_scissors": 0.872, "rock_vs_paper": 0.990, "rock_vs_scissors": 1.000}
    for k in papers:
        claims.append((f"C02 MCC {k} within {tol[k]} of paper",
                       abs(mcc[k] - papers[k]) <= tol[k], round(mcc[k], 4)))

    # ---- C03 sensor ablation ---------------------------------------------
    s3 = load("stage3_ablation_results.json")
    map0 = s3["sensor_0based_to_paper_label"]  # "sensor_0" -> "S1" ...
    def has_label(lst, label):
        return any(map0.get(k, k) == label or k == label for k in lst)

    critA = s3["distributional_shift_ablation"]["criticality"]
    critB = s3["delta_fdr_ablation"]["class_criticality"]
    critBm = s3["delta_fdr_ablation"]["class_criticality_mean"]

    for metric_name, crit in [("C03 metricA_shiftFDR", critA),
                              ("C03 metricB_deltaFDR(max)", critB),
                              ("C03 metricB_deltaFDRmean", critBm)]:
        claims.append((f"{metric_name}: S2 in top-3 for paper",
                       has_label(crit["paper"]["top_3"], "S2"),
                       crit["paper"]["top_3"]))
        redundant_ok = all(
            has_label(crit[g]["bottom_3"], "S6") and has_label(crit[g]["bottom_3"], "S7")
            for g in ["rock", "paper", "scissors"]
        )
        claims.append((f"{metric_name}: S6,S7 in bottom-3 all gestures",
                       bool(redundant_ok),
                       {g: crit[g]["bottom_3"] for g in crit}))

    # ---- FDR-MCC correlation (supplementary claims C07 / C12) -----------
    corr = s3["correlation"]["per_pair"]
    claims.append(("C12 PvS FDR-MCC not significant (p>0.05)",
                   corr["paper_vs_scissors"]["p_value"] > 0.05,
                   (round(corr["paper_vs_scissors"]["pearson_r"], 4),
                    round(corr["paper_vs_scissors"]["p_value"], 4))))
    claims.append(("C07 RvS FDR-MCC significant (p<0.05)",
                   corr["rock_vs_scissors"]["p_value"] < 0.05,
                   (round(corr["rock_vs_scissors"]["pearson_r"], 4),
                    round(corr["rock_vs_scissors"]["p_value"], 4))))
    claims.append(("C07 RvP FDR-MCC significant (p<0.05)",
                   corr["rock_vs_paper"]["p_value"] < 0.05,
                   (round(corr["rock_vs_paper"]["pearson_r"], 4),
                    round(corr["rock_vs_paper"]["p_value"], 4))))

    # ---- print -------------------------------------------------------------
    def show(title, checks):
        width = max(len(c[0]) for c in checks)
        n_fail = 0
        print(f"{title}")
        print(f"{'check':<{width}}  {'status':<8} detail")
        print("-" * (width + 60))
        for name, ok, detail in checks:
            print(f"{name:<{width}}  {'PASS' if ok else 'FAIL':<8} {detail}")
            if not ok:
                n_fail += 1
        return n_fail

    print("== infrastructure checks (exit code) ==")
    infra_fail = show("", infra)
    print("\n== claim checks (informational; FAIL = paper claim not supported by data) ==")
    claim_fail = show("", claims)

    print(f"\ninfrastructure: {infra_fail} failed / {len(infra)} checks"
          f"   claims: {claim_fail} failed / {len(claims)} checks")
    print("Claim FAILs are scientific findings, not pipeline errors; "
          "see solution.md for interpretation.")
    return 1 if infra_fail else 0


if __name__ == "__main__":
    sys.exit(main())
