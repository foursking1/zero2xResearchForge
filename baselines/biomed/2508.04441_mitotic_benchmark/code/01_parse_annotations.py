#!/usr/bin/env python3
"""Step 1 - Parse frozen MIDOG2022 subset and extract patch crops.

Loads the official MS COCO annotation JSON, filters the four frozen images
(002/008/024/063), counts mitotic figures (cat 1) vs hard negatives (cat 2),
and crops square patches centred on each annotation bbox.

Outputs
    results/patches.npz       - X (N,H,W,3) uint8 crops, y (N,) int labels,
                                meta (image file names, patch ids)
    results/annotations_stats.json - subset vs full-dataset statistics
"""
from __future__ import annotations
import argparse
import json
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import resolve_paths, DEFAULT_PNG_NAMES

CAT_MITOTIC = 1
CAT_HARD_NEG = 2
PATCH_SIZE = 224  # native input size of both torchvision backbones (ViT needs 224)


def parse_bbox(bbox):
    """MIDOG COCO bbox stores two corners [x1,y1,x2,y2] (the PNG-version
    annotations use corner boxes rather than COCO x,y,w,h)."""
    x1, y1, x2, y2 = [float(v) for v in bbox]
    if x2 < x1:
        x1, x2 = x2, x1
    if y2 < y1:
        y1, y2 = y2, y1
    return x1, y1, x2, y2


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", default=None)
    ap.add_argument("--out", default=None, help="output directory (default: agent_solution/results)")
    ap.add_argument("--patch-size", type=int, default=PATCH_SIZE)
    args = ap.parse_args()

    json_path, *png_paths = resolve_paths(args.data_root)
    out_dir = args.out or os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results")
    out_dir = os.path.abspath(out_dir)
    os.makedirs(out_dir, exist_ok=True)

    with open(json_path) as f:
        coco = json.load(f)
    idmap = {img["file_name"]: img for img in coco["images"]}
    keep_ids = {idmap[name]["id"] for name in DEFAULT_PNG_NAMES}
    assert set(DEFAULT_PNG_NAMES) <= set(idmap.keys())

    categ = {c["id"]: c["name"] for c in coco["categories"]}
    print("categories:", categ)

    total_counts = {CAT_MITOTIC: 0, CAT_HARD_NEG: 0}
    sub_counts = {n: {CAT_MITOTIC: 0, CAT_HARD_NEG: 0} for n in DEFAULT_PNG_NAMES}
    full = {img["id"]: img for img in coco["images"]}
    for ann in coco["annotations"]:
        if ann["category_id"] not in (CAT_MITOTIC, CAT_HARD_NEG):
            continue
        total_counts[ann["category_id"]] += 1
        img_name = full.get(ann["image_id"], {}).get("file_name")
        if img_name in sub_counts:
            sub_counts[img_name][ann["category_id"]] += 1

    print("full dataset counts:", total_counts)
    for n in DEFAULT_PNG_NAMES:
        print(f"  {n}: mitotic={sub_counts[n][CAT_MITOTIC]}  hard_neg={sub_counts[n][CAT_HARD_NEG]}")

    crops = []
    labels = []
    patch_ids = []
    img_names = []
    sizes = {}
    for png_path, name in zip(png_paths, DEFAULT_PNG_NAMES):
        img = idmap[name]
        img_arr = np.asarray(Image.open(png_path))
        sizes[name] = img_arr.shape
        print(f"loaded {name}: shape={img_arr.shape}")
        for ann in coco["annotations"]:
            if ann["image_id"] != img["id"]:
                continue
            if ann["category_id"] not in (CAT_MITOTIC, CAT_HARD_NEG):
                continue
            x1, y1, x2, y2 = parse_bbox(ann["bbox"])
            cx, cy = (x1 + x2) / 2.0, (y1 + y2) / 2.0
            h2 = args.patch_size // 2
            x0 = int(round(cx - h2))
            y0 = int(round(cy - h2))
            x0 = max(0, min(x0, img_arr.shape[1] - args.patch_size))
            y0 = max(0, min(y0, img_arr.shape[0] - args.patch_size))
            crop = img_arr[y0:y0 + args.patch_size, x0:x0 + args.patch_size]
            if crop.shape[0] != args.patch_size or crop.shape[1] != args.patch_size:
                continue  # annotation too close to the border
            crops.append(crop)
            labels.append(1 if ann["category_id"] == CAT_MITOTIC else 0)
            patch_ids.append(ann["id"])
            img_names.append(name)
        del img_arr

    X = np.stack(crops)
    y = np.asarray(labels, dtype=np.int64)
    meta = np.stack([np.asarray(img_names, dtype=object), np.asarray(patch_ids, dtype=np.int64)], axis=-1)

    np.savez_compressed(
        os.path.join(out_dir, "patches.npz"),
        X=X, y=y, img_names=img_names, patch_ids=np.asarray(patch_ids, dtype=np.int64),
    )

    stats = {
        "subset_label": "MIDOG2022 training subset (frozen: 002,008,024,063)",
        "full_dataset_mitotic": total_counts[CAT_MITOTIC],
        "full_dataset_hard_negative": total_counts[CAT_HARD_NEG],
        "subset_mitotic": int((y == 1).sum()),
        "subset_hard_negative": int((y == 0).sum()),
        "subset_total_annotations": int(len(y)),
        "per_image_mitotic": {n: sub_counts[n][CAT_MITOTIC] for n in DEFAULT_PNG_NAMES},
        "per_image_hard_negative": {n: sub_counts[n][CAT_HARD_NEG] for n in DEFAULT_PNG_NAMES},
        "image_sizes_px": {n: list(sizes[n][:2]) for n in sizes},
        "patch_size_px": args.patch_size,
        "validation": {
            "subset_mitotic_eq_counted": int((y == 1).sum()) == int(
                sum(sub_counts[n][CAT_MITOTIC] for n in DEFAULT_PNG_NAMES)
            ),
        },
}
    with open(os.path.join(out_dir, "annotations_stats.json"), "w") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    print("saved patches:", X.shape, "->", os.path.join(out_dir, "patches.npz"))
    print("saved stats ->", os.path.join(out_dir, "annotations_stats.json"))


if __name__ == "__main__":
    main()