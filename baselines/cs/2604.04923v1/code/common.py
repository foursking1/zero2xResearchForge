"""Shared utilities for reproducing claims of arXiv:2604.04923v1.

All data is read in-place from the frozen reproduction workspace
(no copies of large files are made).
"""
import os
import sys
import json

import numpy as np

# Root of the frozen reproduction workspace (also settable via env var).
DATA_ROOT = os.environ.get("STL_DATA_ROOT", "F:/dataset/2604.04923v1")
CODE_ROOT = os.path.join(DATA_ROOT, "code")
RESULTS_ROOT = os.path.join(DATA_ROOT, "results")
DATA_DIR = os.path.join(DATA_ROOT, "data")

# The frozen reference implementation of VGT / VGT-dot lives in the
# reproduction workspace; import it directly (read-only).
sys.path.insert(0, CODE_ROOT)


def load_embeddings():
    """Return (embeddings (N,D) float32, time_steps (N,) int64)."""
    emb = np.load(os.path.join(DATA_DIR, "embeddings.npy"))
    ts = np.load(os.path.join(DATA_DIR, "time_steps.npy"))
    return emb, ts


def load_trajectory_info():
    with open(os.path.join(DATA_DIR, "trajectory_info.json"), "r") as f:
        return json.load(f)


def load_config():
    with open(os.path.join(RESULTS_ROOT, "config.json"), "r") as f:
        return json.load(f)


def load_training_stats():
    with open(os.path.join(RESULTS_ROOT, "training_stats.json"), "r") as f:
        return json.load(f)


def load_checkpoint(name="checkpoint_final.pt", map_location="cpu"):
    import torch
    path = os.path.join(RESULTS_ROOT, "checkpoints", name)
    ckpt = torch.load(path, map_location=map_location, weights_only=False)
    return ckpt


def load_cluster_labels():
    return np.load(os.path.join(RESULTS_ROOT, "cluster_labels.npy"))


def set_seed(seed=42):
    import torch
    np.random.seed(seed)
    torch.manual_seed(seed)
