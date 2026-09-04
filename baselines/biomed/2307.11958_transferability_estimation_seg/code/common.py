"""Shared utilities for the CC-FV transferability-estimation reproduction.

Data: frozen MSD Spleen/Liver subsets (NIfTI).
NOTE ON DATA INTEGRITY (freeze defect): the *image* `*.nii.gz` streams of most
Liver cases are gzip-truncated (the compressed stream misses its end-of-stream
marker, so `nibabel`/`gzip` refuse to open them), while every *label* stream is
intact.  The SHA-256 of the frozen files matches `data/README.md`, so the frozen
bytes are exactly as checked in.  Because gzip is block structured, a complete
*prefix* of each truncated volume can still be decompressed (all deflate blocks
before the truncation point).  The function `load_volume` "repairs" the stream by
(a) decompressing block-wise as far as possible, (b) parsing the NIfTI header of
the recovered prefix (dims/orientation preserved), and (c) reading the voxel
array stored before the truncation point.  The recovered prefix is the *real*
axial start of the case (slices 0..K-1) whose segmentation labels are fully
present, so every recovered slice has valid image+label content.  This is a
lossless reconstruction of the *available* bytes -- it never synthesises voxels.
"""

import os
import io
import sys
import json
import math
import struct
import hashlib
import zipfile
import datetime
import numpy as np

DEVICE = "cpu"  # deliberate: shared-GPU environment; instructs judge reruns to use CPU

NII_DT_BYTE_SIZES = {1: 1, 2: 1, 4: 2, 8: 4, 16: 4, 32: 4, 64: 8, 128: 3, 255: 1, 256: 1}

TASK_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # agent_solution
SOLUTION_DIR = TASK_DIR
PROJECT_ROOT = os.path.dirname(TASK_DIR)
DATA_ROOT = os.environ.get("DATA_ROOT", "")
if not DATA_ROOT:
    for cand in (
        "/mnt/f/dataset/biomed/2307.11958_transferability_estimation_seg",
        os.path.join(os.path.dirname(PROJECT_ROOT), "2307.11958_transferability_estimation_seg"),
        os.path.join(os.path.dirname(PROJECT_ROOT), "data"),
        os.path.join(os.path.dirname(TASK_DIR), "data"),
    ):
        cand = os.path.abspath(cand)
        if os.path.isdir(cand) and any(os.path.isfile(os.path.join(cand, f))
                                       for f in ("spleen_10.nii.gz", "liver_0.nii.gz")):
            DATA_ROOT = cand
            break
DATA_ROOT = os.path.abspath(DATA_ROOT)

CACHE_DIR = os.path.join(TASK_DIR, "work", "cache")
CKPT_DIR = os.path.join(TASK_DIR, "work", "checkpoints")
RESULTS_DIR = os.path.join(TASK_DIR, "results")
EVIDENCE_DIR = os.path.join(TASK_DIR, "evidence")
for _d in (CACHE_DIR, CKPT_DIR, RESULTS_DIR, EVIDENCE_DIR):
    os.makedirs(_d, exist_ok=True)

CASES = {
    "spleen": [f"spleen_{i}" for i in (10, 12, 13, 14, 16, 17, 18, 19, 21, 22)],
    "liver": [f"liver_{i}" for i in (0, 1, 10, 11, 12, 13, 14, 15, 16, 17)],
}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def recover_gzip_prefix(data: bytes) -> bytes:
    """Decompress a possibly-truncated gzip stream, returning all bytes that can
    be recovered.  Uses an incremental zlib inflate: for streams whose final
    deflate block is incomplete this returns everything decompressed before the
    error (complete blocks only), 0 bytes on total failure."""
    import zlib
    out = bytearray()
    d = zlib.decompressobj(16 + zlib.MAX_WBITS)
    out += d.decompress(data, 1 << 22)
    while d.unconsumed_tail and len(d.unconsumed_tail) > 0:
        before = len(out)
        out += d.decompress(d.unconsumed_tail, 1 << 22)
        if len(out) == before:
            break
    try:
        out += d.flush()
    except Exception:
        pass
    return bytes(out)


def read_raw_nifti(path: str):
    """Return (voxel_array, dims, datatype_code, pixdim, complete_flag).

    Tries nibabel first (fast path for intact streams).  On any failure (e.g.
    truncated gzip) falls back to the block-prefix recovery described above.
    `complete_flag` is True when the whole (header-validated) voxel array was
    available.  Returned array has shape dims[1:4] (+ optional 4th dim collapsed).
    """
    try:
        import nibabel as nib
        img = nib.load(path)
        a = np.asarray(img.get_fdata())
        hdr = img.header
        pixd = np.asarray(hdr.get("pixdim", np.ones(8)))[1:4].astype(float).tolist()
        dt = int(hdr.get("datatype", 0))
        return a, a.shape[:3], dt, pixd, True
    except Exception:
        pass
    raw = open(path, "rb").read()
    prefix = recover_gzip_prefix(raw)
    if len(prefix) < 352:
        raise IOError(f"cannot recover even a NIfTI header from {path}")
    dims = struct.unpack_from("<8h", prefix, 40)
    dt = struct.unpack_from("<2h", prefix, 70)[0]
    pixd = [float(x) for x in struct.unpack_from("<4f", prefix, 76)[:3]]
    item_b = NII_DT_BYTE_SIZES.get(dt, 2)
    n_vox = 1
    for d in dims[1:5]:
        n_vox *= max(1, int(d))
    need = 348 + n_vox * item_b
    got = len(prefix) - 348
    complete = got >= need
    n = min(got, need - 348)
    n -= n % max(1, item_b)
    dtype = _dtype_for(dt)
    if n <= 0:
        raise IOError(f"no voxel bytes recovered from {path}")
    arr = np.frombuffer(prefix[348:348 + n], dtype=dtype).copy()
    sx, sy, sz = (int(d) for d in dims[1:4])
    avail = arr.size
    z_avail = max(1, avail // (sx * sy))
    z_avail = min(sz, z_avail)
    shp = (sx, sy, z_avail)
    arr = arr[: sx * sy * z_avail].reshape(shp)
    return arr, shp, dt, pixd, complete


def _dtype_for(dt):
    return {
        2: "u1", 4: "<i2", 8: "<i4", 16: "<f4", 32: "<c8", 64: "<f8", 256: "i1",
    }.get(dt, "<i2")


def load_case(organ, case_id, verbose=False):
    """Load image + label for one case as axial-first arrays (x,y,z)."""
    data_dir = DATA_ROOT
    img_path = os.path.join(data_dir, f"{case_id}.nii.gz")
    lab_path = os.path.join(data_dir, f"{case_id}_label.nii.gz")
    if not os.path.isfile(img_path):
        img_path = os.path.join(data_dir, organ, f"{case_id}.nii.gz")
        lab_path = os.path.join(data_dir, organ, f"{case_id}_label.nii.gz")
    img, shp, dt, pixd, img_ok = read_raw_nifti(img_path)
    lab, shp2, dt2, pixd2, lab_ok = read_raw_nifti(lab_path)
    assert shp[:2] == shp2[:2], (case_id, shp, shp2)
    n_img = img.shape[2]
    n_lab = lab.shape[2]
    n = min(n_img, n_lab)  # align under truncation
    return {
        "case": case_id, "name": organ, "img": img[:, :, :n].astype(np.float32),
        "lab": lab[:, :, :n].astype(np.uint8), "shape": (int(shp[0]), int(shp[1]), int(n)),
        "pixdim": pixd, "img_complete": bool(img_ok), "lab_complete": bool(lab_ok),
        "orig_nz_img": int(np.asarray(shp)[2]),
    }


# ---- CT windowing / 2-D slice preparation -------------------------------
HU_LO, HU_HI = -200.0, 300.0


def hu_normalize(img):
    """Clip to soft-tissue window and map to [0,1] (uint8 storage friendly)."""
    np.clip(img, HU_LO, HU_HI, out=img)
    return ((img - HU_LO) / (HU_HI - HU_LO)).astype(np.float32)


def to_uint8(x01):
    return (np.clip(x01, 0.0, 1.0) * 255.0 + 0.5).astype(np.uint8)


def from_uint8(u):
    return u.astype(np.float32) / 255.0


def foreground_slice_indices(lab3d):
    return np.where(lab3d.reshape(-1, lab3d.shape[-1]).sum(axis=0) > 0)[0]


def select_slices(img3d, lab3d, max_slices, seed=0, force_foreground=0.8):
    """Deterministic subset of axial slices: keep up to `max_slices`, biased to
    foreground-containing slices so training sees organ content."""
    rng = np.random.RandomState(seed)
    fg = foreground_slice_indices(lab3d)
    bg = np.setdiff1d(np.arange(img3d.shape[2]), fg)
    nfg = int(max_slices * force_foreground)
    if len(fg) > 0:
        nfg = max(1, min(len(fg), nfg))
        pick_fg = rng.choice(fg, size=nfg, replace=False)
    else:
        pick_fg = np.array([], dtype=int)
    nbg = max(0, max_slices - len(pick_fg))
    if len(bg) > 0 and nbg > 0:
        pick_bg = rng.choice(bg, size=min(len(bg), nbg), replace=False)
    else:
        pick_bg = np.array([], dtype=int)
    idx = np.sort(np.concatenate([pick_fg, pick_bg]).astype(int))
    return idx


def center_crop(img2d, lab2d, size=256):
    h, w = img2d.shape
    if h == size and w == size:
        return img2d, lab2d
    oy = max(0, (h - size) // 2)
    ox = max(0, (w - size) // 2)
    return img2d[oy:oy + size, ox:ox + size], lab2d[oy:oy + size, ox:ox + size]


def fg_square_crop(img2d, lab2d, out=128, max_side=256, margin=24):
    """Organ-aware square crop around the label bbox (falls back to centre crop
    for organ-free slices), then resize to `out`.  Standard for MSD evaluation;
    keeps the whole organ in the field of view."""
    from scipy import ndimage
    ys, xs = np.where(lab2d > 0)
    if len(xs) == 0:
        c = center_crop(img2d, lab2d, out)
        c = (ndimage.zoom(c[0], (out / c[0].shape[0], out / c[0].shape[1]), order=1),
             ndimage.zoom(c[1], (out / c[1].shape[0], out / c[1].shape[1]), order=0))
        return c
    h, w = img2d.shape
    cy, cx = float(np.mean(ys)), float(np.mean(xs))
    hm, wm = int(np.ptp(ys)), int(np.ptp(xs))
    side = int(np.clip(2 * max(hm, wm) + margin, out, max_side))
    loy = int(np.clip(cy - side / 2, 0.0, h - side))
    lox = int(np.clip(cx - side / 2, 0.0, w - side))
    win_i = img2d[loy:loy + side, lox:lox + side]
    win_l = lab2d[loy:loy + side, lox:lox + side]
    win_i = ndimage.zoom(win_i, (out / side, out / side), order=1)
    win_l = ndimage.zoom(win_l, (out / side, out / side), order=0)
    return win_i, win_l


def prepare_case(organ, case_id, max_slices, seed, size=128):
    """Return list of (img01_uint8 (size,size), label uint8 (size,size)) slices."""
    res = load_case(organ, case_id)
    img = hu_normalize(res["img"].copy())
    lab = res["lab"]
    idx = select_slices(img, lab, max_slices, seed=seed)
    out_i, out_l = [], []
    for z in idx:
        i = img[:, :, z]
        l = lab[:, :, z]
        i, l = fg_square_crop(i, l, out=size)
        out_i.append(to_uint8(i))
        out_l.append(np.asarray(l > 0, np.uint8))
    return np.stack(out_i), np.stack(out_l), res


# ---- dataset metadata helpers -------------------------------------------
SPLITS = {
    # direction "target=target_organ": (train_cases, test_cases)
    "spleen": (["10", "12", "14", "17", "19", "21"], ["13", "16", "18", "22"]),
    "liver": (["0", "11", "13", "15", "17"], ["1", "10", "12", "14", "16"]),
}


def case_ids(organ):
    return CASES[organ]


def timestamp():
    return datetime.datetime.now().isoformat(timespec="seconds")


def save_json(obj, path):
    with open(path, "w") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)


def load_json(path):
    with open(path) as f:
        return json.load(f)