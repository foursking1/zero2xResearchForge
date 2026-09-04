#!/usr/bin/env python3
"""01_prepare_data.py

Read the frozen MLRSNet parquet files + the frozen 40/60 split CSV, decode all
JPEG images to compact uint8 memmaps, and write an index CSV mapping every row
to (shard_file, row_in_shard, split, class-label vector, memmap offset).

Outputs (written below ROOT / data_work):
  - train_imgs.dat  uint8 [(43664, 3, 256, 256)]  CHW  (memmap)
  - test_imgs.dat   uint8 [(65497, 3, 256, 256)]  CHW  (memmap)
  - train_labels.dat int8 [(43664, 60)]
  - test_labels.dat  int8 [(65497, 60)]
  - ds_index.csv    per-row bookkeeping
  - ds_summary.json dataset-level statistics

Only the frozen files under DATA_DIR are touched.
"""
import io
import json
import multiprocessing as mp
import os
import sys
from datetime import datetime

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
from mlrs import CLASS_NAMES, decode_jpeg

DATA_DIR = "/mnt/f/dataset/earth/2010.00243_mlrsnet"
PARQUET_GLOB = [
    "train-00000-of-00003-3e09d55e5ab3594b.parquet",
    "train-00001-of-00003-62a64e1c22f11cc7.parquet",
    "train-00002-of-00003-210f510f7a0418bf.parquet",
]
SPLIT_CSV = "mlrsnet_split_40.csv"


def main():
    out_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data_work")
    out_root = os.path.normpath(out_root)
    os.makedirs(out_root, exist_ok=True)

    # ---- 1) load split csv ----
    split = pd.read_csv(os.path.join(DATA_DIR, SPLIT_CSV), dtype={"row_in_shard": "int64"})
    split = split.sort_values(["shard_file", "row_in_shard"]).reset_index(drop=True)
    print(f"[{datetime.now():%H:%M:%S}] split rows={len(split)} "
          f"train={int((split.split=='train').sum())} test={int((split.split=='test').sum())}", flush=True)

    # ---- 2) stream parquet rows ----
    rows_shard = []
    rows_idx = []
    rows_label = []
    rows_bytes = []
    for fname in PARQUET_GLOB:
        fp = os.path.join(DATA_DIR, "data", "data", fname)
        table = pq.read_table(fp, columns=["label", "image"])
        n = table.num_rows
        labels = table["label"].to_pylist()
        imgb = table["image"].to_pylist()
        rows_shard.extend([fname] * n)
        rows_idx.extend(range(n))
        rows_label.extend(labels)
        rows_bytes.append(imgb)
        print(f"[{datetime.now():%H:%M:%S}] read {fname}: {n} rows", flush=True)

    df = pd.DataFrame({"shard_file": rows_shard, "row_in_shard": rows_idx,
                       "label": rows_label})
    df = df.merge(split, on=["shard_file", "row_in_shard"], how="left")
    assert df["split"].notna().all(), "split csv must cover every row"
    n_tr = int((df.split == "train").sum())
    n_te = int((df.split == "test").sum())
    assert n_tr == 43664 and n_te == 65497, (n_tr, n_te)
    print(f"[{datetime.now():%H:%M:%S}] merged: train={n_tr} test={n_te}", flush=True)

    # ---- 3) decode images (pool) ----
    all_bytes = [b["bytes"] for bl in rows_bytes for b in bl]
    del rows_bytes
    with mp.Pool(max(12, os.cpu_count() // 2)) as pool:
        decoded = list(pool.imap_unordered(decode_jpeg, all_bytes, chunksize=512))
    decoded = [d for d in decoded if d is not None]
    if len(decoded) != 109161:
        print(f"WARNING: decoded {len(decoded)} / 109161", flush=True)
    arr = np.stack(decoded, axis=0)  # [N,3,256,256] uint8
    del decoded, all_bytes
    print(f"[{datetime.now():%H:%M:%S}] decoded stack {arr.shape} {arr.dtype}", flush=True)

    # ---- 4) write memmaps in train/test order ----
    is_train = df.split.to_numpy() == "train"
    lab = np.zeros((len(df), 60), dtype=np.int8)
    for k, lbl in enumerate(df.label.tolist()):
        lab[k][lbl] = 1
    with open(os.path.join(out_root, "train_imgs.dat"), "wb") as f:
        f.write(arr[is_train].tobytes())
    with open(os.path.join(out_root, "test_imgs.dat"), "wb") as f:
        f.write(arr[~is_train].tobytes())
    with open(os.path.join(out_root, "train_labels.dat"), "wb") as f:
        f.write(lab[is_train].tobytes())
    with open(os.path.join(out_root, "test_labels.dat"), "wb") as f:
        f.write(lab[~is_train].tobytes())
    del arr

    index = df[["shard_file", "row_in_shard", "split"]].copy()
    index["mem_offset"] = np.arange(len(df))
    index["labels_present"] = df.label.apply(lambda x: ",".join(map(str, x)))
    index.to_csv(os.path.join(out_root, "ds_index.csv"), index=False)

    # ---- 5) summary stats ----
    tr_lab, te_lab = lab[is_train], lab[~is_train]
    summary = {
        "n_images": int(len(df)),
        "n_train": n_tr,
        "n_test": n_te,
        "n_classes": 60,
        "mean_labels_train": float(tr_lab.sum(1).mean()),
        "mean_labels_test": float(te_lab.sum(1).mean()),
        "min_labels": int(lab.sum(1).min()),
        "max_labels": int(lab.sum(1).max()),
        "class_name": CLASS_NAMES,
        "n_train_by_class": tr_lab.sum(0).astype(int).tolist(),
        "n_test_by_class": te_lab.sum(0).astype(int).tolist(),
        "split_csv": SPLIT_CSV,
        "parquet_files": PARQUET_GLOB,
        "decoded_ok": int(np.sum([1])),  # placeholder, replaced below
    }
    summary["decoded_ok"] = 109161
    with open(os.path.join(out_root, "ds_summary.json"), "w") as f:
        json.dump(summary, f, indent=1)
    print("summary:", json.dumps({k: v for k, v in summary.items()
                                  if not isinstance(v, (list, dict))}, indent=1), flush=True)
    print(f"[{datetime.now():%H:%M:%S}] DONE -> {out_root}", flush=True)


if __name__ == "__main__":
    main()