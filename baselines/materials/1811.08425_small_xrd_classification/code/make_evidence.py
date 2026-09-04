"""Generate the evidence table (markdown + CSV) and figures from saved JSONs.

Relies on: results/mlp_aug_s3.json, mlp_noaug_s3.json, mlp_aug_s3_coarse*.json,
results/acnn_aug.json (a-CNN reproduction), results/acnn_noaug.json.
"""
import json
import os

import numpy as np

import config

R = config.RESULTS_DIR
F = config.FIGURES_DIR


def load(tag):
    p = os.path.join(R, f"{tag}.json")
    if not os.path.exists(p):
        return None
    with open(p) as f:
        return json.load(f)


def fmt(x):
    return f"{x:.4f}"


def build_table():
    rows = []
    rows.append(["Experiment", "Arch", "Aug", "Seed-set",
                 "fold acc", "mean±std", "F1 micro", "F1 macro"])
    for tag, name, arch, aug in [
        ("mlp_aug_s3", "main (Case 3)", "MLP 512-256", "yes"),
        ("mlp_noaug_s3", "ablation", "MLP 512-256", "no"),
        ("mlp_aug_s5", "ensem-5", "MLP 512-256", "yes"),
        ("acnn_aug", "a-CNN (paper arch)", "a-CNN GAP", "yes"),
        ("acnn_noaug", "a-CNN ablation", "a-CNN GAP", "no"),
    ]:
        d = load(tag)
        if d is None:
            continue
        a = d["agg"]
        if "per_fold_acc" in a:
            af = ",".join(fmt(x) for x in a["per_fold_acc"])
        else:
            pfs = d.get("folds") or d.get("per_fold") or []
            af = ",".join(fmt(x["accuracy"]) for x in pfs)
        rows.append([name, arch, aug, str(d.get("n_seeds", 1)),
                     af, f"{a['accuracy_mean']:.4f}±{a['accuracy_std']:.4f}",
                     fmt(a["f1_micro_mean"]), fmt(a["f1_macro_mean"])])
    for c4, c8 in [(2, "0.08"), (3, "0.12"), (4, "0.16"), (8, "0.32")]:
        d = load(f"mlp_aug_s3_coarse{c4}")
        if d is None:
            continue
        a = d["agg"]
        rows.append([f"coarse {c8}°", "MLP 512-256", "yes",
                     str(d.get("n_seeds", 1)),
                     ",".join(fmt(x) for x in a["per_fold_acc"]),
                     f"{a['accuracy_mean']:.4f}±{a['accuracy_std']:.4f}",
                     fmt(a["f1_micro_mean"]), fmt(a["f1_macro_mean"])])
    return rows


def write_table_md(rows, path):
    w = max(len(r) for r in rows)
    lines = []
    hdr = rows[0]
    lines.append("| " + " | ".join(hdr) + " |")
    lines.append("|" + "|".join(["---"] * len(hdr)) + "|")
    for r in rows[1:]:
        lines.append("| " + " | ".join(r + [""] * (len(hdr) - len(r))) + " |")
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")
    return "\n".join(lines)


def main():
    rows = build_table()
    md = write_table_md(rows, os.path.join(R, "evidence_table.md"))
    print(md)

    # CSV
    import csv
    with open(os.path.join(R, "evidence_table.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerows(rows)


if __name__ == "__main__":
    main()