#!/usr/bin/env python3
"""Part (a): reproduce CTORF evaluation metrics from the frozen per-phase CTORF
prediction files.

The frozen files `phase{1,2,3}_CTO_rf.csv` contain the CTORF model's predicted
probability of trial success (``pred_proba``) for every trial in the CTO
knowledge base. The paper's Table 1 evaluates CTORF against the human-annotated
TOP test set (trials completed 2020-2024) per trial phase.

Protocol used here (mirrors the paper):
  1. Each trial's phase group is assigned through the paper's training design:
     the Phase-I CTORF model covers human phases {PHASE1, PHASE1/PHASE2,
     EARLY_PHASE1}, Phase-II covers {PHASE2, PHASE1/PHASE2, PHASE2/PHASE3} and
     Phase-III covers {PHASE3, PHASE2/PHASE3}. This reproduces the paper's
     matched sample sizes (3,239 / 5,060 / 2,823).
  2. Deduplication: a trial may appear several times within one phase file;
     duplicate rows carry (almost) identical probabilities, so the first row is
     kept (pre-prediction features are otherwise identical).
  3. Decision rule: label "success" if ``pred_proba >= threshold``. The primary
     threshold is the standard 0.5; a full sweep over thresholds is also
     exported so that the effect of the (paper-mandated) "phase-optimized
     threshold" can be inspected.
  4. Metrics: macro F1 on the positive (=success) class, precision, recall,
     Cohen's kappa and accuracy vs the human label.
  5. The "all phases" aggregate pools the per-phase evaluation sets (a trial
     spanning two phases is scored by each relevant phase model, matching the
     paper's phase-wise training + pooled evaluation); the unique-trial variant
     is reported alongside for transparency.
"""

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import (accuracy_score, cohen_kappa_score, f1_score,
                             precision_score, recall_score)

from config import (EXPECTED_SHA256, PHASE_GROUPS, data_path, find_data_dir,
                    results_dir)

PAPER = {
    "I": {"f1": 0.913, "kappa": 0.790},
    "II": {"f1": 0.878, "kappa": 0.693},
    "III": {"f1": 0.941, "kappa": 0.710},
    "all": {"f1": 0.909, "kappa": 0.729},
}
PRIMARY_THRESHOLD = 0.5
SWEEP_THRESHOLDS = np.round(np.arange(0.50, 0.71, 0.01), 2)


def sha256_hex(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def verify_data():
    reports = {}
    for key, fname in {
        "human": "human_labels_2020_2024.csv",
        "tickers": "labels_and_tickers.csv",
    }.items():
        f = data_path(key)
        got = sha256_hex(f)
        exp = EXPECTED_SHA256[fname]
        reports[fname] = {"expected": exp, "actual": got, "match": got == exp}
        status = "OK" if got == exp else "MISMATCH"
        print(f"[checksum] {fname}: {status}")
        if got != exp:
            print(f"  expected {exp}\n  actual   {got}", file=sys.stderr)
    for ph in ["phase1", "phase2", "phase3"]:
        f = data_path(ph)
        got = sha256_hex(f)
        exp = EXPECTED_SHA256[data_path(ph).name]
        reports[data_path(ph).name] = {"expected": exp, "actual": got, "match": got == exp}
        print(f"[checksum] {data_path(ph).name}: {'OK' if got == exp else 'MISMATCH'}")
    return reports


def load_data():
    human = pd.read_csv(data_path("human"))
    phases = {
        "I": pd.read_csv(data_path("phase1"))[["nct_id", "pred_proba"]].drop_duplicates("nct_id"),
        "II": pd.read_csv(data_path("phase2"))[["nct_id", "pred_proba"]].drop_duplicates("nct_id"),
        "III": pd.read_csv(data_path("phase3"))[["nct_id", "pred_proba"]].drop_duplicates("nct_id"),
    }
    return human, phases


def build_eval_frames(human: pd.DataFrame, phases: dict):
    """Join each phase model's predictions to the human labels restricted to
    that phase group. Returns dict phase -> DataFrame(nct_id, labels,
    pred_proba)."""
    frames = {}
    for ph, pred in phases.items():
        mask = human["phase"].isin(PHASE_GROUPS[ph])
        m = (
            human[mask]
            .merge(pred, on="nct_id", how="left")
            .dropna(subset=["pred_proba"])
            .copy()
        )
        m["phase_group"] = ph
        frames[ph] = m
    return frames


def metrics(df: pd.DataFrame, threshold: float, label: str) -> dict:
    y = df["labels"].astype(int)
    y_pred = (df["pred_proba"] >= threshold).astype(int)
    return {
        "phase": label,
        "n": int(len(df)),
        "threshold": float(threshold),
        "f1": float(f1_score(y, y_pred)),
        "precision": float(precision_score(y, y_pred)),
        "recall": float(recall_score(y, y_pred)),
        "kappa": float(cohen_kappa_score(y, y_pred)),
        "accuracy": float(accuracy_score(y, y_pred)),
        "n_human_success": int(y.sum()),
        "n_pred_success": int(y_pred.sum()),
    }


def main():
    data_dir = find_data_dir()
    print(f"[data] using frozen data at {data_dir}")
    checks = verify_data()
    if not all(c["match"] for c in checks.values()):
        print("[warn] one or more checksums mismatched; continuing (verify package integrity)")

    human, phases = load_data()
    print(f"[human] {len(human)} annotated trials; labels ",
          dict(human["labels"].value_counts().sort_index()))
    frames = build_eval_frames(human, phases)
    for ph, m in frames.items():
        print(f"[match] phase {ph}: {len(m)} matched trials "
              f"(paper reports {PAPER[ph]})")

    # ---------------- primary metrics @ 0.5 ----------------
    all_concat = pd.concat([frames[ph][["nct_id", "labels", "pred_proba", "phase_group"]]
                            for ph in ["I", "II", "III"]])
    all_unique = all_concat.drop_duplicates("nct_id")

    primary = {}
    for ph in ["I", "II", "III"]:
        primary[ph] = metrics(frames[ph], PRIMARY_THRESHOLD, ph)
    primary["all_concat"] = metrics(all_concat, PRIMARY_THRESHOLD, "all")
    primary["all_unique"] = metrics(all_unique, PRIMARY_THRESHOLD, "all")

    print("\n================ PRIMARY METRICS @ threshold = 0.5 ================")
    for k, m in primary.items():
        print(f"{k:>10}: n={m['n']:>5}  F1={m['f1']:.4f}  P={m['precision']:.4f}  "
              f"R={m['recall']:.4f}  kappa={m['kappa']:.4f}  "
              f"acc={m['accuracy']:.4f}")

    # ---------------- threshold sweep ----------------
    rows = []
    for ph in ["I", "II", "III", "all"]:
        base = frames[ph] if ph != "all" else all_concat
        for th in SWEEP_THRESHOLDS:
            rows.append(metrics(base, float(th), ph))
    sweep = pd.DataFrame(rows)
    sweep.to_csv(results_dir() / "ctorf_threshold_sweep.csv", index=False)
    print(f"\n[sweep] saved {len(sweep)} rows -> results/ctorf_threshold_sweep.csv")

    # ---------------- paper-anchor comparison ----------------
    comparison = []
    for key in ["I", "II", "III", "all_concat"]:
        m = primary[key]
        anchor_phase = key if key != "all_concat" else "all"
        anchor = PAPER[anchor_phase]
        for metric in ["f1", "kappa"]:
            rel = (
                abs(m[metric] - anchor[metric]) / anchor[metric]
                if anchor[metric]
                else float("nan")
            )
            comparison.append({
                "phase": anchor_phase,
                "group": key,
                "metric": metric,
                "paper_value": anchor[metric],
                "reproduced_value": m[metric],
                "abs_diff": m[metric] - anchor[metric],
                "rel_diff_pct": round(rel * 100.0, 3),
            })
    cmp_df = pd.DataFrame(comparison)
    cmp_df.to_csv(results_dir() / "paper_anchor_comparison.csv", index=False)
    print("\n================ PAPER ANCHOR COMPARISON ================")
    print(cmp_df.to_string(index=False))

    # ---------------- evidence table (part a) ----------------
    ev = []
    for k, m in primary.items():
        if k == "all_unique":
            continue  # keep pooled all_concat as the single "all" row here
        phase = "all" if k.startswith("all") else k
        for metric in ["f1", "precision", "recall", "kappa", "accuracy"]:
            ev.append({"phase": phase, "eval_group": k, "source": "CTORF_reproduction",
                       "metric": metric, "value": round(m[metric], 6), "n": m["n"]})
    ev.append({"phase": "all", "eval_group": "all_concat", "source": "CTORF_reproduction",
               "metric": "matched_trials", "value": primary["all_concat"]["n"], "n": primary["all_concat"]["n"]})
    ev_df = pd.DataFrame(ev)
    ev_df.to_csv(results_dir() / "evidence_table_part_a.csv", index=False)

    # ---------------- machine-readable summary ----------------
    out = {
        "task": "2406.10292_cto_trial_outcomes",
        "part": "a_ctorf_reproduction",
        "primary_threshold": PRIMARY_THRESHOLD,
        "data_dir": str(data_dir),
        "checksums": checks,
        "matched_sample_sizes": {ph: primary[ph]["n"] for ph in ["I", "II", "III"]},
        "paper_matched_expected": {"I": 3239, "II": 5060, "III": 2823},
        "metrics": primary,
        "paper_anchor_comparison": comparison,
    }
    with open(results_dir() / "metrics_part_a.json", "w") as f:
        json.dump(out, f, indent=2, default=str)
    print(f"\n[done] results written to {results_dir()}")


if __name__ == "__main__":
    main()