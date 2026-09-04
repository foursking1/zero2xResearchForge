"""Shared constants, paths, and helpers for the RSI-CB256 reproduction task.

Frozen data (never modified):
  - parquet shards :  /mnt/f/dataset/earth/1705.10450_rsi_cb256/data/data/train-0000X-of-00010-*.parquet
  - split csv      :  /mnt/f/dataset/earth/1705.10450_rsi_cb256/split_train_test_50.csv
"""
import io
import os
import glob

import numpy as np
import pandas as pd
import torch
from PIL import Image

TASK_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_ROOT = "/mnt/f/dataset/earth/1705.10450_rsi_cb256"
PARQUET_DIR = os.path.join(DATA_ROOT, "data", "data")
SPLIT_CSV = os.path.join(DATA_ROOT, "split_train_test_50.csv")
SOLUTION_DIR = os.path.join(TASK_ROOT, "agent_solution")
RESULTS_DIR = os.path.join(SOLUTION_DIR, "results")
EVIDENCE_DIR = os.path.join(SOLUTION_DIR, "evidence")
CHECKPOINT_DIR = os.path.join(SOLUTION_DIR, "checkpoints")

SEED = 1705
RESOLUTION = 224  # input crop used for the pretrained L2 norm backbone

IMG_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
IMG_STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)

LABEL1_NAMES = [
    "transportation", "other objects", "woodland", "water area",
    "other land", "cultivated land", "construction land",
]

LABEL2_NAMES = [
    "parking lot", "avenue", "highway", "bridge", "marina", "crossroads",
    "airport runway", "pipeline", "town", "airplane", "forest", "mangrove",
    "artificial grassland", "river protection forest", "shrubwood", "sapling",
    "sparse forest", "lakeshore", "river", "stream", "coastline", "hirst",
    "dam", "sea", "snow mountain", "sandbeach", "mountain", "desert",
    "dry farm", "green farmland", "bare land", "city building", "residents",
    "container", "storage room",
]

N_L1 = len(LABEL1_NAMES)
N_L2 = len(LABEL2_NAMES)


def parquet_files():
    return sorted(glob.glob(os.path.join(PARQUET_DIR, "train-*.parquet")))


def load_split_frame():
    """Return (idx, split_ser, meta_df) keyed by global row index.

    meta_df: columns [shard_file, row_in_shard, label_1, label_2, split]
    """
    df = pd.read_csv(SPLIT_CSV)
    df["index"] = df["global_idx"]
    df = df.set_index("global_idx", drop=False)
    return df["index"].to_numpy(), df["split"], df


def decode_image_bytes(b):
    """Decode TIFF/JPEG bytes -> PIL RGB uint8 image."""
    return Image.open(io.BytesIO(bytes(b))).convert("RGB")


def normalize(x_uint8):
    """x_uint8: [..., H, W, 3] uint8 -> float32 CHW tensor in [0,1] normalized."""
    x = x_uint8.astype(np.float32) / 255.0
    x = (x - IMG_MEAN) / IMG_STD
    return x


def set_seed(seed=SEED):
    torch.manual_seed(seed)
    np.random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)


def load_labels():
    """load labels.npz with the split column decoded back to 'train'/'test'."""
    lab = dict(np.load(os.path.join(RESULTS_DIR, "labels.npz")))
    lab["split"] = np.where(lab["split"] == 1, "train", "test")
    return lab


def split_tensors(n_images):
    """Return boolean masks for train/test derived from the frozen split csv."""
    idx, split, _ = load_split_frame()
    if len(idx) != n_images:
        raise ValueError(f"split size {len(idx)} != n_images {n_images}")
    tr = (split.astype(str).to_numpy() == "train")
    te = (split.astype(str).to_numpy() == "test")
    return tr, te