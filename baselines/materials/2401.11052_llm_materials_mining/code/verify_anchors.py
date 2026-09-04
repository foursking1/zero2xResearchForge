"""Directly print the two numbers the benchmark rubric audits:

  * GPT-3.5-Turbo zero-shot materials NER: strict micro F1 and the
    formula-matched micro F1 (SuperMat hold-out).
  * fine-tuned GPT-3.5-Turbo RE: strict micro F1 (SuperMat hold-out),
    evaluated over the repository's own fine-tuning output files.

This is the entry point used for spot-checks: it recomputes everything
from the frozen data (no downloaded assets).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import pick_data_home
DATA_HOME = pick_data_home()
from ner_eval import run_ner_eval, summarize
from formula_eval import run_formula_eval
from run_re import run_re_eval

D = DATA_HOME
ENT = os.path.join(D, "superMat", "entities")
REL = os.path.join(D, "superMat", "relations")

expected = os.path.join(ENT, "supermat-expected-holdout-material.csv")
pred = os.path.join(ENT, "results", "run1", "supermat-gpt35_turbo-holdout-material.csv")

print("=" * 78)
print("AUDIT 1  materials NER (SuperMat hold-out)  gpt35_turbo zero-shot run1")
print("=" * 78)
s = summarize(*run_ner_eval(expected, pred, "strict", None, "material"))
print(f"  strict  micro P={s['precision_micro']*100:.2f}  R={s['recall_micro']*100:.2f}  "
      f"F1={s['f1_micro']*100:.2f}   (tp={s['tp']}, fp={s['fp']}, fn={s['fn']})")
f = run_formula_eval(expected, pred, verbose=False)
print(f"  formula micro P={f['P']*100:.2f}  R={f['R']*100:.2f}  F1={f['F1']*100:.2f}   "
      f"(add. matches={f['formula_tp']},  strict F1={f['strict_F1']*100:.2f})")
print(f"  formula gain: +{f['f1_gain']*100:.2f} F1  "
      f"({f['f1_gain_pct']:.0f}% of strict)")

print()
print("=" * 78)
print("AUDIT 2  relation extraction (SuperMat hold-out)  FT GPT-3.5-Turbo")
print("=" * 78)
hold = os.path.join(REL, "supermat-paragraphs-holdout.csv")
ft_pred = os.path.join(REL, "results", "results-fine-tuning",
                       "supermat-paragraphs-holdout.chatgpt-ft-re.1.output.csv")
s = run_re_eval(hold, ft_pred, "strict")
print(f"  fine-tuned gpt35 (base) strict micro P={s['P']*100:.2f}  "
      f"R={s['R']*100:.2f}  F1={s['F1']*100:.2f}   (tp={s['tp']}, fp={s['fp']}, fn={s['fn']})")
ft_shuf = os.path.join(REL, "results", "results-fine-tuning",
                       "supermat-paragraphs-holdout.chatgpt-ft-re.shuffled.1.output.csv")
s2 = run_re_eval(hold, ft_shuf, "strict")
print(f"  fine-tuned gpt35 (prefix-shuffled) strict micro F1={s2['F1']*100:.2f}")

print()
print("NOTE on formula matching:")
print("  The paper's 'formula matching' uses a Grobid supercon-material webservice.")
print("  Offline, code/formula_match.py is a transparent local approximation;")
print("  the exact Grobid value (paper: F1=44.8/45.3) is not reproducible in this")
print("  environment.  See report.md for the discussion and error analysis.")