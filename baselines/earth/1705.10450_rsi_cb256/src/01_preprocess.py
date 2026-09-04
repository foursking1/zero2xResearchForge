"""Build cached uint8 image store (224x224) + labels from the frozen parquet shards.

Outputs (under results/):
  - images_224.memmap : (N, H, W, 3) uint8
  - labels.npz        : label_1, label_2 int arrays + split + global row order
  - manifest.csv      : row bookkeeping used for evidence / recomputation

It never modifies the frozen parquet / split files.
"""
import os
import sys
import time

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (PARQUET_DIR, RESULTS_DIR, SEED, decode_image_bytes,
                    load_split_frame, parquet_files)

import pyarrow.parquet as pq  # noqa: E402
from PIL import Image  # noqa: E402


def main():
    os.makedirs(RESULTS_DIR, exist_ok=True)
    files = parquet_files()
    _, split_ser, spl = load_split_frame()
    n = len(spl)
    print(f"[preprocess] {len(files)} shards, {n} rows")

    imgs = np.lib.format.open_memmap(
        os.path.join(RESULTS_DIR, "images_224.memmap"), mode="w+",
        dtype=np.uint8, shape=(n, 224, 224, 3))
    l1 = np.zeros(n, dtype=np.int64)
    l2 = np.zeros(n, dtype=np.int64)
    t0 = time.time()
    done = 0
    for f in files:
        shard = os.path.basename(f)
        rows = spl[spl["shard_file"] == shard]
        if len(rows) == 0:
            print(f"  ! no rows in split for {shard}, skipped")
            continue
        tab = pq.read_table(f, columns=["label_1", "label_2", "image"])
        df = tab.to_pandas()
        for _, r in rows.iterrows():
            i = int(r["global_idx"])
            j = int(r["row_in_shard"])
            rec = df["image"].iloc[j]["bytes"]
            pil = decode_image_bytes(rec).resize((224, 224), Image.Resampling.BILINEAR)
            arr = np.asarray(pil, dtype=np.uint8)
            imgs[i] = arr
            pil.close()
            l1[i] = int(r["label_1"])
            l2[i] = int(r["label_2"])
            done += 1
        print(f"  shard {shard}: ok, done={done} ({time.time()-t0:.0f}s)")
        del df, tab

    split_int = np.where((split_ser.astype(str).to_numpy() == "train"), 1, 0).astype(np.int8)
    np.savez(os.path.join(RESULTS_DIR, "labels.npz"),
             label_1=l1, label_2=l2,
             global_idx=spl["global_idx"].to_numpy().astype(np.int64),
             split=split_int)
    spl.to_csv(os.path.join(RESULTS_DIR, "manifest.csv"), index=False)
    imgs.flush()
    print(f"[preprocess] done {done} rows in {time.time()-t0:.0f}s")
    print(f"  label_1 classes: {np.unique(l1).size}, label_2 classes: {np.unique(l2).size}")
    print(f"  split sizes: train={(split_int==1).sum()} "
          f"test={(split_int==0).sum()}")


if __name__ == "__main__":
    main()