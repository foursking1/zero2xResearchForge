"""Full SuperMat materials-NER evaluation.

Computes strict / soft / formula micro & macro P/R/F1 for:
  * GPT-3.5-Turbo, GPT-4, GPT-4-Turbo (zero-shot / few-shot / fine-tuned), 3 runs
  * grobid-quantities baseline

Writes NDJSON per-run records to work/ner_runs.json.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import pick_data_home
DATA_HOME = pick_data_home()
from ner_eval import run_ner_eval, summarize
from formula_eval import run_formula_eval

D = DATA_HOME
ENT = os.path.join(D, "superMat", "entities")
EXPECTED = os.path.join(ENT, "supermat-expected-holdout-material.csv")

MODEL_STRAT = {
    "gpt35_turbo": "zero_shot",
    "gpt4": "zero_shot",
    "gpt4_turbo": "zero_shot",
    "gpt35_turbo-few_shot": "few_shot",
    "gpt4-few_shot": "few_shot",
    "gpt4_turbo-few_shot": "few_shot",
    "gpt35_turbo-ft": "fine_tuning",
}
# run2 gpt4_turbo few-shot used a dot instead of a dash in the repo
NAME_FIX = {
    "gpt4_turbo-few_shot": {2: "supermat-gpt4_turbo-few_shot.holdout-material.csv"},
}


def file_for(model, run):
    name = f"supermat-{model}-holdout-material.csv"
    if model in NAME_FIX and run in NAME_FIX[model]:
        name = NAME_FIX[model][run]
    return os.path.join(ENT, "results", f"run{run}", name)


def main(out_path):
    results = []
    for model, strat in MODEL_STRAT.items():
        for run in [1, 2, 3]:
            pred = file_for(model, run)
            for mt in ["strict", "soft"]:
                thr = 0.9 if mt == "soft" else None
                res = run_ner_eval(EXPECTED, pred, mt, thr, "material")
                s = summarize(*res)
                results.append({
                    "model": model, "strategy": strat, "run": run, "matching": mt,
                    "P": s["precision_micro"], "R": s["recall_micro"], "F1": s["f1_micro"],
                    "P_macro": s["precision_macro"], "R_macro": s["recall_macro"],
                    "F1_macro": s["f1_macro"],
                    "tp": s["tp"], "fp": s["fp"], "fn": s["fn"],
                })

    # formula matching for gpt35 zero-shot (all runs)
    for run in [1, 2, 3]:
        pred = file_for("gpt35_turbo", run)
        fr = run_formula_eval(EXPECTED, pred, verbose=False)
        fr["run"] = run
        results.append(fr)

    # grobid baseline
    base = os.path.join(ENT, "results", "supermat-grobid-holdout-material.csv")
    for mt in ["strict", "soft"]:
        thr = 0.9 if mt == "soft" else None
        res = run_ner_eval(EXPECTED, base, mt, thr, "material")
        s = summarize(*res)
        results.append({
            "model": "grobid", "strategy": "baseline", "run": 0, "matching": mt,
            "P": s["precision_micro"], "R": s["recall_micro"], "F1": s["f1_micro"],
            "P_macro": s["precision_macro"], "R_macro": s["recall_macro"],
            "F1_macro": s["f1_macro"],
            "tp": s["tp"], "fp": s["fp"], "fn": s["fn"],
        })

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"wrote {len(results)} records -> {out_path}")
    return results


if __name__ == "__main__":
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "work", "ner_runs.json")
    main(out)