# -*- coding: utf-8 -*-
"""Shared utilities for the 2505.06646 (CheXNet reproduction) task.

Handles:
  * locating the frozen NIH ChestX-ray14 parquet files
  * decoding images / building the 14-way multi-hot labels
  * deterministic train/val split (seed 42), fixed before any training
  * building the ImageNet-pretrained DenseNet-121 with a 14-way head
  * evaluation metrics (per-class ROC-AUC / F1, mean)
"""
import io
import os
import re
import glob

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from PIL import Image
from torchvision import models, transforms

LABELS = [
    "Atelectasis", "Cardiomegaly", "Effusion", "Infiltration", "Mass",
    "Nodule", "Pneumonia", "Pneumothorax", "Consolidation", "Edema",
    "Emphysema", "Fibrosis", "Pleural_Thickening", "Hernia",
]
N_CLASS = len(LABELS)

MEAN = [0.485, 0.456, 0.406]
STD = [0.229, 0.224, 0.225]

SEED = 42


# --------------------------------------------------------------------------
# data discovery
# --------------------------------------------------------------------------
def find_data_dir():
    """Return the directory that contains the frozen parquet files.

    Tries (in order): $PB_DATA_DIR, the F: mount used by the benchmark, a
    local ./data, and several relative locations from the script directory.
    """
    candidates = [
        os.environ.get("PB_DATA_DIR"),
        r"F:/dataset/biomed/2505.06646_chexnet_reproduction",
        "/mnt/f/dataset/biomed/2505.06646_chexnet_reproduction",
        "data",
        "d:/dataset/biomed/2505.06646_chexnet_reproduction",
        "/mnt/d/dataset/biomed/2505.06646_chexnet_reproduction",
    ]
    here = os.path.dirname(os.path.abspath(__file__))
    candidates += [
        os.path.join(here, "..", "data"),
        os.path.join(here, "..", "..", "data"),
        os.path.join(here, "..", "..", "..", "data"),
    ]
    for c in candidates:
        if not c:
            continue
        if os.path.isfile(os.path.join(c, "nih_train-00000.parquet")):
            return c
    # last resort: glob for the file anywhere below two levels up
    for pattern in [
        os.path.join(here, "..", "..", "**", "nih_train*.parquet"),
        os.path.join(here, "..", "..", "..", "**", "nih_train*.parquet"),
    ]:
        hits = glob.glob(pattern, recursive=True)
        if hits:
            return os.path.dirname(hits[0])
    raise FileNotFoundError(
        "Could not locate nih_train-00000.parquet / nih_test-00000.parquet. "
        "Set PB_DATA_DIR or place the parquet files in ./data"
    )


def load_data_split(ps_root):
    """Load the frozen train/test parquet shards and return 1082/640-row frames.

    Only the 'image' (dict with 'bytes') and 'labels' (array of class indices)
    columns are read.
    """
    train = pd.read_parquet(
        os.path.join(ps_root, "nih_train-00000.parquet"),
        columns=["image", "labels"],
    )
    test = pd.read_parquet(
        os.path.join(ps_root, "nih_test-00000.parquet"),
        columns=["image", "labels"],
    )
    return train, test


def labels_to_multihot(labels_series, n_class=N_CLASS):
    """Convert per-row arrays of class indices to an (n, 14) float matrix.

    Index 14 ('No Finding') is ignored: it carries no disease signal; the
    disease bits (0..13) are kept untouched.
    """
    n = len(labels_series)
    Y = np.zeros((n, n_class), dtype=np.float32)
    for i, lab in enumerate(labels_series):
        for c in lab:
            c = int(c)
            if 0 <= c < n_class:
                Y[i, c] = 1.0
    return Y


def train_val_split(train, seed=SEED):
    """Fixed random 85/15 split of the training shard (seed 42).

    The frozen test shard is never touched here.
    """
    rng = np.random.RandomState(seed)
    idx = rng.permutation(len(train))
    n_val = int(len(idx) * 0.15)
    val_idx, tr_idx = idx[:n_val], idx[n_val:]
    return tr_idx, val_idx


# --------------------------------------------------------------------------
# image decoding / transforms
# --------------------------------------------------------------------------
def decode(row):
    """row: a DataFrame/Series row -> PIL RGB image.

    The 'image' column holds a dict with the raw byte payload ('bytes') plus
    a path string.
    """
    payload = row if isinstance(row, dict) else row["image"]
    return Image.open(io.BytesIO(payload["bytes"])).convert("RGB")


def build_transforms(kind, strong=False):
    """kind: 'repro' | 'enhanced' | 'eval'.  strong: stronger crop + erasing."""
    base = transforms.Resize((256, 256))
    crop = transforms.RandomResizedCrop(224, scale=(0.90, 1.0))
    if strong:
        crop = transforms.RandomResizedCrop(224, scale=(0.70, 1.0))
    flip = transforms.RandomHorizontalFlip(p=0.5)
    if kind == "repro":
        train_tf = transforms.Compose([base, crop, flip, transforms.ToTensor(),
                                       transforms.Normalize(MEAN, STD)])
    elif kind == "enhanced":
        train_tf = transforms.Compose([
            base, crop, flip,
            transforms.ColorJitter(brightness=0.2, contrast=0.2),
            transforms.RandomAffine(degrees=8, translate=(0.04, 0.04)),
            transforms.ToTensor(), transforms.Normalize(MEAN, STD),
        ])
    else:
        train_tf = None
    if train_tf is not None and strong:
        train_tf.transforms.append(transforms.RandomErasing(p=0.2, scale=(0.02, 0.10)))
    eval_tf = transforms.Compose([base, transforms.CenterCrop(224),
                                  transforms.ToTensor(), transforms.Normalize(MEAN, STD)])
    return train_tf, eval_tf


# --------------------------------------------------------------------------
# model
# --------------------------------------------------------------------------
def load_imagenet_state(model):
    """Load the cached ImageNet DenseNet-121 state dict into a raw densenet121.

    Falls back to torchvision's own download if the local file is missing.
    """
    here = os.path.dirname(os.path.abspath(__file__))
    paths = [
        os.path.join(here, "weights", "densenet121-a639ec97.pth"),
        os.path.join(here, "..", "weights", "densenet121-a639ec97.pth"),
        os.path.join(here, "code", "weights", "densenet121-a639ec97.pth"),
    ]
    for p in paths:
        if os.path.isfile(p):
            raw = torch.load(p, map_location="cpu")
            remap = {}
            for k, v in raw.items():
                nk = re.sub(r"\.norm\.(\d+)", r".norm\1", k)
                nk = re.sub(r"\.conv\.(\d+)", r".conv\1", nk)
                remap[nk] = v
            model.load_state_dict(remap)
            return model
    # last resort: torchvision download (needs internet)
    model = models.densenet121(weights=models.DenseNet121_Weights.IMAGENET1K_V1)
    return model


def build_model(n_class=N_CLASS, pretrained=True):
    m = models.densenet121(weights=None)
    if pretrained:
        load_imagenet_state(m)
    m.classifier = nn.Linear(m.classifier.in_features, n_class)
    return m


def bce_loss(logits, targets):
    return nn.functional.binary_cross_entropy_with_logits(logits, targets)


def focal_loss(logits, targets, gamma=2.0, alpha=0.25):
    bce = nn.functional.binary_cross_entropy_with_logits(logits, targets, reduction="none")
    pt = torch.exp(-bce)
    at = alpha * targets + (1.0 - alpha) * (1.0 - targets)
    return (at * (1.0 - pt) ** gamma * bce).mean()


# --------------------------------------------------------------------------
# metrics
# --------------------------------------------------------------------------
def per_class_auc(y_true, y_prob):
    """ROC-AUC per class; nan when a class has no positives."""
    from sklearn.metrics import roc_auc_score
    return np.array([
        roc_auc_score(y_true[:, c], y_prob[:, c]) if y_true[:, c].sum() > 0 else np.nan
        for c in range(N_CLASS)
    ])


def per_class_f1(y_true, y_pred):
    from sklearn.metrics import f1_score
    return np.array([
        f1_score(y_true[:, c], y_pred[:, c], zero_division=0) for c in range(N_CLASS)
    ])