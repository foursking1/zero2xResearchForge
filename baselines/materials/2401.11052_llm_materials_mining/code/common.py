"""Shared utilities for the MatSci-LumEn reproduction.

Re-implements (offline) the matching / evaluation logic of the paper's
public evaluation repository (Apache-2.0), which lives under
``data/scripts/evaluation.py`` etc.  Deep-learning / external-service
parts (Sentence-BERT, Grobid supercon material parser) are NOT available
in this offline environment; strict and soft (Ratcliff-Obershelp)
matching are reproduced exactly, and a local chemical-formula matcher is
provided as a transparent approximation of the Grobid "formula matching".

Only the frozen data under ``data/dataset`` (or the original location
``F:\\dataset\\materials\\2401.11052_llm_materials_mining\\dataset``) is
read; no prediction is ever generated here.
"""
import csv
import os
import pickle
import re
import sys
from collections import defaultdict
from difflib import SequenceMatcher

DATA_HOME = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data", "dataset")
DATA_HOME_ALT = "/mnt/f/dataset/materials/2401.11052_llm_materials_mining/dataset"

EMPTY_PRED = {"", " ", "-", "--", "---", "----", ":--", ":---", ":-",
              "unknown", "null", "none", "None", "n/a", "na", "-.-"}


def pick_data_home():
    """Return the frozen-dataset directory: the local snapshot if present,
    otherwise the documented physical location (F:\\dataset\\... moved from
    data/ -- see data/DATA_LOCATION.md)."""
    return DATA_HOME if os.path.isdir(os.path.join(DATA_HOME, "superMat")) else DATA_HOME_ALT

# --------------------------------------------------------------------------
# Readers
# --------------------------------------------------------------------------

def _detect_header(sample_lines):
    try:
        return csv.Sniffer().has_header(sample_lines)
    except csv.Error:
        return False


def load_rows(path):
    """Load a csv/tsv file exactly like the repo's load_texts_and_classes_generic."""
    delimiter = "\t" if not path.endswith(".csv") else ","
    rows = []
    with open(path, encoding="utf-8-sig") as f:
        sample = f.readline()
        sample = sample + f.readline() if sample else ""
        try:
            has_header = csv.Sniffer().has_header(sample)
        except csv.Error:
            has_header = False
        f.seek(0)
        for line in csv.reader(f, delimiter=delimiter):
            if has_header:
                has_header = False
                continue
            if len(line) == 0:
                continue
            rows.append(line)
    return rows


def group_by(rows, column_idx):
    out = {}
    for elem in rows:
        key = elem[column_idx]
        if key not in out:
            out[key] = []
        el = list(elem)
        el.pop(column_idx)
        out[key].append(el)
    return out


# --------------------------------------------------------------------------
# Matching (replica of commons.evaluation.match)
# --------------------------------------------------------------------------

def _ro_similarity(a, b):
    """Ratcliff-Obershelp normalised similarity (= difflib gestalt ratio)."""
    if not a and not b:
        return 1.0
    return SequenceMatcher(None, a, b, autojunk=False).ratio()


def match(expected, predicted, matching_type, matching_threshold=None):
    """Replica of the repo's  match()  for strict/soft (and contains/sbert stubs)."""
    expected = "" if expected is None else expected
    predicted = "" if predicted is None else predicted
    if matching_type == "strict":
        return str.lower(expected) == str.lower(predicted)
    if matching_type == "soft" and matching_threshold is not None:
        return _ro_similarity(str.lower(predicted), str.lower(expected)) >= matching_threshold
    if matching_type == "contains":
        return (str.lower(predicted) in str.lower(expected)
                or str.lower(expected) in str.lower(predicted))
    raise ValueError(f"match type {matching_type} not supported offline")


def get_matches(expected_entities, predicted_entities, matching_type, matching_threshold):
    """Replica of get_matches(): one-to-one greedy matching, order by prediction."""
    tp, fp, fn = [], [], []
    skip_predicted = set()
    skip_expected = set()
    for idxp, predicted_entity_ in enumerate(predicted_entities):
        if idxp in skip_predicted:
            continue
        predicted_entity = predicted_entity_.strip()
        is_match = False
        for idxe, expected_entity_ in enumerate(expected_entities):
            if idxe in skip_expected:
                continue
            expected_entity = expected_entity_.strip()
            if match(predicted_entity, expected_entity, matching_type, matching_threshold):
                tp.append({"expected": expected_entity, "predicted": predicted_entity})
                skip_predicted.add(idxp)
                skip_expected.add(idxe)
                is_match = True
                break
        if not is_match:
            fp.append(predicted_entity)
    for idxe, expected_entity in enumerate(expected_entities):
        if idxe not in skip_expected:
            fn.append(expected_entity)
    assert len(tp) + len(fp) == len(predicted_entities)
    assert len(tp) + len(fn) == len(expected_entities)
    return tp, fp, fn


def calculate_metrics(tp_by_file, fp_by_file, fn_by_file):
    """Replica of calculate_metrics() -> micro + macro P/R/F1."""
    tp_all = sum(len(v) for v in tp_by_file.values())
    fp_all = sum(len(v) for v in fp_by_file.values())
    fn_all = sum(len(v) for v in fn_by_file.values())

    p_micro = tp_all / (tp_all + fp_all) if tp_all + fp_all > 0 else 0.0
    r_micro = tp_all / (tp_all + fn_all) if tp_all + fn_all > 0 else 0.0
    f1_micro = 2 * p_micro * r_micro / (p_micro + r_micro) if p_micro + r_micro > 0 else 0.0

    p_macro, r_macro = [], []
    for fname in tp_by_file:
        tp = len(tp_by_file[fname])
        fp = len(fp_by_file[fname])
        fn = len(fn_by_file[fname])
        p_macro.append(tp / (tp + fp) if tp + fp > 0 else 0.0)
        r_macro.append(tp / (tp + fn) if tp + fn > 0 else 0.0)
    p_macro = sum(p_macro) / len(p_macro) if p_macro else 0.0
    r_macro = sum(r_macro) / len(r_macro) if r_macro else 0.0
    f1_macro = 2 * p_macro * r_macro / (p_macro + r_macro) if p_macro + r_macro > 0 else 0.0

    return p_micro, r_micro, f1_micro, p_macro, r_macro, f1_macro


def pct(x, nd=2):
    return round(100.0 * x, nd)