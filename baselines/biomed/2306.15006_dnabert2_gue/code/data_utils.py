"""Shared utilities: frozen GUE dataset loading and sequence statistics.

Data iron rule: ONLY the frozen gz files shipped with the task may be used.
Frozen location (per data/DATA_LOCATION.md): F:\\dataset\\biomed\\2306.15006_dnabert2_gue\\
On this WSL box that is mounted at /mnt/f/dataset/biomed/2306.15006_dnabert2_gue/.
"""
from __future__ import annotations

import csv
import gzip
import os
from pathlib import Path

DATASETS = ["EMP_H3", "mouse_0", "prom_300_all", "prom_core_all"]
SPLITS = ["train", "val", "test"]
# metric per task per the DNABERT-2 / GUE paper reporting convention
TASK_METRIC = {
    "EMP_H3": "mcc",
    "mouse_0": "mcc",
    "prom_300_all": "f1",
    "prom_core_all": "f1",
}
TASK_NAMES = {
    "EMP_H3": "emp",
    "mouse_0": "tf_m",
    "prom_300_all": "pd",
    "prom_core_all": "cpd",
}


def find_data_dir() -> Path:
    """Locate the frozen data directory (searched in several plausible places)."""
    candidates = [
        os.environ.get("GUE_DATA_DIR"),
        "/mnt/f/dataset/biomed/2306.15006_dnabert2_gue",
        "/mnt/d/dataset/biomed/2306.15006_dnabert2_gue",
        "F:/dataset/biomed/2306.15006_dnabert2_gue",
        str(Path(__file__).resolve().parents[2] / "data"),
    ]
    for c in candidates:
        if c and Path(c).exists() and (Path(c) / "EMP_H3_train.csv.gz").is_file():
            return Path(c)
    raise FileNotFoundError(
        "Could not locate frozen GUE data. Set GUE_DATA_DIR env var to its folder."
    )


def load_gz_split(data_dir: Path, dataset: str, split: str) -> tuple[list[str], list[int]]:
    """Return (sequences, labels) for one frozen file.

    Files are gzip CSV with a `sequence,label` header line.
    """
    path = data_dir / f"{dataset}_{split}.csv.gz"
    seqs, labels = [], []
    with gzip.open(path, "rt", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        try:
            header = next(reader)
        except StopIteration:
            header = []
        if not (header and header[0].strip().lower() == "sequence"):
            # no header -> treat previous row as data
            if header:
                seqs.append(header[0].replace("\x00", ""))
                labels.append(int(float(header[1])))
        for row in reader:
            if not row:
                continue
            seqs.append(row[0].replace("\x00", "").strip().upper())
            labels.append(int(float(row[1])))
    return seqs, labels


def load_dataset(data_dir: Path, dataset: str) -> dict[str, tuple[list[str], list[int]]]:
    return {s: load_gz_split(data_dir, dataset, s) for s in SPLITS}


def seq_stats(seqs: list[str], labels: list[int]) -> dict:
    n = len(seqs)
    pos = sum(1 for l in labels if l == 1)
    lens = [len(s) for s in seqs]
    return {
        "n": n,
        "pos": pos,
        "neg": n - pos,
        "pos_ratio": round(pos / n, 6) if n else 0.0,
        "min_len": min(lens) if n else 0,
        "max_len": max(lens) if n else 0,
        "mean_len": round(sum(lens) / n, 6) if n else 0.0,
    }


def all_stats(data_dir: Path) -> dict[str, dict[str, dict]]:
    res = {}
    for d in DATASETS:
        data = load_dataset(data_dir, d)
        res[d] = {s: seq_stats(*data[s]) for s in SPLITS}
    return res


if __name__ == "__main__":
    import json
    import hashlib

    dd = find_data_dir()
    print("data dir:", dd)
    st = all_stats(dd)
    print(json.dumps(st, indent=1))
    # record per-file checksum sanity check
    for name in sorted(os.listdir(dd)):
        if name.endswith(".csv.gz"):
            h = hashlib.sha256(open(dd / name, "rb").read()).hexdigest().upper()
            print(f"{name}  sha256={h}")