#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
extract_features.py
===================
PatternNet (1706.03424) content-based image retrieval -- feature extraction.

Reads the frozen PatternNet parquet shards, extracts deep CNN embeddings with
ImageNet-pretrained backbones (torchvision, weights loaded from the local torch
hub cache), L2-normalizes them, and saves them for the retrieval step.

Embeddings:
    - resnet18 : (N, 512)  output of torchvision.models.resnet18 avg-pool
    - vit_b_16 : (N, 768)  class token after the final LayerNorm baked into the
                           torchvision ViT-B/16 encoder (encoder.ln)

The backbones are FROZEN ImageNet-pretrained networks; they are never fit to the
retrieval data, so no leakage can come from the feature extractor.

Example
-------
    python extract_features.py \
        --data-dir <dir containing train-*-of-00003.parquet> \
        --out-dir ../artifacts \
        --model resnet18 --device cpu --batch-size 64
"""
from __future__ import annotations

import argparse
import io
import json
import os
import time
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq
import torch
from PIL import Image
from torchvision import transforms
from torchvision.models import resnet18, vit_b_16

CACHE_CKPT = Path.home() / ".cache" / "torch" / "hub" / "checkpoints"

CKPT_FILES = {
    "resnet18": "resnet18-f37072fd.pth",
    "vit_b_16": "vit_b_16-c867db91.pth",
}

IMG_TRANSFORM = transforms.Compose(
    [
        transforms.Resize((256, 256), interpolation=Image.BILINEAR),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ]
)


def find_data_dir(cli_value: str | None) -> Path:
    """Locate the frozen parquet directory (CLI path > task-local > F: drive)."""
    candidates = []
    if cli_value:
        candidates.append(Path(cli_value))
    here = Path(__file__).resolve().parent
    candidates += [
        here.parent.parent.parent / "data" / "data",   # <task>/data/data
        here.parent.parent.parent / "data",            # <task>/data
        Path("/mnt/f/dataset/earth/1706.03424_patternnet") / "data" / "data",
        Path("F:/dataset/earth/1706.03424_patternnet") / "data" / "data",
    ]
    for c in candidates:
        shards = sorted(c.glob("train-*-of-00003.parquet")) if c.exists() else []
        if len(shards) >= 3:
            return c
    raise FileNotFoundError(
        "Could not locate the 3 frozen parquet shards. Pass --data-dir."
    )


def build_model(name: str, ckpt_dir: Path) -> torch.nn.Module:
    ckpt = ckpt_dir / CKPT_FILES[name]
    if not ckpt.exists():
        raise FileNotFoundError(f"local pretrained weights missing: {ckpt}")
    if name == "resnet18":
        model = resnet18()
        model.load_state_dict(torch.load(ckpt, map_location="cpu"))
    elif name == "vit_b_16":
        model = vit_b_16()
        model.load_state_dict(torch.load(ckpt, map_location="cpu"))
    else:
        raise ValueError(f"unsupported model {name}")
    model.eval()
    return model


@torch.no_grad()
def embed_batch(model: torch.nn.Module, images: torch.Tensor, name: str) -> torch.Tensor:
    if name == "resnet18":
        x = model.conv1(images)
        x = model.bn1(x)
        x = model.relu(x)
        x = model.maxpool(x)
        x = model.layer1(x)
        x = model.layer2(x)
        x = model.layer3(x)
        x = model.layer4(x)
        x = model.avgpool(x)
        return torch.flatten(x, 1)
    if name == "vit_b_16":
        x = model._process_input(images)
        batch_class_token = model.class_token.expand(x.shape[0], -1, -1)
        x = torch.cat([batch_class_token, x], dim=1)
        x = model.encoder(x)  # encoder includes final LayerNorm
        return x[:, 0]
    raise ValueError(name)


def decode_batch(chunk: list[dict], batch_size: int) -> torch.Tensor:
    """Decode the raw JPEG bytes in a parquet image-struct batch."""
    tensors = []
    for rec in chunk:
        img = Image.open(io.BytesIO(rec["bytes"])).convert("RGB")
        tensors.append(IMG_TRANSFORM(img))
    return torch.stack(tensors, 0)


def main() -> None:
    ap = argparse.ArgumentParser(description="PatternNet CNN feature extraction")
    ap.add_argument("--data-dir", default=None,
                    help="dir containing train-*-of-00003.parquet (auto-detected)")
    ap.add_argument("--out-dir", default="../artifacts", help="output dir")
    ap.add_argument("--model", default="resnet18", choices=["resnet18", "vit_b_16"])
    ap.add_argument("--device", default="cpu", choices=["cpu", "cuda", "auto"])
    ap.add_argument("--batch-size", type=int, default=64)
    args = ap.parse_args()

    torch.manual_seed(0)
    np.random.seed(0)

    device = args.device
    if device == "auto":
        device = "cuda" if torch.cuda.is_available() else "cpu"
    dev = torch.device(device)

    data_dir = find_data_dir(args.data_dir)
    shards = sorted(data_dir.glob("train-*-of-00003.parquet"))
    n_rows = sum(pq.ParquetFile(s).metadata.num_rows for s in shards)
    print(f"[extract] data dir : {data_dir}", flush=True)
    print(f"[extract] shards   : {len(shards)}  rows: {n_rows}", flush=True)

    model = build_model(args.model, CACHE_CKPT).to(dev)
    print(f"[extract] model {args.model} on {device}", flush=True)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    all_emb, all_labels, all_paths = [], [], []
    n_proc, t0 = 0, time.time()

    for s in shards:
        table = pq.read_table(s, columns=["image", "label"])
        records = table.column("image").to_pylist()  # list of {bytes, path}
        labels = table.column("label").to_pylist()
        for start in range(0, len(records), args.batch_size):
            chunk = records[start:start + args.batch_size]
            images = decode_batch(chunk, args.batch_size)
            emb = embed_batch(model, images.to(dev), args.model).cpu().numpy()
            all_emb.append(emb)
            all_labels.extend(labels[start:start + args.batch_size])
            all_paths.extend(r["path"] for r in chunk)
            n_proc += len(chunk)
            if n_proc == 0 or n_proc % 4000 < args.batch_size:
                print(f"  ... {n_proc}/{n_rows}  ({time.time() - t0:.0f}s)", flush=True)

    feat = np.concatenate(all_emb, axis=0).astype(np.float32)
    feat /= (np.linalg.norm(feat, axis=1, keepdims=True) + 1e-12)  # L2 norm
    labels = np.asarray(all_labels, dtype=np.int64)

    np.save(out_dir / f"features_{args.model}.npy", feat)
    np.save(out_dir / "labels.npy", labels)
    with open(out_dir / "paths.json", "w") as f:
        json.dump(all_paths, f, indent=1)
    meta = {"model": args.model, "dim": int(feat.shape[1]), "n": int(feat.shape[0]),
            "device": device, "l2_normalized": True}
    with open(out_dir / f"features_{args.model}.meta.json", "w") as f:
        json.dump(meta, f, indent=2)

    print(f"[extract] done. shape={feat.shape} time={time.time()-t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()