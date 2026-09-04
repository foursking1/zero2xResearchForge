"""Model capacity / architecture search on the single split (exp-only 80%)."""
import numpy as np
import torch
import torch.nn as nn
from collections import Counter

import config
from data_loader import load_data


def build(variant, n_in, filters=32, device="cuda"):
    m = nn.Module()
    def conv_layers(kerns, strids, filt, pool_gap=True, flatten_dense=None,
                    bn=False, dropout=0.0):
        layers = []
        in_ch = 1
        for k, s in zip(kerns, strids):
            layers.append(nn.Conv1d(in_ch, filt, k, s, padding=k // 2))
            if bn:
                layers.append(nn.BatchNorm1d(filt))
            layers.append(nn.ReLU())
            if dropout:
                layers.append(nn.Dropout(dropout))
            in_ch = filt
        if pool_gap:
            layers.append(nn.AdaptiveAvgPool1d(1))
            head_in = filt
            head = nn.Linear(head_in, 7)
        elif flatten_dense:
            head_in = flatten_dense
            head = nn.Sequential(nn.Linear(in_ch, head_in), nn.ReLU(),
                                 nn.Linear(head_in, 7))
        else:
            head_in = in_ch
            head = nn.Linear(head_in, 7)
        return layers, head
    kerns, strids = variant
    layers, head = conv_layers(kerns, strids, filters)
    feat = nn.Sequential(*layers)
    return feat, head


def run(Xtr, ytr, variant, filters=32, lr=1e-3, epochs=150, seed=0,
        device="cuda", weight_decay=0.0, dropout=0.0, bn=False):
    kerns, strids = variant
    torch.manual_seed(seed)
    feat = nn.Sequential(*[
        nn.Conv1d(1 if i == 0 else filters, filters, k, s, padding=k // 2)
        for i, (k, s) in enumerate(zip(kerns, strids))
    ])
    if bn:
        pass  # (handled below)
    head = nn.Linear(filters, 7)
    layers = []
    in_ch = 1
    for k, s in zip(kerns, strids):
        layers.append(nn.Conv1d(in_ch, filters, k, s, padding=k // 2))
        if bn:
            layers.append(nn.BatchNorm1d(filters))
        layers.append(nn.ReLU())
        in_ch = filters
    feat = nn.Sequential(*layers, nn.AdaptiveAvgPool1d(1))
    head = nn.Linear(filters, 7)
    feat.to(device); head.to(device)
    opt = torch.optim.Adam(list(feat.parameters()) + list(head.parameters()),
                           lr=lr, weight_decay=weight_decay)
    Xt = torch.from_numpy(Xtr.astype(np.float32)).to(device)
    yt = torch.from_numpy(ytr.astype(np.int64)).to(device)
    best = 0
    for e in range(epochs):
        feat.train(); head.train()
        perm = torch.randperm(len(Xt))
        for i in range(0, len(Xt), 128):
            idx = perm[i:i + 128]
            xb, yb = Xt[idx], yt[idx]
            opt.zero_grad()
            lo = nn.functional.cross_entropy(head(feat(xb.unsqueeze(1)).squeeze(-1)), yb)
            lo.backward(); opt.step()
        if e >= epochs - 5 or e in (49, 99):
            feat.eval(); head.eval()
            with torch.no_grad():
                p = head(feat(Xt.unsqueeze(1)).squeeze(-1)).argmax(1).cpu().numpy()
            acc = (p == ytr).mean()
            best = max(best, acc)
    return best


if __name__ == "__main__":
    d = load_data()
    # also raw+max variant
    Xr = d["X_exp"] / d["X_exp"].max(axis=1, keepdims=True)
    for name, Xall in [("preproc-minmax", d["X_exp"]), ("raw+max", Xr)]:
        Xtr, ytr = Xall[:70], d["y_exp"][:70]
        print(f"=== {name} exp-only ===")
        variants = {
            "c3_s111_f32": ([8, 5, 3], [1, 1, 1]),
            "c3_s111_f64": ([8, 5, 3], [1, 1, 1]),
            "c3_s111_f128": ([8, 5, 3], [1, 1, 1]),
            "c3_s222_f64": ([8, 5, 3], [2, 2, 2]),
            "c3_s444_f64": ([8, 5, 3], [4, 4, 4]),
            "c4_s222_f64": ([16, 8, 4, 2], [2, 2, 2, 2]),
        }
        for vname, v in variants.items():
            filters = int(vname.split("f")[1])
            best = run(Xtr, ytr, v, filters=filters, epochs=150)
            print(f"  {vname}: train acc {best:.3f}")
