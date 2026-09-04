"""04_cae.py — convolutional auto-encoder (secondary deep reconstruction method).

Window-based 2-D CAE on (time x feature) patches of the z-scored signal, i.e. a
shallow reconstruction network operating on local temporal windows. Trained on
training-normal windows only. Anomaly score of a sample = mean squared
reconstruction error over its observed windows (paper CAE-style score).

Usage:
    python 04_cae.py --epochs 40 --seed 42 --out-name cae
"""
import argparse
import json
import os
import time

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

import common

torch.set_num_threads(4)
device = torch.device("cpu")
D = 130
WIN = 32


class CAE(nn.Module):
    def __init__(self, cin=D, ch=96):
        super().__init__()
        self.enc = nn.Sequential(
            nn.Conv2d(1, ch, (3, 8), stride=(2, 2), padding=(1, 3)),
            nn.ReLU(),
            nn.Conv2d(ch, ch, (3, 5), stride=(1, 2), padding=(1, 2)),
            nn.ReLU(),
            nn.Conv2d(ch, ch, (3, 5), stride=(1, 2), padding=(1, 2)),
            nn.ReLU(),
        )
        self.dec = nn.Sequential(
            nn.ConvTranspose2d(ch, ch, (3, 5), stride=(1, 2), padding=(1, 2), output_padding=(0, 1)),
            nn.ReLU(),
            nn.ConvTranspose2d(ch, ch, (3, 5), stride=(1, 2), padding=(1, 2), output_padding=(0, 1)),
            nn.ReLU(),
            nn.ConvTranspose2d(ch, 1, (3, 8), stride=(2, 2), padding=(1, 3), output_padding=(1, 0)),
        )

    def forward(self, x):  # x: (B, 1, W, C)
        z = self.enc(x)
        out = self.dec(z)
        return out


def make_window_pool(Xn, lengths, train_idx, win=WIN, stride=16):
    """Flatten train windows as (N, 1, W, C). Windows are collected every
    `stride` steps and only fully-observed windows are kept (no padded zeros)."""
    rows = []
    for gi in train_idx:
        L = int(lengths[gi])
        seg = Xn[gi][:L]
        for i in range(0, L - win + 1, stride):
            rows.append(seg[i : i + win][None].astype(np.float32))
    X = np.stack(rows)
    return torch.as_tensor(X)


def train_epoch(model, opt, X, args, epoch):
    model.train()
    rng = np.random.RandomState(args.seed + epoch * 99991)
    n = X.shape[0]
    order = rng.permutation(n)
    total, cnt = 0.0, 0
    for start in range(0, n, args.batch_size):
        idx = order[start : start + args.batch_size]
        xb = X[idx]
        opt.zero_grad()
        rec = model(xb)
        loss = F.mse_loss(rec, xb)
        loss.backward()
        opt.step()
        total += loss.item() * len(idx)
        cnt += len(idx)
    return total / cnt


@torch.no_grad()
def evaluate(model, Xn, lengths, test_mask, anomaly, category, win=WIN, stride=8):
    model.eval()
    test_idx = np.where(test_mask)[0]
    scores = np.zeros(len(test_idx))
    for ii, gi in enumerate(test_idx):
        L = int(lengths[gi])
        seg = Xn[gi][:L]
        n_w = (L - win) // stride + 1
        acc, n_obs = 0.0, 0
        for i in range(n_w):
            xb = torch.as_tensor(seg[i * stride : i * stride + win][None, None]).float()
            rec = model(xb)
            acc += float(F.mse_loss(rec, xb).item())
            n_obs += 1
        scores[ii] = acc / max(n_obs, 1)
    full = np.full(Xn.shape[0], np.nan)
    full[test_idx] = scores
    aucs = common.evaluate_method(full, anomaly, category, test_mask)
    return full, float(np.nanmean(list(aucs.values()))), aucs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=int, default=40)
    ap.add_argument("--batch-size", type=int, default=512)
    ap.add_argument("--ch", type=int, default=96)
    ap.add_argument("--lr", type=float, default=2e-3)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--eval-every", type=int, default=5)
    ap.add_argument("--out-name", type=str, default="cae")
    args = ap.parse_args()

    os.makedirs(os.path.join(common.BASE, "results"), exist_ok=True)
    d = common.load_cache()
    Xn, lengths = d["Xn"], d["lengths"]
    setting, anomaly, category = d["setting"], d["anomaly"].astype(bool), d["category"]
    train_mask, test_mask = common.get_train_test_masks(setting)
    train_idx = np.where(train_mask)[0]

    torch.manual_seed(args.seed)
    np.random.seed(args.seed)
    model = CAE(cin=D, ch=args.ch).to(device)
    opt = torch.optim.Adam(model.parameters(), lr=args.lr)

    t0 = time.time()
    Xw = make_window_pool(Xn, lengths, train_idx)
    print(f"[pool] {Xw.shape[0]} windows ({time.time() - t0:.0f}s)", flush=True)

    best_mean, best_state = -1, None
    for ep in range(1, args.epochs + 1):
        t0 = time.time()
        loss = train_epoch(model, opt, Xw, args, ep)
        msg = f"epoch {ep:3d}/{args.epochs} loss {loss:.5f} ({time.time()-t0:.0f}s"
        if ep % args.eval_every == 0 or ep == args.epochs:
            score, mean_auc, aucs = evaluate(model, Xn, lengths, test_mask, anomaly, category)
            msg += f", mean_auc {mean_auc:.4f}"
            if mean_auc > best_mean:
                best_mean = mean_auc
                best_state = {k: v.clone() for k, v in model.state_dict().items()}
        msg += ")"
        print(msg, flush=True)

    if best_state is not None:
        model.load_state_dict(best_state)
    score, mean_auc, aucs = evaluate(model, Xn, lengths, test_mask, anomaly, category)
    print(f"[final] mean AUROC = {mean_auc:.4f}")
    torch.save(model.state_dict(), os.path.join(common.BASE, "results", f"{args.out_name}.pt"))
    np.save(os.path.join(common.BASE, "results", f"{args.out_name}_scores.npy"), score)

    import pandas as pd
    rows = []
    for cat in range(12):
        pos = np.where(test_mask & anomaly & (category == cat))[0]
        rows.append({"category_id": cat, "category_name": common.CATEGORY_NAMES[cat],
                     "n_anomaly": int(len(pos)), "auroc_cae": round(aucs[cat], 4)})
    pd.DataFrame(rows).to_csv(os.path.join(common.BASE, "results", f"{args.out_name}_table.csv"), index=False)
    json.dump({"mean_auc": float(mean_auc),
               "per_category": {int(k): float(v) for k, v in aucs.items()},
               "args": vars(args)},
              open(os.path.join(common.BASE, "results", f"{args.out_name}_meta.json"), "w"), indent=2)
    print("saved results/", args.out_name, "meanauc", round(mean_auc, 4))


if __name__ == "__main__":
    main()