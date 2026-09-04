#!/usr/bin/env python3
"""Fast, faithful reproduction of the reported metrics from the frozen data.

Recomputes, directly from the frozen SAT-6 Test split parquet:
  1. the same fixed-seed stratified 70/15/15 split used at training time;
  2. model predictions on the held-out test subset using the shipped
     checkpoint model_sat6.pt;
  3. the full evidence table, metrics.json and confusion matrix.

This guarantees every reported number can be rebuilt from the frozen data
plus the committed artifacts without re-running the (potentially long)
training. Re-running train.py alone regenerates everything from scratch.

Usage:
    python reproduce_metrics.py [--data PATH] [--ckpt ../model_sat6.pt]
                                [--out ../..] [--device auto]
"""
import argparse
import json
import os
import time

import numpy as np
import torch
from sklearn.model_selection import train_test_split

from common import CLASS_NAMES, N_CLASSES, decode_images, load_dataframe, resolve_data_path
from train import Sat6Dataset, evaluate, make_model, metrics, pick_device


def reproduce(args):
    t0 = time.time()
    data_path = resolve_data_path(args.data)
    print(f"[repro] loading frozen parquet: {data_path}")
    df = load_dataframe(data_path)
    labels = df["label"].to_numpy(np.int64)
    images = decode_images(df)

    seed = args.seed
    train_idx, temp_idx = train_test_split(
        np.arange(len(df)), train_size=0.70, random_state=args.seed,
        stratify=labels)
    val_idx, test_idx = train_test_split(
        temp_idx, train_size=0.50, random_state=args.seed + 1,
        stratify=labels[temp_idx])

    # normalization stats recomputed from the TRAIN subset only,
    # with the exact same formula as prepare_data.py
    mean = images[train_idx].astype(np.float32).mean(axis=(0, 1, 2)) / 255.0
    std = images[train_idx].astype(np.float32).std(axis=(0, 1, 2)) / 255.0

    cache_npz = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "..", "data_cache", "sat6_split.npz")
    if os.path.exists(cache_npz):
        cached = np.load(cache_npz)
        assert np.array_equal(train_idx, cached["train_idx"]), "split mismatch!"
        assert np.array_equal(test_idx, cached["test_idx"]), "split mismatch!"
        assert np.allclose(mean, cached["mean"], atol=1e-6), "mean mismatch!"
        print("[repro] recomputed split identical to trained split (cache cross-check ok)")

    ckpt = torch.load(args.ckpt, map_location="cpu", weights_only=False)
    print(f"[repro] split reproduced (train={len(train_idx)} val={len(val_idx)} "
          f"test={len(test_idx)}), checkpoint val_acc={ckpt['val_acc_best']:.4f}")

    device = pick_device(args.device)
    model = make_model().to(device)
    model.load_state_dict(ckpt["model_state"])
    model.eval()

    test_ds = Sat6Dataset(images[test_idx], labels[test_idx], mean, std, train=False)
    test_loader = torch.utils.data.DataLoader(
        test_ds, batch_size=512, shuffle=False, num_workers=0)
    preds, gts = evaluate(model, test_loader, device)
    m = metrics(preds, gts)

    overall_acc = m["accuracy"]
    majority_frac = float(np.bincount(gts).max() / len(gts))
    print(f"[repro] overall accuracy = {overall_acc:.6f}  macro-F1 = {m['macro_f1']:.6f}")

    out_root = os.path.abspath(args.out)
    results_dir = os.path.join(out_root, "results")
    os.makedirs(results_dir, exist_ok=True)

    import csv
    rows = []
    for c in range(N_CLASSES):
        rows.append({
            "split": "test", "class_id": c, "class_name": CLASS_NAMES[c],
            "tp": int(m["tp"][c]), "fp": int(m["fp"][c]),
            "tn": int(m["tn"][c]), "fn": int(m["fn"][c]),
            "precision": round(float(m["precision"][c]), 6),
            "recall": round(float(m["recall"][c]), 6),
            "f1": round(float(m["f1"][c]), 6),
            "accuracy": round(float(m["per_class_accuracy"][c]), 6),
        })
    rows.append({
        "split": "test", "class_id": -1, "class_name": "overall",
        "tp": int(m["tp"].sum()), "fp": int(m["fp"].sum()),
        "tn": int(m["tn"].sum()), "fn": int(m["fn"].sum()),
        "precision": round(float(np.nanmean(m["precision"])), 6),
        "recall": round(float(np.nanmean(m["recall"])), 6),
        "f1": round(m["macro_f1"], 6),
        "accuracy": round(overall_acc, 6),
    })
    with open(os.path.join(results_dir, "evidence_table.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    np.save(os.path.join(results_dir, "confusion_matrix.npy"), m["cm"])

    with open(os.path.join(results_dir, "metrics.json")) as f:
        prev = json.load(f)
    prev.update({
        "reproduced_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "reproduced_overall_accuracy": round(overall_acc, 6),
        "overall_accuracy": round(overall_acc, 6),
        "macro_f1": round(m["macro_f1"], 6),
        "test_confusion_matrix": m["cm"].tolist(),
        "seed": seed,
    })
    with open(os.path.join(results_dir, "metrics.json"), "w") as f:
        json.dump(prev, f, indent=2)
    print(f"[repro] metrics + evidence table rewritten under {results_dir} "
          f"({time.time()-t0:.0f}s)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=None)
    ap.add_argument("--ckpt", default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--device", default="auto")
    args = ap.parse_args()
    src_dir = os.path.dirname(os.path.abspath(__file__))
    if not args.ckpt:
        args.ckpt = os.path.join(src_dir, "..", "model_sat6.pt")
    args.out = args.out or os.path.join(src_dir, "..")
    reproduce(args)