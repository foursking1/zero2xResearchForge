"""Train a compact CNN on frozen EuroSAT RGB data (CPU-first).

Design:
  - Input: 64x64 RGB uint8 decoded from frozen parquet (cached by 01_prepare_data.py).
  - Architecture: compact VGG-style block net (~1.9M params) suited to 64x64 patches.
  - Augmentation: random crop to 60 -> resize to 64, random horizontal flip,
    light color jitter + rotation. Statistics (mean/std) computed on TRAIN ONLY.
  - Optimizer: SGD(momentum 0.9, wd 5e-4), batch 256, cosine LR decay, 40 epochs.
  - Protocol: hyperparameters frozen a priori; validation used for monitoring only;
    the reported test metrics come from the final, fixed-schedule checkpoint.

Usage:
    python 02_train.py [--epochs 40] [--batch 256] [--seed 0] [--threads 12]
                       [--cache-dir ../cache] [--outdir ../artifacts]
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _models import make_model, count_params, CLASS_NAMES


class TrainAug:
    def __init__(self, p=0.5):
        self.p = p

    def __call__(self, x):
        # x: uint8 (N,3,64,64)
        x = x.float().div_(255.0)
        if self.p > 0:
            if torch.rand(1).item() < 0.5:
                x = torch.flip(x, dims=[3])
            if torch.rand(1).item() < 0.9:
                pad = 4
                x = F.pad(x, (pad, pad, pad, pad))
                top = int(torch.randint(0, 2 * pad + 1, (1,)).item())
                left = int(torch.randint(0, 2 * pad + 1, (1,)).item())
                x = x[:, :, top:top + 64, left:left + 64]
            if torch.rand(1).item() < 0.5:
                b = (torch.rand(1).item() - 0.5) * 0.3
                s = 1.0 + (torch.rand(1).item() - 0.5) * 0.5
                x = x * s + b
        return x


@torch.no_grad()
def evaluate(model, x, y, bs, mean=None, std=None, tta=False):
    model.eval()
    preds = []
    probs = []
    for i in range(0, len(x), bs):
        xb = x[i:i + bs].float().div_(255.0)
        if mean is not None:
            xb = (xb - mean) / std
        outputs = [F.softmax(model(xb), dim=1)]
        if tta:
            outputs.append(F.softmax(model(torch.flip(xb, dims=[3])), dim=1))
        prob = torch.stack(outputs).mean(0)
        probs.append(prob)
        preds.append(prob.argmax(1))
    pred = torch.cat(preds).numpy()
    return (pred == y.numpy()).mean(), pred


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=int, default=40)
    ap.add_argument("--batch", type=int, default=256)
    ap.add_argument("--lr", type=float, default=0.1)
    ap.add_argument("--wd", type=float, default=5e-4)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--threads", type=int, default=12)
    ap.add_argument("--cache-dir", default=os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "cache"))
    ap.add_argument("--outdir", default=os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "artifacts"))
    args = ap.parse_args()

    torch.set_num_threads(args.threads)
    torch.manual_seed(args.seed)
    np.random.seed(args.seed)

    cache = Path(args.cache_dir)
    tr = np.load(cache / "train.npz")
    va = np.load(cache / "validation.npz")

    Xtr = torch.from_numpy(tr["images"]).permute(0, 3, 1, 2)
    ytr = torch.from_numpy(tr["labels"]).long()
    Xva = torch.from_numpy(va["images"]).permute(0, 3, 1, 2)
    yva = torch.from_numpy(va["labels"]).long()

    # train-only statistics
    mean = Xtr.float().mean(dim=(0, 2, 3), keepdim=True) / 255.0
    std = Xtr.float().std(dim=(0, 2, 3), keepdim=True) / 255.0
    print("train stats mean", mean.squeeze().numpy().round(4), "std", std.squeeze().numpy().round(4))

    aug = TrainAug()

    model = make_model().to(memory_format=torch.channels_last)
    # warm start collect
    
    print(f"model params: {count_params(model):,d}")
    opt = torch.optim.SGD(model.parameters(), lr=args.lr, momentum=0.9, weight_decay=args.wd)

    def schedule(e):
        return 0.5 * (1 + np.cos(np.pi * e / args.epochs))  # cosine

    steps_per_epoch = int(np.ceil(len(Xtr) / args.batch))
    n_batches = args.epochs * steps_per_epoch
    history = {"train_acc": [], "train_loss": [], "val_acc": [], "epoch_time": []}
    best_val = -1.0

    start = time.time()
    for ep in range(args.epochs):
        model.train()
        lr = args.lr * schedule(ep)
        for g in opt.param_groups:
            g["lr"] = lr
        perm = torch.randperm(len(Xtr))
        tot_loss = 0.0
        tot_cor = 0
        t0 = time.time()
        for b in range(steps_per_epoch):
            idx = perm[b * args.batch:(b + 1) * args.batch]
            xb = Xtr[idx]
            yb = ytr[idx]
            xb = aug(xb)
            if mean.device != xb.device:
                mean = mean.to(xb.device); std = std.to(xb.device)
            xb = (xb - mean) / std
            xb = xb.to(memory_format=torch.channels_last)
            logits = model(xb)
            loss = F.cross_entropy(logits, yb, label_smoothing=0.05)
            opt.zero_grad()
            loss.backward()
            opt.step()
            tot_loss += loss.item() * len(yb)
            tot_cor += (logits.argmax(1) == yb).sum().item()
        tr_acc = tot_cor / len(Xtr)
        tr_loss = tot_loss / len(Xtr)
        va_acc, _ = evaluate(model, Xva, yva, args.batch, mean=mean, std=std)
        history["train_acc"].append(tr_acc)
        history["train_loss"].append(tr_loss)
        history["val_acc"].append(va_acc)
        history["epoch_time"].append(time.time() - t0)
        if va_acc > best_val:
            best_val = va_acc
        print(f"ep {ep+1}/{args.epochs} lr={lr:.4f} tr_acc={tr_acc:.4f} "
              f"tr_loss={tr_loss:.4f} val_acc={va_acc:.4f} "
              f"{time.time()-t0:.1f}s", flush=True)

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    torch.save({"state_dict": model.state_dict(), "mean": mean.squeeze(), "std": std.squeeze(),
                "class_names": CLASS_NAMES, "epochs": args.epochs, "seed": args.seed,
                "best_val_acc": best_val}, outdir / "eurosat_cnn_seed00.pt")
    history["total_seconds"] = time.time() - start
    history["best_val_acc"] = best_val
    history["train_mean"] = mean.squeeze().numpy().round(6).tolist()
    history["train_std"] = std.squeeze().numpy().round(6).tolist()
    with open(outdir / "training_history.json", "w") as f:
        json.dump(history, f, indent=2)
    print(f"done in {time.time()-start:.0f}s; final val_acc={va_acc:.4f} best_val={best_val:.4f}")


if __name__ == "__main__":
    main()