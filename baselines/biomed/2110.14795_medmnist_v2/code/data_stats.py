#!/usr/bin/env python3
"""Statistic pass over the frozen MedMNIST v2 2D datasets.

Reads each frozen npz (train/val/test) and writes:
  - results/class_counts.json   per-dataset per-split label counts
  - results/split_sizes.csv     dataset, split, size, n_classes, channels
Also prints a quick sanity report on shapes / dtypes.
Test set is only counted, never loaded into training code here.
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import DATA_DIR, DATASETS

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
os.makedirs(OUT_DIR, exist_ok=True)

KEYS = ["train", "val", "test"]


def main():
    class_counts = {}
    split_sizes = []
    for name, n_classes, channels in DATASETS:
        path = os.path.join(DATA_DIR, f"{name}.npz")
        with np.load(path) as d:
            counts = {}
            for split in KEYS:
                imgs = d[f"{split}_images"]
                labels = d[f"{split}_labels"].squeeze().astype(int)
                assert len(imgs) == len(labels), (name, split)
                total = len(imgs)
                per_class = {int(c): int((labels == c).sum()) for c in range(n_classes)}
                assert sum(per_class.values()) == total, (name, split)
                counts[split] = {"n": total, "per_class": per_class}
                shape = tuple(imgs.shape)
                expected_h = expected_w = 28
                assert shape[1:3] == (expected_h, expected_w), (name, split, shape)
                actual_ch = shape[-1] if len(shape) == 4 else 1
                assert actual_ch == channels, (name, split, actual_ch)
                split_sizes.append({
                    "dataset": name, "split": split, "n": total,
                    "n_classes": n_classes, "channels": channels,
                    "img_h": expected_h, "img_w": expected_w, "dtype": str(imgs.dtype),
                })
        class_counts[name] = counts
        tr = counts["train"]["per_class"]
        print(f"{name}: n_classes={n_classes} channels={channels} "
              f"train_total={counts['train']['n']} train_distribution={tr}")

    with open(os.path.join(OUT_DIR, "class_counts.json"), "w") as f:
        json.dump(class_counts, f, indent=2, sort_keys=True)
    with open(os.path.join(OUT_DIR, "split_sizes.csv"), "w") as f:
        f.write("dataset,split,n,n_classes,channels,img_h,img_w,dtype\n")
        for row in split_sizes:
            f.write(",".join(str(row[k]) for k in
                             ["dataset", "split", "n", "n_classes", "channels",
                              "img_h", "img_w", "dtype"]) + "\n")
    print(f"\nWrote {OUT_DIR}/class_counts.json and split_sizes.csv")
    # sanity print
    print(f"\n{'dataset':<15}{'train':>8}{'val':>8}{'test':>8}")
    for row in split_sizes:
        if row["split"] == "train":
            name = row["dataset"]
            d = {r["split"]: r["n"] for r in split_sizes if r["dataset"] == name}
            print(f"{name:<15}{d['train']:>8}{d['val']:>8}{d['test']:>8}")


if __name__ == "__main__":
    main()