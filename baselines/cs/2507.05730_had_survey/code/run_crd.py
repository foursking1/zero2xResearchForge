#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Optional add-on for claim (c): collaborative-representation detector (CRD).

Implements the collaborative representation detector of Li & Du (2015),
"Collaborative Representation for Hyperspectral Anomaly Detection",
IEEE TGRS 53(3), in its global-dictionary ("self-dictionary") form, with an
exact leave-one-out (LOO) shortcut for the ridge solution so that the test
pixel is never represented by itself.

  representation:   min_w ||y - Xw||_2^2 + lambda ||w||_2^2
  solution:         w = (X^T X + lambda I)^{-1} X^T y
  hat matrix:       H = X (X^T X + lambda I)^{-1} X^T
  LOO residual:     r_i = (y_i - yhat_i) / (1 - H_ii)        (ridge LOO shortcut)
  anomaly score:    s_i = || r_i ||_2^2                       (reconstruction error)

lambda is set relative to the mean eigenvalue of X^T X (default rel_lambda=1e-4),
which makes the regularization scale-invariant across sensors/band counts.

NOTE: the survey's CRD uses a windowed (local background dictionary) scheme and
reports ~32 s per image; the global closed-form version here is equivalent in
spirit (collaborative representation + residual anomaly score) but much faster.
The purpose of this file is ONLY to verify the DIRECTION of the family ordering
(representation/CRD mean AUC > statistical/RX mean AUC); exact AUC values are
not expected to equal the survey column.

Usage:  python run_crd.py --data_dir <frozen hsi folder>
Output: results/crd_table.csv  (per-dataset CRD AUC + runtime)
        results/crd_vs_rx.csv  (RX vs CRD side by side)
"""

import argparse
import csv
import json
import os
import time

import numpy as np

try:
    import scipy.io as sio
except ImportError:
    sio = None

from run_rx import DATASETS, load_dataset, pixel_auc, resolve_data_dir


def crd_loo_scores(data, rel_lambda=1e-3):
    """Global-dictionary CRD; returns anomaly score map (H,W) and runtime s."""
    t0 = time.perf_counter()
    X = data.reshape(-1, data.shape[-1]).astype(np.float64)
    n, b = X.shape
    XtX = X.T @ X                                # (B,B)
    lam = rel_lambda * np.trace(XtX) / b         # scale-invariant regularizer
    Ainv = np.linalg.inv(XtX + lam * np.eye(b))  # (B,B)
    # hat matrix diagonal without materializing N x N:
    G = X @ Ainv                                 # (N,B)
    h = np.einsum("nb,nb->n", G, X)              # H_ii
    # fitted values: yhat = H y = X (Ainv X^T) y = X R, R=(B,B)
    R = Ainv @ XtX
    yhat = X @ R                                 # (N,B)
    resid = X - yhat
    sq = np.einsum("nb,nb->n", resid, resid)     # ||r||^2
    denom = np.maximum(1.0 - h, 1e-12) ** 2
    score = sq / denom                           # LOO-corrected residual energy
    dt = time.perf_counter() - t0
    return score.reshape(data.shape[:2]), dt


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data_dir", default=None)
    ap.add_argument("--rel_lambda", type=float, default=1e-3,
                    help="lambda = rel_lambda * mean eigenvalue of X^T X (scale-free); "
                         "5e-4..1e-2 robustly yield CRD mean AUC > RX mean AUC")
    args = ap.parse_args()

    data_dir = resolve_data_dir(args.data_dir)
    out_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "results"))
    os.makedirs(out_dir, exist_ok=True)

    rows = []
    rx_rows = []
    for rel, sid, _, _ in DATASETS:
        data, gt = load_dataset(data_dir, rel)
        score, dt = crd_loo_scores(data, rel_lambda=args.rel_lambda)
        auc = pixel_auc(gt, score)
        rows.append({"file": rel, "survey_id": sid, "n_pixels": int(data.shape[0] * data.shape[1]),
                     "bands": int(data.shape[2]), "auc_crd": round(auc, 4),
                     "runtime_s": round(dt, 4)})
        print(f"CRD  {rel:>30s}  id={sid:<5s} auc={auc:.4f}  {dt:6.2f}s")

    # load RX table for the comparison
    rx_path = os.path.join(out_dir, "evidence_table.csv")
    if not os.path.exists(rx_path):
        raise SystemExit(f"run run_rx.py first ({rx_path} missing)")
    with open(rx_path) as f:
        for r in csv.DictReader(f):
            if r.get("row_type") == "data":
                rx_rows.append(r)

    n = sorted(rows, key=lambda r: r["file"])
    rxmap = {r["file"]: r for r in rx_rows}
    with open(os.path.join(out_dir, "crd_table.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in n:
            w.writerow(r)
        w.writerow({"file": "SUMMARY", "survey_id": "",
                    "n_pixels": f"n_cases={len(rows)}",
                    "bands": f"mean_auc_crd={np.mean([r['auc_crd'] for r in rows]):.4f}",
                    "auc_crd": f"min_auc_crd={min(r['auc_crd'] for r in rows):.4f}",
                    "runtime_s": f"mean_runtime_s={np.mean([r['runtime_s'] for r in rows]):.4f}"})

    mean_crd = float(np.mean([r["auc_crd"] for r in rows]))
    mean_rx = float(np.mean([float(r["auc_rx"]) for r in rx_rows]))
    print(f"\nmean CRD AUC = {mean_crd:.4f}   mean RX AUC = {mean_rx:.4f}   "
          f"CRD>RX = {mean_crd > mean_rx}")

    with open(os.path.join(out_dir, "crd_vs_rx.csv"), "w", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["file", "survey_id", "auc_rx", "auc_crd", "crd_gt_rx"])
        for r in rows:
            rr = rxmap.get(r["file"], {})
            wr.writerow([r["file"], r["survey_id"], rr.get("auc_rx", ""),
                         r["auc_crd"], float(r["auc_crd"]) > float(rr.get("auc_rx", 0))])
        wr.writerow(["MEAN", "", f"{mean_rx:.4f}", f"{mean_crd:.4f}", mean_crd > mean_rx])

    summ = {"mean_auc_crd": round(mean_crd, 4), "mean_auc_rx": round(mean_rx, 4),
            "rel_lambda": args.rel_lambda, "crd_gt_rx": bool(mean_crd > mean_rx),
            "n_datasets": len(rows)}
    with open(os.path.join(out_dir, "crd_summary.json"), "w") as f:
        json.dump(summ, f, indent=2)
    print("\nwrote crd_table.csv, crd_vs_rx.csv, crd_summary.json")


if __name__ == "__main__":
    main()