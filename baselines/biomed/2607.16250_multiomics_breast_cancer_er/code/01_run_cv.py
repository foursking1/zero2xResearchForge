#!/usr/bin/env python3
"""01_run_cv.py — Run the full ER-status experiment matrix.

Main table (no leakage): 6 models x 5 omic sets x stratified 5-fold CV,
fold-internal variance-based feature selection.

Secondary no-leakage variant for RF & XGBoost on RNA / RNA+CNV+RPPA:
fold-internal univariate (F-test) selection.

Leakage control (RF & XGBoost on RNA / RNA+CNV+RPPA):
the SAME selection rules but estimated on the FULL dataset before splitting
(variance_full and univariate_full scopes).

Outputs:
  results/evidence_table.csv   (rows: model,omic_set,feature_selection,balanced_acc,macro_f1,roc_auc,...)
  results/perfold_results.json
  results/metrics.json
"""
import argparse
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pipeline import OMIC_SETS, cv_to_row, run_cv  # noqa: E402

SEED = 42


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default="results", help="dir holding assembled.npz")
    ap.add_argument("--out-dir", default="results")
    ap.add_argument("--quick", action="store_true", help="subset of configs (smoke test)")
    args = ap.parse_args()
    os.makedirs(args.out_dir, exist_ok=True)

    d = np.load(os.path.join(args.data_dir, "assembled.npz"), allow_pickle=True)
    X_by_omic = {"rna": d["X_rna"].astype(float), "cna": d["X_cna"].astype(float),
                 "rppa": d["X_rppa"].astype(float)}
    y = d["y"].astype(int)
    print(f"[run] cohort: {len(y)} samples, ER+ {y.mean():.3f}")

    main_omic_sets = list(OMIC_SETS.keys())
    if args.quick:
        main_omic_sets = ["RNA", "RNA+CNV+RPPA"]

    results = []
    # ---- main table: fold-internal variance selection, all models x all omic sets
    for omic_set in main_omic_sets:
        for model in ["RF", "XGBoost", "LightGBM", "CatBoost", "SVM", "LR"]:
            r = run_cv(X_by_omic, y, omic_set, model, method="variance",
                       scope="fold_internal", seed=SEED)
            results.append(r)
            print(f"[main] {model:<10} {omic_set:<12} BA={r['balanced_acc']:.4f} "
                  f"mF1={r['macro_f1']:.4f} AUC={r['roc_auc']:.4f}")

    # ---- secondary no-leak variant: fold-internal univariate selection (RF, XGBoost)
    for omic_set in ["RNA", "RNA+CNV+RPPA"]:
        for model in ["RF", "XGBoost"]:
            r = run_cv(X_by_omic, y, omic_set, model, method="univariate",
                       scope="fold_internal", seed=SEED)
            results.append(r)
            print(f"[uni ] {model:<10} {omic_set:<12} BA={r['balanced_acc']:.4f} "
                  f"mF1={r['macro_f1']:.4f} AUC={r['roc_auc']:.4f}")

    # ---- leakage control: selection/scaling on FULL data before splitting
    for omic_set in ["RNA", "RNA+CNV+RPPA"]:
        for model in ["RF", "XGBoost"]:
            for method in ["variance", "univariate"]:
                r = run_cv(X_by_omic, y, omic_set, model, method=method,
                           scope="full_data", seed=SEED)
                results.append(r)
                print(f"[leak] {model:<10} {omic_set:<12} {method:<9} "
                      f"BA={r['balanced_acc']:.4f} AUC={r['roc_auc']:.4f}")

    rows = [cv_to_row(r) for r in results]
    table = pd.DataFrame(rows).sort_values(["feature_selection", "omic_set", "model"])
    table.to_csv(os.path.join(args.out_dir, "evidence_table.csv"), index=False)

    with open(os.path.join(args.out_dir, "perfold_results.json"), "w") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"[run] wrote {len(results)} configs -> evidence_table.csv, perfold_results.json")


if __name__ == "__main__":
    main()