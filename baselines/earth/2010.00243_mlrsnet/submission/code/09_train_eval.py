#!/usr/bin/env python3
"""09_train_eval.py -- fine-tune / train a multi-label scene classifier on the
frozen MLRSNet 40% train split, then evaluate on the frozen 40/60 test split.

Usage example:
    python3 09_train_eval.py --model vit_b16 --pretrained 1 --epochs 15 \
        --lr 3e-5 --batch 64 --wd 1e-4 --seed 20260813 --tag vit_b16_p1

Writes:
  checkpoints/<tag>_best.pt   best state_dict (by internal validation mAP)
  preds/<tag>_test_logits.npz (logits, labels, splits)
"""
import argparse
import json
import os
import time
from datetime import datetime

import numpy as np
import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader

import mlrs
from mlrs import CLASS_NAMES, DATA_WORK, PREDS, N_CLASS
from mlrs import MLRSNetMemmap, build_model, make_train_transform, set_seed

AUX_CKPT = "/mnt/f/dataset/earth/2010.00243_mlrsnet/agent_solution/checkpoints"


def fmt(x):
    return f"{x:.4f}"


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--model", required=True, choices=["resnet18", "densenet201", "vgg16", "vit_b16"])
    p.add_argument("--pretrained", type=int, default=1)
    p.add_argument("--epochs", type=int, default=15)
    p.add_argument("--lr", type=float, default=3e-4)
    p.add_argument("--batch", type=int, default=64)
    p.add_argument("--wd", type=float, default=1e-4)
    p.add_argument("--seed", type=int, default=20260813)
    p.add_argument("--tag", required=True)
    p.add_argument("--num-workers", type=int, default=8)
    p.add_argument("--val-frac", type=float, default=0.05)
    p.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    p.add_argument("--img-size", type=int, default=256)
    p.add_argument("--label-smooth", type=float, default=0.0)
    return p.parse_args()


def make_internal_split(n_train, val_frac, seed):
    rng = np.random.RandomState(seed)
    idx = rng.permutation(n_train)
    n_val = int(round(n_train * val_frac))
    return idx[:n_val], idx[n_val:]


def main():
    a = parse_args()
    set_seed(a.seed)
    os.makedirs(AUX_CKPT, exist_ok=True)
    os.makedirs(PREDS, exist_ok=True)
    log = []
    def L(msg):
        print(f"[{datetime.now():%H:%M:%S}] {msg}", flush=True); log.append(msg)

    use_gpu = a.device.startswith("cuda") and torch.cuda.is_available()
    device = torch.device(a.device if use_gpu else "cpu")
    L(f"device={device}  model={a.model} pretrained={bool(a.pretrained)} tag={a.tag}")

    # ---- frozen data ----
    tr_set = MLRSNetMemmap(os.path.join(DATA_WORK, "train_imgs.dat"),
                           os.path.join(DATA_WORK, "train_labels.dat"),
                           transform=make_train_transform(a.img_size), is_train=True)
    n_tr = len(tr_set)
    tr_val_idx, tr_train_idx = make_internal_split(n_tr, a.val_frac, a.seed)
    L(f"internal split: train={len(tr_train_idx)} val={len(tr_val_idx)}")
    np.save(os.path.join(PREDS, f"{a.tag}_internal_split.npy"),
            np.stack([tr_train_idx, tr_val_idx], axis=0))

    class Subset(torch.utils.data.Dataset):
        def __init__(self, base, idx):
            self.base = base
            self.idx = idx
            self.transform = None
            self.is_train = False

        def __len__(self):
            return len(self.idx)

        def __getitem__(self, i):
            return self.base[self.idx[i]]

    tr_sub = Subset(tr_set, tr_train_idx)
    val_sub = Subset(tr_set, tr_val_idx)

    te_set = MLRSNetMemmap(os.path.join(DATA_WORK, "test_imgs.dat"),
                           os.path.join(DATA_WORK, "test_labels.dat"), None)

    # ---- model / optim ----
    model, desc = build_model(a.model, pretrained=bool(a.pretrained), device=device)
    L(f"model: {desc}")
    params = [p for p in model.parameters() if p.requires_grad]
    opt = torch.optim.AdamW(params, lr=a.lr, weight_decay=a.wd)
    steps_per_epoch = (len(tr_sub) + a.batch - 1) // a.batch
    sched = torch.optim.lr_scheduler.OneCycleLR(
        opt, max_lr=a.lr, total_steps=a.epochs * steps_per_epoch,
        pct_start=0.1, anneal_strategy="cos", div_factor=10, final_div_factor=100)

    train_loader = DataLoader(tr_sub, batch_size=a.batch, shuffle=True,
                              num_workers=a.num_workers, pin_memory=use_gpu,
                              persistent_workers=a.num_workers > 0, drop_last=False)
    val_loader = DataLoader(val_sub, batch_size=a.batch, shuffle=False,
                            num_workers=a.num_workers, pin_memory=use_gpu)
    n_class = N_CLASS

    def run_epoch(split_name, loader, train=True):
        model.train(train)
        total = tp = 0.0
        t0 = time.time()
        loss_sum = 0.0
        n_steps = 0
        for xb, yb in loader:
            xb = xb.to(device); yb = yb.to(device)
            if train:
                opt.zero_grad(set_to_none=True)
            with torch.autocast(device_type=str(device).split(":")[0], enabled=use_gpu):
                out = model(xb)
                if isinstance(out, tuple):
                    out = out[0]
                loss = F.binary_cross_entropy_with_logits(out, yb)
            if train:
                loss.backward()
                opt.step()
                sched.step()
            else:
                loss_sum += loss.item()
            with torch.no_grad():
                prob = torch.sigmoid(out)
                pred = (prob >= 0.5).float()
                tp += (pred == yb).float().mean().item() * xb.size(0)
            total += xb.size(0)
            n_steps += 1
        acc = tp / total
        return acc, (loss_sum / max(n_steps, 1)), time.time() - t0

    def evaluate(loader, best_map=-1):
        model.eval()
        scores = []; ys = []
        with torch.no_grad():
            for xb, yb in loader:
                xb = xb.to(device)
                with torch.autocast(device_type=str(device).split(":")[0], enabled=use_gpu):
                    out = model(xb)
                    if isinstance(out, tuple): out = out[0]
                scores.append(torch.sigmoid(out).float().cpu().numpy())
                ys.append(yb.numpy())
        S = np.concatenate(scores, 0); Y = np.concatenate(ys, 0)
        cols, agg = mlrs.per_class_metrics(Y, S, threshold=0.5)
        return agg["mAP"], agg, S, Y

    best = -1
    for ep in range(1, a.epochs + 1):
        a1, _, dt = run_epoch("train", train_loader, True)
        vmap, vagg, _, _ = evaluate(val_loader)
        lr_now = sched.get_last_lr()[0]
        L(f"epoch {ep}/{a.epochs} train_acc={a1:.4f} val_mAP={fmt(vmap)} "
          f"val_f1={fmt(vagg['macro_f1'])} lr={lr_now:.2e} {dt:.0f}s")
        if vmap > best + 1e-6:
            best = vmap
            torch.save(model.state_dict(), os.path.join(AUX_CKPT, f"{a.tag}_best.pt"))
            L(f"  -> saved best val_mAP={fmt(best)}")

    # reload best
    try:
        model.load_state_dict(torch.load(os.path.join(AUX_CKPT, f"{a.tag}_best.pt"), map_location=device))
        L("reloaded best checkpoint")
    except Exception as e:
        L(f"checkpoint reload skipped: {e}")

    # ---- evaluate on the FROZEN test split ----
    te_loader = DataLoader(te_set, batch_size=a.batch, shuffle=False,
                           num_workers=a.num_workers, pin_memory=use_gpu)
    tmap, tagg, S, Y = evaluate(te_loader)
    L(f"FINAL test mAP={fmt(tmap)} macro_f1={fmt(tagg['macro_f1'])} "
      f"micro_f1={fmt(tagg['micro_f1'])} per_image_f1={fmt(tagg['per_image_f1'])}")

    os.makedirs(PREDS, exist_ok=True)
    np.savez_compressed(os.path.join(PREDS, f"{a.tag}_test_logits.npz"),
                        logits=S.astype(np.float16), labels=Y.astype(np.int8),
                        split="test")
    with open(os.path.join(PREDS, f"{a.tag}_summary.json"), "w") as f:
        json.dump({"model": a.model, "pretrained": bool(a.pretrained), "tag": a.tag,
                   "desc": desc, "epochs": a.epochs, "lr": a.lr, "batch": a.batch,
                   "wd": a.wd, "seed": a.seed, "val_frac": a.val_frac,
                   "best_val_mAP": round(best, 4), "test_mAP": round(tmap, 4),
                   "test_macro_f1": tagg["macro_f1"], "n_test": int(len(te_set))},
                  f, indent=1)
    L("DONE")


if __name__ == "__main__":
    main()