"""Common helpers for the SAT-6 reproduction pipeline.

Everything is derived from the frozen official SAT-6 Test split parquet
(TerraMoon/DeepSat HF mirror). No external / synthetic data is used.
"""
import os
import sys

import numpy as np
import pandas as pd

CLASS_NAMES = [
    "barren land",
    "building",
    "grassland",
    "road",
    "trees",
    "water",
]
N_CLASSES = len(CLASS_NAMES)

DEFAULT_DATA_PATHS = [
    # explicit frozen location used on this machine
    "/mnt/f/dataset/earth/1509.03602_deepsat/data/data/train-00000-of-00001-c47ada2c92f814d2.parquet",
    # relative to this src/ directory when re-run elsewhere
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "data",
                 "train-00000-of-00001-c47ada2c92f814d2.parquet"),
    os.path.join(os.path.dirname(__file__), "..", "data_cache",
                 "train-00000-of-00001-c47ada2c92f814d2.parquet"),
]


def resolve_data_path(arg=None):
    """Return the parquet path from (1) CLI arg (2) DSAT_DATA env (3) defaults."""
    if arg:
        return arg
    env = os.environ.get("DSAT_DATA")
    if env and os.path.exists(env):
        return env
    for p in DEFAULT_DATA_PATHS:
        if os.path.exists(p):
            return p
    raise FileNotFoundError(
        "Could not locate the frozen SAT-6 parquet. Pass it via the --data "
        "argument or the DSAT_DATA environment variable."
    )


def load_dataframe(path):
    df = pd.read_parquet(path)
    expected = 81000
    if len(df) != expected:
        raise RuntimeError(f"Unexpected row count {len(df)} (expected {expected}). "
                           "Refusing to proceed on an unexpected file.")
    return df


def decode_images(df):
    """Decode the stored PNG/JPEG bytes into a numpy array Nx28x28x3 uint8."""
    from PIL import Image
    import io
    n = len(df)
    out = np.empty((n, 28, 28, 3), dtype=np.uint8)
    for i, rec in enumerate(df["image"]):
        if isinstance(rec, dict):
            b = rec["bytes"]
        else:  # pyarrow struct -> row accessor
            b = rec["bytes"]
        im = Image.open(io.BytesIO(b)).convert("RGB")
        out[i] = np.asarray(im)
    return out