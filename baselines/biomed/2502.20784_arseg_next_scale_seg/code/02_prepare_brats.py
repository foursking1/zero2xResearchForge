#!/usr/bin/env python3
"""Prepare the frozen BraTS 2021 mini subset for the 2D axial-slice segmentation task.

The shared frozen file ``brats2021_mini.parquet`` (from 2112.10074 card) holds 10 cases
of single-modality 240x240x155 NIFTI volumes with 4-class labels {0:BG, 1:NEC, 2:ED, 4:ET}.
Protocol (documented simplification, TASK.md direction 2): 2D axial slices, resized to
128x128, trained on slices that contain tumor, evaluated on all tumor-bearing axial
slices of the fixed test patients.  Labels are mapped to three clinical regions
  WT = 1|2|4, TC = 1|4, ET = 4   (BraTS convention; Dice per region, then averaged).

Patient-level split (fixed): patients [0..6] train, [7] val, [8,9] test (order in parquet).
Note on relation to full BraTS 2021: the full benchmark has 1,251 subjects and 4 input
modalities; the frozen mini set has 10 subjects and a single modality — our numbers are a
*sanity / mechanism* check on the mini subset, not a reproduction of Table 2.
"""
from __future__ import annotations
import os, sys, io, time, json, argparse
import numpy as np
import pandas as pd
import nibabel as nib
from scipy.ndimage import zoom

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CACHE = os.path.join(ROOT, "results", "cache", "brats")
os.makedirs(CACHE, exist_ok=True)

def _resolve_brats_path():
    local = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         "..", "data", "brats2021_mini.parquet")
    if os.path.exists(local):
        return local
    shared = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))), "2112.10074_qubrats_uncertainty_seg",
        "brats2021_mini.parquet")
    if os.path.exists(shared):
        return shared
    return None


DEFAULT_PARQUET = _resolve_brats_path()
SIZE = 128
SEED = 0


def brats_normalize(v: np.ndarray) -> np.ndarray:
    lo, hi = np.percentile(v, [0.5, 99.5])
    v = np.clip(v, lo, hi).astype(np.float32)
    v = (v - v.mean()) / (v.std() + 1e-6)
    return v.astype(np.float32)


def load_case(row, tmpdir="/tmp/opencode/brats_tmp"):
    os.makedirs(tmpdir, exist_ok=True)
    p_img = os.path.join(tmpdir, "case_img.nii.gz")
    p_seg = os.path.join(tmpdir, "case_seg.nii.gz")
    with open(p_img, "wb") as f:
        f.write(row["image"]["bytes"])
    with open(p_seg, "wb") as f:
        f.write(row["annotations"]["bytes"])
    img = nib.load(p_img).get_fdata().astype(np.float32)
    seg = nib.load(p_seg).get_fdata().astype(np.int16)
    return img, seg


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--parquet", default=DEFAULT_PARQUET)
    args = ap.parse_args()
    df = pd.read_parquet(args.parquet)
    assert len(df) == 10

    train_pts = [0, 1, 2, 3, 4, 5, 6]
    val_pts = [7]
    test_pts = [8, 9]
    split = {"train": train_pts, "val": val_pts, "test": test_pts}

    records = []
    for pi in range(len(df)):
        img, seg = load_case(df.iloc[pi])
        seg_map = seg.copy()
        seg_map[seg_map == 4] = 3          # ET class index 3 in {0,1,2,3} map
        seg_map[seg_map == 1] = 1          # NEC -> 1
        seg_map[seg_map == 2] = 2          # ED  -> 2
        for z in range(img.shape[2]):
            sl_img = img[..., z]
            sl_seg = seg_map[..., z]
            if sl_seg.sum() == 0:
                continue                    # skip non-tumour slices
            if sl_img.shape[0] != SIZE:
                iz, jz = zoom_factor(sl_img.shape, SIZE)
                sl_img = zoom(sl_img, iz, order=1)
                sl_seg = zoom(sl_seg, jz, order=0)
            records.append((pi, z, sl_img.astype(np.float32), sl_seg.astype(np.uint8)))

    print(f"[brats] extracted {len(records)} tumor-bearing axial slices from {len(df)} patients")

    rng = np.random.RandomState(SEED)
    for name, pts in split.items():
        sel = [r for r in records if r[0] in pts]
        rec = list(sel)
        if name == "train" and len(rec) > 900:   # CPU budget cap, deterministic
            rec = rng.choice(len(sel), size=900, replace=False)
            rec = np.sort(rec)
            rec = [sel[int(i)] for i in rec]
        arr_img = np.stack([r[2] for r in rec], 0)
        arr_seg = np.stack([r[3] for r in rec], 0)
        np.save(os.path.join(CACHE, f"x_{name}.npy"), arr_img.astype(np.float32))
        np.save(os.path.join(CACHE, f"y_{name}.npy"), arr_seg.astype(np.uint8))
        with open(os.path.join(CACHE, f"meta_{name}.txt"), "w") as f:
            for pi, z, *_ in rec:
                f.write(f"case{pi}_{z}\n")
        counts = {"wt": int((arr_seg > 0).sum()), "tc": int(np.isin(arr_seg, [1, 3]).sum()),
                  "et": int((arr_seg == 3).sum())}
        print(f"[brats] {name:5s} slices={len(rec):3d} fg-voxels={counts}")

    summary = {
        "source_parquet": args.parquet,
        "n_cases": 10, "shape": [240, 240, 155],
        "modalities": "single (mini provides one sequence)",
        "full_brats2021_cases": 1251,
        "split_cases": {k: v for k, v in split.items()},
        "slice_size": SIZE,
        "regions": {"WT": "1|2|4", "TC": "1|4", "ET": "4"},
    }
    with open(os.path.join(CACHE, "summary.json"), "w") as f:
        json.dump(summary, f, indent=2, default=str)
    print("[brats] done.")


def zoom_factor(shape, target):
    return (target / shape[0], target / shape[0])


if __name__ == "__main__":
    main()