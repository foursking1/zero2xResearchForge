"""Formula-matching evaluation (replica of formula_matching-eval.py flow).

Pipeline (mirrors the repo):
  1. strict one-to-one matching -> tp_strict / fp_strict / fn_strict
  2. build the set of *unmatched* expected (FN) and predicted (FP) entities
  3. run formula matching only on those pairs
  4. combine strict tp + formula tp -> final P/R/F1 (micro & macro)

``matcher`` defaults to the local chemical-formula parser (formula_match).
"""
import os

from common import load_rows, group_by, calculate_metrics
from ner_eval import summarize, evaluate
from formula_match import compute_formula_tp_fp


def _dedup_by_material(d):
    for fname in d:
        seen = set()
        keep = []
        for item in d[fname]:
            if item[2] not in seen:
                seen.add(item[2])
                keep.append(item)
        d[fname] = keep


def run_formula_eval(expected_csv, predicted_csv, matcher=None, verbose=False):
    predicted_rows = load_rows(predicted_csv)
    expected_rows = load_rows(expected_csv)

    predicted_dict = group_by(predicted_rows, 1)
    expected_dict = group_by(expected_rows, 1)
    _dedup_by_material(predicted_dict)
    _dedup_by_material(expected_dict)

    # ---- strict pass ----------------------------------------------------
    tp_strict, fp_strict, fn_strict = evaluate(expected_dict, predicted_dict,
                                               "strict", None)
    strict = summarize(tp_strict, fp_strict, fn_strict)

    # ---- unmatched sets --------------------------------------------------
    matched_expected = {f: set(v["expected"] for v in vals)
                        for f, vals in tp_strict.items()}

    new_expected = {}
    for f, vals in expected_dict.items():
        new_expected[f] = [item for item in vals
                           if item[2] not in matched_expected.get(f, set())]

    not_matched = {}
    for f, vals in fp_strict.items():
        not_matched[f] = [[idx, pid, ent] for idx, (pid, ent) in enumerate(vals)]

    # ---- formula pass (only on strict-unmatched) ------------------------
    tp_form, fp_form, fn_form = {}, {}, {}
    all_errors = []
    for fname in new_expected:
        tp_form[fname], fp_form[fname], fn_form[fname] = [], [], []
        exp_by_pid = group_by(new_expected[fname], 1)
        prd_by_pid = group_by(not_matched.get(fname, []), 1)
        for pid in exp_by_pid:
            exp_text = [x[1] for x in exp_by_pid[pid]]   # rows are [id, material]
            prd_text = [x[1] for x in prd_by_pid.get(pid, [])]
            tp, fp, fn = compute_formula_tp_fp(exp_text, prd_text, matcher)
            tp_form[fname] += [{"expected": e, "predicted": p} for e, p in tp]
            fp_form[fname] += [(pid, e) for e in fp]
            fn_form[fname] += [(pid, e) for e in fn]
            all_errors.extend(tp)

    # ---- combined scores -------------------------------------------------
    new_tp = {f: list(vals) + tp_strict.get(f, []) for f, vals in tp_form.items()}

    p, r, f1, pma, rma, f1ma = calculate_metrics(new_tp, fp_form, fn_form)

    additional = sum(len(v) for v in tp_form.values())

    result = {
        "model": "gpt35_turbo", "strategy": "zero_shot", "matching": "formula",
        "P": p, "R": r, "F1": f1,
        "P_macro": pma, "R_macro": rma, "F1_macro": f1ma,
        "strict_F1": strict["f1_micro"],
        "tp_strict": strict["tp"], "fp_strict": strict["fp"], "fn_strict": strict["fn"],
        "formula_tp": additional, "formula_fp": sum(len(v) for v in fp_form.values()),
        "formula_fn": sum(len(v) for v in fn_form.values()),
        "f1_gain": f1 - strict["f1_micro"],
        "f1_gain_pct": (f1 / strict["f1_micro"] * 100.0) if strict["f1_micro"] else None,
    }
    if verbose:
        result["_new_matches"] = all_errors
    return result