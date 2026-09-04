"""Train ResNeXt-CBAM on So2Sat (S2-only or S1+S2 fusion) and evaluate on the
held-out eval subset (20% of frozen validation split).

Usage:
  python code/train_cnn.py --bands s2 --variant l --epochs 35 --device cpu
  python code/train_cnn.py --bands s1s2 --variant l --epochs 32 --device cpu
"""
import argparse
import json
import os
import time

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from models import build_model
from metrics import compute_metrics

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "results")
SEED = 42

LPZ = ["Compact high-rise", "Compact midrise", "Compact low-rise", "Open high-rise",
       "Open midrise", "Open low-rise", "Lightweight low-rise", "Large low-rise",
       "Sparsely built", "Heavy industry", "Dense trees", "Scattered trees",
       "Bush/scrub", "Low plants", "Paved", "Bare rock/sand", "Water"]


def set_seed(seed):
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def augment(x):
    """Batch-level data augmentation (all samples share the same geometric op sample)."""
    k = np.random.randint(0, 4)
    if k:
        x = torch.rot90(x, k, dims=(2, 3))
    if np.random.rand() < 0.5:
        x = torch.flip(x, dims=(3,))
    if np.random.rand() < 0.5:
        x = torch.flip(x, dims=(2,))
    pad = 2
    x = F.pad(x, (pad, pad, pad, pad), mode="constant", value=0)
    dh = np.random.randint(-pad, pad + 1)
    dw = np.random.randint(-pad, pad + 1)
    x = x[:, :, pad - dh: pad + 32 - dh, pad - dw: pad + 32 - dw]
    return x


def load_arrays(bands):
    train_y = np.load(os.path.join(DATA, "train_y.npy"))
    val_y = np.load(os.path.join(DATA, "val_y.npy"))
    if bands == "s2":
        tr = np.load(os.path.join(DATA, "train_s2.npy"))
        va = np.load(os.path.join(DATA, "val_s2.npy"))
        in_ch = 10
    elif bands == "s1":
        tr = np.load(os.path.join(DATA, "train_s1.npy"))
        va = np.load(os.path.join(DATA, "val_s1.npy"))
        in_ch = 8
    else:  # fusion
        tr = np.concatenate([np.load(os.path.join(DATA, "train_s2.npy")),
                             np.load(os.path.join(DATA, "train_s1.npy"))], axis=-1)
        va = np.concatenate([np.load(os.path.join(DATA, "val_s2.npy")),
                             np.load(os.path.join(DATA, "val_s1.npy"))], axis=-1)
        in_ch = 18
    return tr, va, train_y, val_y, in_ch


def train(args):
    set_seed(SEED)
    os.makedirs(OUT, exist_ok=True)
    tr, va, train_y, val_y, in_ch = load_arrays(args.bands)
    # NHWC -> NCHW
    tr = tr.transpose(0, 3, 1, 2)
    va = va.transpose(0, 3, 1, 2)

    device = torch.device(args.device)
    if args.device == "cpu":
        torch.set_num_threads(args.threads)
    elif args.device == "cuda":
        torch.backends.cudnn.benchmark = True
        if not torch.cuda.is_available():
            raise RuntimeError("CUDA not available")
    model = build_model(in_ch, nclass=17, variant=args.variant).to(device)
    n_params = sum(p.numel() for p in model.parameters())

    train_mask = np.zeros(len(train_y), dtype=bool)
    train_mask[: int(len(train_y) * args.core_frac)] = True
    tr_x = torch.from_numpy(tr[train_mask]).to(device)
    tr_y = torch.from_numpy(train_y[train_mask]).to(device)
    va_x = torch.from_numpy(va).to(device)
    va_y = val_y

    epochs = args.epochs
    bs = args.batch_size
    steps_per_epoch = len(tr_y) // bs
    lr = float(args.lr)
    criterion = nn.CrossEntropyLoss()
    opt = torch.optim.SGD(model.parameters(), lr=lr, momentum=0.9, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=epochs)

    best_oa, best_state, best_preds = 0.0, None, None
    ckpt_path = os.path.join(OUT, f"ckpt_{args.bands}_{args.variant}.pt")
    start_ep = 0
    if args.resume and os.path.exists(ckpt_path):
        ck = torch.load(ckpt_path, map_location=device)
        model.load_state_dict(ck["model"])
        opt.load_state_dict(ck["optim"])
        sched.load_state_dict(ck["sched"])
        start_ep = ck["epoch"]
        best_oa = ck["best_oa"]
        best_state = ck["best_state"]
        best_preds = ck["best_preds"]
        print(f"resumed from epoch {start_ep}")

    for ep in range(start_ep, epochs):
        model.train()
        t0 = time.time()
        perm = torch.randperm(len(tr_y))
        running, correct = 0.0, 0
        for it in range(steps_per_epoch):
            idx = perm[it * bs:(it + 1) * bs]
            xb, yb = tr_x[idx], tr_y[idx]
            xb = augment(xb) if args.aug else xb
            opt.zero_grad()
            logits = model(xb)
            loss = criterion(logits, yb)
            loss.backward()
            opt.step()
            running += loss.item()
            correct += (logits.argmax(1) == yb).sum().item()
        sched.step()
        oa_tr = correct / (steps_per_epoch * bs)
        # eval
        model.eval()
        preds = []
        with torch.no_grad():
            for i in range((len(va_y) + bs - 1) // bs):
                xb = va_x[i * bs:(i + 1) * bs]
                preds.append(model(xb).argmax(1).cpu().numpy())
        preds = np.concatenate(preds) if preds else np.array([])
        oa_va = float((preds == va_y).mean())
        print(f"[{args.bands}/{args.variant}] ep {ep + 1}/{epochs} "
              f"loss={running / steps_per_epoch:.4f} tr_oa={oa_tr:.4f} "
              f"va_oa={oa_va:.4f} ({time.time() - t0:.0f}s/ep)", flush=True)
        if oa_va > best_oa:
            best_oa = oa_va
            best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
            best_preds = preds
        torch.save({"model": model.state_dict(), "optim": opt.state_dict(),
                    "sched": sched.state_dict(), "epoch": ep + 1,
                    "best_oa": best_oa, "best_state": best_state, "best_preds": best_preds,
                    "args": vars(args)}, ckpt_path)

    tag = f"{args.bands}_{args.variant}"
    if args.core_frac < 1.0:
        tag += f"_cfrac{args.core_frac}"
    torch.save({"state_dict": best_state, "n_params": n_params,
                "args": vars(args)}, os.path.join(OUT, f"model_{tag}.pt"))
    np.save(os.path.join(OUT, f"preds_{tag}.npy"), best_preds)
    np.save(os.path.join(OUT, f"logits_{tag}.npy"), best_preds.astype(np.float64))

    metrics, cm = compute_metrics(val_y, best_preds, split="eval",
                                  bands=args.bands, seed=SEED, train_size=int(tr_y.shape[0]),
                                  out_dir=os.path.join(OUT, tag))
    metrics["n_params"] = int(n_params)
    metrics["epochs"] = int(epochs)
    metrics["best_val_oa"] = float(best_oa)
    with open(os.path.join(OUT, tag, "training.json"), "w") as fh:
        json.dump({"args": vars(args), "n_params": int(n_params),
                   "best_val_oa": float(best_oa), "final_train_loss": float(running / steps_per_epoch)}, fh, indent=2)
    print(f"[{args.bands}] final best val OA {best_oa:.4f}, saved to {OUT}/{tag}")
    return metrics


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--bands", choices=["s1", "s2", "s1s2"], default="s2")
    ap.add_argument("--variant", choices=["s", "l"], default="l")
    ap.add_argument("--epochs", type=int, default=35)
    ap.add_argument("--batch-size", type=int, default=64)
    ap.add_argument("--lr", type=float, default=0.1)
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--aug", type=int, default=1)
    ap.add_argument("--threads", type=int, default=10)
    ap.add_argument("--resume", type=int, default=0)
    ap.add_argument("--core-frac", type=float, default=1.0)
    args = ap.parse_args()
    train(args)