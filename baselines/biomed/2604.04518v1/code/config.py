"""Shared configuration and utilities for the reproducibility study.

Paper: "Reproducibility study on how to find Spurious Correlations, Shortcut
Learning, Clever Hans or Group-Distributional non-robustness and how to fix
them" (arXiv:2604.04518v1).

This module centralizes hyper-parameters, paths and small helpers.
"""
import os
import random

import numpy as np
import torch

# ---------------------------------------------------------------------------
# Paths (frozen data lives in-place; we only write derived small artifacts)
# ---------------------------------------------------------------------------
DATA_ROOT_F = r"F:\dataset\2604.04518v1"
DATA_ROOT_E = r"E:\scisolvebench-data\raw\2604.04518v1"

CELEBA_CURATED_IMG = os.path.join(
    DATA_ROOT_E, "curated_source_subset", "celeba", "images")
CELEBA_CURATED_ATTR = os.path.join(
    DATA_ROOT_E, "curated_source_subset", "celeba", "list_attr_celeba_subset.txt")
CAMELYON_CURATED_META = os.path.join(
    DATA_ROOT_E, "curated_source_subset", "camelyon17", "metadata_subset.csv")
CAMELYON_CURATED_PATCHES = os.path.join(
    DATA_ROOT_E, "curated_source_subset", "camelyon17", "patches")

FULL_CELEBA_IMG = os.path.join(DATA_ROOT_E, "celeba", "celeba", "img_align_celeba")
FULL_CELEBA_ATTR = os.path.join(DATA_ROOT_E, "celeba", "celeba", "list_attr_celeba.txt")
FULL_CELEBA_PARTITION = os.path.join(DATA_ROOT_E, "celeba", "celeba", "list_eval_partition.txt")
FULL_CAMELYON_META = os.path.join(DATA_ROOT_E, "camelyon17", "camelyon17_v1.0", "metadata.csv")
FULL_CAMELYON_PATCHES = os.path.join(DATA_ROOT_E, "camelyon17", "camelyon17_v1.0", "patches")

# Derived artifacts are written here (small; not the big datasets)
WORKSPACE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "workspace")
os.makedirs(WORKSPACE, exist_ok=True)

# ---------------------------------------------------------------------------
# Random seeds
# ---------------------------------------------------------------------------
SEED = 42


def set_seed(seed: int = SEED):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def get_device():
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


# ---------------------------------------------------------------------------
# Dataset-level group configuration
# ---------------------------------------------------------------------------
# Group index order: 0 = A-, 1 = A+, 2 = B-, 3 = B+
#   A-: (t=0, q=0), A+: (t=0, q=1), B-: (t=1, q=0), B+: (t=1, q=1)
# Symmetric relative group sizes (train/val):  [0.49, 0.01, 0.01, 0.49]
# Asymmetric relative group sizes:             [0.25, 0.25, 0.49, 0.01]

TRAIN_N = 800
VAL_N = 200

SYM_GROUP_FRAC = np.array([0.49, 0.01, 0.01, 0.49])
ASYM_GROUP_FRAC = np.array([0.25, 0.25, 0.49, 0.01])


def group_sizes(n, poison):
    if poison == "symmetric":
        frac = SYM_GROUP_FRAC
    elif poison == "asymmetric":
        frac = ASYM_GROUP_FRAC
    elif poison == "unpoisoned":
        frac = np.array([0.25, 0.25, 0.25, 0.25])
    else:
        raise ValueError(poison)
    sizes = np.round(n * frac).astype(int)
    # fix rounding so the sum is exact
    diff = n - int(sizes.sum())
    sizes[-1] += diff
    return sizes


def group_to_target_conf(group):
    """Map group index -> (target, confounder)."""
    t = 0 if group < 2 else 1
    q = group % 2
    return t, q


def conf_to_group(t, q):
    return t * 2 + q


# ---------------------------------------------------------------------------
# Metric helpers
# ---------------------------------------------------------------------------
def compute_group_metrics(preds, targets, groups, n_groups=4):
    """Return (empirical_accuracy, AGA, WGA)."""
    preds = np.asarray(preds)
    targets = np.asarray(targets)
    groups = np.asarray(groups)
    acc = float((preds == targets).mean())
    group_accs = []
    for g in range(n_groups):
        mask = groups == g
        if mask.sum() == 0:
            group_accs.append(float("nan"))
        else:
            group_accs.append(float((preds[mask] == targets[mask]).mean()))
    aga = float(np.nanmean(group_accs))
    wga = float(np.nanmin(group_accs))
    return acc, aga, wga, group_accs


def save_pt(obj, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    torch.save(obj, path)
