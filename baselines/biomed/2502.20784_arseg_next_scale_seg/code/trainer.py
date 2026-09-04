"""Generic training helpers (binary = LIDC, multi-class = BraTS)."""
from __future__ import annotations
import os, time
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader


class ArrayDataset(Dataset):
    def __init__(self, x, y):
        self.x = torch.from_numpy(x).float()
        self.y = torch.from_numpy(y).float() if y is not None else None

    def __len__(self):
        return len(self.x)

    def __getitem__(self, i):
        return self.x[i], self.y[i]


def multichannel_load(x1d):
    return x1d.unsqueeze(1)


def make_loader(x, y, batch_size, shuffle, num_workers=2):
    ds = ArrayDataset(x, y)
    return DataLoader(ds, batch_size=batch_size, shuffle=shuffle, num_workers=num_workers,
                      pin_memory=False, drop_last=False)


def dice_coef(probs, target, eps=1e-6):
    num = (probs * target).sum((1, 2, 3)) * 2 + eps
    den = probs.sum((1, 2, 3)) + target.sum((1, 2, 3)) + eps
    return (num / den)


def train_binary_epoch(model, loader, opt, device, arstyle=False, coarse_weight=0.3):
    model.train()
    total = 0.0
    n = 0
    for x, y in loader:
        x = x.to(device).unsqueeze(1)
        y = y.to(device).unsqueeze(1)
        opt.zero_grad()
        if arstyle:
            logits_f, logits_m, logits_c = model(x)
            y_4 = F.interpolate(y, size=logits_c.shape[-2:], mode="nearest")
            y_2 = F.interpolate(y, size=logits_m.shape[-2:], mode="nearest")
            # balance: smallest scale weight, mid weight, fine weight 1
            l_f = dice_bce(logits_f, y)
            l_m = dice_bce(logits_m, y_2) * coarse_weight
            l_c = dice_bce(logits_c, y_4) * coarse_weight
            loss = l_f + l_m + l_c
        else:
            logits = model(x)
            loss = dice_bce(logits, y)
        loss.backward()
        opt.step()
        total += float(loss.detach())
        n += 1
    return total / n


def dice_bce(logits, target, reduction="mean"):
    probs = torch.sigmoid(logits)
    eps = 1e-6
    num = (probs * target).sum(dim=(2, 3)) * 2 + eps
    den = probs.sum(dim=(2, 3)) + target.sum(dim=(2, 3)) + eps
    d = (num / den).mean()
    bce = F.binary_cross_entropy_with_logits(logits, target)
    return (1 - d) + bce


@torch.no_grad()
def eval_binary(model, x, y, device, batch_size=256, arstyle=False, n_samples=1):
    """Returns (per-sample soft dice, hard dice, iou) over slices."""
    model.eval()
    sd, hd, iou = [], [], []
    for i in range(0, len(x), batch_size):
        xi = torch.from_numpy(x[i:i + batch_size]).to(device).unsqueeze(1)
        yi = y[i:i + batch_size]
        if n_samples > 1 and hasattr(model, "sample"):
            p = model.sample(xi, K=n_samples)
        else:
            if arstyle:
                p = torch.sigmoid(model.forward_single(xi))
            else:
                p = torch.sigmoid(model(xi))
        p = p.detach().cpu().numpy()[:, 0]
        for a, b in zip(p, yi):
            sd.append(soft_dice(a, b))
            hd.append(hard_dice(a, b))
            iou.append(_iou(a, b))
    return np.mean(sd), np.mean(hd), np.mean(iou), sd, hd, iou


def soft_dice(p, y, eps=1e-6):
    p = p.ravel().astype(np.float32)
    y = y.ravel().astype(np.float32)
    return float(2 * np.sum(p * y) / (np.sum(p) + np.sum(y) + eps))


def hard_dice(p, y):
    return soft_dice((p > 0.5).astype(np.float32), y)


def _iou(p, y, eps=1e-6):
    p = (p > 0.5).astype(np.float32).ravel()
    y = y.ravel().astype(np.float32)
    inter = np.sum(p * y)
    return float(inter / (np.sum(p) + np.sum(y) - inter + eps))


def train_multiclass_epoch(model, loader, opt, device, arstyle=False, coarse_weight=0.3, n_classes=4):
    model.train()
    total = 0.0
    n = 0
    for x, y in loader:
        x = x.to(device).unsqueeze(1)
        y = y.to(device).long()
        opt.zero_grad()
        if arstyle:
            logits_f, logits_m, logits_c = model(x)
            loss = ce_dice(logits_f, y, n_classes)
            yf = y.float().unsqueeze(1)
            y_2 = F.interpolate(yf, size=logits_m.shape[-2:], mode="nearest").long()[:, 0]
            y_4 = F.interpolate(yf, size=logits_c.shape[-2:], mode="nearest").long()[:, 0]
            loss = loss + coarse_weight * ce_dice(logits_m, y_2, n_classes) \
                         + coarse_weight * ce_dice(logits_c, y_4, n_classes)
        else:
            logits = model(x)
            loss = ce_dice(logits, y, n_classes)
        loss.backward()
        opt.step()
        total += float(loss.detach())
        n += 1
    return total / n


def ce_dice(logits, target, n_classes, class_weights=None):
    """Focal-free CE + multiclass soft-Dice (WT/TC/ET surrogate coding: map {BG=0,NEC=1,ED=2,ET=3})."""
    b, c, h, w = logits.shape
    ce = F.cross_entropy(logits, target, weight=class_weights)
    probs = F.softmax(logits, dim=1)                    # (B,C,H,W)
    onehot = F.one_hot(target, num_classes=c).permute(0, 3, 1, 2).float()
    inter = (probs * onehot).sum((2, 3)) * 2 + 1e-6
    union = probs.sum((2, 3)) + onehot.sum((2, 3)) + 1e-6
    d = (inter / union).mean()                          # macro over classes & batch
    return ce + (1 - d)


@torch.no_grad()
def eval_multiclass(model, x, y, device, batch_size=64, n_samples=1, arstyle=False, K=8):
    """Global-pooled region Dice (ET=class{3}, TC={1,3}, WT={1,2,3}).

    Returns per-region global Dice + per-slice lists for patient-level pooling.
    """
    model.eval()
    preds = []
    for i in range(0, len(x), batch_size):
        xi = torch.from_numpy(x[i:i + batch_size]).to(device).unsqueeze(1)
        if n_samples > 1 and hasattr(model, "sample"):
            was = model.training
            model.train()
            ps = []
            with torch.no_grad():
                for _ in range(K):
                    if hasattr(model, "forward_single"):
                        lg = model.forward_single(xi)
                    else:
                        lg = model(xi)
                    ps.append(F.softmax(lg, dim=1))
            model.train(was)
            p = torch.stack(ps).mean(0)
        else:
            if arstyle:
                p = torch.softmax(model.forward_single(xi), dim=1)
            else:
                p = torch.softmax(model(xi), dim=1)
        preds.append(p.detach().cpu().numpy())
    preds = np.concatenate(preds, 0)                  # (N,C,H,W)
    cl = np.argmax(preds, axis=1)
    dice = {"et": [], "tc": [], "wt": []}
    for j in range(len(y)):
        seg = y[j].astype(np.int16)
        dice["et"].append(_dice_region(cl[j] == 3, seg == 3))
        dice["tc"].append(_dice_region(np.isin(cl[j], [1, 3]), np.isin(seg, [1, 3])))
        dice["wt"].append(_dice_region(cl[j] > 0, seg > 0))
    pooled = {k: float(np.mean(v)) for k, v in dice.items()}
    return pooled, dice         # pooled + per-slice Dice


def _dice_region(pred, ref, eps=1e-6):
    pred = pred.ravel().astype(np.float32)
    ref = ref.ravel().astype(np.float32)
    return float(2 * np.sum(pred * ref) / (np.sum(pred) + np.sum(ref) + eps))