"""Prepare CelebA (Smiling / Blond) and Camelyon17 splits.

Follows the paper's experimental design (Sec. 3.1):
  * Binary tasks, 4 groups (t in {0,1}, q in {0,1}).
  * Train = 800, Val = 200 with symmetric or asymmetric poisoning.
  * Test sets are balanced (except CelebA Blond which keeps a natural-ish
    minority; the paper uses 20260 test images).

Data sources (frozen, in-place):
  * Full CelebA:  img_align_celeba + list_attr_celeba.txt + partition file.
  * Full Camelyon17: metadata.csv + patches (centers 0 and 1 only).

CelebA Smiling confounder is a synthetic watermark whose opacity is set per
group (q=0 -> transparent [0,0.5), q=1 -> opaque [0.5,1)).
CelebA Blond confounder is the real Male attribute.
Camelyon17 confounder is the hospital (center).
"""
import json
import os
import numpy as np
import pandas as pd
from PIL import Image

from config import (
    DATA_ROOT_E, FULL_CELEBA_IMG, FULL_CELEBA_ATTR, FULL_CELEBA_PARTITION,
    FULL_CAMELYON_META, FULL_CAMELYON_PATCHES, TRAIN_N, VAL_N, SEED,
    group_sizes, WORKSPACE,
)

IMG_SIZE = 64


# ---------------------------------------------------------------------------
# CelebA helpers
# ---------------------------------------------------------------------------
def load_celeba_attributes():
    """Return dict: image_id -> {attr: +/-1} and list of attribute names."""
    lines = open(FULL_CELEBA_ATTR).read().splitlines()
    attrs = lines[1].split()
    data = {}
    for ln in lines[2:]:
        parts = ln.split()
        data[parts[0]] = dict(zip(attrs, [int(x) for x in parts[1:]]))
    return data, attrs


def load_celeba_partition():
    """Return dict image_id -> partition (0 train, 1 val, 2 test)."""
    part = {}
    for ln in open(FULL_CELEBA_PARTITION).read().splitlines():
        k, p = ln.split()
        part[k] = int(p)
    return part


def pick_groups(attr_data, partition, target_attr, conf_attr=None,
                group_targets=None, poison=None, n_train=TRAIN_N, n_val=VAL_N,
                seed=SEED, exclude=None, train_partitions=(0, 1)):
    """Pick image ids for each group.

    group_targets: list of (t, q) per group index or None -> standard mapping.
    train_partitions: which CelebA partitions are allowed in train/val pools
        (default (0,1) = train+val partition; keeps test images out of
        training to avoid leakage).
    """
    rng = np.random.default_rng(seed)
    pool = {}
    for img_id, a in attr_data.items():
        if partition is not None and partition.get(img_id) not in train_partitions:
            continue
        t = 0 if a[target_attr] == -1 else 1
        if conf_attr is None:
            q = None
        else:
            q = 0 if a[conf_attr] == -1 else 1
        key = (t, q) if q is not None else (t,)
        pool.setdefault(key, []).append(img_id)
    # remove excluded images (used elsewhere)
    if exclude:
        for k in pool:
            pool[k] = [i for i in pool[k] if i not in exclude]

    sizes_train = group_sizes(n_train, poison)
    sizes_val = group_sizes(n_val, poison)
    chosen = {"train": [], "val": [], "test": []}
    group_idx = 0
    for g in range(4):
        t = 0 if g < 2 else 1
        q = g % 2
        key = (t, q) if conf_attr is not None else (t,)
        candidates = pool[key]
        rng.shuffle(candidates)
        need_train = int(sizes_train[g])
        need_val = int(sizes_val[g])
        chosen["train"] += [(i, t, q) for i in candidates[:need_train]]
        chosen["val"] += [(i, t, q) for i in candidates[need_train:need_train + need_val]]
        chosen["test"] += [(i, t, q) for i in candidates[need_train + need_val:]]
    return chosen


def apply_watermark(img, opacity, box_frac=0.22):
    """Apply a semi-transparent dark rectangle (watermark) bottom-right.

    img: float array in [0,1] of shape [H,W,3] or [H,W].
    opacity: in [0,1].
    """
    h, w = img.shape[:2]
    bw, bh = int(w * box_frac), int(h * box_frac)
    if img.ndim == 2:
        img = np.stack([img] * 3, axis=-1)
    out = img.copy()
    y0, x0 = h - bh, w - bw
    # dark gray watermark
    wm = np.full((bh, bw, 3), 0.2)
    out[y0:, x0:] = (1 - opacity) * out[y0:, x0:] + opacity * wm
    return out


def load_celeba_img(img_id, size=IMG_SIZE):
    path = os.path.join(FULL_CELEBA_IMG, img_id)
    img = Image.open(path).convert("RGB")
    img = img.resize((size, size), Image.BILINEAR)
    return np.asarray(img, dtype=np.float32) / 255.0


# ---------------------------------------------------------------------------
# Camelyon17 helpers
# ---------------------------------------------------------------------------
def camelyon_patch_path(row):
    p = int(row["patient"])
    n = int(row["node"])
    return os.path.join(
        FULL_CAMELYON_PATCHES,
        f"patient_{p:03d}_node_{n}",
        f"patch_patient_{p:03d}_node_{n}_"
        f"x_{int(row['x_coord'])}_y_{int(row['y_coord'])}.png",
    )


def load_camelyon_patch(path, size=IMG_SIZE):
    img = Image.open(path).convert("RGB")
    img = img.resize((size, size), Image.BILINEAR)
    return np.asarray(img, dtype=np.float32) / 255.0


def prepare_camelyon_splits(poison, out_dir, seed=SEED,
                            n_train=TRAIN_N, n_val=VAL_N, n_test=6800):
    meta = pd.read_csv(FULL_CAMELYON_META)
    # use only centers 0 and 1
    meta = meta[meta["center"].isin([0, 1])].copy()
    # q = 0 for center 0, q = 1 for center 1; target = tumor
    meta["target"] = meta["tumor"].values
    meta["conf"] = meta["center"].values
    meta["group"] = meta["target"] * 2 + meta["conf"]

    rng = np.random.default_rng(seed)
    # split per group
    pools = {g: meta[meta["group"] == g].index.values for g in range(4)}
    sizes_train = group_sizes(n_train, poison)
    sizes_val = group_sizes(n_val, poison)
    # test: balanced
    per_group_test = n_test // 4
    selected_train, selected_val, selected_test = [], [], []
    for g in range(4):
        idx = pools[g].copy()
        rng.shuffle(idx)
        nt, nv = int(sizes_train[g]), int(sizes_val[g])
        selected_train += list(idx[:nt])
        selected_val += list(idx[nt:nt + nv])
        selected_test += list(idx[nt + nv:nt + nv + per_group_test])
    splits = {"train": selected_train, "val": selected_val, "test": selected_test}
    os.makedirs(out_dir, exist_ok=True)
    manifests = {}
    for split_name, idx in splits.items():
        sub = meta.loc[idx]
        records = []
        for _, row in sub.iterrows():
            records.append({
                "path": camelyon_patch_path(row),
                "target": int(row["target"]),
                "conf": int(row["conf"]),
                "group": int(row["group"]),
            })
        manifests[split_name] = records
        json.dump(records, open(os.path.join(out_dir, f"{split_name}.json"), "w"))
        g = np.array([r["group"] for r in records])
        print(f"[camelyon17-{poison}] {split_name}: n={len(records)} groups={np.bincount(g)}")
    return manifests


# ---------------------------------------------------------------------------
# CelebA top-level
# ---------------------------------------------------------------------------
def prepare_celeba_smiling(poison, out_dir, seed=SEED, n_test_per_group=4850):
    """CelebA Smiling: watermark-opacity confounder (synthetic)."""
    attr_data, _ = load_celeba_attributes()
    partition = load_celeba_partition()
    rng = np.random.default_rng(seed)
    picked = pick_groups(attr_data, partition, target_attr="Smiling", poison=poison,
                         seed=seed, train_partitions=(0, 1))
    os.makedirs(out_dir, exist_ok=True)
    manifests = {}
    for split_name in ["train", "val"]:
        records = []
        for img_id, t, q in picked[split_name]:
            opacity = rng.uniform(0.0, 0.5) if q == 0 else rng.uniform(0.5, 1.0)
            records.append({"id": img_id, "target": t, "conf": q, "group": t * 2 + q,
                            "opacity": float(opacity)})
        manifests[split_name] = records
        json.dump(records, open(os.path.join(out_dir, f"{split_name}.json"), "w"))
        g = np.array([r["group"] for r in records])
        print(f"[smiling-{poison}] {split_name}: n={len(records)} groups={np.bincount(g)}")
    # test: balanced from the test-partition pool; q assigned by opacity
    test_pool = {}
    for img_id, a in attr_data.items():
        if partition.get(img_id) != 2:
            continue
        t = 0 if a["Smiling"] == -1 else 1
        test_pool.setdefault(t, []).append(img_id)
    records = []
    for g in range(4):
        t = 0 if g < 2 else 1
        q = g % 2
        cands = test_pool[t]
        rng.shuffle(cands)
        for img_id in cands[:n_test_per_group]:
            opacity = rng.uniform(0.0, 0.5) if q == 0 else rng.uniform(0.5, 1.0)
            records.append({"id": img_id, "target": t, "conf": q, "group": g,
                            "opacity": float(opacity)})
    manifests["test"] = records
    json.dump(records, open(os.path.join(out_dir, "test.json"), "w"))
    g = np.array([r["group"] for r in records])
    print(f"[smiling-{poison}] test: n={len(records)} groups={np.bincount(g)}")
    return manifests


def prepare_celeba_blond(poison, out_dir, seed=SEED, n_test=20260):
    """CelebA Blond: gender (Male) confounder (real attribute)."""
    attr_data, _ = load_celeba_attributes()
    partition = load_celeba_partition()
    rng = np.random.default_rng(seed)
    picked = pick_groups(attr_data, partition, target_attr="Blond_Hair",
                         conf_attr="Male", poison=poison, seed=seed,
                         train_partitions=(0, 1))
    os.makedirs(out_dir, exist_ok=True)
    manifests = {}
    for split_name in ["train", "val"]:
        records = [{"id": i, "target": t, "conf": q, "group": t * 2 + q}
                   for i, t, q in picked[split_name]]
        manifests[split_name] = records
        json.dump(records, open(os.path.join(out_dir, f"{split_name}.json"), "w"))
        g = np.array([r["group"] for r in records])
        print(f"[blond-{poison}] {split_name}: n={len(records)} groups={np.bincount(g)}")
    # test: use partition-test images not used in train/val
    used = set(i for s in ["train", "val"] for i, _, _ in picked[s])
    pool = {}
    for img_id, a in attr_data.items():
        if partition.get(img_id) != 2 or img_id in used:
            continue
        t = 0 if a["Blond_Hair"] == -1 else 1
        q = 0 if a["Male"] == -1 else 1
        pool.setdefault(t * 2 + q, []).append(img_id)
    # mimic natural-ish distribution: sample n_test from the pool
    # (minority group will be naturally small)
    total_pool = sum(len(v) for v in pool.values())
    frac = n_test / total_pool
    records = []
    for g in range(4):
        cands = pool[g]
        rng.shuffle(cands)
        k = max(1, int(len(cands) * frac))
        for img_id in cands[:k]:
            t, q = divmod(g, 2)
            records.append({"id": img_id, "target": t, "conf": q, "group": g})
    manifests["test"] = records
    json.dump(records, open(os.path.join(out_dir, "test.json"), "w"))
    g = np.array([r["group"] for r in records])
    print(f"[blond-{poison}] test: n={len(records)} groups={np.bincount(g)}")
    return manifests


if __name__ == "__main__":
    base = os.path.join(WORKSPACE, "real")
    prepare_celeba_smiling("symmetric", os.path.join(base, "smiling_symmetric"))
    prepare_celeba_smiling("asymmetric", os.path.join(base, "smiling_asymmetric"))
    prepare_celeba_blond("symmetric", os.path.join(base, "blond_symmetric"))
    prepare_celeba_blond("asymmetric", os.path.join(base, "blond_asymmetric"))
    prepare_camelyon_splits("symmetric", os.path.join(base, "camelyon_symmetric"))
    prepare_camelyon_splits("asymmetric", os.path.join(base, "camelyon_asymmetric"))
    print("done")
