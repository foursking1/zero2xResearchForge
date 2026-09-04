#!/usr/bin/env python3
"""Parts (b) & (c): human-vs-automatic label consistency and coverage /
failure-scenario analysis.

Part (b)
-------
The automatic (CTO) outcome labels are the CTORF binarized predictions from the
frozen phase files (``pred_proba >= 0.5 -> success``). ``labels_and_tickers.csv``
contains no outcome-label column (it is the trial <-> company-ticker linkage
table with LF-style features only), so agreement statistics must be computed by
joining the human labels to the CTORF predictions on ``nct_id``. This is the
same pairing used in part (a); here it is framed as an inter-rater-agreement
question (auto vs. human) and reported with matched-sample sizes per phase.

Part (c)
--------
Failure scenarios / coverage of the fully automatic pipeline:
  * trials in the human gold set never scored by any CTORF phase model
    (e.g. Phase-4 trials, which the paper's framework does not cover);
  * trials with no company ticker link (no stock-price LF);
  * missing values of the individual labeling functions (GPT abstract
    interpretation, headline sentiment, p-values, phase linkage hints) inside
    the phase files;
  * the ``pred_proba == 0`` subgroup (model's all-signals-absent => "clean
    failure" mode) and its agreement with human labels.
"""

import json
from collections import defaultdict

import numpy as np
import pandas as pd
from sklearn.metrics import (accuracy_score, cohen_kappa_score, f1_score,
                             precision_score, recall_score)

from config import PHASE_GROUPS, data_path, find_data_dir, results_dir

LF_COLUMNS = [
    "hint_train", "gpt", "gpt2", "linkage", "linkage2", "stock_price",
    "results_reported", "new_headlines", "pvalues", "update_more_recent",
    "sites", "serious_ae", "patient_drop", "num_patients", "death_ae",
    "amendments", "all_ae", "status",
]
THRESHOLD = 0.5


def load():
    human = pd.read_csv(data_path("human"))
    phases = {
        "I": pd.read_csv(data_path("phase1")).drop_duplicates("nct_id"),
        "II": pd.read_csv(data_path("phase2")).drop_duplicates("nct_id"),
        "III": pd.read_csv(data_path("phase3")).drop_duplicates("nct_id"),
    }
    tickers = pd.read_csv(data_path("tickers"))
    return human, phases, tickers


def _pair(human, phases, ph):
    pred = phases[ph][["nct_id", "pred_proba"]]
    m = human[human["phase"].isin(PHASE_GROUPS[ph])].merge(pred, on="nct_id", how="inner")
    m = m.dropna(subset=["pred_proba"])
    return m


def agreement(df, label):
    y = df["labels"].astype(int)
    y_auto = (df["pred_proba"] >= THRESHOLD).astype(int)
    return {
        "pairing": "human_labels_vs_CTORF_auto_labels",
        "phase": label,
        "n_matched": int(len(df)),
        "f1": float(f1_score(y, y_auto)),
        "precision": float(precision_score(y, y_auto)),
        "recall": float(recall_score(y, y_auto)),
        "kappa": float(cohen_kappa_score(y, y_auto)),
        "accuracy": float(accuracy_score(y, y_auto)),
        "n_human_success": int(y.sum()),
        "n_auto_success": int(y_auto.sum()),
        "threshold": THRESHOLD,
    }


def main():
    human, phases, tickers = load()
    print(f"[load] human={len(human)}  ticker-linkage rows={len(tickers)} "
          f"unique nct={tickers['nct_id'].nunique()}")

    # ---------------- (b) human vs auto agreement ----------------
    pairs = {ph: _pair(human, phases, ph) for ph in ["I", "II", "III"]}
    allc = pd.concat([pairs[ph][["nct_id", "labels", "pred_proba"]] for ph in ["I", "II", "III"]])
    agreements = {ph: agreement(pairs[ph], ph) for ph in ["I", "II", "III"]}
    agreements["all_concat"] = agreement(allc, "all")

    print("\n================ (b) HUMAN vs AUTO (CTORF @0.5) CONSISTENCY ================")
    for k, m in agreements.items():
        print(f"{k:>10}: matched={m['n_matched']:>5}  F1={m['f1']:.4f} "
              f"P={m['precision']:.4f}  R={m['recall']:.4f}  "
              f"kappa={m['kappa']:.4f}  acc={m['accuracy']:.4f}")

    # ---------------- (c) coverage / failure scenarios ----------------
    print("\n================ (c) COVERAGE & FAILURE SCENARIOS ================")

    pid_all = set()
    for ph in ["I", "II", "III"]:
        pid_all |= set(phases[ph]["nct_id"])
    human["in_any_phase_model"] = human["nct_id"].isin(pid_all)
    uncovered = human[~human["in_any_phase_model"]]
    print(f"[coverage] human trials NOT scored by any CTORF phase model: "
          f"{len(uncovered)} / {len(human)} "
          f"-> phase mix {uncovered['phase'].value_counts().to_dict()}")

    human["has_ticker_link"] = human["nct_id"].isin(set(tickers["nct_id"]))
    print(f"[coverage] human trials with a company ticker link (stock LF available): "
          f"{int(human['has_ticker_link'].sum())} / {len(human)} "
          f"({100*human['has_ticker_link'].mean():.1f}%)")

    missing_stats = {}
    for ph in ["I", "II", "III"]:
        df = phases[ph]
        cols = [c for c in LF_COLUMNS if c in df.columns]
        miss = {c: int(((df[c] == -1) | df[c].isna()).sum()) for c in cols}
        missing_stats[ph] = {
            "n_rows": int(len(df)),
            "lf_missing_frac": {c: round(miss[c] / len(df), 4) for c in cols},
        }
    for ph in ["I", "II", "III"]:
        print(f"[missing-LF] phase {ph}: "
              + ", ".join(f"{k}={v:.2f}" for k, v in
                          missing_stats[ph]["lf_missing_frac"].items()
                          if k in ["gpt", "stock_price", "new_headlines",
                                   "pvalues", "linkage", "hint_train"]))

    # pred==0 subgroup within matched eval sets
    zero_stats = {}
    for ph in ["I", "II", "III", "all"]:
        base = pairs[ph] if ph != "all" else allc
        z = base[base["pred_proba"] == 0]
        zero_stats[ph] = {
            "n_pred0": int(len(z)),
            "frac_pred0": round(len(z) / len(base), 4),
            "human_labels_at_pred0": dict(z["labels"].value_counts().sort_index().astype(int)),
        }
    print(f"[pred=0 subgroup] (all human-failure in our data): {zero_stats}")

    # any auto signal the ticker table itself can supply: slope sign distribution
    slope_pos = (tickers["Slope"] > 0).sum()
    print(f"[ticker LFs] Slope>0 (positive stock signal): {slope_pos}/{len(tickers)} "
          f"({100*slope_pos/len(tickers):.1f}%); mean-slope rows with NaN AE info: "
          f"{int(tickers['total_ae'].isna().sum())}/{len(tickers)}")

    # ---------------- write outputs ----------------
    ag_df = pd.DataFrame(list(agreements.values()))
    ag_df.to_csv(results_dir() / "consistency_table.csv", index=False)

    miss_rows = []
    for ph in ["I", "II", "III"]:
        for k, v in missing_stats[ph]["lf_missing_frac"].items():
            miss_rows.append({"phase": ph, "labeling_function": k,
                              "n_rows": missing_stats[ph]["n_rows"],
                              "missing_frac": v})
    miss_df = pd.DataFrame(miss_rows)
    miss_df.to_csv(results_dir() / "coverage_lf_missing.csv", index=False)

    cov = pd.DataFrame([
        {"analysis": "human_trials_covered_by_phase_model",
         "numerator": int(human["in_any_phase_model"].sum()),
         "denominator": len(human), "frac": round(human["in_any_phase_model"].mean(), 4)},
        {"analysis": "human_trials_with_ticker_link",
         "numerator": int(human["has_ticker_link"].sum()),
         "denominator": len(human), "frac": round(human["has_ticker_link"].mean(), 4)},
        {"analysis": "uncovered_human_phase4_trials",
         "numerator": int(((~human["in_any_phase_model"]) & (human["phase"] == "PHASE4")).sum()),
         "denominator": len(human), "frac": None},
    ])
    cov.to_csv(results_dir() / "coverage_summary.csv", index=False)

    out = {
        "task": "2406.10292_cto_trial_outcomes",
        "part": "bc_consistency_and_failure_scenarios",
        "auto_label_definition": "CTORF pred_proba >= 0.5 -> success",
        "labels_and_tickers_role": ("trial<->ticker linkage + stock/AE features; "
                                    "no outcome-label column present in the frozen file"),
        "human_auto_agreement": agreements,
        "matched_sample_sizes_paper_expected": {"I": 3239, "II": 5060, "III": 2823},
        "coverage": {
            "human_total": len(human),
            "human_covered_by_any_phase_model": int(human["in_any_phase_model"].sum()),
            "uncovered_by_phase": dict(uncovered["phase"].value_counts()),
            "human_with_ticker_link": int(human["has_ticker_link"].sum()),
            "ticker_links_total": len(tickers),
            "lf_missing_frac": missing_stats,
            "pred0_subgroup": zero_stats,
        },
    }
    with open(results_dir() / "metrics_part_bc.json", "w") as f:
        json.dump(out, f, indent=2, default=str)

    # ---------------- combined evidence table (a + b) ----------------
    ev_rows = []
    for k, m in agreements.items():
        phase = "all" if k.startswith("all") else k
        for metric in ["f1", "precision", "recall", "kappa", "accuracy"]:
            ev_rows.append({"phase": phase, "source": "human_vs_auto_CTORF",
                            "metric": metric, "value": round(m[metric], 6)})
    ev_df = pd.DataFrame(ev_rows)
    part_a = pd.read_csv(results_dir() / "evidence_table_part_a.csv")
    combined = pd.concat([part_a[["phase", "source", "metric", "value"]],
                          ev_df], ignore_index=True).drop_duplicates()
    combined = combined.round({"value": 6})
    combined.to_csv(results_dir() / "evidence_table.csv", index=False)
    print(f"\n[done] results written to {results_dir()}")


if __name__ == "__main__":
    main()