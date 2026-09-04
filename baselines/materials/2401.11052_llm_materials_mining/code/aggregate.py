"""Aggregate per-run results into evidence tables (mean +/- std).

Turns the per-run NDJSON records into:
  * results/*_runs.json        per-run values
  * results/*_summary.csv      mean+/-std tables
  * results/evidence_table.md  combined human-readable tables
"""
import csv
import json
import os
import statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "..", "results")


def load_ndjson(path):
    rows = []
    if os.path.exists(path):
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line:
                    rows.append(json.loads(line))
    return rows


def fmt(x, nd=2):
    if x is None:
        return ""
    if isinstance(x, float):
        return f"{100.0 * x:.{nd}f}"
    return str(x)


def mean_std(vals):
    if len(vals) < 2:
        return (sum(vals) / len(vals), 0.0)
    return (st.mean(vals), st.stdev(vals))


def write_csv(path, header, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def dump(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)


def main():
    os.makedirs(RES, exist_ok=True)

    ner = load_ndjson(os.path.join(HERE, "..", "work", "ner_runs.json"))
    mea = load_ndjson(os.path.join(HERE, "..", "work", "measeval_runs.json"))
    re_ = load_ndjson(os.path.join(HERE, "..", "work", "re_runs.json"))

    md = []
    md.append("# Evidence tables\n")
    md.append("(all numbers are percentages; N = 3 runs unless stated; "
              "recall/computed from the frozen raw model outputs).\n")

    # ------------------------------------------------------------------
    # 1) SuperMat materials NER (holdout)
    # ------------------------------------------------------------------
    md.append("\n## 1. SuperMat materials NER (hold-out), GPT models + grobid\n")
    hdr = ["model", "strategy", "matching", "P(mean)", "P(std)", "R(mean)",
           "R(std)", "F1(mean)", "F1(std)", "runs"]
    rows = []
    groups = {}
    for r in ner:
        key = (r.get("model"), r.get("strategy"), r.get("matching"))
        groups.setdefault(key, []).append(r)
    order = {}
    for (m, s, mt), rs in sorted(groups.items()):
        ms = mean_std([x["F1"] for x in rs])
        ps = mean_std([x["P"] for x in rs])
        rrc = mean_std([x["R"] for x in rs])
        rows.append([m, s, mt, fmt(ps[0]), fmt(ps[1]), fmt(rrc[0]), fmt(rrc[1]),
                     fmt(ms[0]), fmt(ms[1]), str(len(rs))])
        order[(m, s, mt)] = ms
    write_csv(os.path.join(RES, "ner_materials_summary.csv"), hdr, rows)
    md.append("### materials NER – micro P/R/F1\n")
    md.append("| " + " | ".join(hdr) + " |")
    md.append("|" + "---|" * len(hdr))
    for r in rows:
        md.append("| " + " | ".join(r) + " |")

    # per-run detail for gpt35 zero-shot (key anchor)
    md.append("\n### per-run detail – gpt35_turbo zero-shot (strict / formula)\n")
    md.append("| run | matching | tp | fp | fn | P | R | F1 |")
    md.append("|---:|---:|---:|---:|---:|---:|---:|---:|")
    for r in ner:
        if r.get("model") == "gpt35_turbo" and r.get("strategy") == "zero_shot" \
                and r.get("matching") in ("strict", "formula"):
            tpf = (r.get("tp", r.get("formula_tp")), r.get("fp", r.get("formula_fp")),
                   r.get("fn", r.get("formula_fn")))
            md.append(f"| {r.get('run')} | {r.get('matching')} | {tpf[0]} | "
                      f"{tpf[1]} | {tpf[2]} | {fmt(r.get('P'))} | "
                      f"{fmt(r.get('R'))} | {fmt(r.get('F1'))} |")

    md.append("\n### formula-matching gain (strict -> formula), gpt35_turbo zero-shot\n")
    md.append("| run | strict F1 | formula F1 | F1 gain | gain % | new matches |")
    md.append("|---:|---:|---:|---:|---:|---:|")
    for r in ner:
        if r.get("model") == "gpt35_turbo" and r.get("matching") == "formula":
            gain = r.get("f1_gain")
            gain_pct = r.get("f1_gain_pct")
            md.append(f"| {r.get('run')} | {fmt(r.get('strict_F1'))} | {fmt(r.get('F1'))} | "
                      f"{fmt(gain)} | {gain_pct:.0f}% | {r.get('formula_tp')} |")

    # ------------------------------------------------------------------
    # 2) MeasEval properties NER
    # ------------------------------------------------------------------
    md.append("\n## 2. MeasEval properties/quantities NER (soft matching focus)\n")
    hdr2 = ["model", "strategy", "P(mean)", "R(mean)", "F1(mean)", "F1(std)", "runs"]
    rows2 = []
    groups = {}
    for r in mea:
        key = (r["model"], r["strategy"])
        groups.setdefault(key, []).append(r)
    for (m, s), rs in sorted(groups.items()):
        g = {}
        for field in ["P_soft", "R_soft", "F1_soft"]:
            ms = mean_std([x[field] for x in rs])
            g[field] = ms
        rows2.append([m, s, fmt(g["P_soft"][0]), fmt(g["R_soft"][0]),
                      fmt(g["F1_soft"][0]), fmt(g["F1_soft"][1]), str(len(rs))])
    write_csv(os.path.join(RES, "measeval_soft_summary.csv"), hdr2, rows2)
    # sort by F1 descending for ranking view
    md.append("### soft micro F1 (threshold 0.9), ranked\n")
    md.append("| " + " | ".join(hdr2) + " |")
    md.append("|" + "---|" * len(hdr2))
    for r in sorted(rows2, key=lambda x: -float(x[4])):
        md.append("| " + " | ".join(r) + " |")

    md.append("\n### strict micro F1 (reference)\n")
    md.append("| model | strategy | P(mean) | R(mean) | F1(mean) | F1(std) |")
    md.append("|---|---:|---:|---:|---:|---:|")
    groups = {}
    for r in mea:
        groups.setdefault((r["model"], r["strategy"]), []).append(r)
    for (m, s), rs in sorted(groups.items()):
        ps = mean_std([x["P_strict"] for x in rs])
        rrc = mean_std([x["R_strict"] for x in rs])
        f1 = mean_std([x["F1_strict"] for x in rs])
        md.append(f"| {m} | {s} | {fmt(ps[0])} | {fmt(rrc[0])} | {fmt(f1[0])} | {fmt(f1[1])} |")

    # ------------------------------------------------------------------
    # 3) SuperMat RE
    # ------------------------------------------------------------------
    md.append("\n## 3. SuperMat material→property RE (strict micro F1)\n")
    md.append("\n### fine-tuned GPT-3.5-Turbo variants (hold-out corpus)\n")
    hdr3 = ["ft_label", "run", "P", "R", "F1", "tp", "fp", "fn"]
    md.append("| " + " | ".join(hdr3) + " |")
    md.append("|" + "---|" * len(hdr3))
    for r in re_:
        if r.get("strategy") == "fine_tuning" and r.get("matching") == "strict":
            md.append(f"| {r.get('ft_label')} | {r.get('run')} | {fmt(r.get('P'))} | "
                      f"{fmt(r.get('R'))} | {fmt(r.get('F1'))} | {r.get('tp')} | "
                      f"{r.get('fp')} | {r.get('fn')} |")
    re_ft_rows = [r for r in re_ if r.get("strategy") == "fine_tuning"
                  and r.get("matching") == "strict"]
    write_csv(os.path.join(RES, "re_ft_variants.csv"),
              hdr3, [[r.get("ft_label"), r.get("run"), fmt(r.get("P")), fmt(r.get("R")),
                      fmt(r.get("F1")), r.get("tp"), r.get("fp"), r.get("fn")]
                     for r in re_ft_rows])

    md.append("\n### zero-shot / few-shot over full corpus – strict micro F1 (mean±std, shuffled vs not)\n")
    hdr4 = ["strategy", "model", "shuffled", "F1(mean)", "F1(std)", "P(mean)", "R(mean)"]
    md.append("| " + " | ".join(hdr4) + " |")
    md.append("|" + "---|" * len(hdr4))
    groups = {}
    for r in re_:
        if r.get("strategy") in ("zero_shot", "few_shot") and r.get("matching") == "strict":
            key = (r.get("strategy"), r.get("model"), r.get("shuffled"))
            groups.setdefault(key, []).append(r)
    re_summ = []
    for (s, m, sh), rs in sorted(groups.items()):
        f1 = mean_std([x["F1"] for x in rs])
        ps = mean_std([x["P"] for x in rs])
        rrc = mean_std([x["R"] for x in rs])
        re_summ.append([s, m, str(sh), fmt(f1[0]), fmt(f1[1]), fmt(ps[0]), fmt(rrc[0])])
        md.append(f"| {s} | {m} | {sh} | {fmt(f1[0])} | {fmt(f1[1])} | {fmt(ps[0])} | {fmt(rrc[0])} |")
    write_csv(os.path.join(RES, "re_zerofew_summary.csv"), hdr4,
              [[*r[:3], float(r[3]), float(r[4]), r[5], r[6]] for r in re_summ])

    with open(os.path.join(RES, "evidence_table.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md))

    print("wrote", os.path.join(RES, "evidence_table.md"))


if __name__ == "__main__":
    main()