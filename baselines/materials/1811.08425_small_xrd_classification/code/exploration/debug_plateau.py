"""Diagnose why the small CNN plateaus at the majority class."""
import numpy as np
import torch
import torch.nn as nn
from collections import Counter

import config
from data_loader import load_data


def make_feat(kernels, strides, filters=32, pool=True):
    layers = []
    in_ch = 1
    for k, s in zip(kernels, strides):
        layers.append(nn.Conv1d(in_ch, filters, k, s, padding=k // 2))
        layers.append(nn.ReLU())
        in_ch = filters
    if pool:
        layers.append(nn.AdaptiveAvgPool1d(1))
    return nn.Sequential(*layers)


def run(Xtr, ytr, kernels, strides, loss="ce", lr=1e-3, epochs=100,
        filters=32, seed=0, device="cuda"):
    torch.manual_seed(seed)
    feat = make_feat(kernels, strides, filters).to(device)
    head = nn.Linear(filters, 7).to(device)
    opt = torch.optim.Adam(list(feat.parameters()) + list(head.parameters()),
                           lr=lr)
    Xt = torch.from_numpy(Xtr.astype(np.float32)).to(device)
    yt = torch.from_numpy(ytr.astype(np.int64)).to(device)
    for e in range(epochs):
        feat.train(); head.train()
        perm = torch.randperm(len(Xt))
        for i in range(0, len(Xt), 128):
            idx = perm[i:i + 128]
            xb, yb = Xt[idx], yt[idx]
            opt.zero_grad()
            logits = head(feat(xb.unsqueeze(1)).squeeze(-1))
            lo = (nn.functional.cross_entropy(logits, yb) if loss == "ce"
                  else nn.functional.binary_cross_entropy_with_logits(
                      logits, nn.functional.one_hot(yb, 7).float()))
            lo.backward(); opt.step()
        if e in (0, 9, 49, 99):
            feat.eval(); head.eval()
            with torch.no_grad():
                logits = head(feat(Xt.unsqueeze(1)).squeeze(-1))
                p = logits.argmax(1).cpu().numpy()
                lo = (nn.functional.cross_entropy(logits, yt).item() if loss
                      == "ce" else nn.functional.binary_cross_entropy_with_logits(
                          logits, nn.functional.one_hot(yt, 7).float()).item())
            print(f"  {loss} lr{lr} k{kernels} s{strides}: ep{e} "
                  f"train_acc {(p==ytr).mean():.3f} loss {lo:.3f} "
                  f"dist {dict(Counter(p))}")


if __name__ == "__main__":
    d = load_data()
    Xtr, ytr = d["X_exp"][:70], d["y_exp"][:70]
    print("labels", dict(Counter(ytr.tolist())))
    print("== exp-only (70 samples), stride 1 ==")
    for loss in ("ce", "bce"):
        for lr in (1e-3, 3e-3, 1e-2):
            run(Xtr, ytr, [8, 5, 3], [1, 1, 1], loss, lr)
    print("== exp+sim, stride 1 ==")
    Xa = np.concatenate([Xtr, d["X_theo"]])
    ya = np.concatenate([ytr, d["y_theo"]])
    run(Xa, ya, [8, 5, 3], [1, 1, 1], "ce", 1e-3)
