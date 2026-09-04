#!/usr/bin/env python3
"""Shared configuration: locate the frozen OGBG-MOLHIV data and define paths.

Resolution order for the frozen data directory:
  1. $MOLHIV_DATA_DIR  (explicit override)
  2. /mnt/f/dataset/biomed/2005.00687_ogb_molhiv     (frozen package location)
  3. <bench_dir>/data
"""

import os

BENCH_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CANDIDATES = [
    os.environ.get("MOLHIV_DATA_DIR", ""),
    "/mnt/f/dataset/biomed/2005.00687_ogb_molhiv",
    "/mnt/d/dataset/biomed/2005.00687_ogb_molhiv",
    os.path.join(BENCH_DIR, "data"),
]


def find_data_dir():
    for cand in CANDIDATES:
        if cand and all(os.path.isfile(os.path.join(cand, f"{s}.jsonl"))
                        for s in ("train", "valid", "test")):
            return cand
    raise FileNotFoundError(
        "Frozen OGBG-MOLHIV data not found. Set MOLHIV_DATA_DIR (dir with "
        "train.jsonl / valid.jsonl / test.jsonl).")


DATA_DIR = find_data_dir()


def results_dir():
    d = os.path.join(BENCH_DIR, "results")
    os.makedirs(d, exist_ok=True)
    return d


def ckpt_dir():
    d = os.path.join(BENCH_DIR, "results", "checkpoints")
    os.makedirs(d, exist_ok=True)
    return d