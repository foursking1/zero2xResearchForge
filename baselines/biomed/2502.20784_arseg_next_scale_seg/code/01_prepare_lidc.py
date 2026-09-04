#!/usr/bin/env python3
"""Prepare the frozen LIDC-IDRI nodule-patch dataset for the 2D binary segmentation task.

WHAT THE DATA IS
----------------
`lidc_train.parquet` (HF mirror `ykeselman/lidc-idri-patches`, train split) contains
40,187 nodule patches from 875 patients / 2,651 nodule clusters.  Each row has a
64x64 (or 64x96..) uint16 CT patch (``image``), the enclosing nodule bounding box in
original-slice coordinates (xmin..ymax; bbox span == patch span) and metadata
(t_z, malignancy, patient/scan/cluster id, pixel spacing).

WHY A PSEUDO-MASK
-----------------
The frozen mirror stores patch-centred crops (bbox==patch extent), i.e. **no per-pixel
radiological segmentation labels** are present.  Per TASK.md direction 1 we therefore
derive a deterministic, intensity-based *pseudo-mask* that is generated **once, before
any model is trained**, using only the frozen data:

  1. decode uint16 CT patch, clip contrast to [0.1, 99.9] percentiles, normalise to [0,1];
  2. mildly smooth (Gaussian sigma=1.2);
  3. Otsu threshold (automatically separates lung background from dense nodule/soft
     tissue); take the largest connected component as the foreground pseudo-mask.

This is a documented approximation of the true nodule boundaries (which are not
available in the frozen mirror) and it is applied identically to baseline and AR-style
models so that the *relative* comparison A2 remains meaningful.

About the full LIDC-IDRI: the original dataset has 1,018 CT studies; the frozen mirror
has patches from 875 of them (reported in metrics.json as subset-coverage).
"""
from __future__ import annotations
import os, sys, io, time, argparse
import numpy as np
import pandas as pd
from PIL import Image
from scipy import ndimage
from skimage import filters as skf

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CACHE = os.path.join(ROOT, "results", "cache", "lidc")
os.makedirs(CACHE, exist_ok=True)

def _resolve_lidc_path():
    local = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         "..", "data", "lidc_train.parquet")
    if os.path.exists(local):
        return local
    fallback = "/mnt/f/dataset/biomed/2502.20784_arseg_next_scale_seg/lidc_train.parquet"
    return fallback if os.path.exists(fallback) else None


DEFAULT_PARQUET = _resolve_lidc_path()
SEED = 0
PSEUDO = dict(sigma=1.2, clip=(0.1, 99.9), min_fg_px=25)
PATCH_SIZE = 64   # canonical patch size (mirror has 64/96/128 variants -> resized here)


def make_pseudomask(v: np.ndarray) -> np.ndarray:
    """Deterministic Otsu + largest-component pseudo-mask (see module docstring)."""
    lo, hi = np.percentile(v, PSEUDO["clip"])
    if hi <= lo:
        return np.zeros_like(v, dtype=np.uint8)
    vv = np.clip(v, lo, hi)
    vs = ndimage.gaussian_filter(vv, sigma=PSEUDO["sigma"])
    thr = skf.threshold_otsu(vs)
    binary = vs > thr
    if binary.sum() == 0:
        return np.zeros_like(v, dtype=np.uint8)
    lab, n = ndimage.label(binary)
    if n == 1:
        m = binary.astype(np.uint8)
    else:
        sizes = ndimage.sum(binary, lab, range(1, n + 1))
        m = (lab == (np.argmax(sizes) + 1)).astype(np.uint8)
    if int(m.sum()) < PSEUDO["min_fg_px"]:
        return np.zeros_like(v, dtype=np.uint8)
    return m


def normalize(v: np.ndarray) -> np.ndarray:
    lo, hi = np.percentile(v, PSEUDO["clip"])
    v = np.clip(v, lo, hi).astype(np.float32)
    if hi > lo:
        v = (v - lo) / (hi - lo)
    return v.astype(np.float32)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--parquet", default=DEFAULT_PARQUET)
    ap.add_argument("--max_train_patches", type=int, default=12000,
                    help="deterministic per-cluster capped subsample for CPU budget")
    args = ap.parse_args()

    if not os.path.exists(args.parquet):
        sys.exit(f"frozen parquet not found: {args.parquet}  (see data/DATA_LOCATION.md)")

    cols = ["image", "patient_id", "scan_id", "cluster_id", "patch_id",
            "malignancy", "z", "xmin", "xmax", "ymin", "ymax", "pixel_spacing_mm"]
    df = pd.read_parquet(args.parquet, columns=cols)
    print(f"[lidc] rows={len(df)} patients={df.patient_id.nunique()} "
          f"clusters={df.cluster_id.nunique()} scans={df.scan_id.nunique()}")

    t0 = time.time()
    X, Y, M = [], [], []
    bad = 0
    for i in range(len(df)):
        raw = df.iloc[i]
        try:
            a = np.asarray(Image.open(io.BytesIO(raw["image"]["bytes"])), dtype=np.float32)
        except Exception:
            bad += 1
            continue
        if a.ndim != 2:
            bad += 1
            continue
        if a.shape[0] != PATCH_SIZE or a.shape[1] != PATCH_SIZE:
            a = ndimage.zoom(a, (PATCH_SIZE / a.shape[0], PATCH_SIZE / a.shape[1]), order=1)
        mask = make_pseudomask(a)
        if mask.shape[0] != PATCH_SIZE or mask.shape[1] != PATCH_SIZE:
            mask = (ndimage.zoom(mask.astype(np.float32),
                                 (PATCH_SIZE / mask.shape[0], PATCH_SIZE / mask.shape[1]), order=0) > 0.5)
        X.append(normalize(a))
        Y.append(mask.astype(np.uint8))
        M.append(raw)
    X = np.stack(X, 0)
    Y = np.stack(Y, 0)
    meta = pd.DataFrame(M).reset_index(drop=True)
    print(f"[lidc] decoded {len(X)} patches (bad={bad}) in {time.time()-t0:.1f}s; "
          f"mask foreground fraction mean={Y.mean():.4f} zero-mask frac={(Y.sum((1,2))==0).mean():.3f}")

    # ---- deterministic patient-level split 70/15/15 (no patient leakage) ----
    rng = np.random.RandomState(SEED)
    patients = np.sort(meta.patient_id.unique())
    perm = rng.permutation(len(patients))
    n1 = int(round(0.70 * len(patients)))
    n2 = int(round(0.15 * len(patients)))
    tr_pts = set(patients[perm[:n1]].tolist())
    va_pts = set(patients[perm[n1:n1 + n2]].tolist())
    te_pts = set(patients[perm[n1 + n2:]].tolist())
    assert len(tr_pts) + len(va_pts) + len(te_pts) == len(patients)

    parts = {"train": tr_pts, "val": va_pts, "test": te_pts}
    for name, pts in parts.items():
        idx = np.where(meta.patient_id.isin(pts))[0]
        if name == "train" and args.max_train_patches and len(idx) > args.max_train_patches:
            sub = np.random.RandomState(SEED).choice(idx, size=args.max_train_patches, replace=False)
            sub = np.sort(sub)
            idx = sub
        np.save(os.path.join(CACHE, f"x_{name}.npy"), X[idx].astype(np.float32))
        np.save(os.path.join(CACHE, f"y_{name}.npy"), Y[idx].astype(np.uint8))
        meta.iloc[idx].reset_index(drop=True).to_csv(os.path.join(CACHE, f"meta_{name}.csv"), index=False)
        fg = Y[idx].mean()
        nz = (Y[idx].sum((1, 2)) > 0).mean()
        print(f"[lidc] {name:5s} patients={len(pts):3d} patches={len(idx):5d} "
              f"mask-fg={fg:.4f} nonzero-mask={nz:.3f}")

    summary = {
        "source_parquet": args.parquet,
        "n_patches": int(len(df)),
        "n_patients": int(df.patient_id.nunique()),
        "n_clusters": int(df.cluster_id.nunique()),
        "n_scans": int(df.scan_id.nunique()),
        "full_lidc_cases_1o18": "frozen mirror covers 875 of the 1018 LIDC-IDRI subjects",
        "split_patients": {k: int(len(v)) for k, v in parts.items()},
        "pseudomask_pipeline": {
            "type": "Otsu + largest connected component",
            "sigma": PSEUDO["sigma"], "clip_percentiles": list(PSEUDO["clip"]),
            "min_fg_px": PSEUDO["min_fg_px"],
            "note": "frozen mirror stores nodule patches (bbox span==patch span); "
                    "no per-pixel labels, pseudo-mask is a documented proxy generated once.",
        },
    }
    import json
    with open(os.path.join(CACHE, "summary.json"), "w") as f:
        json.dump(summary, f, indent=2, default=str)
    print("[lidc] done.")


if __name__ == "__main__":
    main()