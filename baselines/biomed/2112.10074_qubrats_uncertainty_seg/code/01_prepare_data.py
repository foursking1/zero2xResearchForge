"""Parse frozen BraTS2021 mini parquet -> per-case NIFTI arrays + derived masks + train/test split.

Outputs (all saved under DATA_CACHE defined below):
  data_cache/raw/<case_id>.npz        : image (FLAIR z-scored within brain), brain, label
  data_cache/raw_meta.json            : per-case stats (shapes, ranges, label counts, brain bbox)
  data_cache/split.json               : fixed patient-level split (train/val/test case ids)
  data_cache/2d/<split>.npz           : 2D axial slices for training (x: Nx160x160x1, y: Nx160x160x3)
Usage:
  python 01_prepare_data.py --data <path to brats2021_mini.parquet> [--seed 0]
"""
import argparse
import gzip
import io
import json
import os
import tempfile

import numpy as np
import nibabel as nib
import pandas as pd

from scipy.ndimage import zoom


def load_nii_from_bytes(b):
    tmp = tempfile.NamedTemporaryFile(suffix=".nii", delete=False)
    try:
        tmp.write(gzip.decompress(b))
        tmp.flush()
        return nib.load(tmp.name).get_fdata()
    finally:
        tmp.close()
        os.unlink(tmp.name)


def parse_case_id(img_bytes):
    try:
        hdr = img_bytes[:10]
        flags = hdr[3]
        if flags & 0x08:  # FNAME flag
            idx = 10
            return img_bytes[idx:img_bytes.index(b"\x00", idx)].decode()
    except Exception:
        pass
    return "unknown"


def prepare(data_path, cache_dir, seed=0):
    df = pd.read_parquet(data_path)
    assert len(df) == 10, f"expected 10 rows, got {len(df)}"

    os.makedirs(os.path.join(cache_dir, "raw"), exist_ok=True)
    os.makedirs(os.path.join(cache_dir, "2d"), exist_ok=True)

    meta = {}
    case_ids = []
    cases = []
    for i, row in df.iterrows():
        cid = parse_case_id(row["image"]["bytes"]).replace("_brain_flair.nii", "")
        case_ids.append(cid)
        img = load_nii_from_bytes(row["image"]["bytes"])
        seg = load_nii_from_bytes(row["annotations"]["bytes"])

        img = np.asarray(img).astype(np.float32)
        seg = np.asarray(seg).astype(np.int16)
        brain = (img > 0).astype(np.uint8)

        # per-case z-score within brain
        brain_vox = img[brain == 1]
        mu, sd = brain_vox.mean(), brain_vox.std() + 1e-6
        img_norm = (img - mu) / sd
        img_norm[brain == 0] = 0.0

        wt = (seg > 0).astype(np.uint8)
        tc = np.isin(seg, (1, 4)).astype(np.uint8)
        et = (seg == 4).astype(np.uint8)
        entities = np.stack([et, tc, wt], axis=0).astype(np.uint8)  # 3xHxWxD

        # brain bbox (in-plane, axial)
        bm_vol = brain  # HxWxD
        z = np.any(bm_vol, axis=(0, 1))
        y = np.any(bm_vol, axis=(0, 2))
        x = np.any(bm_vol, axis=(1, 2))
        z0, z1 = np.where(z)[0][[0, -1]] if z.any() else (0, 0)
        y0, y1 = np.where(y)[0][[0, -1]] if y.any() else (0, 0)
        x0, x1 = np.where(x)[0][[0, -1]] if x.any() else (0, 0)

        meta[cid] = {
            "shape": list(img.shape),
            "dtype_img": row["image"]["bytes"][:4].hex(),
            "img_min": float(img.min()),
            "img_max": float(img.max()),
            "label_vals": [int(v) for v in sorted(np.unique(seg))],
            "label_counts": {str(v): int((seg == v).sum()) for v in np.unique(seg)},
            "brain_bbox_axial": [int(x0), int(x1), int(y0), int(y1), int(z0), int(z1)],
            "n_wt": int(wt.sum()),
            "n_tc": int(tc.sum()),
            "n_et": int(et.sum()),
        }

        np.savez_compressed(
            os.path.join(cache_dir, "raw", f"{cid}.npz"),
            image=img_norm.astype(np.float32),
            brain=brain.astype(np.uint8),
            seg=seg.astype(np.int16),
            entities=entities,
        )
        cases.append((cid, img_norm, brain, seg, entities))
        print(f"[{cid}] img={img.shape} labels={meta[cid]['label_vals']} "
              f"counts={meta[cid]['label_counts']} bbox={meta[cid]['brain_bbox_axial']}")

    # ---- fixed split (patient-level) ----
    rng = np.random.default_rng(seed)
    idx = rng.permutation(len(case_ids))
    n_test, n_val = 3, 1
    test_ids = [case_ids[i] for i in idx[:n_test]]
    val_ids = [case_ids[i] for i in idx[n_test:n_test + n_val]]
    train_ids = [case_ids[i] for i in idx[n_test + n_val:]]
    split = {"train": train_ids, "val": val_ids, "test": test_ids,
             "seed": seed, "n_total": len(case_ids)}
    with open(os.path.join(cache_dir, "split.json"), "w") as f:
        json.dump(split, f, indent=2, default=str)
    print("split:", {k: (v if isinstance(v, list) else v) for k, v in split.items()})

    with open(os.path.join(cache_dir, "raw_meta.json"), "w") as f:
        json.dump(meta, f, indent=2)

    # ---- build 2D slices (axial) ----
    # per-case in-plane crop window centered at brain centroid, size W=160
    W = 160
    out = {}
    crop_params = {}
    for cid, img, brain, seg, entities in cases:
        H, Wd, D = img.shape
        cy, cx = np.array(np.where(brain.mean(axis=2) > 0)).mean(axis=1).astype(int)
        y0 = min(max(int(cy - W // 2), 0), H - W)
        y1 = y0 + W
        x0 = min(max(int(cx - W // 2), 0), Wd - W)
        x1 = x0 + W
        crop_params[cid] = ([int(y0), int(y1), int(x0), int(x1)])
        sl_img = img[y0:y1, x0:x1]                       # W x W x D
        sl_ent = entities[:, y0:y1, x0:x1]                # 3 x W x W x D
        # transpose to axial slices: (D, W, W)
        im_slices = np.transpose(sl_img, (2, 0, 1))[:, :, :, None].astype(np.float32)
        ent_slices = np.transpose(sl_ent, (0, 3, 1, 2))  # 3 x D x W x W
        ent_slices = np.moveaxis(ent_slices, 0, -3)       # D x 3 x W x W
        keep = im_slices[..., 0].max(axis=(1, 2)) > 0.05  # slices with content
        out[cid] = {"x": im_slices[keep], "y": ent_slices[keep]}
        print(f"[{cid}] kept {out[cid]['x'].shape[0]}/{D} slices")

    for spl in ["train", "val", "test"]:
        xs = [out[c]["x"] for c in split[spl]]
        ys = [out[c]["y"] for c in split[spl]]
        X = np.concatenate(xs, axis=0)
        Y = np.concatenate(ys, axis=0)
        np.savez_compressed(
            os.path.join(cache_dir, "2d", f"{spl}.npz"),
            x=X.astype(np.float32), y=Y.astype(np.uint8),
            case_ids=np.array(split[spl]),
        )
        print(f"split {spl}: X={X.shape} Y={Y.shape}")

    # dump a small summary
    with open(os.path.join(cache_dir, "crop_params.json"), "w") as f:
        json.dump(crop_params, f, indent=2)
    with open(os.path.join(cache_dir, "dataset_stats.json"), "w") as f:
        json.dump({
            "n_cases": len(case_ids),
            "case_ids": case_ids,
            "shape": list(img.shape),
            "per_case_voxels": int(img.shape[0] * img.shape[1] * img.shape[2]),
            "total_wt_voxels": sum(m["n_wt"] for m in meta.values()),
            "split": split,
        }, f, indent=2, default=str)

    print("done. cache dir:", cache_dir)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=None)
    ap.add_argument("--cache", default=os.path.join(os.path.dirname(__file__), "..", "data_cache"))
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    if args.data is None:
        args.data = os.path.join(os.path.dirname(__file__), "..", "..", "data", "brats2021_mini.parquet")
    prepare(args.data, args.cache, args.seed)