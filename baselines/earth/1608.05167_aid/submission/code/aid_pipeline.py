"""Fix the orientation ambiguity: AID_MultiLabel mirror has 17 classes and 3000
images; the paper's single-label AID has 30 classes / 10000 images.

Task data slightly differs from the paper. We do (a) multi-label 17-class
classification on the frozen parquet, and (b) single-label 30-class
classification on the original AID image folders for direct OA comparison.
"""
import argparse
import hashlib
import io
import os
import random

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from PIL import Image

from aid_common import (
    CLASS_NAMES_17,
    CLASS_NAMES_30,
    AID_30_ROOT,
    AID_30_SPLIT_CSV,
    FROZEN_PARQUET,
    N_CLASSES_17,
    N_CLASSES_30,
    SEED,
)


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_frozen_parquet(path=FROZEN_PARQUET):
    """Expected checksum recorded in the frozen package manifest."""
    expected = "87AC8EE463927CE5B5E491F9259D8701906C2F967609E6665648D972AB334485"
    actual = sha256_of(path).upper()
    if actual != expected:
        raise RuntimeError(
            f"parquet checksum mismatch: got {actual}, expected {expected}"
        )
    return actual


def load_multilabel(path=FROZEN_PARQUET, verify=True):
    if verify:
        verify_frozen_parquet(path)
    df = pd.read_parquet(path)
    images = np.empty(len(df), dtype=object)
    labels = np.zeros((len(df), N_CLASSES_17), dtype=np.float32)
    for i, row in enumerate(df.itertuples(index=False)):
        images[i] = row.image["bytes"]
        for lbl in row.label:
            labels[i, int(lbl)] = 1.0
    return images, labels


def load_singlelabel(root=AID_30_ROOT, csv_path=AID_30_SPLIT_CSV):
    """Load original AID 30-class images using the frozen fixed 50/50 split."""
    df = pd.read_csv(csv_path)
    assert len(df) == 10000
    files, y = [], []
    for _, r in df.iterrows():
        rel = r["file"].replace("\\", "/")
        files.append(os.path.join(root, rel))
        y.append(CLASS_NAMES_30.index(r["class"]))
    y = np.asarray(y, dtype=np.int64)
    split = df["split"].values
    return files, y, split


def split_isotropic(images, labels, seed=SEED, val_frac=0.2, test_frac=0.2):
    """Fixed-seed 60/20/20 random split of multi-label rows."""
    rng = np.random.default_rng(seed)
    n = len(images)
    perm = rng.permutation(n)
    n_val = int(round(n * val_frac))
    n_test = int(round(n * test_frac))
    n_train = n - n_val - n_test
    return {
        "train": perm[:n_train],
        "val": perm[n_train : n_train + n_val],
        "test": perm[n_train + n_val :],
    }


def set_seed(seed=SEED):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


_pil_transform = None


def get_transform(split, size=224):
    from torchvision import transforms

    if split == "train":
        return transforms.Compose(
            [
                transforms.Resize((size, size)),
                transforms.RandomHorizontalFlip(),
                transforms.RandomRotation(15),
                transforms.ColorJitter(
                    brightness=0.2, contrast=0.2, saturation=0.2
                ),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]
                ),
            ]
        )
    return transforms.Compose(
        [
            transforms.Resize((size, size)),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]
            ),
        ]
    )


class ParquetMultilabelDataset(torch.utils.data.Dataset):
    def __init__(self, images_bytes, labels, indices, split="train", size=224):
        self.images = images_bytes
        self.labels = labels
        self.indices = indices
        self.transform = get_transform(split, size=size)

    def __len__(self):
        return len(self.indices)

    def __getitem__(self, i):
        idx = self.indices[i]
        raw = self.images[idx]
        img = Image.open(io.BytesIO(raw)).convert("RGB")
        img = img.resize((256, 256), Image.BILINEAR)
        x = self.transform(img)
        y = torch.as_tensor(self.labels[idx], dtype=torch.float32)
        return x, y


class SingleLabelDataset(torch.utils.data.Dataset):
    def __init__(self, files, y, indices, split="train", size=224):
        self.files = files
        self.y = y
        self.indices = indices
        self.transform = get_transform(split, size=size)

    def __len__(self):
        return len(self.indices)

    def __getitem__(self, i):
        idx = self.indices[i]
        img = Image.open(self.files[idx]).convert("RGB")
        img = img.resize((256, 256), Image.BILINEAR)
        x = self.transform(img)
        return x, int(self.y[idx])


def make_model_multilabel(backbone="resnet18", n_classes=N_CLASSES_17):
    from torchvision import models

    weights_path = os.path.expanduser(
        "~/.cache/torch/hub/checkpoints/resnet18-f37072fd.pth"
    )
    model = models.resnet18(weights=None)
    if os.path.exists(weights_path):
        state = torch.load(weights_path, map_location="cpu")
        model.load_state_dict(state)
    in_f = model.fc.in_features
    model.fc = nn.Linear(in_f, n_classes)
    return model


def make_model_singlelabel_like_googlenet(backbone="resnet18", n_classes=N_CLASSES_30):
    from torchvision import models

    weights_path = os.path.expanduser(
        "~/.cache/torch/hub/checkpoints/resnet18-f37072fd.pth"
    )
    model = models.resnet18(weights=None)
    if os.path.exists(weights_path):
        state = torch.load(weights_path, map_location="cpu")
        model.load_state_dict(state)
    in_f = model.fc.in_features
    model.fc = nn.Linear(in_f, n_classes)
    return model


def average_precision_per_class(y_true, scores):
    """Per-class AP using sklearn (already installed)."""
    from sklearn.metrics import average_precision_score

    return [
        average_precision_score(y_true[:, c], scores[:, c])
        for c in range(y_true.shape[1])
    ]