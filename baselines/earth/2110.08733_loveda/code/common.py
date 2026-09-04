"""Shared constants and utilities for the LoveDA reproduction."""
import os

import numpy as np

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # agent_solution/
DATA = os.path.join(BASE, "data_decoded")
SPLITS = os.path.join(BASE, "splits")
RESULTS = os.path.join(BASE, "results")
CKPT = os.path.join(BASE, "checkpoints")
EVIDENCE = os.path.join(BASE, "evidence")
for d in (RESULTS, CKPT, EVIDENCE):
    os.makedirs(d, exist_ok=True)

SEED = 2026
VAL = 7
CLASS_NAMES = {
    1: "background", 2: "building", 3: "road", 4: "water",
    5: "barren", 6: "forest", 7: "agriculture",
}
# train/val index lists (set by split.py with seed=2026, 85/15)
TRAIN_IDX = np.loadtxt(os.path.join(SPLITS, "train.csv"), delimiter=",", skiprows=1, dtype=int)
VAL_IDX = np.loadtxt(os.path.join(SPLITS, "val.csv"), delimiter=",", skiprows=1, dtype=int)


def load_all():
    from PIL import Image
    n = 562
    images = np.zeros((n, 1024, 1024, 3), dtype=np.uint8)
    masks = np.zeros((n, 1024, 1024), dtype=np.uint8)
    for i in range(n):
        images[i] = np.array(Image.open(os.path.join(DATA, "images", f"{i:04d}.png")))
        masks[i] = np.array(Image.open(os.path.join(DATA, "masks", f"{i:04d}.png")))
    return images, masks


def detect_domain(mask):
    """Heuristic urban/rural split from label statistics (no domain tags in mirror).
    rural if agriculture+forest dominates building+road+barren, else urban."""
    u, c = np.unique(mask, return_counts=True)
    frac = {int(v): int(cc) for v, cc in zip(u, c)}
    tot = max(1, mask.size - frac.get(0, 0))
    rural = (frac.get(7, 0) + frac.get(6, 0)) / tot
    urban = (frac.get(2, 0) + frac.get(3, 0) + frac.get(5, 0)) / tot
    return "rural" if rural > urban else "urban"


def compute_pixel_stats(mask):
    u, c = np.unique(mask, return_counts=True)
    return {int(v): int(cc) for v, cc in zip(u, c)}