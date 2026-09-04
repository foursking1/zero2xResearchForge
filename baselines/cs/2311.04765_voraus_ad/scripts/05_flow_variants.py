"""05_flow_variants.py — quick sweep of preprocessing/model variants to select
the best configuration for the main MVT-Flow-style model.

Variants:
  global_bs256 : z-score w/ training stats; small batch => more optimizer
                 steps (paper-style); lower LR
  persamp      : per-sample standardization of each signal (its own mean/std)
  delta        : global z-score + 1-lag differences concatenated (260 dims)

Each variant trains the same CondRealNVP for `epochs` epochs and reports the
12-class mean AUROC. Runs on GPU if available (tiny model).

Usage: python 05_flow_variants.py
"""
import argparse
import json
import os
import time

import numpy as np
import torch

import common
import mvtflow_module as MF
from mvtflow_module import CondRealNVP, D, device, evaluate, train_epoch


def make_train_pool(Xn, lengths, action, train_idx, kind):
    rows_x, rows_a = [], []
    for gi in train_idx:
        L = int(lengths[gi])
        seg = Xn[gi][:L]
        if kind == "persamp":
            seg = seg.copy()
            m = seg.mean(axis=0, keepdims=True)
            s = seg.std(axis=0, keepdims=True)
            seg = (seg - m) / np.where(s < 1e-8, 1.0, s)
            rows_x.append(seg)
        elif kind == "delta":
            dseg = np.diff(seg, axis=0, prepend=seg[:1])
            rows_x.append(np.concatenate([seg, dseg], axis=1))
        else:
            rows_x.append(seg)
        rows_a.extend([action[gi]] * L)
    return np.concatenate(rows_x).astype(np.float32), np.array(rows_a, dtype=np.int64)


def make_test_pool(Xn, lengths, test_idx, kind, rows2global):
    segs = []
    off = 0
    for gi in test_idx:
        L = int(lengths[gi])
        seg = Xn[gi][:L]
        if kind == "persamp":
            seg = seg.copy()
            m = seg.mean(axis=0, keepdims=True)
            s = seg.std(axis=0, keepdims=True)
            seg = (seg - m) / np.where(s < 1e-8, 1.0, s)
        elif kind == "delta":
            dseg = np.diff(seg, axis=0, prepend=seg[:1])
            seg = np.concatenate([seg, dseg], axis=1)
        rows2global[gi] = (off, off + L)
        segs.append(seg)
        off += L
    return np.concatenate(segs).astype(np.float32)


def run_variant(name, args, d):
    torch.manual_seed(args.seed)
    np.random.seed(args.seed)
    Xn, lengths = d["Xn"], d["lengths"]
    setting, anomaly, category, action = d["setting"], d["anomaly"].astype(bool), d["category"], d["action"]
    train_mask, test_mask = common.get_train_test_masks(setting)
    train_idx = np.where(train_mask)[0]
    test_idx = np.where(test_mask)[0]

    D_feat = D if args.feat != "delta" else 2 * D
    t0 = time.time()
    Xp, Ap = make_train_pool(Xn, lengths, action, train_idx, args.feat)
    rows2global = {}
    Xte = None
    if args.feat in ("persamp", "delta"):
        Xte = make_test_pool(Xn, lengths, test_idx, args.feat, rows2global)
    print(f"[{name}] pool {Xp.shape} ({time.time()-t0:.0f}s)", flush=True)

    model = CondRealNVP(d=D_feat, n_blocks=args.n_blocks, ctx_dim=32, hidden=args.hidden).to(device)
    opt = torch.optim.Adam(model.parameters(), lr=args.lr)

    best_mean, best_state = -1, None
    for ep in range(1, args.epochs + 1):
        t0 = time.time()
        tr_loss = train_epoch(model, opt, Xp, Ap, args, ep, d_feat=D_feat)
        if ep % args.eval_every == 0 or ep == args.epochs:
            score, mean_auc, aucs = evaluate(
                model, Xn, lengths, action, test_mask, anomaly, category,
                d_feat=D_feat, pool=Xte, rows2global=rows2global)
            if mean_auc > best_mean:
                best_mean = mean_auc
                best_state = {k: v.clone() for k, v in model.state_dict().items()}
            print(f"[{name}] ep {ep:3d} loss {tr_loss:.1f} mean_auc {mean_auc:.4f} "
                  f"(best {best_mean:.4f})", flush=True)
    return best_mean, best_state


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=int, default=40)
    ap.add_argument("--batch-size", type=int, default=2048)
    ap.add_argument("--lr", type=float, default=8e-4)
    ap.add_argument("--hidden", type=int, default=256)
    ap.add_argument("--n-blocks", type=int, default=4)
    ap.add_argument("--subsample", type=float, default=1.0)
    ap.add_argument("--eval-every", type=int, default=5)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    os.makedirs(os.path.join(common.BASE, "results"), exist_ok=True)
    d = common.load_cache()

    variants = [
        ("global_bs256", "global"),
        ("persamp", "persamp"),
        ("delta", "delta"),
    ]
    out = {}
    for name, feat in variants:
        va = argparse.Namespace(**vars(args))
        va.feat = feat
        if name == "global_bs256":
            va.batch_size = 256
            va.lr = 2e-4
            va.subsample = 0.25
        best, _ = run_variant(name, va, d)
        out[name] = round(float(best), 4)
        print(f"[summary] {name}: best mean AUROC = {out[name]}", flush=True)

    with open(os.path.join(common.BASE, "results", "flow_variants.json"), "w") as f:
        json.dump(out, f, indent=2)


if __name__ == "__main__":
    main()