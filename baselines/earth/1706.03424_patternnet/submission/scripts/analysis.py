#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
analysis.py
===========
Aggregates retrieval results, performs a class-difficulty analysis and produces
figures for the PatternNet (1706.03424) reproduction task.

Outputs (into --out-dir):
    class_summary.csv      per-class mAP / P@5 / P@10 (sorted by mAP)
    class_centroids.csv    mean pairwise inter-class centroid cosine similarity
                           (a proxy for class visual confusability)
    fig_per_class_map.png  horizontal bar chart of per-class mAP
    fig_top_confusions.csv most confusable class pairs
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--features", required=True)
    ap.add_argument("--labels", required=True)
    ap.add_argument("--evidence", required=True, help="evidence_table.csv")
    ap.add_argument("--class-names", default=None)
    ap.add_argument("--out-dir", default="../results")
    aa = ap.parse_args()

    names_raw = None
    if aa.class_names and Path(aa.class_names).exists():
        names_raw = json.load(open(aa.class_names))

    labels = np.load(aa.labels).astype(np.int64)
    F = np.load(aa.features)
    n_classes = int(labels.max()) + 1

    rows = list(csv.DictReader(open(aa.evidence)))
    per_class = {int(r["class_id"]): r for r in rows if int(r["class_id"]) >= 0}

    if names_raw is None:
        names_raw = [per_class[c]["class_name"] for c in range(n_classes)]

    out = Path(aa.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    # ---- sorted per-class summary ----
    ordered = sorted(range(n_classes), key=lambda c: float(per_class[c]["mAP"]),
                     reverse=True)
    with open(out / "class_summary.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["rank", "class_id", "class_name", "mAP", "p_at_5", "p_at_10",
                    "queries"])
        for rk, cid in enumerate(ordered, 1):
            r = per_class[cid]
            w.writerow([rk, cid, names_raw[cid], r["mAP"], r["p_at_5"],
                        r["p_at_10"], r["queries"]])

    # ---- class centroid cosine similarity (confusability proxy) ----
    centroids = np.stack([F[labels == c].mean(axis=0) for c in range(n_classes)])
    centroids /= np.linalg.norm(centroids, axis=1, keepdims=True) + 1e-12
    C = centroids @ centroids.T
    np.fill_diagonal(C, -1.0)
    iu = np.triu_indices(n_classes, k=1)
    pairs = [(i, j, float(C[i, j])) for i, j in zip(*iu)]
    pairs.sort(key=lambda t: t[2], reverse=True)
    with open(out / "class_centroids.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["class_a", "class_b", "centroid_cosine"])
        for i, j, s in pairs:
            w.writerow([names_raw[i], names_raw[j], f"{s:.4f}"])
    with open(out / "top_confusions.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["class_a", "class_b", "centroid_cosine"])
        for i, j, s in pairs[:15]:
            w.writerow([names_raw[i], names_raw[j], f"{s:.4f}"])

    # ---- figure ----
    fig, ax = plt.subplots(figsize=(11, 9))
    maps = [float(per_class[c]["mAP"]) for c in ordered]
    names_sorted = [names_raw[c] for c in ordered]
    ax.barh(np.arange(n_classes), maps, color="#4C72B0")
    ax.set_yticks(np.arange(n_classes))
    ax.set_yticklabels(names_sorted, fontsize=8)
    ax.invert_yaxis()
    ax.axvline(0.61, color="darkred", lw=1.2, ls="--",
               label="paper anchor mAP 0.61")
    ax.set_xlabel("class mAP (each image as query over full gallery)")
    ax.set_title("PatternNet retrieval per-class mAP -- resnet18 features")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out / "fig_per_class_map.png", dpi=180)
    plt.close(fig)

    print(f"[analysis] wrote {out/'class_summary.csv'}, {out/'class_centroids.csv'}, "
          f"{out/'top_confusions.csv'}, {out/'fig_per_class_map.png'}")
    print("[analysis] top-5 confusable centroid pairs:")
    for i, j, s in pairs[:5]:
        print(f"    {names_raw[i]:20s} ~ {names_raw[j]:20s}  cos={s:.3f}")


if __name__ == "__main__":
    main()