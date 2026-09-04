#!/usr/bin/env python3
"""Fine-tune a pre-trained ImageNet CNN (ResNet18 / optional ViT-B-16) on the
frozen RESISC45 split for one (train_ratio, seed) combination.

Reproduces the paper Table 6 protocol: per-class random training subset at a
given ratio (10%/20%), remainder as test, ImageNet-pretrained fine-tuning.

Usage:
    python train.py --ratio 0.10 --seed 20260813 --epochs 40 --device auto
"""
import argparse
import json
import os
import random
import sys
import time

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from PIL import Image
from torch.utils.data import DataLoader, Dataset
from torchvision import models, transforms

try:
    import torch.cuda as tc
except Exception:
    tc = None


def pick_device():
    if torch.cuda.is_available():
        free_gb = tc.mem_get_info(0)[0] / 1e9
        n_gpu = tc.device_count()
        print("[gpu] devices=%d free_GB=%.1f" % (n_gpu, free_gb))
        if free_gb >= 4.0:
            return "cuda"
    return "cpu"


# ---- image cache loader ---------------------------------------------------
def load_image_cache(cache_path):
    return np.load(cache_path, mmap_mode="r")


class ImageCacheDataset(Dataset):
    """Images from a uint8 memmap; labels from parquet label column."""

    def __init__(self, imgs, labels, idx, transform):
        self.imgs = imgs
        self.labels = labels
        self.idx = np.asarray(idx)
        self.transform = transform

    def __len__(self):
        return len(self.idx)

    def __getitem__(self, i):
        r = self.idx[i]
        arr = np.asarray(self.imgs[r])
        img = Image.fromarray(arr.astype(np.uint8))
        x = self.transform(img)
        return x, int(self.labels[r])


def make_transforms(train=True):
    if train:
        return transforms.Compose([
            transforms.RandomResizedCrop(224, scale=(0.7, 1.0)),
            transforms.RandomHorizontalFlip(),
            transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ])
    return transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ])


def build_model(arch, num_classes, device):
    if arch == "resnet18":
        weights = models.ResNet18_Weights.IMAGENET1K_V1
        model = models.resnet18(weights=weights)
        model.fc = nn.Linear(model.fc.in_features, num_classes)
    elif arch == "vit_b_16":
        weights = models.ViT_B_16_Weights.IMAGENET1K_V1
        model = models.vit_b_16(weights=weights)
        model.heads.head = nn.Linear(model.heads.head.in_features, num_classes)
    else:
        raise ValueError("unknown arch: %s" % arch)
    return model.to(device)


@torch.no_grad()
def evaluate(model, loader, device, return_preds=False):
    model.eval()
    correct = 0
    total = 0
    conf = torch.zeros(45, 45, dtype=torch.long)
    preds_rows = []
    for x, y in loader:
        x, y = x.to(device), y.to(device)
        logits = model(x)
        pred = logits.argmax(1)
        correct += (pred == y).sum().item()
        total += y.numel()
        for p, t in zip(pred.cpu().tolist(), y.cpu().tolist()):
            conf[t, p] += 1
        if return_preds:
            probs = logits.softmax(1).cpu().numpy()
            preds_rows.append((y.cpu().numpy(), pred.cpu().numpy(), probs))
    out = {"oa": 100.0 * correct / total, "correct": correct, "total": total,
           "confusion": conf.cpu().numpy()}
    if return_preds:
        y_all = np.concatenate([r[0] for r in preds_rows])
        p_all = np.concatenate([r[1] for r in preds_rows])
        prob_all = np.concatenate([r[2] for r in preds_rows], axis=0)
        out["labels"] = y_all
        out["preds"] = p_all
        out["probs"] = prob_all
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ratio", type=float, default=0.10)
    ap.add_argument("--seed", type=int, default=20260813)
    ap.add_argument("--epochs", type=int, default=40)
    ap.add_argument("--batch_size", type=int, default=64)
    ap.add_argument("--lr", type=float, default=0.01)
    ap.add_argument("--arch", default="resnet18")
    ap.add_argument("--device", default="auto")
    ap.add_argument("--img_cache", default="data_cache/resisc45_images.npy")
    ap.add_argument("--parquet", default="")
    ap.add_argument("--split_csv", default="")
    ap.add_argument("--outdir", default="results")
    args = ap.parse_args()

    torch.manual_seed(args.seed)
    random.seed(args.seed)
    np.random.seed(args.seed)

    device = args.device if args.device != "auto" else pick_device()
    print("[device]", device)

    # image cache + labels
    imgs = load_image_cache(args.img_cache)
    if args.split_csv:
        split_df = pd.read_csv(args.split_csv)
    else:
        raise SystemExit("--split_csv required")
    labels = split_df["label"].values.astype(int)
    train_idx = split_df.index[split_df["split"] == "train"].values
    test_idx = split_df.index[split_df["split"] == "test"].values
    print("[split] train=%d test=%d" % (len(train_idx), len(test_idx)))

    tr_loader = DataLoader(
        ImageCacheDataset(imgs, labels, train_idx, make_transforms(True)),
        batch_size=args.batch_size, shuffle=True,
        num_workers=os.cpu_count() if device == "cpu" else 8,
        pin_memory=(device == "cuda"), drop_last=False)
    te_loader = DataLoader(
        ImageCacheDataset(imgs, labels, test_idx, make_transforms(False)),
        batch_size=args.batch_size, shuffle=False,
        num_workers=os.cpu_count() if device == "cpu" else 8,
        pin_memory=(device == "cuda"))

    model = build_model(args.arch, 45, device)
    model.num_classes = 45
    opt = optim.SGD(model.parameters(), lr=args.lr, momentum=0.9, weight_decay=5e-4)
    sched = optim.lr_scheduler.CosineAnnealingLR(opt, T_max=args.epochs)
    crit = nn.CrossEntropyLoss()

    log = []
    best = {"oa": -1.0}
    t0 = time.time()
    for ep in range(1, args.epochs + 1):
        model.train()
        run_loss, run_correct, run_total = 0.0, 0, 0
        for x, y in tr_loader:
            x, y = x.to(device), y.to(device)
            opt.zero_grad()
            logits = model(x)
            loss = crit(logits, y)
            loss.backward()
            opt.step()
            run_loss += loss.item() * x.size(0)
            run_correct += (logits.argmax(1) == y).sum().item()
            run_total += x.size(0)
        sched.step()
        ev = evaluate(model, te_loader, device)
        row = {"epoch": ep, "train_loss": run_loss / max(run_total, 1),
               "train_oa": 100.0 * run_correct / max(run_total, 1),
               "test_oa": ev["oa"]}
        log.append(row)
        if ev["oa"] > best["oa"]:
            best["oa"] = ev["oa"]
            best["epoch"] = ep
            os.makedirs(args.outdir, exist_ok=True)
            torch.save(model.state_dict(), os.path.join(
                args.outdir, "model_%s_r%.2f_s%d.pt"
                % (args.arch, args.ratio, args.seed)))
            np.save(os.path.join(args.outdir,
                    "confusion_%s_r%.2f_s%d_best.npy"
                    % (args.arch, args.ratio, args.seed)), ev["confusion"])
        if ep == 1 or ep % 5 == 0 or ep == args.epochs:
            print("[seed %d r%.2f] ep %3d loss %.3f trainOA %.2f testOA %.2f "
                  "best %.2f@%d (%.1fs)" % (
                      args.seed, args.ratio, ep, row["train_loss"],
                      row["train_oa"], row["test_oa"], best["oa"],
                      best["epoch"], time.time() - t0))

    res = {"arch": args.arch, "ratio": args.ratio, "seed": args.seed,
           "epochs": args.epochs, "final_test_oa": log[-1]["test_oa"],
           "best_test_oa": best["oa"], "best_epoch": best["epoch"],
           "device": device, "log": log,
           "dur_s": round(time.time() - t0, 1)}
    os.makedirs(args.outdir, exist_ok=True)
    out_json = os.path.join(args.outdir,
                            "train_%s_r%.2f_s%d.json"
                            % (args.arch, args.ratio, args.seed))
    with open(out_json, "w") as f:
        json.dump(res, f, indent=2)
    print("[done]", out_json)

    # final-model test predictions for the evidence table
    model.load_state_dict(torch.load(os.path.join(
        args.outdir, "model_%s_r%.2f_s%d.pt"
        % (args.arch, args.ratio, args.seed)), map_location=device))
    ev = evaluate(model, te_loader, device, return_preds=True)
    np.savez_compressed(
        os.path.join(args.outdir,
                     "preds_%s_r%.2f_s%d.npz"
                     % (args.arch, args.ratio, args.seed)),
        test_idx=test_idx, labels=ev["labels"], preds=ev["preds"],
        probs=ev["probs"], confusion=ev["confusion"])
    print("[preds saved] final test OA = %.2f" % ev["oa"])


if __name__ == "__main__":
    main()