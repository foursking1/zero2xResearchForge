#!/usr/bin/env python3
"""Audit rebuild of the evidence table *directly from saved decision scores*.

Every method/seed pairing wrote <outdir>/scores/<method>_seed<seed>_test_scores.npy
during run_experiment.py. This script reloads those scores, recomputes AUROC
against the frozen test labels and regenerates:
  auroc_per_seed.json, auroc_<method>.json, evidence_table.csv, summary_meta.json

It never touches the test labels for training/selection, only for metric
computation on final scores.
"""
import argparse
import glob
import json
import os
import re

import numpy as np
from sklearn.metrics import roc_auc_score

PAPER_ROW = {
    "knn": 93.96, "ae": 92.63, "dsvdd": 86.98, "dpad": 92.53,
    "iforest": 89.65, "ocsvm": 92.22, "lof": 91.47, "pca": 91.78,
    "kde": 92.14, "ecod": 85.26,
}
ORDER = ["knn", "ae", "dsvdd", "dpad", "iforest", "ocsvm", "lof", "pca", "kde", "ecod"]


def load_data(data_dir):
    test_y = np.asarray(np.load(
        os.path.join(data_dir, "test", "mntp_embedding_labels.npy"),
        allow_pickle=True)).ravel()
    return test_y


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scores-dir", default="scores")
    ap.add_argument("--data-dir", default=None)
    ap.add_argument("--outdir", default=".")
    args = ap.parse_args()

    candidates = [
        args.data_dir or "",
        "embedding/data/DATA-INTERNAL/sms_spam/Llama3-8b",
        "/mnt/f/dataset/cs/2507.12295_textadbench/embeddings/sms_spam/Llama3-8b",
        os.path.join(args.outdir, "..", "data", "embeddings", "sms_spam", "Llama3-8b"),
    ]
    data_dir = next((c for c in candidates if c and os.path.isfile(
        os.path.join(c, "test", "mntp_embedding_labels.npy"))), None)
    if data_dir is None:
        raise SystemExit("frozen data/test labels not found")
    test_y = load_data(data_dir)

    rows = {}
    for path in sorted(glob.glob(os.path.join(args.scores_dir, "*_test_scores.npy"))):
        name = os.path.basename(path)
        m = re.match(r"(.+?)_seed(\d+)_test_scores\.npy$", name)
        if not m:
            continue
        method, seed = m.group(1), int(m.group(2))
        score = np.load(path)
        auroc = float(roc_auc_score(test_y, score))
        rows.setdefault(method, {})[seed] = auroc

    per_seed = []
    for method in sorted(rows):
        per_seed.append({
            "method": method,
            "seeds": sorted(rows[method]),
            "per_seed": [rows[method][s] for s in sorted(rows[method])],
            "mean": float(np.mean(list(rows[method].values()))),
            "std": float(np.std(list(rows[method].values()))),
        })

    with open(os.path.join(args.outdir, "auroc_per_seed.json"), "w") as f:
        json.dump(per_seed, f, indent=2)
    for r in per_seed:
        with open(os.path.join(args.outdir, f"auroc_{r['method']}.json"), "w") as f:
            json.dump(r, f, indent=2)

    rows_map = {r["method"]: r for r in per_seed}
    methods_sorted = sorted(rows_map, key=lambda m: rows_map[m]["mean"], reverse=True)
    knn_rank = methods_sorted.index("knn") + 1 if "knn" in rows_map else None
    deep_methods = [m for m in ("ae", "dsvdd", "dpad") if m in rows_map]
    deep_max = max(rows_map[m]["mean"] for m in deep_methods) * 100.0

    lines = ["method,type,n_train,n_test,auroc(%),auroc_std(%),knn_rank,deep_max_minus_knn(pp),paper_auroc(%)"]
    for method in ORDER:
        if method not in rows_map:
            continue
        r = rows_map[method]
        auroc_pct = r["mean"] * 100.0
        std_pct = r["std"] * 100.0
        dmk = round(deep_max - auroc_pct, 2) if method == "knn" else ""
        lines.append(
            f"{method},{'deep' if method in deep_methods else 'shallow'},4044,1490,"
            f"{auroc_pct:.2f},{std_pct:.2f},{knn_rank},{dmk},{PAPER_ROW.get(method,'')}"
        )
    with open(os.path.join(args.outdir, "evidence_table.csv"), "w", newline="") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))

    meta = {
        "knn_rank": knn_rank,
        "deep_max_auroc": round(deep_max, 2),
        "deep_max_minus_knn": round(deep_max - rows_map["knn"]["mean"] * 100.0, 2),
        "deep_max_method": max(deep_methods, key=lambda m: rows_map[m]["mean"]),
    }
    with open(os.path.join(args.outdir, "summary_meta.json"), "w") as f:
        json.dump(meta, f, indent=2)
    print(f"\nknn_rank = {knn_rank}; deep_max = {deep_max:.2f}% ({meta['deep_max_method']}); "
          f"deep_max - knn = {meta['deep_max_minus_knn']:.2f}pp")


if __name__ == "__main__":
    main()