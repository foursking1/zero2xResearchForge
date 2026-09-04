"""Train a 2D multi-entity U-Net on the prepared slice dataset (CPU-friendly).

Usage:
    python train.py --name mcd_s0 --seed 0 --p-drop 0.3 --mc-dropout --epochs 25
    python train.py --name det_s2 --seed 2 --p-drop 0.0 --epochs 25
"""
import argparse
import json
import os
import time

import numpy as np
import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader, TensorDataset

from model import UNet2D

ENTITIES = ["ET", "TC", "WT"]


def set_seed(seed):
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def load_slices(cache_dir, split):
    z = np.load(os.path.join(cache_dir, "2d", f"{split}.npz"))
    return z["x"], z["y"]


def dice_score(pred_logits, target):
    """Mean Dice over channels for a batch. pred_logits: B x C x H x W."""
    p = (torch.sigmoid(pred_logits) > 0.5).float()
    t = target.float()
    inter = (p * t).sum(dim=(2, 3))
    denom = p.sum(dim=(2, 3)) + t.sum(dim=(2, 3))
    d = (2 * inter) / (denom + 1e-6)
    return d.mean(dim=0), d


def dice_loss(logits, target, eps=1.0):
    p = torch.sigmoid(logits)
    inter = (p * target).sum(dim=(2, 3))
    denom = p.sum(dim=(2, 3)) + target.sum(dim=(2, 3)) + eps
    return 1.0 - (2 * inter / denom).mean()


def train_model(name, seed, cache_dir, outdir, p_drop=0.3, mc_dropout=True,
                base_ch=16, levels=4, epochs=25, batch_size=16, lr=1e-3,
                device="cpu", patience=8, eval_every=2):
    set_seed(seed)
    X_tr, Y_tr = load_slices(cache_dir, "train")
    X_va, Y_va = load_slices(cache_dir, "val")

    ds = TensorDataset(torch.from_numpy(X_tr).permute(0, 3, 1, 2),
                       torch.from_numpy(Y_tr).float())
    dl = DataLoader(ds, batch_size=batch_size, shuffle=True, num_workers=0)
    dl_va = DataLoader(TensorDataset(torch.from_numpy(X_va).permute(0, 3, 1, 2),
                                     torch.from_numpy(Y_va).float()),
                       batch_size=64, num_workers=0)

    model = UNet2D(in_ch=1, out_ch=3, base_ch=base_ch, levels=levels,
                   p_drop=p_drop, mc_dropout=mc_dropout).to(device)
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=epochs)

    pos_frac = Y_tr.mean(axis=(0, 2, 3))  # per channel foreground fraction
    pos_weight = torch.tensor(((1 - pos_frac) / (pos_frac + 1e-6)),
                              dtype=torch.float32).view(1, -1, 1, 1)
    print(f"[{name}] n_train={len(ds)} pos_frac={np.round(pos_frac, 4)} pos_weight={np.round(pos_weight.numpy(), 2)}")

    best_va = -1.0
    patience_ct = 0
    history = []
    t0 = time.time()
    for ep in range(epochs):
        model.train()
        loss_acc, n = 0.0, 0
        for xb, yb in dl:
            if epoch_flip(xb, ep):  # stochastic horizontal flip
                xb = torch.flip(xb, dims=[3])
                yb = torch.flip(yb, dims=[3])
            xb, yb = xb.to(device), yb.to(device)
            logits = model(xb)
            loss = F.binary_cross_entropy_with_logits(
                logits, yb, pos_weight=pos_weight.to(device))
            loss = loss + 0.4 * dice_loss(logits, yb)
            opt.zero_grad()
            loss.backward()
            opt.step()
            loss_acc += loss.item() * len(xb)
            n += len(xb)
        sched.step()

        # validation (every eval_every epochs)
        if (ep + 1) % eval_every == 0:
            model.eval()
            val_d = torch.zeros(3, device=device)
            with torch.no_grad():
                for xb, yb in dl_va:
                    xb, yb = xb.to(device), yb.to(device)
                    logits = model(xb)
                    d, _ = dice_score(logits, yb)
                    val_d += d * len(xb)
                val_d /= len(dl_va.dataset)
        else:
            val_d = None
        hist = {"epoch": ep + 1, "train_loss": loss_acc / n,
                "val_dice": ([float(v) for v in val_d] if val_d is not None else None),
                "val_dice_mean": (float(val_d.mean()) if val_d is not None else float("nan")),
                "elapsed_s": round(time.time() - t0, 1)}
        history.append(hist)
        if val_d is not None and val_d.mean() > best_va:
            best_va = val_d.mean()
            torch.save({"state_dict": model.state_dict(), "config": {
                "name": name, "seed": seed, "p_drop": p_drop,
                "mc_dropout": mc_dropout, "base_ch": base_ch, "levels": levels},
                "history": history}, os.path.join(outdir, f"{name}.pt"))
            patience_ct = 0
        else:
            if val_d is not None:
                patience_ct += 1
        if ep % 5 == 0 or patience_ct == 0:  # (val_d is None or val_d.mean() == best_va)
            print(f"[{name}] ep {ep + 1}/{epochs} loss={loss_acc / n:.4f} "
                  f"val_dice={np.round(val_d.cpu().numpy(), 4) if val_d is not None else None} "
                  f"best={best_va:.4f} ({time.time() - t0:.0f}s)")
        if patience_ct >= patience:
            print(f"[{name}] early stop at ep {ep + 1}")
            break
    return best_va


def epoch_flip(xb, ep):
    return (ep + np.random.randint(0, 2)) % 2 == 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--p-drop", type=float, default=0.3)
    ap.add_argument("--mc-dropout", action="store_true")
    ap.add_argument("--base-ch", type=int, default=16)
    ap.add_argument("--epochs", type=int, default=25)
    ap.add_argument("--batch-size", type=int, default=16)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--cache", default=os.path.join(os.path.dirname(__file__), "..", "data_cache"))
    ap.add_argument("--outdir", default=os.path.join(os.path.dirname(__file__), "..", "models"))
    ap.add_argument("--device", default="cpu")
    args = ap.parse_args()
    os.makedirs(args.outdir, exist_ok=True)
    torch.set_num_threads(max(1, torch.get_num_threads()))
    best = train_model(args.name, args.seed, args.cache, args.outdir,
                       p_drop=args.p_drop, mc_dropout=args.mc_dropout,
                       base_ch=args.base_ch, epochs=args.epochs,
                       batch_size=args.batch_size, lr=args.lr, device=args.device)
    print(f"[{args.name}] done, best_val_dice={best:.4f}")


if __name__ == "__main__":
    main()