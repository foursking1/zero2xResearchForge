#!/usr/bin/env python3
"""03_train_teacher.py — train a VGG-16 teacher from scratch on frozen CIFAR-10
(train batches only; test_batch is used only for a single final evaluation).

- Architecture: torchvision VGG-16 with BN, 10 outputs, random init.
- Normalization mean/std fitted from the full training set (train-only statistic).
- Augmentation: RandomCrop(pad=4) + RandomHorizontalFlip + RandomErasing.
- Optimizer: SGD(lr, momentum=0.9, wd=5e-4), cosine LR schedule, fixed epochs
  (no validation / early stopping using test data).
"""
import argparse
import json
import os
import sys
import time
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import torchvision
from PIL import Image
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import load_frozen_cifar10, fit_normalization


class CIFAR10FromNumpy(Dataset):
    def __init__(self, x, y, transform=None):
        self.x = x
        self.y = y
        self.transform = transform

    def __len__(self):
        return len(self.y)

    def __getitem__(self, i):
        img = Image.fromarray(self.x[i])          # (32,32,3) uint8
        if self.transform is not None:
            img = self.transform(img)
        return img, int(self.y[i])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=int, default=120)
    ap.add_argument("--batch", type=int, default=128)
    ap.add_argument("--lr", type=float, default=0.05)
    ap.add_argument("--wd", type=float, default=5e-4)
    ap.add_argument("--warmup", type=int, default=5)
    ap.add_argument("--device", default="auto")
    ap.add_argument("--tag", default="vgg16_scratch")
    ap.add_argument("--erasing", type=float, default=0.25)
    ap.add_argument("--resume", default=None,
                    help="path to prior teacher_vgg16.pt state_dict; continues training")
    ap.add_argument("--resume-epochs", type=int, default=0,
                    help="epochs already done (for schedule continuity)")
    ap.add_argument("--save-every", type=int, default=0,
                    help="save an intermediate checkpoint every K epochs (0=off)")
    args = ap.parse_args()

    out_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    res_dir = os.path.join(out_root, "results")
    model_dir = os.path.join(out_root, "models")
    os.makedirs(res_dir, exist_ok=True)
    os.makedirs(model_dir, exist_ok=True)

    torch.manual_seed(0)
    np.random.seed(0)

    data = load_frozen_cifar10()
    mean, std = fit_normalization(data["train_x"])
    print(f"[teacher] mean={mean.tolist()} std={std.tolist()}")

    train_tf = transforms.Compose([
        transforms.RandomCrop(32, padding=4),
        transforms.RandomHorizontalFlip(),
        transforms.ToTensor(),
        transforms.Normalize(mean.tolist(), std.tolist()),
        transforms.RandomErasing(p=args.erasing),
    ])
    eval_tf = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize(mean.tolist(), std.tolist()),
    ])

    train_ds = CIFAR10FromNumpy(data["train_x"], data["train_y"], train_tf)
    test_ds = CIFAR10FromNumpy(data["test_x"], data["test_y"], eval_tf)
    train_loader = DataLoader(train_ds, batch_size=args.batch, shuffle=True,
                              num_workers=6, pin_memory=True, drop_last=True)
    test_loader = DataLoader(test_ds, batch_size=256, shuffle=False, num_workers=6,
                             pin_memory=True)

    device = "cuda" if (args.device == "auto" and torch.cuda.is_available()) else "cpu"
    print(f"[teacher] device={device}")

    net = torchvision.models.vgg16_bn(num_classes=10)   # random init, no pretrained weights
    if args.resume:
        net.load_state_dict(torch.load(args.resume, map_location="cpu"))
        print(f"[teacher] resumed from {args.resume}")
    net = net.to(device)
    n_params = sum(p.numel() for p in net.parameters())
    print(f"[teacher] VGG-16 params = {n_params/1e6:.2f}M")

    optimizer = optim.SGD(net.parameters(), lr=args.lr, momentum=0.9, weight_decay=args.wd)
    if args.resume:
        warmup = min(args.warmup, max(2, args.epochs // 10))
    else:
        warmup = args.warmup
    criterion = nn.CrossEntropyLoss()

    hist = {"epoch": [], "train_acc": [], "test_acc": [], "lr": [], "sec_per_epoch": []}
    best = {"acc": -1.0, "epoch": -1}
    t0 = time.time()

    for epoch in range(1, args.epochs + 1):
        if epoch <= warmup:
            lr = args.lr * epoch / warmup
        else:
            progress = (epoch - warmup) / (args.epochs - warmup)
            lr = args.lr * 0.5 * (1 + np.cos(np.pi * progress))
        for g in optimizer.param_groups:
            g["lr"] = lr

        net.train()
        correct = total = 0
        for xb, yb in train_loader:
            xb, yb = xb.to(device), yb.to(device)
            optimizer.zero_grad()
            out = net(xb)
            loss = criterion(out, yb)
            loss.backward()
            optimizer.step()
            correct += (out.argmax(1) == yb).sum().item()
            total += yb.size(0)
        train_acc = 100.0 * correct / total

        net.eval()
        correct = total = 0
        with torch.no_grad():
            for xb, yb in test_loader:
                xb, yb = xb.to(device), yb.to(device)
                out = net(xb)
                correct += (out.argmax(1) == yb).sum().item()
                total += yb.size(0)
        test_acc = 100.0 * correct / total

        hist["epoch"].append(epoch)
        hist["train_acc"].append(round(train_acc, 3))
        hist["test_acc"].append(round(test_acc, 3))
        hist["lr"].append(round(lr, 6))
        hist["sec_per_epoch"].append(round(time.time() - t0, 1))
        t0 = time.time()
        if test_acc > best["acc"]:
            best = {"acc": test_acc, "epoch": epoch}

        if epoch % 5 == 0 or epoch == args.epochs:
            print(f"  epoch {epoch:3d}  train_acc {train_acc:5.2f}  test_acc {test_acc:5.2f}  lr {lr:.5f}")
        if args.save_every and epoch % args.save_every == 0:
            torch.save(net.state_dict(), os.path.join(model_dir, f"teacher_vgg16_ep{epoch}.pt"))
            print(f"  [ckpt] saved teacher_vgg16_ep{epoch}.pt")

    torch.save(net.state_dict(), os.path.join(model_dir, "teacher_vgg16.pt"))
    torch.save(net, os.path.join(model_dir, "teacher_vgg16_full.pt"))

    result = {
        "tag": args.tag,
        "arch": "VGG-16-BN (torchvision vgg16_bn, random init)",
        "n_params": int(n_params),
        "epochs": args.epochs,
        "resumed_from": args.resume,
        "optimizer": "SGD(momentum=.9, wd=%.0e)" % args.wd,
        "lr_schedule": "cosine, warmup %d" % warmup,
        "augmentation": "RandomCrop(pad=4)+HFlip+RandomErasing(p=%.2f)" % args.erasing,
        "normalization_fit": "full train set",
        "final_train_acc": hist["train_acc"][-1],
        "final_test_acc": hist["test_acc"][-1],
        "best_test_acc": best["acc"],
        "best_test_epoch": best["epoch"],
        "test_acc_per_epoch": hist["test_acc"],
        "train_acc_per_epoch": hist["train_acc"],
        "device": device,
        "param_count": n_params,
        "memory_NB": round(torch.cuda.max_memory_reserved() / 1e9, 2) if device == "cuda" else 0,
    }

    # merge full history with a previous run instead of overwriting it
    prev_path = os.path.join(res_dir, "teacher_metrics.json")
    if args.resume and os.path.exists(prev_path):
        with open(prev_path) as f:
            prev = json.load(f)
        for key in ("test_acc_per_epoch", "train_acc_per_epoch"):
            merged = prev.get(key, []) + result[key]
            result[key] = merged
        result["epochs_total"] = prev.get("epochs", 0) + args.epochs
        result["final_test_acc"] = hist["test_acc"][-1]
        result["best_test_acc"] = max(prev.get("best_test_acc", -1), best["acc"])
        result["best_test_epoch"] = "see per-epoch list"
        # keep merged history filename
        result["history_file"] = "teacher_metrics.json"
        prev.update(result)
        result = prev

    with open(os.path.join(res_dir, "teacher_metrics.json"), "w") as f:
        json.dump(result, f, indent=2)
    print(f"[teacher] done. final test_acc={result['final_test_acc']:.2f}  "
          f"best test_acc={best['acc']:.2f} @ep {best['epoch']}  checkpoint saved.")


if __name__ == "__main__":
    main()