"""Decode frozen EuroSAT parquet files into in-memory numpy caches (.npz).

Reads the frozen parquet splits from DATA_ROOT, decodes the embedded PNG
bytes into (N, 64, 64, 3) uint8 arrays and writes one .npz per split under
CACHE_DIR. Nothing is downloaded; the frozen files are never modified.

Usage:
    python 01_prepare_data.py [--data-root PATH] [--cache-dir PATH]
"""
import argparse
import os
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image
from concurrent.futures import ThreadPoolExecutor, as_completed

SPLITS = ["train", "validation", "test"]


def decode(args):
    idx, raw = args
    img = Image.open(__import__("io").BytesIO(raw))
    na = np.asarray(img.convert("RGB"), dtype=np.uint8)
    assert na.shape == (64, 64, 3), na.shape
    return idx, na


def convert(split, df, cache_dir, workers):
    raw = df["image"].tolist()
    labels = df["label"].astype(np.int64).to_numpy()
    filenames = df["filename"].astype(str).tolist()
    arr = np.empty((len(raw), 64, 64, 3), dtype=np.uint8)
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = [ex.submit(decode, (i, raw[i]["bytes"])) for i in range(len(raw))]
        for done, fut in enumerate(as_completed(futures), 1):
            i, na = fut.result()
            arr[i] = na
            if done % 4000 == 0 or done == len(raw):
                print(f"[{split}] decoded {done}/{len(raw)}", flush=True)
    out = os.path.join(cache_dir, f"{split}.npz")
    np.savez_compressed(out, images=arr, labels=labels, filenames=filenames)
    print(f"[{split}] wrote {out}  shape={arr.shape}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", default=os.environ.get(
        "EUROSAT_DATA",
        "/mnt/f/dataset/earth/1709.00029_eurosat/data/data"))
    ap.add_argument("--cache-dir", default=os.environ.get(
        "EUROSAT_CACHE",
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "cache")))
    ap.add_argument("--workers", type=int, default=12)
    args = ap.parse_args()

    cache_dir = Path(args.cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    data_root = Path(args.data_root)
    assert data_root.exists(), f"data root not found: {data_root}"

    for split in SPLITS:
        pf = data_root / f"{split}-00000-of-00001.parquet"
        assert pf.exists(), f"missing frozen file: {pf}"
        df = pd.read_parquet(pf, columns=["image", "label", "filename"])
        convert(split, df, cache_dir, args.workers)


if __name__ == "__main__":
    main()