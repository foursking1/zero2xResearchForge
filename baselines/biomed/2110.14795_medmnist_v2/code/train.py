#!/usr/bin/env python3
"""Train a ResNet-18 (28x28-friendly stem) CNN on the five frozen MedMNIST v2
2D datasets and evaluate on the held-out test split.

Design (maintains MedMNIST conventions):
  * normalization stats (per-channel mean/std) are computed from the TRAIN split
    only; test/val images are only transformed, never summarized;
  * the model mirrors the paper's ResNet-18 baseline but with a 3x3/stride-1
    stem and no initial max-pool, the standard adaptation for 28x28 inputs;
  * multi-class AUC == macro-averaged one-vs-rest AUC (official MedMNIST rule);
  * model selection (early stopping, LR scheduling) uses ONLY the val split;
    the test split is evaluated exactly once at the end.

Outputs (written under ../results):
  evidence_table.csv   one row per dataset: dataset,n_classes,train_size,...
  metrics.json         class counts, AUC/ACC, paper-anchor deltas, verdict
  per-dataset best-weights dir under results/checkpoints/

Usage:
  python3 train.py [--device cpu|cuda] [--data-dir PATH] [--epochs N]
                   [--seed S] [--out-dir DIR] [--dataset NAME...]
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
from sklearn.metrics import accuracy_score, roc_auc_score
from torch.utils.data import DataLoader, TensorDataset

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import (BATCH_SIZE, DATASETS, EPOCHS, INIT_LR, EARLY_STOP_PATIENCE,
                    LR_FACTOR, LR_PATIENCE, PAPER_ANCHOR, SEED, VERIFY_RANGE,
                    WEIGHT_DECAY)

TORCH_GE_2 = int(torch.__version__.split(".")[0]) >= 2


def set_seed(seed):
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


# --------------------------------------------------------------------------- #
# Data
# --------------------------------------------------------------------------- #
def load_npz(path):
    with np.load(path) as d:
        return {k: d[k] for k in d.files}


def make_tensor_loader(images, labels, batch_size, shuffle, mean, std, train=False):
    """images: uint8 (N,H,W[,C]); returns DataLoader of normalized tensors."""
    x = torch.from_numpy(images.astype(np.float32))
    if x.dim() == 3:                      # (N,H,W) -> (N,1,H,W)
        x = x.unsqueeze(1)
    else:                                 # (N,H,W,C) -> (N,C,H,W)
        x = x.permute(0, 3, 1, 2)
    x = (x / 255.0 - mean.view(1, -1, 1, 1)) / std.view(1, -1, 1, 1)
    y = torch.from_numpy(labels.astype(np.int64)).long().view(-1)
    ds = TensorDataset(x, y)
    return DataLoader(ds, batch_size=batch_size, shuffle=shuffle,
                      num_workers=0, drop_last=False)


def compute_norm_stats(images):
    """Per-channel mean/std over pixel values (uint8 -> [0,1]), train split only."""
    x = torch.from_numpy(images.astype(np.float32))
    if x.dim() == 3:
        x = x.unsqueeze(1)                # grayscale
    else:
        x = x.permute(0, 3, 1, 2)         # (N,C,H,W)
    x = x / 255.0
    mean = x.mean(dim=(0, 2, 3))
    std = x.std(dim=(0, 2, 3)) + 1e-6
    return mean, std


def train_augment(x):
    """Modest on-the-fly augmentation applied to the normalized train batch."""
    # random horizontal flip
    flip = torch.rand(x.shape[0], 1, 1, 1, device=x.device) < 0.5
    x = torch.where(flip, torch.flip(x, dims=[3]), x)
    # random rotation in {-10,-5,0,5,10} degrees (bilinear, fills with 0)
    if TORCH_GE_2:
        deg = torch.randint(-10, 11, (x.shape[0],), device=x.device).float()
        theta = torch.deg2rad(deg)
        cos, sin = torch.cos(theta), torch.sin(theta)
        for i in range(x.shape[0]):
            if deg[i].abs() > 0.1:
                a = cos[i]; b = sin[i]
                M = torch.zeros(2, 3, device=x.device)
                M[0, 0] = a; M[0, 1] = -b; M[1, 0] = b; M[1, 1] = a
                grid = F.affine_grid(M.unsqueeze(0), x[i:i+1].shape, align_corners=False)
                x[i] = F.grid_sample(x[i:i+1], grid, align_corners=False)
    return x


# --------------------------------------------------------------------------- #
# Model
# --------------------------------------------------------------------------- #
def make_resnet18(num_classes, in_channels):
    """ResNet-18 with 28x28-friendly stem (3x3/1 conv, no max-pool)."""
    import torchvision.models as tvmodels
    model = tvmodels.resnet18(weights=None, num_classes=num_classes)
    model.conv1 = nn.Conv2d(in_channels, 64, kernel_size=3, stride=1,
                            padding=1, bias=False)
    model.bn1 = nn.BatchNorm2d(64)
    model.maxpool = nn.Identity()
    return model


# --------------------------------------------------------------------------- #
# Metrics
# --------------------------------------------------------------------------- #
def eval_metrics(y_true, proba):
    """AUC: macro one-vs-rest AUC for multi-class (official MedMNIST rule),
    plain ROC AUC over the positive class for binary. ACC = argmax accuracy."""
    n_classes = proba.shape[1]
    if n_classes == 2:
        auc = roc_auc_score(y_true, proba[:, 1])
    else:
        auc = roc_auc_score(y_true, proba, multi_class="ovr", average="macro",
                            labels=list(range(n_classes)))
    acc = accuracy_score(y_true, proba.argmax(axis=1))
    return float(auc), float(acc)


@torch.no_grad()
def predict_proba(model, loader, device):
    model.eval()
    ys, probs = [], []
    for x, y in loader:
        x = x.to(device)
        p = torch.softmax(model(x.float()), dim=1)
        ys.append(y.numpy())
        probs.append(p.cpu().numpy())
    return np.concatenate(ys), np.concatenate(probs)


# --------------------------------------------------------------------------- #
# Training
# --------------------------------------------------------------------------- #
def train_dataset(name, n_classes, channels, data_dir, device, out_dir, cfg):
    path = os.path.join(data_dir, f"{name}.npz")
    d = np.load(path)
    tr_img, tr_lab = d["train_images"], d["train_labels"].squeeze().astype(int)
    va_img, va_lab = d["val_images"], d["val_labels"].squeeze().astype(int)
    te_img, te_lab = d["test_images"], d["test_labels"].squeeze().astype(int)

    mean, std = compute_norm_stats(tr_img)
    tr_loader = make_tensor_loader(tr_img, tr_lab, cfg["batch_size"],
                                   shuffle=True, mean=mean, std=std, train=True)
    va_loader = make_tensor_loader(va_img, va_lab, cfg["batch_size"],
                                   shuffle=False, mean=mean, std=std)
    te_loader = make_tensor_loader(te_img, te_lab, cfg["batch_size"],
                                   shuffle=False, mean=mean, std=std)

    model = make_resnet18(num_classes=n_classes, in_channels=channels).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=cfg["lr"],
                                 weight_decay=cfg["weight_decay"])
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode="max", factor=LR_FACTOR, patience=LR_PATIENCE, min_lr=1e-6)
    criterion = nn.CrossEntropyLoss()

    best_val_auc = -1.0
    best_state = None
    bad_epochs = 0
    history = []

    for epoch in range(1, cfg["epochs"] + 1):
        model.train()
        t0 = time.time()
        total, correct, loss_sum = 0, 0, 0.0
        for x, y in tr_loader:
            x = train_augment(x)
            x, y = x.to(device), y.to(device)
            out = model(x)
            loss = criterion(out, y)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            loss_sum += loss.item() * y.size(0)
            total += y.size(0)
            correct += (out.argmax(1) == y).sum().item()
        tr_acc = correct / total

        # validation (early-stop / LR schedule signal -> VALIDATION ONLY)
        va_y, va_p = predict_proba(model, va_loader, device)
        va_auc, va_acc = eval_metrics(va_y, va_p)
        scheduler.step(va_auc)

        improved = va_auc > best_val_auc
        history.append({"epoch": epoch, "tr_acc": tr_acc,
                        "val_acc": va_acc, "val_auc": va_auc})
        if improved:
            best_val_auc = va_auc
            best_state = {k: v.detach().clone() for k, v in model.state_dict().items()}
            best_epoch = epoch
            bad_epochs = 0
        else:
            bad_epochs += 1
        elapsed = time.time() - t0
        print(f"[{name}] epoch {epoch:3d}/{cfg['epochs']} | tr_acc={tr_acc:.4f} "
              f"| val_auc={va_auc:.4f} val_acc={va_acc:.4f} | best_val_auc={best_val_auc:.4f} "
              f"| {elapsed:.1f}s".rstrip())
        if bad_epochs >= cfg["early_stop"]:
            print(f"[{name}] early stop @ epoch {epoch} (best @ {best_epoch})")
            break

    # final test evaluation (exactly once, best-val checkpoint)
    assert best_state is not None
    model.load_state_dict(best_state)
    te_y, te_p = predict_proba(model, te_loader, device)
    te_auc, te_acc = eval_metrics(te_y, te_p)
    va_y, va_p = predict_proba(model, va_loader, device)
    va_auc, _ = eval_metrics(va_y, va_p)

    ckpt_dir = os.path.join(out_dir, "checkpoints")
    os.makedirs(ckpt_dir, exist_ok=True)
    torch.save({"state_dict": best_state, "cfg": cfg, "history": history},
               os.path.join(ckpt_dir, f"{name}_best.pt"))

    return {
        "dataset": name, "n_classes": n_classes, "channels": channels,
        "model": "ResNet-18@28 (3x3 stem, no maxpool)",
        "normalize": {"mean": mean.tolist(), "std": std.tolist()},
        "train_size": int(len(tr_img)), "val_size": int(len(va_img)),
        "test_size": int(len(te_img)),
        "best_epoch": int(best_epoch),
        "val_auc": float(va_auc),
        "test_auc": te_auc, "test_acc": te_acc,
        "history": history,
    }


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def build_verdict(name, res):
    lo, hi = VERIFY_RANGE[name]
    auc = res["test_auc"]
    if lo <= auc <= hi:
        return "in_range"
    if auc > hi:
        return "above_paper_range"
    return "below_paper_range"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", default="cpu", choices=["cpu", "cuda"])
    ap.add_argument("--data-dir", default=None)
    ap.add_argument("--epochs", type=int, default=EPOCHS)
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--batch-size", type=int, default=BATCH_SIZE)
    ap.add_argument("--lr", type=float, default=INIT_LR)
    ap.add_argument("--weight-decay", type=float, default=WEIGHT_DECAY)
    ap.add_argument("--early-stop", type=int, default=EARLY_STOP_PATIENCE)
    ap.add_argument("--out-dir",
                    default=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                         "results"))
    ap.add_argument("--dataset", nargs="*", default=None,
                    help="subset of {bloodmnist,breastmnist,dermamnist,"
                         "pneumoniamnist,retinamnist} (default: all)")
    args = ap.parse_args()

    import config
    if args.data_dir:
        config.DATA_DIR = args.data_dir
    data_dir = config.DATA_DIR

    set_seed(args.seed)
    device = torch.device("cuda" if (args.device == "cuda" and torch.cuda.is_available()) else "cpu")
    if device.type == "cuda" and torch.cuda.is_available():
        free = torch.cuda.mem_get_info(device)[0] / (1024 ** 3)
        if free < 6.0:                      # guard against GPU contention with other jobs
            print(f"WARNING: only {free:.1f} GiB free VRAM, falling back to CPU")
            device = torch.device("cpu")
        else:
            torch.backends.cudnn.benchmark = False
            torch.backends.cudnn.deterministic = True
            torch.set_num_threads(max(2, int(os.cpu_count() // 2)))
    else:
        torch.set_num_threads(max(2, int(os.cpu_count() // 2)))
    print(f"device={device} data_dir={data_dir} seed={args.seed} "
          f"torch_threads={torch.get_num_threads()}")

    if args.dataset:
        datasets = [d for d in DATASETS if d[0] in args.dataset]
    else:
        datasets = DATASETS

    cfg = {"epochs": args.epochs, "batch_size": args.batch_size, "lr": args.lr,
           "weight_decay": args.weight_decay, "early_stop": args.early_stop,
           "seed": args.seed}

    os.makedirs(args.out_dir, exist_ok=True)
    results = []
    for name, n_classes, channels in datasets:
        print(f"\n========== {name} (n_classes={n_classes}, channels={channels}) ==========")
        t0 = time.time()
        r = train_dataset(name, n_classes, channels, data_dir, device,
                          args.out_dir, cfg)
        r["elapsed_s"] = round(time.time() - t0, 1)
        results.append(r)
        print(f"[{name}] FINAL test_auc={r['test_auc']:.4f} "
              f"test_acc={r['test_acc']:.4f} ({r['elapsed_s']}s)")

    # evidence table
    import csv
    tbl_path = os.path.join(args.out_dir, "evidence_table.csv")
    cols = ["dataset", "n_classes", "channels", "model", "train_size",
            "val_size", "test_size", "best_epoch", "val_auc", "auc", "acc",
            "paper_auc", "paper_acc", "verdict"]
    with open(tbl_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in results:
            src = PAPER_ANCHOR[r["dataset"]]
            w.writerow({**{c: r.get(c, "") for c in cols},
                        "val_auc": f"{r['val_auc']:.4f}",
                        "auc": f"{r['test_auc']:.4f}",
                        "acc": f"{r['test_acc']:.4f}",
                        "paper_auc": src["auc"], "paper_acc": src["acc"],
                        "verdict": build_verdict(r["dataset"], r)})
    print(f"\nWrote {tbl_path}")

    # metrics json (stripped history, keep class counts too)
    d = np.load(os.path.join(data_dir, f"{results[0]['dataset']}.npz"))  # noqa: just sanity
    metrics = {
        "task_id": "2110.14795_medmnist_v2",
        "model": "ResNet-18@28 (stem adapted for 28x28)",
        "device": str(device), "seed": args.seed,
        "auc_definition": "macro one-vs-rest AUC (official MedMNIST rule)",
        "datasets": {},
        "paper_note": "Paper values are anchors from Table 3 (ResNet-18@28), reported for comparison only; not used as training signal.",
        "conclusion": {},
    }
    auc_order = []
    for r in results:
        name = r["dataset"]
        metrics["datasets"][name] = {
            "n_classes": r["n_classes"], "channels": r["channels"],
            "train_size": r["train_size"], "val_size": r["val_size"],
            "test_size": r["test_size"], "model": r["model"],
            "best_epoch": r["best_epoch"],
            "normalize": r["normalize"],
            "val_auc": r["val_auc"], "test_auc": r["test_auc"], "test_acc": r["test_acc"],
            "paper_auc": PAPER_ANCHOR[name]["auc"], "paper_acc": PAPER_ANCHOR[name]["acc"],
            "delta_auc_vs_paper": round(r["test_auc"] - PAPER_ANCHOR[name]["auc"], 4),
            "delta_acc_vs_paper": round(r["test_acc"] - PAPER_ANCHOR[name]["acc"], 4),
            "verdict": build_verdict(name, r),
        }
        auc_order.append((name, r["test_auc"]))

    # difficulty ordering
    our_order = [n for n, _ in sorted(auc_order, key=lambda t: -t[1])]
    paper_order = ["bloodmnist", "pneumoniamnist", "dermamnist", "breastmnist", "retinamnist"]
    metrics["difficulty"] = {
        "ours_by_test_auc": our_order,
        "paper_anchor_order": paper_order,
        "fully_consistent": our_order == paper_order,
    }

    # overall conclusion label (four-way verdict)
    all_in_range = all(metrics["datasets"][n]["verdict"] == "in_range"
                       for n in metrics["datasets"])
    order_ok = metrics["difficulty"]["fully_consistent"]
    n_below = sum(1 for n in metrics["datasets"]
                  if metrics["datasets"][n]["verdict"] == "below_paper_range")
    n_above = sum(1 for n in metrics["datasets"]
                  if metrics["datasets"][n]["verdict"] == "above_paper_range")
    if all_in_range and order_ok:
        label = "supported"
    elif n_below <= 2:
        label = "partially_supported"
    elif all(metrics["datasets"][n]["verdict"] == "below_paper_range"
             for n in metrics["datasets"]):
        label = "contradicted"
    else:
        label = "inconclusive"
    metrics["conclusion"] = {
        "label": label,
        "all_datasets_in_verify_range": all_in_range,
        "n_below_range": n_below,
        "n_above_range": n_above,
        "difficulty_ordering_consistent": order_ok,
        "note": "Verdict based on test AUC falling inside the rubric A3 ranges for all five "
                "datasets and on the dataset difficulty ordering matching the paper.",
    }

    from collections import Counter
    metrics["class_counts_train"] = {}
    for name, _, _ in datasets:
        dd = np.load(os.path.join(data_dir, f"{name}.npz"))
        metrics["class_counts_train"][name] = \
            dict(sorted(Counter(dd["train_labels"].squeeze().astype(int).tolist()).items()))

    with open(os.path.join(args.out_dir, "metrics.json"), "w") as f:
        json.dump(metrics, f, indent=2, sort_keys=False)
    print(f"Wrote {args.out_dir}/metrics.json")
    print(f"\nDifficulty ordering (test AUC desc): {our_order}")


if __name__ == "__main__":
    main()