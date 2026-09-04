"""
Shared feature-extraction utilities for remote-sensing image classification tasks.
Uses ImageNet-pretrained torchvision ResNet backbones as frozen feature extractors.

Memory-efficient: images are decoded and processed in batches, never all held in RAM.
"""
import io
import os

import numpy as np
from PIL import Image

os.environ.setdefault("OMP_NUM_THREADS", "8")


def get_backbone(name="resnet18", device="cpu"):
    import torch
    import torchvision
    torch.set_num_threads(int(os.environ.get("OMP_NUM_THREADS", "8")))
    if name == "resnet18":
        m = torchvision.models.resnet18(
            weights=torchvision.models.ResNet18_Weights.IMAGENET1K_V1)
    elif name == "resnet34":
        m = torchvision.models.resnet34(
            weights=torchvision.models.ResNet34_Weights.IMAGENET1K_V1)
    elif name == "resnet50":
        m = torchvision.models.resnet50(
            weights=torchvision.models.ResNet50_Weights.IMAGENET1K_V1)
    elif name == "resnet101":
        m = torchvision.models.resnet101(
            weights=torchvision.models.ResNet101_Weights.IMAGENET1K_V1)
    else:
        raise ValueError(name)
    m.eval()
    m.to(device)
    feat_dim = m.fc.in_features
    m.fc = torch.nn.Identity()
    return m, feat_dim


def _count_path(cache_path):
    return cache_path + ".count"


def _write_count(cache_path, written):
    """Atomically write the completed-row counter as a text file."""
    tmp = _count_path(cache_path) + ".tmp"
    with open(tmp, "w") as f:
        f.write(str(int(written)))
    os.replace(tmp, _count_path(cache_path))


def _read_count(cache_path):
    """Best-effort resume position, in priority order:
    1. atomic text counter (current code),
    2. legacy numpy-format counter (older code wrote .count.npy),
    3. last non-zero row in the memmap (most robust; survives corrupt counters).
    """
    try:
        with open(_count_path(cache_path)) as f:
            return int(f.read().strip() or 0)
    except Exception:
        pass
    try:
        return int(np.load(_count_path(cache_path) + ".npy").reshape(()))
    except Exception:
        pass
    try:
        mm = np.load(cache_path, mmap_mode="r")
        arr = np.asarray(mm)
        nz = np.nonzero(np.linalg.norm(arr, axis=1))[0]
        return int(nz[-1]) + 1 if len(nz) else 0
    except Exception:
        return 0


def extract_features_stream(byte_iter, backbone, img_size=224, device="cpu",
                            batch_size=64, cache_path=None, n_total=None, feat_dim=None):
    """byte_iter: iterable of JPEG/PNG bytes. Returns (N, D) float32 features.

    If cache_path is provided, features are streamed into a memory-mapped .npy file
    and can be resumed after interruption (a .count file stores completed rows and a
    .done flag marks completion). n_total and feat_dim are required with cache_path.
    """
    import torch
    import torchvision.transforms as T
    torch.set_num_threads(int(os.environ.get("OMP_NUM_THREADS", "8")))
    tf = T.Compose([
        T.Resize((img_size, img_size)),
        T.ToTensor(),
        T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])
    if cache_path is not None:
        if n_total is None or feat_dim is None:
            raise ValueError("cache_path requires n_total and feat_dim")
        if os.path.exists(cache_path) and os.path.exists(cache_path + ".done"):
            print(f"[feat_utils] loading completed cache {cache_path}", flush=True)
            return np.load(cache_path)
    start = 0
    mem = None
    if cache_path is not None:
        if os.path.exists(cache_path):
            mem = np.load(cache_path, mmap_mode="r+")
            start = _read_count(cache_path)
            print(f"[feat_utils] resuming cache {cache_path} at row {start}/{n_total}", flush=True)
        else:
            mem = np.lib.format.open_memmap(cache_path, mode="w+", dtype=np.float32,
                                            shape=(n_total, feat_dim))
            _write_count(cache_path, 0)
            print(f"[feat_utils] creating cache {cache_path} shape {(n_total, feat_dim)}", flush=True)
    feats = None if mem is not None else []
    batch_bytes = []
    batch_imgs = []
    written = start
    it = iter(byte_iter)
    for _ in range(start):
        try:
            next(it)
        except StopIteration:
            break

    def flush():
        nonlocal batch_bytes, batch_imgs, written
        if not batch_imgs:
            return
        tensors = [tf(im) for im in batch_imgs]
        x = torch.stack(tensors).to(device)
        with torch.no_grad():
            f = backbone(x).cpu().numpy()
        if mem is not None:
            mem[written:written + f.shape[0]] = f
            mem.flush()
            written += f.shape[0]
            _write_count(cache_path, written)
        else:
            feats.append(f)
        batch_bytes = []
        batch_imgs = []

    for b in it:
        im = Image.open(io.BytesIO(b)).convert("RGB")
        batch_imgs.append(im)
        if len(batch_imgs) >= batch_size:
            flush()
    flush()
    if mem is not None:
        mem.flush()
        _write_count(cache_path, written)
        with open(cache_path + ".done", "w") as f:
            f.write("done")
        print(f"[feat_utils] cache complete {cache_path}", flush=True)
        return np.array(mem)
    return np.concatenate(feats, axis=0).astype(np.float32)


def extract_features_arrays(arr_iter, backbone, img_size=224, device="cpu",
                            batch_size=64):
    """arr_iter: iterable of (H,W,3) uint8 numpy arrays. Returns (N, D) features."""
    import torch
    import torchvision.transforms as T
    torch.set_num_threads(int(os.environ.get("OMP_NUM_THREADS", "8")))
    tf = T.Compose([
        T.Resize((img_size, img_size)),
        T.ToTensor(),
        T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])
    feats = []
    batch = []
    for arr in arr_iter:
        batch.append(Image.fromarray(arr).convert("RGB"))
        if len(batch) >= batch_size:
            tensors = [tf(im) for im in batch]
            x = torch.stack(tensors).to(device)
            with torch.no_grad():
                f = backbone(x).cpu().numpy()
            feats.append(f)
            batch = []
    if batch:
        tensors = [tf(im) for im in batch]
        x = torch.stack(tensors).to(device)
        with torch.no_grad():
            f = backbone(x).cpu().numpy()
        feats.append(f)
    return np.concatenate(feats, axis=0).astype(np.float32)
