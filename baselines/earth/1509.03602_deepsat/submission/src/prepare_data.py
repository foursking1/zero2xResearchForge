#!/usr/bin/env python3
"""Data preparation for SAT-6 (arXiv:1509.03602) reproduction.

Reads the frozen official SAT-6 *Test split* parquet (81,000 28x28 RGB tiles,
6 classes), decodes images, performs a fixed-seed STRATIFIED split into
train / val / test subsets (70 / 15 / 15), computes per-channel
normalization statistics from the TRAIN subset only, and caches everything
as .npz so the downstream training script can re-run from the cache or
directly from the frozen parquet.

Usage:
    python prepare_data.py --data /path/to/frozen.parquet [--seed 42] [--cache dir]
"""
import argparse
import json
import os
import time

import numpy as np
from sklearn.model_selection import train_test_split

from common import CLASS_NAMES, N_CLASSES, decode_images, load_dataframe, resolve_data_path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=None, help="path to frozen sat6 parquet")
    ap.add_argument("--seed", type=int, default=42, help="fixed seed for the split")
    ap.add_argument("--cache", default=None, help="output directory for the cache")
    args = ap.parse_args()

    data_path = resolve_data_path(args.data)
    print(f"[prepare] loading frozen parquet: {data_path}")
    t0 = time.time()
    df = load_dataframe(data_path)
    print(f"[prepare] {len(df)} rows in {time.time()-t0:.1f}s")

    labels = df["label"].to_numpy(np.int64)
    print("[prepare] label counts:", dict(zip(*np.unique(labels, return_counts=True))))

    images = decode_images(df)
    print(f"[prepare] images array: {images.shape} {images.dtype}")

    # ---- fixed-seed stratified split 70 / 15 / 15 (train / val / test) ----
    train_idx, temp_idx = train_test_split(
        np.arange(len(df)), train_size=0.70, random_state=args.seed,
        stratify=labels)
    val_idx, test_idx = train_test_split(
        temp_idx, train_size=0.50, random_state=args.seed + 1,
        stratify=labels[temp_idx])

    print(f"[prepare] train={len(train_idx)} val={len(val_idx)} test={len(test_idx)}")

    tr_images = images[train_idx]
    tr_labels = labels[train_idx]

    # normalization stats from TRAIN subset only (anti-leakage)
    mean = tr_images.astype(np.float32).mean(axis=(0, 1, 2)) / 255.0
    std = tr_images.astype(np.float32).std(axis=(0, 1, 2)) / 255.0
    print(f"[prepare] train mean={mean} std={std}")

    cache_dir = args.cache or os.path.join(os.path.dirname(__file__), "..", "data_cache")
    os.makedirs(cache_dir, exist_ok=True)
    # NOTE: pixel arrays are intentionally NOT cached here; every script re-decodes
    # them from the frozen parquet. The cache stores only the (seed-fixed) split
    # indices and the train-only normalization statistics.
    np.savez_compressed(
        os.path.join(cache_dir, "sat6_split.npz"),
        train_idx=train_idx, val_idx=val_idx, test_idx=test_idx,
        mean=mean, std=std,
        class_names=np.array(CLASS_NAMES),
    )

    summary = {
        "seed": args.seed,
        "n_total": int(len(df)),
        "train": int(len(train_idx)),
        "val": int(len(val_idx)),
        "test": int(len(test_idx)),
        "mean": mean.tolist(),
        "std": std.tolist(),
        "overall_majority_class": CLASS_NAMES[int(np.argmax(np.bincount(labels)))],
        "overall_majority_frac": float(np.max(np.bincount(labels)) / len(labels)),
    }
    with open(os.path.join(cache_dir, "split_stats.json"), "w") as f:
        json.dump(summary, f, indent=2)
    print(f"[prepare] cache written to {cache_dir}")


if __name__ == "__main__":
    main()