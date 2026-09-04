"""MeasEval properties/quantities NER evaluation.

Faithful re-implementation of the repo pipeline for the "quantity
extraction" (properties) task: grobid-quantities baseline vs
GPT-3.5-Turbo / GPT-4 / GPT-4-Turbo under zero-shot / few-shot / fine-tuned
prompting (3 runs each).

Scores: strict, soft (Ratcliff-Obershelp >= threshold), reported for the
micro aggregation (as in the paper's appendix); macro also computed.
Sentence-BERT matching requires a model that is not cached in this offline
environment -- it is omitted here (documented in report.md).
"""
import os
import json
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (load_rows, group_by, get_matches, calculate_metrics,
                    DATA_HOME)
from ner_eval import evaluate, summarize


def evaluate_now(event, threshold=0.9):
    expected_csv = event["expected"]
    predicted_csv = event["predicted"]
    expected_rows = load_rows(expected_csv)
    predicted_rows = load_rows(predicted_csv)

    predicted_dict = group_by(predicted_rows, 1)
    expected_dict = group_by(expected_rows, 1)

    out = {}
    for mt in ["strict", "soft"]:
        thr = threshold if mt == "soft" else None
        tp, fp, fn = evaluate(expected_dict, predicted_dict, mt, thr)
        s = summarize(tp, fp, fn)
        out[mt] = s
    return out


def main():
    D = DATA_HOME
    base = os.path.join(D, "measeval")
    exp = os.path.join(base, "measeval-expected.csv")
    models = {
        "gpt35_turbo": ["", "few_shot", "ft"],
        "gpt4": ["", "few_shot"],
        "gpt4_turbo": ["", "few_shot"],
    }
    rows = []
    for model, strats in models.items():
        for strat in strats:
            tag = f"{model}-{strat}-properties" if strat else f"{model}-properties"
            for run in [1, 2, 3]:
                pred = os.path.join(base, "results", f"run{run}", f"measeval-{tag}.csv")
                ev = evaluate_now({"expected": exp, "predicted": pred})
                rows.append({
                    "model": model, "strategy": strat if strat else "zero_shot",
                    "run": run,
                    "strict": ev["strict"], "soft": ev["soft"],
                })
                print(json.dumps({
                    "model": model, "strategy": strat if strat else "zero_shot", "run": run,
                    "P_strict": round(ev["strict"]["precision_micro"], 4),
                    "R_strict": round(ev["strict"]["recall_micro"], 4),
                    "F1_strict": round(ev["strict"]["f1_micro"], 4),
                    "P_soft": round(ev["soft"]["precision_micro"], 4),
                    "R_soft": round(ev["soft"]["recall_micro"], 4),
                    "F1_soft": round(ev["soft"]["f1_micro"], 4),
                }))
    # grobid baseline
    pred = os.path.join(base, "results", "measeval-grobid-quantities.csv")
    ev = evaluate_now({"expected": exp, "predicted": pred})
    print(json.dumps({
        "model": "grobid", "strategy": "baseline", "run": 0,
        "P_strict": round(ev["strict"]["precision_micro"], 4),
        "R_strict": round(ev["strict"]["recall_micro"], 4),
        "F1_strict": round(ev["strict"]["f1_micro"], 4),
        "P_soft": round(ev["soft"]["precision_micro"], 4),
        "R_soft": round(ev["soft"]["recall_micro"], 4),
        "F1_soft": round(ev["soft"]["f1_micro"], 4),
    }))
    return rows


if __name__ == "__main__":
    main()