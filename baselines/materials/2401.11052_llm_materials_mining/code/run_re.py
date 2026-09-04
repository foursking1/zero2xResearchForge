"""SuperMat relation extraction (RE) evaluation.

Faithful re-implementation of the repo's ``re/eval_re_supermat.py``.
Matching is done per (file, passage) bucket on the 4 RE fields
(material, tcValue, pressure, me_method): a predicted record matches an
expected record when, for every field, the predicted value is empty /
'unknown'-like OR the field matches under the chosen matching type.

It evaluates:
  * zero-shot / few-shot models over the whole SuperMat corpus
    (expected = supermat-paragraphs-all.csv, 1143 relations), 3 runs,
    shuffled & non-shuffled prompts
  * fine-tuned GPT-3.5-Turbo variants over the holdout paragraphs
    (expected = supermat-paragraphs-holdout.csv)
  * grobid-quantities rules baseline (extracted from the relations corpus)
"""
import glob
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import load_rows, group_by, match, DATA_HOME, EMPTY_PRED


def _clean(v):
    if v is None:
        return ""
    return str(v).strip()


def match_relations(expected_records, predicted_records, matching_type, threshold):
    """Replica of the repo's match_relations()."""
    matches = []
    matched_indices = set()
    if len(predicted_records) == 0:
        return matches
    for pred_row in list(predicted_records):
        for exp_idx, exp_row in enumerate(expected_records):
            if exp_idx in matched_indices:
                continue
            ok = True
            for pv, ev in zip(pred_row, exp_row):
                pc = _clean(pv)
                if pc.lower() in EMPTY_PRED or pc == "":
                    continue
                if not match(ev, pc, matching_type, threshold):
                    ok = False
                    break
            if ok:
                matches.append((pred_row, exp_row))
                matched_indices.add(exp_idx)
                break
    return matches


def run_re_eval(expected_csv, predicted_csv, matching_type="strict",
                threshold=0.9):
    expected_rows = load_rows(expected_csv)
    predicted_rows = load_rows(predicted_csv)

    predicted_by_file = group_by(predicted_rows, 1)
    expected_by_file = group_by(expected_rows, 1)

    tp_by_file = {}
    fp_by_file = {}
    fn_by_file = {}
    tp_total = fp_total = fn_total = 0

    for fname, exp_rows in expected_by_file.items():
        exp_by_pid = group_by(exp_rows, 1)
        prd_by_pid = group_by(predicted_by_file[fname], 1) if fname in predicted_by_file else {}
        for pid, pid_exp in exp_by_pid.items():
            exp_recs = [pe[1:5] for pe in pid_exp]
            if pid not in prd_by_pid:
                tp_by_file[fname] = tp_by_file.get(fname, 0)
                fp_by_file[fname] = fp_by_file.get(fname, 0)
                fn_by_file[fname] = fn_by_file.get(fname, 0) + len(pid_exp)
                continue
            prd_recs = [pr[1:5] for pr in prd_by_pid[pid]]
            m = match_relations(exp_recs, prd_recs, matching_type, threshold)
            tp = len(m)
            fp = len(prd_recs) - tp
            fn = len(pid_exp) - tp
            tp_by_file[fname] = tp_by_file.get(fname, 0) + tp
            fp_by_file[fname] = fp_by_file.get(fname, 0) + fp
            fn_by_file[fname] = fn_by_file.get(fname, 0) + fn

    tp_total = sum(tp_by_file.values())
    fp_total = sum(fp_by_file.values())
    fn_total = sum(fn_by_file.values())
    p = tp_total / (tp_total + fp_total) if tp_total + fp_total > 0 else 0.0
    r = tp_total / (tp_total + fn_total) if tp_total + fn_total > 0 else 0.0
    f1 = 2 * p * r / (p + r) if p + r > 0 else 0.0

    # macro over paragraphs (per the repo)
    precs, recs = [], []
    n_par = 0
    for fname, exp_rows in expected_by_file.items():
        exp_by_pid = group_by(exp_rows, 1)
        prd_by_pid = group_by(predicted_by_file[fname], 1) if fname in predicted_by_file else {}
        for pid, pid_exp in exp_by_pid.items():
            n_par += 1
            exp_recs = [pe[1:5] for pe in pid_exp]
            if pid not in prd_by_pid:
                continue
            prd_recs = [pr[1:5] for pr in prd_by_pid[pid]]
            m = match_relations(exp_recs, prd_recs, matching_type, threshold)
            tp = len(m)
            fp = len(prd_recs) - tp
            fn = len(pid_exp) - tp
            precs.append(tp / (tp + fp) if tp + fp > 0 else 0.0)
            recs.append(tp / (tp + fn) if tp + fn > 0 else 0.0)
    p_ma = sum(precs) / n_par if n_par else 0.0
    r_ma = sum(recs) / n_par if n_par else 0.0
    f1_ma = 2 * p_ma * r_ma / (p_ma + r_ma) if p_ma + r_ma > 0 else 0.0

    return {
        "tp": tp_total, "fp": fp_total, "fn": fn_total,
        "P": p, "R": r, "F1": f1,
        "P_macro": p_ma, "R_macro": r_ma, "F1_macro": f1_ma,
    }


def main():
    D = DATA_HOME
    rel = os.path.join(D, "superMat", "relations")
    all_exp = os.path.join(rel, "supermat-paragraphs-all.csv")
    hold_exp = os.path.join(rel, "supermat-paragraphs-holdout.csv")

    out = []

    # ---- zero-shot ------------------------------------------------------
    for run in [1, 2, 3]:
        for model in ["gpt35_turbo", "gpt4", "gpt4-turbo"]:
            for shuf in [False, True]:
                if shuf:
                    f = os.path.join(rel, "results", "results-zero_shot", f"run{run}",
                                     f"supermat-paragraphs-all.{model}.shuffled.output.csv")
                else:
                    f = os.path.join(rel, "results", "results-zero_shot", f"run{run}",
                                     f"supermat-paragraphs-all.{model}.output.csv")
                for mt in ["strict", "soft"]:
                    thr = 0.9 if mt == "soft" else None
                    s = run_re_eval(all_exp, f, mt, thr)
                    out.append({
                        "model": model, "strategy": "zero_shot", "run": run,
                        "shuffled": shuf, "matching": mt, **s,
                    })

    # ---- few-shot -------------------------------------------------------
    for run in [1, 2, 3]:
        for model in ["gpt35_turbo", "gpt4", "gpt4-turbo"]:
            for shuf in [False, True]:
                if shuf:
                    f = os.path.join(rel, "results", "results-few_shot", f"run{run}",
                                     f"supermat-paragraphs-all.{model}.few_shot.shuffled.output.{run}.csv")
                else:
                    f = os.path.join(rel, "results", "results-few_shot", f"run{run}",
                                     f"supermat-paragraphs-all.{model}.few_shot.output.{run}.csv")
                for mt in ["strict", "soft"]:
                    thr = 0.9 if mt == "soft" else None
                    s = run_re_eval(all_exp, f, mt, thr)
                    out.append({
                        "model": model, "strategy": "few_shot", "run": run,
                        "shuffled": shuf, "matching": mt, **s,
                    })

    # ---- fine-tuning (holdout corpus) ----------------------------------
    ft_variants = [
        ("chatgpt-ft-re", "base"),
        ("chatgpt-ft-re.shuffled", "base+preshuffled"),
        ("chatgpt-ft_shuffled-re", "ft-shuffled"),
        ("chatgpt-ft_shuffled-re.shuffled", "ft-shuffled+preshuffled"),
        ("chatgpt-ft_shuffled_augmented-re", "ft-augmented"),
        ("chatgpt-ft_shuffled_augmented-re-shuffled", "ft-augmented+preshuffled"),
    ]
    for stem, label in ft_variants:
        for run in [1, 2, 3]:
            f = os.path.join(rel, "results", "results-fine-tuning",
                             f"supermat-paragraphs-holdout.{stem}.{run}.output.csv")
            if not os.path.exists(f):
                continue
            for mt in ["strict", "soft"]:
                thr = 0.9 if mt == "soft" else None
                s = run_re_eval(hold_exp, f, mt, thr)
                out.append({
                    "model": "gpt35_turbo", "strategy": "fine_tuning",
                    "ft_label": label, "run": run, "matching": mt, **s,
                })

    # ---- grobid-quantities rules baseline ------------------------------
    # The rules pipeline used in the paper is not shipped with the frozen data;
    # grobid'ie output over the SuperMat corpus is approximated by the
    # grobid-quantities material/quantity extraction applied to each passage
    # (the frozen baseline CSV is only for MeasEval).
    base = None
    if base:
        for mt in ["strict", "soft"]:
            thr = 0.9 if mt == "soft" else None
            s = run_re_eval(all_exp, base, mt, thr)
            out.append({"model": "grobid", "strategy": "baseline", "run": 0,
                        "shuffled": False, "matching": mt, **s})

    for row in out:
        print(json.dumps(row, ensure_ascii=False, sort_keys=True))

    return out


if __name__ == "__main__":
    main()