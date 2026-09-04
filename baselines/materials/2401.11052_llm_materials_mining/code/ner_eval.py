"""NER evaluation (materials SuperMat holdout, properties MeasEval).

Faithful offline re-implementation of the repo's
``llm_mat_evaluation/ner/eval_ner.py`` (Apache-2.0), with one extension:
an optional local *formula* matcher (see formula_match.py) that replaces
the Grobid supercon-material webservice used in the original pipeline.
"""
import os

from common import (load_rows, group_by, get_matches, calculate_metrics,
                    pick_data_home)


def evaluate(expected_dict, predicted_dict, matching_type, matching_threshold, matcher=None):
    """Per-file tp/fp/fn dicts.  matcher: callable(entity_str)->result for formula matching."""
    tp_by_file, fp_by_file, fn_by_file = {}, {}, {}
    for filename in expected_dict:
        tp_by_file[filename] = []
        fp_by_file[filename] = []
        fn_by_file[filename] = []

        expected_records = expected_dict[filename]
        predicted_records = predicted_dict.get(filename, [])

        expected_by_pid = group_by(expected_records, 1)
        predicted_by_pid = group_by(predicted_records, 1)

        for pid in expected_by_pid:
            predicted_in_pid = [x[1] for x in predicted_by_pid[pid]] if pid in predicted_by_pid else []
            expected_in_pid = [x[1] for x in expected_by_pid[pid]]

            if matcher is not None:
                tp, fp, fn = match_by_formula_lists(expected_in_pid, predicted_in_pid, matcher)
            else:
                tp, fp, fn = get_matches(expected_in_pid, predicted_in_pid,
                                         matching_type, matching_threshold)
            tp_by_file[filename] += tp
            fp_by_file[filename] += [(pid, f) for f in fp]
            fn_by_file[filename] += [(pid, f) for f in fn]

    return tp_by_file, fp_by_file, fn_by_file


def match_by_formula_lists(expected_in_pid, predicted_in_pid, matcher):
    """One-to-one greedy match by chemical composition (formula matching)."""
    from formula_match import match_by_formula
    tp, fp, fn = [], [], []
    skip_predicted, skip_expected = set(), set()
    for idxp, predicted_entity in enumerate(predicted_in_pid):
        if idxp in skip_predicted:
            continue
        is_match = False
        for idxe, expected_entity in enumerate(expected_in_pid):
            if idxe in skip_expected:
                continue
            # exact string equality is always a formula match ground case
            if match_by_formula(expected_entity, predicted_entity, matcher):
                tp.append({"expected": expected_entity, "predicted": predicted_entity})
                skip_predicted.add(idxp)
                skip_expected.add(idxe)
                is_match = True
                break
        if not is_match:
            fp.append(predicted_entity)
    for idxe, expected_entity in enumerate(expected_in_pid):
        if idxe not in skip_expected:
            fn.append(expected_entity)
    assert len(tp) + len(fp) == len(predicted_in_pid)
    assert len(tp) + len(fn) == len(expected_in_pid)
    return tp, fp, fn


def load_expected(path):
    rows = load_rows(path)
    return group_by(rows, 1)


def run_ner_eval(expected_csv, predicted_csv, matching_type="strict",
                 matching_threshold=None, entity_type="material", matcher=None):
    """Wrapper replicating eval_ner.py CLI behaviour."""
    predicted_rows = load_rows(predicted_csv)
    expected_rows = load_rows(expected_csv)

    predicted_dict = group_by(predicted_rows, 1)
    expected_dict = group_by(expected_rows, 1)

    if entity_type == "material":
        for d in (predicted_dict, expected_dict):
            for fname in d:
                seen = set()
                keep = []
                for item in d[fname]:
                    if item[2] not in seen:
                        seen.add(item[2])
                        keep.append(item)
                d[fname] = keep

    return evaluate(expected_dict, predicted_dict, matching_type, matching_threshold, matcher)


def summarize(tp, fp, fn):
    p, r, f1, pma, rma, f1ma = calculate_metrics(tp, fp, fn)
    return {
        "tp": sum(len(v) for v in tp.values()),
        "fp": sum(len(v) for v in fp.values()),
        "fn": sum(len(v) for v in fn.values()),
        "precision_micro": p, "recall_micro": r, "f1_micro": f1,
        "precision_macro": pma, "recall_macro": rma, "f1_macro": f1ma,
    }