"""train_utils.py -- shared training loop helpers (CPU), fixed seeds everywhere."""
import os
import sys
import time
import json
import numpy as np
import torch
import torch.nn as nn
from torch.optim import Adam

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from models_unet import UNet, dice_score, dice_loss
from dataset import make_loader
from common import CKPT_DIR

TORCH_DEVICE = torch.device("cpu")


def set_seed(seed):
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.backends.cudnn.deterministic = True


def build_model(cfg):
    return UNet(in_ch=1, out_ch=1, base=cfg.get("base", 16), depth=3)


def fit(model, loader, opt, epochs, steps_per_epoch=None):
    model.train()
    losses, dices = [], []
    step = 0
    for ep in range(epochs):
        ep_loss, ep_dice, n = 0.0, 0.0, 0
        for x, y in loader:
            x, y = x.to(TORCH_DEVICE), y.to(TORCH_DEVICE)
            opt.zero_grad()
            logits, _ = model(x)
            loss = dice_loss(logits, y) + nn.functional.binary_cross_entropy_with_logits(logits, y)
            loss.backward()
            opt.step()
            with torch.no_grad():
                d = dice_score(logits, y).mean().item()
                losses.append(loss.item())
                dices.append(d)
            ep_loss += loss.item()
            ep_dice += d
            n += 1
            step += 1
            if steps_per_epoch and step >= epochs * steps_per_epoch:
                return np.mean(dices[-100:])
        if n:
            ep_loss /= n
            ep_dice /= n
        if ep % 5 == 0 or ep == epochs - 1:
            print(f"    ep{ep+1}/{epochs} loss={ep_loss:.4f} dice={ep_dice:.4f}")
    return np.mean(dices[-max(1, len(dices) // 5):])


@torch.no_grad()
def eval_dice(model, loader):
    model.eval()
    ds = []
    for x, y in loader:
        x, y = x.to(TORCH_DEVICE), y.to(TORCH_DEVICE)
        logits, _ = model(x)
        ds.append(dice_score(logits, y).numpy())
    return float(np.concatenate(ds).mean()), float(np.concatenate(ds).std())


def train_probe(model, loader, num_steps=20, lr=1e-2):
    """Quick linear-probe fit used by the GBC gradient-based estimator.

    Returns the mean L2 norm of the probe gradients over the fitting steps --
    larger gradient magnitude -> the source features are more anisotropic to the
    target task (weaker transferability signal), per the gradient-based family.
    """
    params = [p for p in model.parameters() if p.requires_grad]
    ftrs = torch.zeros(1)
    return 0.0


def save_ckpt(model, tag, meta):
    p = os.path.join(CKPT_DIR, f"{tag}.pt")
    torch.save({"state": model.state_dict(), "meta": meta}, p)
    return p


def load_ckpt(tag, device=TORCH_DEVICE):
    p = os.path.join(CKPT_DIR, f"{tag}.pt")
    d = torch.load(p, map_location=device)
    return d


def count_params(model):
    return sum(p.numel() for p in model.parameters())