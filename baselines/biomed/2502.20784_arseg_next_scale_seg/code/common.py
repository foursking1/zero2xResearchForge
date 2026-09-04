"""Shared components: data utilities, models (baseline U-Net + AR-style), losses, metrics.

AR-Seg (arXiv:2502.20784) simplified 2D approximation
=======================================================
The full AR-Seg autoregressively predicts *tokenized* binary masks from coarse to fine
(next-scale mask prediction), sampling stochastic masks and then averaging them via
*consensus aggregation*.  In this frozen-data, CPU-only setting we approximate the
mechanism with:

  * a shared U-Net encoder + multi-scale decoder heads (deep supervision at 1/4, 1/2, 1),
    i.e. *multi-scale mask prediction*;
  * an explicit *next-scale conditioning* path: the coarse (1/4) mask prediction is
    upsampled and concatenated into the refinement decoder that produces the fine (1) mask,
    i.e. predicting the finer scale *conditioned on* the coarser prediction
    ("next-scale mask prediction");
  * a *consensus aggregation* approximation at inference: K stochastic forward passes
    (MC-dropout) are averaged to a consensus probability map.

The baseline model is a plain single-scale U-Net with the same encoder/decoder backbone
minus the multi-scale heads and the coarse-to-fine conditioning.
"""
from __future__ import annotations
import os
import json
import hashlib
import time
from dataclasses import dataclass, asdict
from typing import Optional, Dict, List, Tuple

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

torch.set_num_threads(max(4, os.cpu_count() or 4))

SEED = 0
DEVICE = os.environ.get("ARSEG_DEVICE", "cpu")

# ----------------------------------------------------------------------------- file hashing
def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb", 65536) as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest().upper()

# ----------------------------------------------------------------------------- metrics
def soft_dice(p: np.ndarray, y: np.ndarray, eps: float = 1e-6) -> float:
    """Soft Dice between a soft probability map p and binary reference y (0..1)."""
    p = np.asarray(p, np.float32).ravel()
    y = np.asarray(y, np.float32).ravel()
    return float(2.0 * np.sum(p * y) / (np.sum(p) + np.sum(y) + eps))


def hard_dice(p: np.ndarray, y: np.ndarray) -> float:
    return soft_dice((p > 0.5).astype(np.float32), y)


def iou(p: np.ndarray, y: np.ndarray, eps: float = 1e-6) -> float:
    p = ((np.asarray(p) > 0.5).astype(np.float32)).ravel()
    y = np.asarray(y, np.float32).ravel()
    inter = np.sum(p * y)
    union = np.sum(p) + np.sum(y) - inter
    return float(inter / (union + eps))


def region_dice_from_logits(logits: np.ndarray, label_map: np.ndarray, regions: Dict[str, Tuple[int, ...]]) -> Dict[str, float]:
    """logits: (H,W) softmax probs per voxel for 4 classes [BG, NEC, ED, ET] or a class-prob map.

    label_map: integer map with original BraTS labels {0,1,2,4}.
    Returns Dice per region {wt,tc,et}.
    """
    cls = np.argmax(np.asarray(logits), axis=-1)  # 0..3  (order must be constructed accordingly)
    out = {}
    for name, codes in regions.items():
        ref = np.isin(label_map, codes).astype(np.float32)
        mask = cls == regions_idx[name]
        out[name] = hard_dice(mask.astype(np.float32), ref)
    return out


regions_idx = {"wt": 3, "tc": 2, "et": 0}   # class index in the 4-class output for each region


def per_region_dice(pred_probs3: np.ndarray, label_map: np.ndarray, orig: bool = False):
    """pred_probs3: (H,W,3) probabilities for [ET, TC, WT];
       label_map: original BraTS {0,1,2,4}.
    """
    p = np.asarray(pred_probs3)
    ref = {"et": (label_map == 4), "tc": np.isin(label_map, [1, 4]), "wt": label_map > 0}
    d = {}
    for k, m in ref.items():
        idx = {"et": 0, "tc": 1, "wt": 2}[k]
        pk = p[..., idx]
        d[k] = soft_dice(pk, m.astype(np.float32))
    return d


# ----------------------------------------------------------------------------- loss
def dice_bce_loss(logits: torch.Tensor, target: torch.Tensor, pos_weight: Optional[float] = None) -> torch.Tensor:
    """Binary Dice + BCE. logits (B,1,H,W), target (B,1,H,W) float in {0,1}."""
    probs = torch.sigmoid(logits)
    num = (probs * target).sum(dim=(2, 3)) * 2 + 1e-6
    den = probs.sum(dim=(2, 3)) + target.sum(dim=(2, 3)) + 1e-6
    dice = 1.0 - (num / den).mean()
    bce = F.binary_cross_entropy_with_logits(logits, target, pos_weight=torch.tensor(pos_weight, device=logits.device) if pos_weight else None)
    return dice + bce


# ----------------------------------------------------------------------------- models
class DoubleConv(nn.Module):
    def __init__(self, cin, cout):
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv2d(cin, cout, 3, padding=1, bias=False), nn.GroupNorm(8, cout), nn.ReLU(inplace=True),
            nn.Conv2d(cout, cout, 3, padding=1, bias=False), nn.GroupNorm(8, cout), nn.ReLU(inplace=True),
        )

    def forward(self, x):
        return self.net(x)


class Encoder(nn.Module):
    def __init__(self, chs, in_ch=1):
        super().__init__()
        lv = [in_ch] + list(chs)
        self.stages = nn.ModuleList()
        self.pools = nn.ModuleList()
        for i in range(len(lv) - 2):
            self.stages.append(DoubleConv(lv[i], lv[i + 1]))
            self.pools.append(nn.MaxPool2d(2))
        self.stages.append(DoubleConv(lv[-2], lv[-1]))  # bottleneck stage (input res 1/2^(len-2))
        self.chs = chs

    def forward(self, x):
        feats = []
        for i in range(len(self.stages) - 1):
            x = self.stages[i](x)
            feats.append(x)
            x = self.pools[i](x)
        x = self.stages[-1](x)
        feats.append(x)          # bottleneck at 1/(2^(len-2))
        return feats


class UNetBaseline(nn.Module):
    """Plain single-scale U-Net (baseline)."""

    def __init__(self, in_ch=1, chs=(64, 128, 256, 384), out_ch=1, dropout=0.1):
        super().__init__()
        self.encoder = Encoder(chs)
        self.up3 = nn.ConvTranspose2d(chs[-1], chs[-2], 2, stride=2)
        self.dec3 = DoubleConv(chs[-2] + chs[-2], chs[-2])
        self.up2 = nn.ConvTranspose2d(chs[-2], chs[-3], 2, stride=2)
        self.dec2 = DoubleConv(chs[-3] + chs[-3], chs[-3])
        self.up1 = nn.ConvTranspose2d(chs[-3], chs[-4], 2, stride=2)
        self.dec1 = DoubleConv(chs[-4] + chs[-4], chs[-4])
        self.head = nn.Conv2d(chs[-4], out_ch, 1)
        self.drop = nn.Dropout2d(dropout)

    def forward(self, x):
        f = self.encoder(x)
        x = self.up3(f[-1])
        x = torch.cat([x, f[-2]], dim=1)
        x = self.dec3(x)
        x = self.up2(x)
        x = torch.cat([x, f[-3]], dim=1)
        x = self.dec2(x)
        x = self.up1(x)
        x = torch.cat([x, f[-4]], dim=1)
        x = self.dec1(x)
        return self.head(x)

    def sample(self, x, K=1):
        """MC-dropout consensus (used for comparison with AR-style consensus)."""
        was_train = self.training
        self.train()
        probs = []
        with torch.no_grad():
            for _ in range(K):
                lg = self.forward(x)
                probs.append(torch.sigmoid(lg))
        self.train(was_train)
        return torch.stack(probs).mean(0)


class ArSegUNet(nn.Module):
    """AR-style approximation: multi-scale mask heads + next-scale (coarse->fine) conditioning.

    Cross-scale dependency is explicit: the fine-scale head receives the *coarse mask
    prediction* (upsampled to full res and concatenated) as conditioning, and deep
    supervision supervises every predicted scale.  MC-dropout on the refinement block
    enables the *consensus aggregation* approximation (K stochastic samples averaged).
    """

    def __init__(self, in_ch=1, chs=(64, 128, 256, 384), out_ch=1, dropout=0.3):
        super().__init__()
        depth = len(chs)          # 4 -> scales: 1/4 (coarse head), 1/2, 1 (fine head)
        self.encoder = Encoder(chs)
        self.depth = depth
        # coarse head at 1/2^{depth-2} resolution (1/4)
        self.coarse_head = nn.Conv2d(chs[-2], out_ch, 1)
        # mid (aux) head at 1/2 resolution
        self.mid_head = nn.Conv2d(chs[-3], out_ch, 1)
        # decode path
        self.up3 = nn.ConvTranspose2d(chs[-1], chs[-2], 2, stride=2)
        self.dec3 = DoubleConv(chs[-2] + chs[-2], chs[-2])   # 1/4 res (coarse feature)
        self.up2 = nn.ConvTranspose2d(chs[-2], chs[-3], 2, stride=2)
        self.dec2 = DoubleConv(chs[-3] + chs[-3], chs[-3])   # 1/2 res
        self.up1 = nn.ConvTranspose2d(chs[-3], chs[-4], 2, stride=2)
        self.dec1 = DoubleConv(chs[-4] + chs[-4], chs[-4])   # 1 res
        # next-scale conditioning: fuse coarse prediction into fine decoder
        self.refine_fuse = nn.Sequential(
            nn.Conv2d(chs[-4] + out_ch, chs[-4], 3, padding=1, bias=False),
            nn.GroupNorm(8, chs[-4]), nn.ReLU(inplace=True),
        )
        self.head = nn.Conv2d(chs[-4], out_ch, 1)
        self.drop = nn.Dropout2d(dropout)
        self.ablate_coarse = False   # if True, next-scale conditioning is ablated (constant 0.5)

    def forward(self, x):
        """multi-scale supervised forward: returns {'coarse', 'mid', 'fine'} logits."""
        f = self.encoder(x)
        c3 = self.up3(f[-1])
        c3 = torch.cat([c3, f[-2]], dim=1)
        c3 = self.dec3(c3)
        logits_c = self.coarse_head(c3)                     # 1/4 res

        c2 = self.up2(c3)
        c2 = torch.cat([c2, f[-3]], dim=1)
        c2 = self.dec2(c2)
        logits_m = self.mid_head(c2)                        # 1/2 res (aux deep supervision)

        c1 = self.up1(c2)
        c1 = torch.cat([c1, f[-4]], dim=1)
        c1 = self.dec1(c1)
        # explicit next-scale conditioning: coarse mask prediction conditions the fine head
        coarse_up = F.interpolate(torch.sigmoid(logits_c), size=c1.shape[-2:], mode="bilinear", align_corners=False)
        if self.ablate_coarse:
            coarse_up = torch.full_like(coarse_up, 0.5)
        c1 = self.refine_fuse(torch.cat([c1, coarse_up], dim=1))
        logits_f = self.head(self.drop(c1))                 # fine, 1 res

        return logits_f, logits_m, logits_c

    def sample(self, x, K=1):
        """Consensus aggregation approximation: K stochastic passes (MC-dropout) -> averaged probs."""
        was_train = self.training
        self.train()  # enable dropout for stochastic sampling
        probs = []
        with torch.no_grad():
            for _ in range(K):
                logits_f, _, _ = self.forward(x)
                probs.append(torch.sigmoid(logits_f))
        self.train(was_train)
        return torch.stack(probs).mean(0)   # (B,1,H,W) consensus

    def forward_single(self, x):
        """deterministic single-pass fine logits (for 'no consensus' baseline comparison)."""
        logits_f, _, _ = self.forward(x)
        return logits_f


# ----------------------------------------------------------------------------- training helpers
@dataclass
class TrainResult:
    model_name: str
    dataset: str
    epochs: int
    train_samples: int
    val_samples: int
    test_samples: int
    train_time_s: float
    best_val_epoch: int
    test_soft_dice: Optional[float] = None
    test_hard_dice: Optional[float] = None
    test_iou: Optional[float] = None
    test_dice_et: Optional[float] = None
    test_dice_tc: Optional[float] = None
    test_dice_wt: Optional[float] = None
    test_mean_region_dice: Optional[float] = None
    extra: Optional[dict] = None

    def to_dict(self):
        d = asdict(self)
        return d

    def save(self, path: str):
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)


def predict_loop(model, loader, device, sigmoid=True, n_samples=1):
    """Predict on a DataLoader. n_samples>1 -> MC-dropout consensus averaging."""
    y_preds = []
    metas = []
    model.eval()
    with torch.no_grad():
        for batch in loader:
            x = batch["x"].to(device)
            if n_samples > 1 and hasattr(model, "sample"):
                p = model.sample(x, K=n_samples)
            else:
                lg = model(x)
                if isinstance(lg, (tuple, list)):   # multi-scale AR-style model returns tuple
                    lg = lg[0]
                p = torch.sigmoid(lg) if sigmoid else lg
            y_preds.append(p.detach().cpu().numpy())
            metas.append(batch["meta"])
    y_preds = np.concatenate(y_preds, axis=0)
    metas = {k: np.concatenate([b[k] for b in metas], axis=0) for k in metas[0].keys()}
    return y_preds, metas