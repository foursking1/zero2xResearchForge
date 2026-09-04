"""Pre-render real-dataset splits into in-memory tensor files.

Reads the JSON manifests produced by prep_real_data.py and converts them into
.pt files with keys: images [N,3,H,W] float32 in [0,1], targets, groups, confs.
For CelebA Smiling the synthetic watermark is applied at load time using the
opacity recorded in the manifest (matches the paper's confounder definition:
opacity < 0.5 -> q=0, opacity >= 0.5 -> q=1).

Usage:
    python build_tensors.py <dataset_key> <poison>
    e.g. python build_tensors.py smiling symmetric
    dataset_key in {smiling, blond, camelyon}
"""
import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import torch
from PIL import Image

from config import WORKSPACE, FULL_CELEBA_IMG, FULL_CAMELYON_PATCHES
from prep_real_data import apply_watermark

IMG_SIZE = int(os.environ.get("IMG_SIZE", "128"))
BUILD_WORKERS = int(os.environ.get("BUILD_WORKERS", "6"))
REAL_ROOT = os.path.join(WORKSPACE, "real")


def _load_celeba(img_id, opacity=None):
    img = Image.open(os.path.join(FULL_CELEBA_IMG, img_id)).convert("RGB")
    img = img.resize((IMG_SIZE, IMG_SIZE), Image.BILINEAR)
    arr = np.asarray(img, dtype=np.float32) / 255.0
    if opacity is not None:
        arr = apply_watermark(arr, opacity)
    return arr


def _load_camelyon(rel_path):
    img = Image.open(rel_path).convert("RGB")
    img = img.resize((IMG_SIZE, IMG_SIZE), Image.BILINEAR)
    return np.asarray(img, dtype=np.float32) / 255.0


def _worker(args):
    kind, rec = args
    if kind == "camelyon":
        return _load_camelyon(rec["path"])
    return _load_celeba(rec["id"], rec.get("opacity"))


def build(kind, poison):
    src_dir = os.path.join(REAL_ROOT, f"{kind}_{poison}")
    out_root = os.path.join(WORKSPACE, "real_tensors", f"{kind}_{poison}")
    os.makedirs(out_root, exist_ok=True)
    for split in ["train", "val", "test"]:
        recs = json.load(open(os.path.join(src_dir, f"{split}.json")))
        args = [(kind, r) for r in recs]
        imgs = []
        with ProcessPoolExecutor(max_workers=BUILD_WORKERS) as ex:
            for arr in ex.map(_worker, args, chunksize=64):
                imgs.append(arr)
        images = np.stack(imgs)                      # [N,128,128,3]
        images = torch.from_numpy(images.transpose(0, 3, 1, 2)).float()
        targets = torch.tensor([r["target"] for r in recs], dtype=torch.long)
        groups = torch.tensor([r["group"] for r in recs], dtype=torch.long)
        confs = torch.tensor([r["conf"] for r in recs], dtype=torch.long)
        torch.save({"images": images, "targets": targets, "groups": groups,
                    "confs": confs}, os.path.join(out_root, f"{split}.pt"))
        print(f"[{kind}-{poison}] {split}: n={len(recs)} "
              f"groups={np.bincount(groups.numpy()).tolist()} "
              f"mem={images.numel()*4/1e9:.2f}GB", flush=True)


if __name__ == "__main__":
    kind = sys.argv[1]
    poison = sys.argv[2]
    build(kind, poison)
    print("done", kind, poison)
