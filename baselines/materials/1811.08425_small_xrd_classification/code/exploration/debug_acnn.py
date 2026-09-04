"""Tune the a-CNN (GAP) to break the feature-collapse: test input reps,
BatchNorm, lr, epochs, and fully-convolutional head variants."""
import numpy as np
import torch
import torch.nn as nn
from sklearn.model_selection import StratifiedKFold

import config
from data_loader import load_data, preprocess
from augmentation import make_augmented

torch.set_num_threads(16)


def make(kerns, strids, filters, bn=False, fconv=False, drop=0.0):
    layers = []
    in_ch = 1
    for k, s in zip(kerns, strids):
        out = 7 if (fconv and (k, s) == zip(kerns, strids)[-1]) else filters
        layers.append(nn.Conv1d(in_ch, out, k, s, padding=k // 2))
        if bn:
            layers.append(nn.BatchNorm1d(out))
        if not (fconv and (k, s) == zip(kerns, strids)[-1]):
            layers.append(nn.ReLU())
            if drop:
                layers.append(nn.Dropout(drop))
        in_ch = out
    layers.append(nn.AdaptiveAvgPool1d(1))
    feat = nn.Sequential(*layers)
    head = None if fconv else nn.Linear(filters, 7)
    return feat, head


def train(Xtr, ytr, Xte, yte, feat, head, epochs=250, lr=1e-2, seed=0,
          device="cuda"):
    torch.manual_seed(seed)
    feat.to(device)
    if head is not None:
        head.to(device)
    params = (list(feat.parameters()) + (list(head.parameters())
              if head is not None else []))
    opt = torch.optim.Adam(params, lr=lr)
    Xt = torch.from_numpy(Xtr.astype(np.float32)).to(device)
    yt = torch.from_numpy(ytr.astype(np.int64)).to(device)
    Xtt = torch.from_numpy(Xte.astype(np.float32)).to(device)
    for e in range(epochs):
        feat.train()
        if head is not None:
            head.train()
        perm = torch.randperm(len(Xt))
        for i in range(0, len(Xt), 128):
            idx = perm[i:i + 128]
            xb, yb = Xt[idx], yt[idx]
            z = feat(xb.unsqueeze(1)).squeeze(-1)
            lo = (nn.functional.cross_entropy(z, yb) if head is None
                  else nn.functional.cross_entropy(head(z), yb))
            opt.zero_grad(); lo.backward(); opt.step()
    feat.eval()
    with torch.no_grad():
        z = feat(Xtt.unsqueeze(1)).squeeze(-1)
        p = (z if head is None else head(z)).argmax(1).cpu().numpy()
    return (p == yte).mean()


def main():
    d = load_data(preprocessed=False)
    Xe_raw, ye, Xs_raw, ys = d["X_exp"], d["y_exp"], d["X_theo"], d["y_theo"]
    tw = d["tw"]
    reps = {
        "raw_max": lambda X: X / X.max(1, keepdims=True),
        "preproc": preprocess,
    }
    skf = StratifiedKFold(5, shuffle=True, random_state=config.CV_SEED)
    tr, te = next(iter(skf.split(Xe_raw, ye)))
    configs = [
        # name, kerns, strids, filters, bn, fconv, lr, epochs
        ("s1_f32_bn", [8, 5, 3], [1, 1, 1], 32, True, False, 1e-2, 200),
        ("s1_f64_bn", [8, 5, 3], [1, 1, 1], 64, True, False, 1e-2, 200),
        ("s1_f128_bn", [8, 5, 3], [1, 1, 1], 128, True, False, 1e-2, 200),
        ("s1_f32_fconv", [8, 5, 3], [1, 1, 1], 32, True, True, 1e-2, 200),
        ("s222_f64_bn", [8, 5, 3], [2, 2, 2], 64, True, False, 1e-2, 200),
        ("s222_f128_bn", [8, 5, 3], [2, 2, 2], 128, True, False, 1e-2, 200),
    ]
    for rep_name, repf in reps.items():
        Xe = repf(Xe_raw)
        Xtr, ytr, Xte, yte = Xe[tr], ye[tr], Xe[te], ye[te]
        # with augmentation
        rng = np.random.default_rng(config.AUG_SEED)
        Xae, yae = make_augmented(Xtr, tw, 1500, rng, label=None); yae = ytr[yae]
        Xas, yas = make_augmented(repf(Xs_raw), tw, 1500, rng, label=None); yas = ys[yas]
        Xb = np.concatenate([Xtr, Xs := repf(Xs_raw), Xae, Xas])
        yb = np.concatenate([ytr, ys, yae, yas])
        print(f"=== {rep_name} exp+sim+aug (n={len(Xb)}) ===")
        for cname, k, s, f, bn, fconv, lr, ep in configs:
            feat, head = make(k, s, f, bn=bn, fconv=fconv)
            acc = train(Xb, yb, Xte, yte, feat, head, epochs=ep, lr=lr)
            print(f"  {cname:18s} test acc {acc:.4f}")


if __name__ == "__main__":
    main()
