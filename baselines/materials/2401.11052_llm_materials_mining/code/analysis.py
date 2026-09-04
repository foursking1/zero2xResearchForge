"""Error analysis and evidence exports (beyond the aggregate tables).

* SuperMat materials NER strict matcher: FP / FN examples
* formula matching: every new (matched-by-formula, strict-unmatched) pair
* RE: per-run shuffled vs non-shuffled effect table
* MeasEval: per-run soft F1 detail
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (DATA_HOME, load_rows, group_by, get_matches)
from formula_match import match_by_formula
from formula_eval import run_formula_eval

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "evidence")
V = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "work")
os.makedirs(OUT, exist_ok=True)

D = DATA_HOME
ENT = os.path.join(D, "superMat", "entities")
EXPECTED = os.path.join(ENT, "supermat-expected-holdout-material.csv")
PRED = os.path.join(ENT, "results", "run1", "supermat-gpt35_turbo-holdout-material.csv")


def ner_strict_errors():
    pred_rows = load_rows(PRED)
    exp_rows = load_rows(EXPECTED)
    pd = group_by(pred_rows, 1)
    ed = group_by(exp_rows, 1)
    for d in (pd, ed):
        for fname in d:
            seen, keep = set(), []
            for item in d[fname]:
                if item[2] not in seen:
                    seen.add(item[2])
                    keep.append(item)
            d[fname] = keep
    lines = ["pid\tfile\tdirection\tentity"]
    for fname in ed:
        ebp = group_by(ed[fname], 1)
        pbp = group_by(pd[fname], 1) if fname in pd else {}
        for pid in ebp:
            ei = [x[1] for x in ebp[pid]]
            pi = [x[1] for x in pbp[pid]] if pid in pbp else []
            tp, fn, fp = get_matches(ei, pi, "strict", None)
            for e in fn:
                lines.append(f"{pid}\t{fname}\tFN(exptected-but-missed)\t{e}")
            for e in fp[:40]:
                lines.append(f"{pid}\t{fname}\tFP(predicted-but-wrong)\t{e}")
    path = os.path.join(OUT, "ner_strict_fn_and_sample_fp.tsv")
    open(path, "w", encoding="utf-8").write("\n".join(lines))
    print("wrote", path)


def formula_matches():
    res = run_formula_eval(EXPECTED, PRED, verbose=True)
    ms = res["_new_matches"]
    lines = ["expected\tpredicted"]
    for e, p in ms:
        lines.append(e.replace("\t", " ") + "\t" + p.replace("\t", " "))
    path = os.path.join(OUT, "formula_new_matches_run1.tsv")
    open(path, "w", encoding="utf-8").write("\n".join(lines))
    # human-review oriented notes: candidates that are probably wrong
    import re
    suspect = [x for x in ms if re.fullmatch(r"[A-Z]\d?", x[0].strip())
               or re.fullmatch(r"[A-Z]\d?", x[1].strip())]
    p2 = os.path.join(OUT, "formula_suspect_matches.md")
    with open(p2, "w", encoding="utf-8") as f:
        f.write(f"# Formula-matching review (run1)\n\n")
        f.write(f"Newly matched-by-formula pairs: **{len(ms)}** "
                f"(strict-unmatched, then matched on chemical composition).\n\n")
        f.write("## Pairs flagged for human review (single-symbol strings)\n\n")
        for e, p in suspect:
            f.write(f"- `{e[:60]}`  vs  `{p[:60]}`\n")
        f.write(f"\ncount: {len(suspect)}\n")
    print("wrote", path, "and", p2)


def re_shuffled():
    rows = [json.loads(l) for l in open(os.path.join(V, "re_runs.json"))]
    lines = ["strategy\tmodel\trun\tshuffled\tstrict_F1\tsoft_F1"]
    for r in rows:
        if r["strategy"] in ("zero_shot", "few_shot"):
            lines.append(f"{r['strategy']}\t{r['model']}\t{r['run']}\t"
                         f"{r['shuffled']}\t{r['F1']:.4f}\t{r.get('F1', 0):.4f}")
    path = os.path.join(OUT, "re_shuffled_per_run.tsv")
    open(path, "w", encoding="utf-8").write("\n".join(lines))
    print("wrote", path)


def measeval_detail():
    rows = [json.loads(l) for l in open(os.path.join(V, "measeval_runs.json"))]
    lines = ["model\tstrategy\trun\tstrict_P\tstrict_R\tstrict_F1\tsoft_P\tsoft_R\tsoft_F1"]
    for r in rows:
        lines.append(f"{r['model']}\t{r['strategy']}\t{r['run']}\t"
                     f"{r['P_strict']:.4f}\t{r['R_strict']:.4f}\t{r['F1_strict']:.4f}\t"
                     f"{r['P_soft']:.4f}\t{r['R_soft']:.4f}\t{r['F1_soft']:.4f}")
    path = os.path.join(OUT, "measeval_per_run.tsv")
    open(path, "w", encoding="utf-8").write("\n".join(lines))
    print("wrote", path)


if __name__ == "__main__":
    ner_strict_errors()
    formula_matches()
    re_shuffled()
    measeval_detail()