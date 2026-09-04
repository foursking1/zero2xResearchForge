#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
evaluate_retrieval.py
=====================
PatternNet (1706.03424) content-based image retrieval -- evaluation.

Retrieval protocol (following Zhou et al. 2018, PatternNet §5.2):
    * every image in the dataset is used as a query (or a fixed sampled subset);
    * the gallery is the whole dataset with the query itself excluded;
    * images are ranked by cosine similarity of L2-normalized CNN embeddings
      (cosine sim == dot product after L2 normalization);
    * mAP is the mean over queries of average precision (same class = relevant);
    * P@5 / P@10 are the fraction of the top-5 / top-10 retrievals that share
      the query's class.

The similarity ranking depends only on the L2-normalized embeddings, so the
evaluation is fully deterministic (no RNG influence on ranking; the sampling
RNG is seeded).

Outputs
-------
    <out-dir>/evidence_table.csv : one row per class (38) + global row
    <out-dir>/metrics.json      : overall metrics
    <out-dir>/per_query.csv     : per-image details (optional --dump-per-query)

Example
-------
    python evaluate_retrieval.py \
        --features ../artifacts/features_resnet18.npy \
        --labels ../artifacts/labels.npy \
        --out-dir ../results \
        --class-names ../artifacts/class_names.json
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np


CLASS_NAMES = [
    "airplane", "baseballfield", "basketballcourt", "beach",
    "bridge", "cemetery", "chaparral", "christmastreefarm",
    "closedroad", "coastalmansion", "crosswalk", "denseresidential",
    "ferryterminal", "footballfield", "forest", "freeway",
    "golfcourse", "harbor", "intersection", "mobilehomepark",
    "nursinghome", "oilgasfield", "oilwell", "overpass",
    "parkinglot", "parkingspace", "railway", "river",
    "runway", "runwaymarking", "shippingyard", "solarpanel",
    "sparseresidential", "storagetank", "swimmingpool", "tenniscourt",
    "transformerstation", "wastewaterplant",
]


def ap_metrics_one_row(sims: np.ndarray, gal_labels: np.ndarray, target_label: int,
                       self_idx: int) -> tuple[float, float, float]:
    """AP, P@5, P@10 for one query given its cosine similarities to a gallery."""
    s = sims.copy()
    s[self_idx] = -np.inf  # exclude the query itself
    order = np.argsort(-s)
    rel = gal_labels[order] == target_label
    n_rel = rel.sum()
    if n_rel == 0:
        return 0.0, 0.0, 0.0
    cum = np.cumsum(rel)
    ranks = np.arange(1, len(rel) + 1)
    prec = cum / ranks
    ap = float((prec * rel).sum() / n_rel)
    p5 = float(rel[:5].mean())
    p10 = float(rel[:10].mean())
    return ap, p5, p10


def main() -> None:
    ap = argparse.ArgumentParser(description="PatternNet retrieval evaluation")
    ap.add_argument("--features", required=True,
                    help="L2-normalized features .npy (N x D)")
    ap.add_argument("--labels", required=True, help="labels .npy (N,)")
    ap.add_argument("--out-dir", default="../results")
    ap.add_argument("--class-names", default=None, help="optional json list of 38 names")
    ap.add_argument("--exclude-self", action="store_true", default=True)
    ap.add_argument("--sample-per-class", type=int, default=0,
                    help="if >0 use fixed-RNG subsample of queries per class")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--dump-per-query", action="store_true")
    args = ap.parse_args()

    F = np.load(args.features)
    labels = np.load(args.labels).astype(np.int64)
    n_all = F.shape[0]
    n_classes = int(labels.max()) + 1

    names = CLASS_NAMES[:n_classes]
    if args.class_names and Path(args.class_names).exists():
        names = json.load(open(args.class_names))
    assert len(names) == n_classes, (len(names), n_classes)

    if args.sample_per_class:
        rng = np.random.RandomState(args.seed)
        query_idx = np.concatenate([
            rng.choice(np.where(labels == c)[0],
                       size=min(args.sample_per_class, int((labels == c).sum())),
                       replace=False)
            for c in range(n_classes)])
        query_idx.sort()
        print(f"[eval] sampling {len(query_idx)} queries "
              f"({args.sample_per_class}/class, seed={args.seed})")
    else:
        query_idx = np.arange(n_all)
        print(f"[eval] every-image-as-query protocol ({n_all} queries)")

    n_q = len(query_idx)
    # gallery index each query maps to (itself) for self-exclusion
    gal_self = query_idx  # query i retrieves over full F and excludes F[query_idx[i]]

    aps = np.empty(n_q)
    p5s = np.empty(n_q)
    p10s = np.empty(n_q)
    q_labels = labels[query_idx]

    block = 512
    for lo in range(0, n_q, block):
        hi = min(lo + block, n_q)
        Fq = F[query_idx[lo:hi]]
        # similarities: (block, n_all)
        S = Fq @ F.T
        for j in range(hi - lo):
            aps[lo + j], p5s[lo + j], p10s[lo + j] = ap_metrics_one_row(
                S[j], labels, q_labels[lo + j], gal_self[lo + j])
        print(f"  ... {hi}/{n_q}", flush=True)

    mAP, P5, P10 = float(aps.mean()), float(p5s.mean()), float(p10s.mean())

    rows = []
    for c in range(n_classes):
        m = q_labels == c
        n_rel = int((labels == c).sum()) - 1  # exclude the query itself
        rows.append({
            "split": "retrieval_full_gallery",
            "class_id": c,
            "class_name": names[c],
            "queries": int(m.sum()),
            "retrieved": n_all - 1,
            "relevant": n_rel,
            "mAP": float(aps[m].mean()),
            "p_at_5": float(p5s[m].mean()),
            "p_at_10": float(p10s[m].mean()),
        })
    rows.append({
        "split": "retrieval_full_gallery",
        "class_id": -1,
        "class_name": "OVERALL",
        "queries": n_q,
        "retrieved": n_all - 1,
        "relevant": n_all - n_classes,
        "mAP": mAP,
        "p_at_5": P5,
        "p_at_10": P10,
    })

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    with open(out / "evidence_table.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    metrics = {
        "mAP": mAP,
        "p_at_5": P5,
        "p_at_10": P10,
        "num_queries": int(n_q),
        "gallery_size": int(n_all),
        "exclude_self": bool(args.exclude_self),
        "feature": str(Path(args.features).stem),
        "seed": args.seed,
        "sample_per_class": args.sample_per_class,
    }
    with open(out / "metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)

    if args.dump_per_query:
        with open(out / "per_query.csv", "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["query_idx", "label", "class_name", "AP", "P@5", "P@10"])
            for i, qi in enumerate(query_idx):
                w.writerow([int(qi), int(q_labels[i]), names[int(q_labels[i])],
                            f"{aps[i]:.6f}", f"{p5s[i]:.4f}", f"{p10s[i]:.4f}"])

    print(f"[eval] mAP={mAP:.4f}  P@5={P5:.4f}  P@10={P10:.4f} "
          f" (queries={n_q}, gallery={n_all}, feature={Path(args.features).stem})")


if __name__ == "__main__":
    main()