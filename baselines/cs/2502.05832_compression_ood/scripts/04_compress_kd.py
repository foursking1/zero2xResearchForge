#!/usr/bin/env python3
"""04_compress_kd.py — few-sample knowledge-distillation compression.

Pipeline (identical for balanced and imbalanced configs, identical hyper-params,
*only the training subset differs*):
  1. Build subset from frozen CIFAR-10 train batches (fixed seed, common.build_subsets).
  2. Fit per-channel mean/std from that training subset only.
  3. Load the frozen VGG-16 teacher (random-init, trained from scratch on CIFAR-10).
  4. Train a small student (StudentNet, ~2.4M params vs 134M teacher) using
     logit KD:  L = alpha*T^2*KL(student, teacher) + (1-alpha)*CE(student, hard label)
  5. Evaluate once on the frozen test set (final evaluation only).

No validation split, no early stopping, no test-set statistical fitting.
"""
import argparse
import json
import os
import sys
import time
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from PIL import Image
from torch.utils.data import DataLoader, Dataset

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (build_subsets, fit_normalization, get_data_dir,
                    load_frozen_cifar10, INIT_SEED)
from teacher_models import StudentNet


class TensorSubset(Dataset):
    """Slices of the frozen training array identified by indices; stochastic aug."""
    def __init__(self, x_all, y_all, idx, transform=None):
        self.x = x_all[idx]
        self.y = y_all[idx]
        self.transform = transform

    def __len__(self):
        return len(self.y)

    def __getitem__(self, i):
        img = Image.fromarray(self.x[i])
        if self.transform is not None:
            img = self.transform(img)
        return img, int(self.y[i])


class TestSet(Dataset):
    def __init__(self, x, y, transform=None):
        self.x, self.y, self.transform = x, y, transform

    def __len__(self):
        return len(self.y)

    def __getitem__(self, i):
        img = Image.fromarray(self.x[i])
        if self.transform is not None:
            img = self.transform(img)
        return img, int(self.y[i])


def evaluate(net, loader, device):
    net.eval()
    correct = total = 0
    with torch.no_grad():
        for xb, yb in loader:
            xb, yb = xb.to(device), yb.to(device)
            out = net(xb)
            correct += (out.argmax(1) == yb).sum().item()
            total += yb.size(0)
    return 100.0 * correct / total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--N", type=int, default=10)
    ap.add_argument("--config", choices=["balanced", "imbalanced"], default="balanced")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--epochs", type=int, default=0, help="0 -> auto by N")
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--wd", type=float, default=5e-4)
    ap.add_argument("--temp", type=float, default=4.0)
    ap.add_argument("--alpha", type=float, default=0.6)
    ap.add_argument("--device", default="auto")
    ap.add_argument("--teacher", default=None, help="path to teacher checkpoint pt")
    args = ap.parse_args()

    if args.epochs <= 0:
        args.epochs = {10: 400, 50: 300, 100: 260}.get(args.N, 300)

    out_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    res_dir = os.path.join(out_root, "results")
    run_dir = os.path.join(res_dir, "students", f"{args.config}_N{args.N}_seed{args.seed}")
    os.makedirs(run_dir, exist_ok=True)

    device = "cuda" if (args.device == "auto" and torch.cuda.is_available()) else "cpu"

    # ---- data & subset (re-built deterministically from the frozen pickles) ----
    data = load_frozen_cifar10()
    all_x, all_y = data["train_x"], data["train_y"]
    subs = [s for s in build_subsets([args.N], data={"train_x": all_x, "train_y": all_y})
            if s["seed"] == args.seed][0]
    idx = subs["balanced_idx"] if args.config == "balanced" else subs["imbalanced_idx"]

    mean, std = fit_normalization(all_x[idx])

    import torchvision.transforms as T
    train_tf = T.Compose([
        T.RandomCrop(32, padding=4),
        T.RandomHorizontalFlip(),
        T.ToTensor(),
        T.Normalize(mean.tolist(), std.tolist()),
    ])
    eval_tf = T.Compose([T.ToTensor(), T.Normalize(mean.tolist(), std.tolist())])

    train_ds = TensorSubset(all_x, all_y, idx, train_tf)
    test_ds = TestSet(data["test_x"], data["test_y"], eval_tf)
    gen = torch.Generator().manual_seed(args.seed)
    train_loader = DataLoader(train_ds, batch_size=args.batch, shuffle=True,
                              generator=gen, num_workers=2)
    test_loader = DataLoader(test_ds, batch_size=256, shuffle=False, num_workers=2)

    # ---- teacher (frozen, eval mode) ----
    teacher_path = args.teacher or os.path.join(out_root, "models", "teacher_vgg16.pt")
    teacher = torchvision_vgg16(num_classes=10)
    teacher.load_state_dict(torch.load(teacher_path, map_location=device))
    teacher = teacher.to(device).eval()
    for p in teacher.parameters():
        p.requires_grad_(False)

    def teacher_logits(x):
        with torch.no_grad():
            return teacher(x)

    # ---- student: IDENTICAL init across configs (INIT_SEED) ----
    torch.manual_seed(INIT_SEED)
    student = StudentNet(num_classes=10)
    student = student.to(device)
    n_stu = sum(p.numel() for p in student.parameters())

    optimizer = torch.optim.AdamW(student.parameters(), lr=args.lr, weight_decay=args.wd)
    # cosine schedule, no warmup
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs)
    ce = nn.CrossEntropyLoss()

    t0 = time.time()
    for epoch in range(1, args.epochs + 1):
        student.train()
        for xb, yb in train_loader:
            xb, yb = xb.to(device), yb.to(device)
            with torch.autocast(device_type=device, dtype=torch.bfloat16):
                logits_s = student(xb)
                with torch.no_grad():
                    logits_t = teacher_logits(xb)
                kl = F.kl_div(F.log_softmax(logits_s / args.temp, dim=1),
                              F.softmax(logits_t / args.temp, dim=1),
                              reduction="batchmean")
                hard = ce(logits_s, yb)
                loss = args.alpha * args.temp ** 2 * kl + (1 - args.alpha) * hard
            loss.backward()
            optimizer.step()
            optimizer.zero_grad()
        sched.step()

        if epoch % 20 == 0 or epoch == args.epochs:
            tr_acc = evaluate(student, train_loader, device)
            print(f"  [{args.config} N={args.N} seed={args.seed}] ep {epoch:3d} "
                  f"train_acc {tr_acc:5.2f}  loss {loss.item():.4f}  "
                  f"({time.time() - t0:.0f}s)")

    test_acc = evaluate(student, test_loader, device)
    tr_acc = evaluate(student, train_loader, device)
    torch.save(student.state_dict(), os.path.join(run_dir, "student.pt"))

    result = {
        "config": args.config, "N": args.N, "seed": args.seed,
        "subset_total": int(len(idx)),
        "per_class_sizes": (subs["balanced_sizes"] if args.config == "balanced"
                            else subs["imbalanced_sizes"]),
        "method": "knowledge-distillation (logit KD, T=%.1f, alpha=%.2f)" % (args.temp, args.alpha),
        "student_params": int(n_stu),
        "teacher_params": 134_211_146,
        "epochs": args.epochs,
        "optim": "AdamW(lr=%.0e,wd=%.0e)" % (args.lr, args.wd),
        "aug": "RandomCrop(pad=4)+HFlip",
        "normalization_fit": "from training subset only",
        "train_acc": round(tr_acc, 3),
        "test_acc": round(test_acc, 3),
        "time_s": round(time.time() - t0, 1),
        "device": device,
    }
    with open(os.path.join(run_dir, "metrics.json"), "w") as f:
        json.dump(result, f, indent=2)
    print(f"[kd] {args.config} N={args.N} seed={args.seed} "
          f"train_acc={tr_acc:.2f} test_acc={test_acc:.2f}  -> {run_dir}")


def torchvision_vgg16(num_classes=10):
    import torchvision.models as tv
    return tv.vgg16_bn(num_classes=num_classes)


if __name__ == "__main__":
    main()