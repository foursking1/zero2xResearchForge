#!/usr/bin/env python3
"""Step 5 - Light last-stage fine-tuning of an ImageNet CNN (optional head).

Mirrors the paper's "adaptation" viewpoint: keep the ImageNet encoder frozen up
to layer3 and fine-tune only the final CNN stage (layer4) plus a linear head,
with strong on-the-fly augmentation (rot90/h-flip/v-flip). This is a low-rank,
parameter-cheap head analogous to the paper's LoRA-style transfer, scaled to
the 153-patch frozen subset.

Protocol mirrors step 3: stratified 5-fold CV with the same split seed,
evaluated on rotation-0 crops, probabilities pooled across folds.  `--seeds`
repeats the whole CV with de-correlated split seeds and *averages the pooled
probabilities* (bagged ensemble) which stabilises the tiny-sample estimate.

Appends a row to results/evidence_table.csv and pooled predictions to
results/fold_predictions.csv; adds metrics to results/classifier_detail.json.
"""
from __future__ import annotations
import argparse
import csv
import json
import os
import os.path as osp
import sys
import time

for _k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ.setdefault(_k, os.environ.get(_k, "2"))

sys.path.insert(0, osp.dirname(osp.abspath(__file__)))

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader
from sklearn.metrics import balanced_accuracy_score, f1_score, roc_auc_score
from sklearn.model_selection import StratifiedKFold


def make_net(device):
    from torchvision import models
    base = models.resnet18(weights=models.ResNet18_Weights.IMAGENET1K_V1)
    for name, p in base.named_parameters():
        p.requires_grad = name.startswith(("layer4.", "fc."))
    base.fc = nn.Linear(512, 2)
    return base.to(device)


def augment(xb):
    """xb: (B,3,H,W) in [0,1]. Returns random rot90 + flips."""
    b = xb.shape[0]
    ks = torch.randint(0, 4, (b,))
    xs = torch.stack([torch.rot90(xb[i], int(ks[i]), dims=(1, 2)) for i in range(b)])
    hf = torch.randint(0, 2, (b,))
    xs = torch.stack([torch.flip(xs[i], [2]) if hf[i] else xs[i] for i in range(b)])
    vf = torch.randint(0, 2, (b,))
    xs = torch.stack([torch.flip(xs[i], [1]) if vf[i] else xs[i] for i in range(b)])
    return xs


def train_one_fold(net, Xtr, ytr, Xte, device, epochs, lr, bs):
    opt = torch.optim.AdamW([p for p in net.parameters() if p.requires_grad], lr=lr)
    crit = nn.CrossEntropyLoss()
    mean = torch.tensor([0.485, 0.456, 0.406], device=device).view(1, 3, 1, 1)
    std = torch.tensor([0.229, 0.224, 0.225], device=device).view(1, 3, 1, 1)
    n = len(Xtr)
    for ep in range(epochs):
        perm = torch.randperm(n)
        net.train()
        for i in range(0, n, bs):
            idx = perm[i:i + bs]
            xb = torch.from_numpy(Xtr[idx]).permute(0, 3, 1, 2).float()[:, :3].to(device) / 255.0
            yb = torch.from_numpy(ytr[idx]).long().to(device)
            xb = augment(xb)
            xb = (xb - mean) / std
            opt.zero_grad()
            loss = crit(net(xb), yb)
            loss.backward()
            opt.step()
    net.eval()
    with torch.no_grad():
        te = torch.from_numpy(Xte).permute(0, 3, 1, 2).float()[:, :3].to(device) / 255.0
        te = (te - mean) / std
        prob = torch.softmax(net(te), 1).cpu().numpy()[:, 1]
    return prob


def run_ft(X, y, *, device, folds=5, seed0=0, epochs=30, lr=5e-4, bs=16, seeds=1):
    """Pooled bagged ensemble: mean probability over `seeds` CV repetitions."""
    n = len(y)
    acc = np.zeros((n, 3))
    acc[:, 0] = np.arange(n)
    acc[:, 1] = y
    for rep in range(seeds):
        skf = StratifiedKFold(n_splits=folds, shuffle=True, random_state=seed0 + rep * 37)
        for tr_idx, te_idx in skf.split(np.arange(n), y):
            net = make_net(device)
            prob = train_one_fold(net, X[tr_idx], y[tr_idx], X[te_idx], device,
                                  epochs, lr, bs)
            acc[te_idx, 2] += prob
    acc[:, 2] /= seeds
    return acc


def metrics(acc):
    yt = acc[:, 1].astype(int)
    yp = (acc[:, 2] >= 0.5).astype(int)
    return {
        "balanced_acc": float(balanced_accuracy_score(yt, yp)),
        "weighted_f1": float(f1_score(yt, yp, average="weighted", zero_division=0)),
        "auroc": float(roc_auc_score(yt, acc[:, 2])),
        "n_pooled_predictions": int(len(acc)),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", default="cpu", choices=["cpu", "cuda"])
    ap.add_argument("--epochs", type=int, default=30)
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--folds", type=int, default=5)
    ap.add_argument("--lr", type=float, default=5e-4)
    ap.add_argument("--batch-size", type=int, default=16)
    args = ap.parse_args()

    res_dir = osp.join(osp.dirname(osp.abspath(__file__)), "..", "results")
    pz = np.load(osp.join(res_dir, "patches.npz"), allow_pickle=True)
    X, y = pz["X"], pz["y"]
    device = torch.device(args.device)
    print(f"device={device} patches={X.shape} y={y.shape}", flush=True)

    torch.manual_seed(0)
    t0 = time.time()
    acc = run_ft(X, y, device=device, folds=args.folds, epochs=args.epochs,
                 lr=args.lr, bs=args.batch_size, seeds=args.seeds)
    m = metrics(acc)
    print(f"FT-ResNet18-layer4+head bagged({args.seeds} seeds): "
          f"BAcc={m['balanced_acc']:.3f} WF1={m['weighted_f1']:.3f} AUROC={m['auroc']:.3f} "
          f"[{time.time()-t0:.0f}s]", flush=True)

    tag = f"FT-ResNet18-layer4+head|100%"
    model_name = "FT-ResNet18-layer4+head"
    table_path = osp.join(res_dir, "evidence_table.csv")
    with open(table_path, "r", newline="") as f:
        existing = [dict(r) for r in csv.DictReader(f)]
    with open(table_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["model", "data_fraction", "balanced_acc", "weighted_f1", "auroc"])
        w.writeheader()
        for r in existing:
            w.writerow(r)
        w.writerow({"model": model_name, "data_fraction": 1.0,
                    "balanced_acc": round(m["balanced_acc"], 4),
                    "weighted_f1": round(m["weighted_f1"], 4),
                    "auroc": round(m["auroc"], 4)})

    pred_path = osp.join(res_dir, "fold_predictions.csv")
    existing_preds = []
    if osp.isfile(pred_path):
        with open(pred_path, "r", newline="") as f:
            existing_preds = list(csv.DictReader(f))
    with open(pred_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["config", "patch_idx", "true_label", "prob_positive"])
        w.writeheader()
        for r in existing_preds:
            w.writerow(r)
        for i in range(len(acc)):
            w.writerow({"config": tag, "patch_idx": int(acc[i, 0]),
                        "true_label": int(acc[i, 1]),
                        "prob_positive": round(float(acc[i, 2]), 6)})

    detail_path = osp.join(res_dir, "classifier_detail.json")
    detail = {}
    if osp.isfile(detail_path):
        with open(detail_path) as f:
            detail = json.load(f)
    detail[tag] = {"metrics": {k: round(v, 4) for k, v in m.items()},
                   "train_frac": 1.0,
                   "note": "ImageNet ResNet18, layer4+fc fine-tuned, rot/flip aug, bagged CV"}
    with open(detail_path, "w") as f:
        json.dump(detail, f, indent=2)


if __name__ == "__main__":
    main()