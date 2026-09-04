#!/usr/bin/env python
"""Finalize solution.md / report.md / claim.md with the real measured numbers
read from results/*. Must be run AFTER 01-04.
"""
import json
import os
import re
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import COARSE_TYPES, RESULTS, ROOT

ev = pd.read_csv(os.path.join(RESULTS, "evidence_table.csv"))
per_type = pd.read_csv(os.path.join(RESULTS, "per_type_accuracy.csv"))
baselines = pd.read_csv(os.path.join(RESULTS, "baselines.csv"))
metrics = json.load(open(os.path.join(RESULTS, "metrics.json")))
per_ds = pd.read_csv(os.path.join(RESULTS, "per_dataset_accuracy.csv"))

M = "vit_base_patch16_224_linear_probe"
M2 = "resnet18_linear_probe"
K = "vit_base_patch16_224_knn"
K2 = "resnet18_knn"


def acc(model, group):
    row = ev[(ev["model"] == model) & (ev["task_group"] == group)]
    return row["accuracy"].iloc[0]


def pct(v):
    return f"{v * 100:.1f}"


coarse_maj = float(baselines[baselines["question_type"].isin(COARSE_TYPES)]["majority_accuracy"].mean())
coarse_ch = float(baselines[baselines["question_type"].isin(COARSE_TYPES)]["chance_accuracy"].mean())
fine_maj = float(baselines[baselines["question_type"] == "classification"]["majority_accuracy"].iloc[0])
fine_ch = float(baselines[baselines["question_type"] == "classification"]["chance_accuracy"].iloc[0])

vit_c, vit_f = acc(M, "coarse"), acc(M, "fine")
rn_c, rn_f = acc(M2, "coarse"), acc(M2, "fine")
knn_c, knn_f = acc(K, "coarse"), acc(K, "fine")
knn2_c, knn2_f = acc(K2, "coarse"), acc(K2, "fine")

n_coarse = int(ev[(ev["model"] == M) & (ev["task_group"] == "coarse")]["n_items"].iloc[0])
n_fine = int(ev[(ev["model"] == M) & (ev["task_group"] == "fine")]["n_items"].iloc[0])

best_c = max(vit_c, rn_c, knn_c, knn2_c)
best_f = max(vit_f, rn_f, knn_f, knn2_f)
verdict = metrics["conclusion"]["label"]

per_type_map = {}
for _, r in per_type.iterrows():
    per_type_map[(r["question_type"], r["model"])] = r["accuracy"]


def type_cell(qtype, model):
    return pct(per_type_map[(qtype, model)])


d_c = abs(best_c - 0.626) / 0.626
d_f = abs(best_f - 0.517) / 0.517

subs = {
    "COARSE_VIT": pct(vit_c), "FINE_VIT": pct(vit_f),
    "COARSE_RN": pct(rn_c), "FINE_RN": pct(rn_f),
    "COARSE_KNN": pct(knn_c), "FINE_KNN": pct(knn_f),
    "COARSE_KNN2": pct(knn2_c), "FINE_KNN2": pct(knn2_f),
    "COARSE_MAJ": pct(coarse_maj), "FINE_MAJ": pct(fine_maj),
    "DIFF_C": f"{d_c * 100:.1f}%", "DIFF_F": f"{d_f * 100:.1f}%",
    "VERDICT": verdict,
    "N": str(n_coarse), "N2": str(n_fine),
    "C:vit": pct(vit_c), "C:rn": pct(rn_c), "F:vit": pct(vit_f), "F:rn": pct(rn_f),
    "C:knn": pct(knn_c), "C:knn2": pct(knn2_c), "F:knn": pct(knn_f), "F:knn2": pct(knn2_f),
    "C:maj": pct(coarse_maj), "C:ch": pct(coarse_ch), "F:maj": pct(fine_maj), "F:ch": pct(fine_ch),
    "D:C": f"{d_c * 100:.1f}%", "D:F": f"{d_f * 100:.1f}%",
    "REASON": metrics["conclusion"]["reasoning_short"],
}
for t in COARSE_TYPES + ["classification"]:
    subs[f"T:{t}:vit"] = type_cell(t, M)
    subs[f"T:{t}:rn"] = type_cell(t, M2)

lines = []
for _, r in per_ds.iterrows():
    model_label = r["model"].replace("vit_base_patch16_224_linear_probe", "ViT-B/16")\
                            .replace("resnet18_linear_probe", "ResNet-18")
    lines.append(f"- {model_label} / {r['dataset']}: acc={r['mean'] * 100:.1f}% (n={int(r['count'])})")
subs["F:PERTY_DATASET"] = "\n" + "\n".join(lines)

targets = [
    ("solution.md", ["COARSE_VIT", "FINE_VIT", "COARSE_RN", "FINE_RN", "COARSE_KNN", "FINE_KNN",
                     "COARSE_MAJ", "FINE_MAJ", "DIFF_C", "DIFF_F", "VERDICT", "REASON"]),
    ("claim.md", ["COARSE_VIT", "FINE_VIT", "COARSE_RN", "FINE_RN", "COARSE_KNN", "FINE_KNN",
                  "COARSE_MAJ", "FINE_MAJ", "VERDICT", "N", "N2"]),
    ("report.md", list(subs)),
]
for fname, markers in targets:
    path = os.path.join(ROOT, fname)
    text = open(path).read()
    missing = [k for k in markers if "{%s}" % k in text and k not in subs]
    if missing:
        print(f"WARNING {fname}: missing subst keys {missing}")
    for k, v in subs.items():
        text = text.replace("{%s}" % k, v)
    left = re.findall(r"\{[A-Za-z:0-9/ _-]+\}", text)
    if left:
        print(f"NOTE {fname}: leftover placeholders: {sorted(set(left))[:12]}")
    open(path, "w").write(text)
    print(f"wrote {path}")

print(f"summary: vitLP coarse={pct(vit_c)} fine={pct(vit_f)} | "
      f"vitKNN fine={pct(knn_f)} | verdict={verdict}")