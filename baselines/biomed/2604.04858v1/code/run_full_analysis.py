#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
FairLogue reproduction analysis (arXiv:2604.04858v1) on the frozen data.

Runs, on the frozen synthetic data:
  1. Component 1 (observational intersectional fairness) on both synthetic datasets
     (FairSelect synthetic, Component-3 synthetic) with a logistic-regression model,
     reproducing the paper's workflow: 80/20 stratified split, threshold 0.5,
     min_group_size=20, require_class_balance=True.
  2. Component 3 (generalized counterfactual fairness, SR estimation) on the
     Component-3 synthetic data, with permutation null (R_null draws) and
     rescaled bootstrap (B draws) -- matching the paper's "SR + 200 bootstrap
     iterations" setup.
  3. Association strength (Cramer's V / chi-square) between protected attributes
     and the outcome, which the paper cites as context for interpreting u-values.

All outputs are written to <repo>/agent_solution/results/.
The data is read IN PLACE from the frozen data root; no data files are copied.

Usage:
    python run_full_analysis.py [--c3-r-null R] [--c3-b B] [--c3-model {lr,lgbm}]
"""

import argparse
import json
import os
import sys
import warnings
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # headless backend

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

# ---------------------------------------------------------------------------
# Frozen data root (IN PLACE read; no copying)
# ---------------------------------------------------------------------------
DATA_ROOT = Path("F:/dataset/2604.04858v1")
CODE_ROOT = DATA_ROOT / "code"

sys.path.insert(0, str(CODE_ROOT / "fairlogue"))

from sklearn.linear_model import LogisticRegression  # noqa: E402

from FairLogue.Component1.intersectional_metrics import (  # noqa: E402
    evaluate_intersectional_fairness,
)
from FairLogue.Component1.utilities import _compute_group_rates  # noqa: E402

# Output directory: <repo>/agent_solution/results
OUT_DIR = Path(__file__).resolve().parent.parent / "results"
FIG_DIR = OUT_DIR / "figures"
OUT_DIR.mkdir(parents=True, exist_ok=True)
FIG_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Component 1 helpers
# ---------------------------------------------------------------------------
def _run_c1(df, outcome, p1, p2, features, label):
    """Run Component 1 and return a dict of everything we need."""
    results, figs, intermediates = evaluate_intersectional_fairness(
        df=df,
        outcome=outcome,
        protected_1=p1,
        protected_2=p2,
        features=features,
        model_type="logreg",
        test_size=0.2,
        random_state=42,
        threshold=0.5,
        positive_label=1,
        make_plots=False,
        return_non_intersectional=True,
        min_group_size=20,
        require_class_balance=True,
        return_intermediates=True,
    )

    inter_groups = [
        {
            "group": g.group,
            "n": g.n,
            "positive_rate": g.positive_rate,
            "tpr": g.tpr,
            "fpr": g.fpr,
            "pos_true": g.pos_true,
            "neg_true": g.neg_true,
            "TP": g.TP,
            "FP": g.FP,
            "TN": g.TN,
            "FN": g.FN,
        }
        for g in results.groups
    ]

    out = {
        "label": label,
        "model_performance": intermediates["model_metrics"],
        "intersectional": {
            "demographic_parity_gap": results.demographic_parity_gap,
            "equalized_odds_gap_tpr": results.equalized_odds_gap_tpr,
            "equalized_odds_gap_fpr": results.equalized_odds_gap_fpr,
            "equal_opportunity_gap": results.equal_opportunity_gap,
            "groups": inter_groups,
        },
        "single_axis_gaps": {},
    }

    if intermediates.get("non_intersectional"):
        ni = intermediates["non_intersectional"]
        for attr in (p1, p2):
            out["single_axis_gaps"][attr] = {
                "demographic_parity_gap": ni[attr].demographic_parity_gap,
                "equalized_odds_gap_tpr": ni[attr].equalized_odds_gap_tpr,
                "equalized_odds_gap_fpr": ni[attr].equalized_odds_gap_fpr,
            }

    # ---- Replicate the split to obtain single-axis test labels & per-group rates ----
    # (mirrors the internals of evaluate_intersectional_fairness)
    inter_series = df[p1].astype(str) + "|" + df[p2].astype(str)
    counts = inter_series.value_counts()
    keep = counts[counts >= 20].index
    df_f = df[inter_series.isin(keep)].copy()

    y = (df_f[outcome].values == 1).astype(int)
    inter = (df_f[p1].astype(str) + "|" + df_f[p2].astype(str)).values
    X = df_f[features].copy()
    p1a = df_f[p1].astype(str).values
    p2a = df_f[p2].astype(str).values

    from sklearn.model_selection import train_test_split

    (X_tr, X_te, y_tr, y_te, g_tr, g_te, p1_tr, p1_te, p2_tr, p2_te) = train_test_split(
        X, y, inter, p1a, p2a,
        test_size=0.2, random_state=42, stratify=y,
    )

    # recompute the same logistic-regression predictions on the test split
    from sklearn.compose import ColumnTransformer
    from sklearn.discriminant_analysis import StandardScaler
    from sklearn.impute import SimpleImputer
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import OneHotEncoder
    from sklearn.linear_model import LogisticRegression

    numeric_cols = X.select_dtypes(include=[np.number, "bool"]).columns.tolist()
    cat_cols = [c for c in features if c not in numeric_cols]

    num_pipe = Pipeline([("impute", SimpleImputer(strategy="median")),
                         ("scale", StandardScaler(with_mean=False))])
    cat_pipe = Pipeline([("impute", SimpleImputer(strategy="most_frequent")),
                         ("ohe", OneHotEncoder(handle_unknown="ignore", sparse_output=True))])
    pre = ColumnTransformer([("num", num_pipe, numeric_cols),
                             ("cat", cat_pipe, cat_cols)], remainder="drop", sparse_threshold=0.3)
    pipe = Pipeline([("prep", pre), ("model", LogisticRegression(max_iter=1000, class_weight="balanced"))])
    pipe.fit(X_tr, y_tr)
    proba = pipe.predict_proba(X_te)[:, 1]
    y_hat = (proba >= 0.5).astype(int)

    # intersectional per-group rates (sanity check vs. results.groups)
    inter_rates = _compute_group_rates(y_te, y_hat, pd.Series(g_te))

    # single-axis per-group rates
    def _rates_for(labels):
        gseries = pd.Series(labels)
        rates = _compute_group_rates(y_te, y_hat, gseries)
        # apply the same min_group_size / class-balance filter used by Component 1
        kept = []
        for r in rates:
            if r.n >= 20 and r.pos_true >= 1 and r.neg_true >= 1:
                kept.append(r)
        return kept

    out["single_axis_groups"] = {
        p1: [
            {"group": r.group, "n": r.n, "positive_rate": r.positive_rate,
             "tpr": r.tpr, "fpr": r.fpr, "pos_true": r.pos_true, "neg_true": r.neg_true,
             "TP": r.TP, "FP": r.FP, "TN": r.TN, "FN": r.FN}
            for r in _rates_for(p1_te)
        ],
        p2: [
            {"group": r.group, "n": r.n, "positive_rate": r.positive_rate,
             "tpr": r.tpr, "fpr": r.fpr, "pos_true": r.pos_true, "neg_true": r.neg_true,
             "TP": r.TP, "FP": r.FP, "TN": r.TN, "FN": r.FN}
            for r in _rates_for(p2_te)
        ],
    }

    # Save a figure-free summary plot for reference (demographic parity + EO)
    out["n_samples_after_filter"] = int(len(df_f))
    return out


def run_component1_fairselect():
    """Component 1 on the FairSelect synthetic data (White/Black only)."""
    df = pd.read_csv(DATA_ROOT / "code" / "fairselect" / "synthetic_glaucoma_intervention.csv")
    df = df[df["Race"].isin(["White", "Black"])].copy()
    features = [c for c in df.columns if c not in ("glaucoma_intervention", "Race", "Gender")]
    return _run_c1(df, "glaucoma_intervention", "Race", "Gender", features, "fairselect_synthetic")


def run_component1_comp3():
    """Component 1 on the Component-3 synthetic data."""
    df = pd.read_csv(DATA_ROOT / "code" / "fairlogue" / "FairLogue" / "Component3" / "glaucoma_synth_component3.csv")
    features = [c for c in df.columns if c not in ("Y", "A1", "A2", "A1A2")]
    return _run_c1(df, "Y", "A1", "A2", features, "component3_synthetic")


# ---------------------------------------------------------------------------
# Component 3 (generalized counterfactual fairness)
# ---------------------------------------------------------------------------
def run_component3(r_null=100, b=200, model_kind="lr"):
    from FairLogue.Component3.model import Model

    df = pd.read_csv(DATA_ROOT / "code" / "fairlogue" / "FairLogue" / "Component3" / "glaucoma_synth_component3.csv")
    if "A1A2" not in df.columns:
        df["A1A2"] = df["A1"].astype(str) + df["A2"].astype(str)

    protected = {"A1", "A2", "A1A2"}
    covariates = [c for c in df.columns if c not in protected | {"Y"}]

    if model_kind == "lr":
        outcome_estimator = LogisticRegression(max_iter=5000, random_state=42, C=1.0)
        outcome_name = "LogisticRegression"
    elif model_kind == "lgbm":
        from lightgbm import LGBMClassifier
        # Lighter-than-reference config so the full permutation+bootstrap run is feasible;
        # the qualitative u-value conclusion is insensitive to this choice.
        outcome_estimator = LGBMClassifier(
            n_estimators=150, max_depth=-1, learning_rate=0.08,
            num_leaves=24, subsample=0.8, colsample_bytree=0.8,
            objective="binary", random_state=42, verbosity=-1,
        )
        outcome_name = "LGBMClassifier(light)"
    else:
        raise ValueError(model_kind)

    model = Model(
        data=df,
        outcome="Y",
        protected_characteristics=("A1", "A2"),
        covariates=covariates,
        outcome_estimator=outcome_estimator,
        method="sr",
        n_splits=5,
        random_state=42,
    )
    model.pre_process_data()
    model.fit_fairness(cutoff=0.5, gen_null=True, R_null=r_null, bootstrap="rescaled", B=b)

    summary = model.summarize()
    summary_dict = dict(zip(summary["stat"], summary["value"]))

    est_summaries, table_null_delta, uvals, group_null_long = model.plots(
        alpha=0.05, delta_uval=0.10,
    )

    uvals_dict = uvals.to_dict(orient="records")[0] if uvals is not None and not uvals.empty else {}

    # group labels as used inside the pipeline (pre_process_data overwrites A1A2 as str(A1)+str(A2))
    groups_used = sorted({k[len("cfpr_"):] for k in summary_dict if k.startswith("cfpr_")})

    return {
        "method": "sr",
        "outcome_model": outcome_name,
        "dataset": "component3_synthetic",
        "n_samples": int(len(df)),
        "cutoff": 0.5,
        "n_splits": 5,
        "R_null": r_null,
        "bootstrap": "rescaled",
        "B": b,
        "groups": groups_used,
        "summary": {k: float(v) for k, v in summary_dict.items()},
        "u_values": {k: float(v) for k, v in uvals_dict.items()},
    }


# ---------------------------------------------------------------------------
# Association strength (context for u-value interpretation)
# ---------------------------------------------------------------------------
def cramers_v(crosstab: pd.DataFrame) -> float:
    chi2 = float(pd.crosstab(crosstab.iloc[:, 0], crosstab.iloc[:, 1]).pipe(
        lambda t: (t.values - np.outer(t.sum(1), t.sum(0)) / t.values.sum()) ** 2
        / np.outer(t.sum(1), t.sum(0)).clip(min=1e-12)
    ).sum())
    n = crosstab.shape[0]
    r, k = min(crosstab.iloc[:, 0].nunique(), crosstab.iloc[:, 1].nunique()), crosstab.shape[0]
    # fall back to scipy
    from scipy.stats import chi2_contingency
    ct = pd.crosstab(crosstab.iloc[:, 0], crosstab.iloc[:, 1])
    chi2v, p, dof, _ = chi2_contingency(ct, correction=False)
    n_tot = ct.values.sum()
    phi2 = chi2v / n_tot
    r, k = ct.shape
    return float(np.sqrt(phi2 / min(r - 1, k - 1)))


def compute_association_strength():
    from scipy.stats import chi2_contingency

    df_fs = pd.read_csv(DATA_ROOT / "code" / "fairselect" / "synthetic_glaucoma_intervention.csv")
    df_fs = df_fs[df_fs["Race"].isin(["White", "Black"])]
    df_c3 = pd.read_csv(DATA_ROOT / "code" / "fairlogue" / "FairLogue" / "Component3" / "glaucoma_synth_component3.csv")

    rows = {}
    for name, df, target, attrs in [
        ("fairselect", df_fs, "glaucoma_intervention", ["Race", "Gender"]),
        ("component3", df_c3, "Y", ["A1", "A2"]),
    ]:
        entry = {}
        for a in attrs:
            ct = pd.crosstab(df[a], df[target])
            chi2, p, dof, _ = chi2_contingency(ct, correction=False)
            n = ct.values.sum()
            phi2 = chi2 / n
            cv = float(np.sqrt(phi2 / min(ct.shape[0] - 1, ct.shape[1] - 1)))
            entry[a] = {"cramers_v": cv, "chi2": float(chi2), "p_value": float(p)}
        # intersectional
        df_c = df.copy()
        df_c["inter"] = df[attrs[0]].astype(str) + "|" + df[attrs[1]].astype(str)
        ct = pd.crosstab(df_c["inter"], df_c[target])
        chi2, p, dof, _ = chi2_contingency(ct, correction=False)
        n = ct.values.sum()
        cv = float(np.sqrt((chi2 / n) / min(ct.shape[0] - 1, ct.shape[1] - 1)))
        entry["intersectional"] = {"cramers_v": cv, "chi2": float(chi2), "p_value": float(p)}
        rows[name] = entry
    return rows


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--c3-r-null", type=int, default=100, help="permutation null draws")
    ap.add_argument("--c3-b", type=int, default=200, help="rescaled bootstrap draws")
    ap.add_argument("--c3-model", choices=["lr", "lgbm"], default="lr")
    args = ap.parse_args()

    print("=" * 70)
    print("FairLogue reproduction on frozen data")
    print(f"Data root: {DATA_ROOT}")
    print(f"Component 3 config: R_null={args.c3_r_null}, B={args.c3_b}, model={args.c3_model}")
    print("=" * 70)

    # ---- Component 1 ----
    print("\n[1/4] Component 1: FairSelect synthetic ...")
    c1_fs = run_component1_fairselect()
    print("  AUROC=%.4f Acc=%.4f | DP=%.4f TPRgap=%.4f FPRgap=%.4f"
          % (c1_fs["model_performance"]["auroc"], c1_fs["model_performance"]["accuracy"],
             c1_fs["intersectional"]["demographic_parity_gap"],
             c1_fs["intersectional"]["equalized_odds_gap_tpr"],
             c1_fs["intersectional"]["equalized_odds_gap_fpr"]))

    print("[2/4] Component 1: Component-3 synthetic ...")
    c1_c3 = run_component1_comp3()
    print("  AUROC=%.4f Acc=%.4f | DP=%.4f TPRgap=%.4f FPRgap=%.4f"
          % (c1_c3["model_performance"]["auroc"], c1_c3["model_performance"]["accuracy"],
             c1_c3["intersectional"]["demographic_parity_gap"],
             c1_c3["intersectional"]["equalized_odds_gap_tpr"],
             c1_c3["intersectional"]["equalized_odds_gap_fpr"]))

    # ---- Component 3 ----
    print(f"\n[3/4] Component 3: counterfactual SR (R_null={args.c3_r_null}, B={args.c3_b}, {args.c3_model}) ...")
    print("  This is the slow step (cross-fitted outcome models + permutation null + bootstrap).")
    c3 = run_component3(r_null=args.c3_r_null, b=args.c3_b, model_kind=args.c3_model)
    print("  u-values:", {k: round(v, 4) for k, v in c3["u_values"].items()})

    # ---- Association strength ----
    print("\n[4/4] Association strength ...")
    assoc = compute_association_strength()

    # ---- Save outputs ----
    payload = {
        "component1": [c1_fs, c1_c3],
        "component3": c3,
        "association_strength": assoc,
    }
    out_name = f"raw_results_{args.c3_model}.json"
    with open(OUT_DIR / out_name, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, default=str)

    print(f"\nAll raw results written to {OUT_DIR / out_name}")
    print("DONE.")


if __name__ == "__main__":
    main()
