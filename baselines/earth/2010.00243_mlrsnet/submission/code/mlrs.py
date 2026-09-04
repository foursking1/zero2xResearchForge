#!/usr/bin/env python3
"""mlrs.py -- shared utilities for the MLRSNet reproduction.

Contains:
  * dataset/loader (memmap-backed uint8 images)
  * model builders (pretrained ResNet18 / ViT-B-16 from LOCAL cache only,
    plus from-scratch DenseNet201 / VGG16 for the depth-control experiments)
  * multi-label metrics (per-class AP, mAP, macro/micro F1, precision/recall)
"""
import os
import random

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset
from torchvision import models, transforms

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
DATA_WORK = os.path.join(ROOT, "data_work")
PREDS = os.path.join(ROOT, "preds")
N_CLASS = 60


def decode_jpeg(b):
    """Decode one JPEG binary blob into a CHW uint8 ndarray (256x256x3 RGB)."""
    import io
    from PIL import Image
    try:
        img = Image.open(io.BytesIO(b)).convert("RGB")
        a = np.asarray(img, dtype=np.uint8)  # HWC
        if a.shape[:2] != (256, 256):
            img = img.resize((256, 256), Image.BILINEAR)
            a = np.asarray(img, dtype=np.uint8)
        return np.ascontiguousarray(a.transpose(2, 0, 1))
    except Exception:  # noqa: BLE001
        return None

# ----------------------------------------------------------------------------
# class names (mirrors data/README.md, index == label id)
# ----------------------------------------------------------------------------
CLASS_NAMES = [
    "airplane", "airport", "bare soil", "baseball diamond", "basketball court",
    "beach", "bridge", "buildings", "cars", "chaparral", "cloud", "containers",
    "crosswalk", "dense residential area", "desert", "dock", "factory", "field",
    "football field", "forest", "freeway", "golf course", "grass", "greenhouse",
    "gully", "habor", "intersection", "island", "lake", "mobile home",
    "mountain", "overpass", "park", "parking lot", "parkway", "pavement",
    "railway", "railway station", "river", "road", "roundabout", "runway",
    "sand", "sea", "ships", "snow", "snowberg", "sparse residential area",
    "stadium", "swimming pool", "tanks", "tennis court", "terrace", "track",
    "trail", "transmission tower", "trees", "water", "wetland", "wind turbine",
]

# ----------------------------------------------------------------------------
# dataset
# ----------------------------------------------------------------------------
class MLRSNetMemmap(Dataset):
    """uint8 CHW (N,3,256,256) memmap + int8 multi-hot target matrix."""

    def __init__(self, imgs_path, labels_path, transform=None, is_train=False):
        self.images = np.memmap(imgs_path, dtype=np.uint8, mode="r")
        self.n = self.images.shape[0] // (3 * 256 * 256)
        self.images = self.images.reshape(self.n, 3, 256, 256)
        self.labels = np.memmap(labels_path, dtype=np.int8, mode="r").reshape(self.n, N_CLASS)
        self.transform = transform
        self.is_train = is_train

    def __len__(self):
        return self.n

    def __getitem__(self, i):
        x = self.images[i]                      # (3,256,256) uint8
        x = torch.from_numpy(np.ascontiguousarray(x)).float().div_(255.0)
        if self.transform is not None:
            x = self.transform(x)
        y = torch.from_numpy(np.ascontiguousarray(self.labels[i])).float()
        return x, y

    @property
    def num_classes(self):
        return N_CLASS


def make_train_transform(img_size=256, pad=8):
    return transforms.Compose([
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.RandomCrop(img_size, padding=pad, padding_mode="reflect"),
        transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.1, hue=0.02),
    ])


def make_eval_transform():
    return None


# ----------------------------------------------------------------------------
# models
# ----------------------------------------------------------------------------
def build_model(name, pretrained=True, device="cpu"):
    """Return (nn.Module with 60-output sparse head, description string)."""
    if name == "resnet18":
        w = models.ResNet18_Weights.IMAGENET1K_V1 if pretrained else None
        m = models.resnet18(weights=w)
        m.fc = nn.Linear(m.fc.in_features, N_CLASS)
        src = "resnet18-f37072fd.pth (torchvision IMAGENET1K_V1, local cache)" if pretrained else "random init"
        desc = f"ResNet18 pretrained={pretrained} ({src})"
    elif name == "densenet201":
        w = models.DenseNet201_Weights.IMAGENET1K_V1 if pretrained else None
        m = models.densenet201(weights=w)
        m.classifier = nn.Linear(m.classifier.in_features, N_CLASS)
        src = "IMAGENET1K_V1" if pretrained else "random init"
        desc = f"DenseNet201 pretrained={pretrained} ({src})"
    elif name == "vgg16":
        w = models.VGG16_Weights.IMAGENET1K_V1 if pretrained else None
        m = models.vgg16(weights=w)
        m.classifier[6] = nn.Linear(4096, N_CLASS)
        src = "IMAGENET1K_V1" if pretrained else "random init"
        desc = f"VGG16 pretrained={pretrained} ({src})"
    elif name == "vit_b16":
        # torchvision ViT-B/16, weights cached locally (vit_b_16-c867db91.pth)
        w = models.ViT_B_16_Weights.IMAGENET1K_V1 if pretrained else None
        m = models.vit_b_16(weights=w)
        m.heads.head = nn.Linear(m.heads.head.in_features, N_CLASS)
        src = "vit_b_16-c867db91.pth (torchvision IMAGENET1K_V1, local cache)" if pretrained else "random init"
        desc = f"ViT-B/16 pretrained={pretrained} ({src})"
    else:
        raise ValueError(name)
    if device != "cpu":
        m.to(device)
    return m, desc


# ----------------------------------------------------------------------------
# metrics
# ----------------------------------------------------------------------------
def per_class_metrics(y_true, y_score, threshold=0.5, eps=1e-9):
    """y_true: (n,60) binary, y_score: (n,60) probabilities in [0,1].
    Returns dict per-class plus aggregate rows."""
    from sklearn.metrics import average_precision_score

    n, c = y_true.shape
    y_pred = (y_score >= threshold).astype(np.float32)
    cols = {}
    aps = []
    for k in range(c):
        tp = int((y_true[:, k] == 1) & (y_pred[:, k] == 1))
        fp = int((y_true[:, k] == 0) & (y_pred[:, k] == 1))
        fn = int((y_true[:, k] == 1) & (y_pred[:, k] == 0))
        pre = tp / (tp + fp + eps)
        rec = tp / (tp + fn + eps)
        f1 = 2 * pre * rec / (pre + rec + eps)
        try:
            ap = float(average_precision_score(y_true[:, k], y_score[:, k]))
        except ValueError as e:  # single class in y_true
            # retry with a tiny perturbation to still get a usable AP
            y2 = y_true[:, k].copy()
            if y2.max() == 0:
                ap = 0.0
            else:
                ap = float(average_precision_score(y2, y_score[:, k]))
        aps.append(ap)
        cols[k] = {
            "label": k,
            "class_name": CLASS_NAMES[k],
            "n_train_and_test": "see splits",
            "n_true_any": int(y_true[:, k].sum()),
            "n_correct": tp,
            "precision": round(pre, 4),
            "recall": round(rec, 4),
            "f1": round(f1, 4),
            "ap": round(ap, 4),
        }
    # aggregates
    tp_all = sum(cols[k]["n_correct"] for k in cols)
    n_positive = int(y_true.sum())
    n_pred_pos = int(y_pred.sum())
    micro_p = (tp_all + eps) / (n_pred_pos + eps)
    micro_r = (tp_all + eps) / (n_positive + eps)
    micro_f1 = 2 * micro_p * micro_r / (micro_p + micro_r + eps)
    macro_f1 = float(np.mean([cols[k]["f1"] for k in cols]))
    macro_p = float(np.mean([cols[k]["precision"] for k in cols]))
    macro_r = float(np.mean([cols[k]["recall"] for k in cols]))
    mAP = float(np.mean(aps))
    # per-image f1 (another commonly reported F1 in MLRSNet literature)
    img_tp = (y_true * y_pred).sum(1)
    img_fp = ((1 - y_true) * y_pred).sum(1)
    img_fn = (y_true * (1 - y_pred)).sum(1)
    img_pre = img_tp / (img_tp + img_fp + eps)
    img_rec = img_tp / (img_tp + img_fn + eps)
    img_f1 = 2 * img_pre * img_rec / (img_pre + img_rec + eps)
    agg = {
        "label": -1,
        "class_name": "ALL",
        "mAP": round(mAP, 4),
        "macro_f1": round(macro_f1, 4),
        "micro_f1": round(micro_f1, 4),
        "per_image_f1": round(float(img_f1.mean()), 4),
        "macro_precision": round(macro_p, 4),
        "macro_recall": round(macro_r, 4),
        "micro_precision": round(micro_p, 4),
        "micro_recall": round(micro_r, 4),
        "threshold": threshold,
        "n_test": n,
        "n_positive_total": n_positive,
    }
    return cols, agg


@torch.no_grad()
def predict(model, loader, device):
    model.eval()
    scores = []
    y = []
    for xb, yb in loader:
        xb = xb.to(device, non_blocking=True)
        out = model(xb)
        if isinstance(out, tuple):
            out = out[0]
        scores.append(out.float().cpu().numpy())
        y.append(yb.numpy())
    return np.concatenate(scores, 0), np.concatenate(y, 0)


def set_seed(seed=0):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


if __name__ == "__main__":
    print("mlrs.py loaded. N_CLASS =", N_CLASS)