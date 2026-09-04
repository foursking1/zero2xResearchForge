"""Inspect why the GAP-CNN underperforms: check feature separability and
try high-capacity GAP variants."""
import numpy as np
import torch
import torch.nn as nn

import config
from data_loader import load_data
from augmentation import make_augmented
from sklearn.model_selection import StratifiedKFold
from sklearn.neighbors import KNeighborsClassifier

torch.set_num_threads(16)


def build_acnn(kerns, strids, filters, head=None, bn=False):
    layers = []
    in_ch = 1
    for k, s in zip(kerns, strids):
        layers.append(nn.Conv1d(in_ch, filters, k, s, padding=k // 2))
        if bn:
            layers.append(nn.BatchNorm1d(filters))
        layers.append(nn.ReLU())
        in_ch = filters
    layers.append(nn.AdaptiveAvgPool1d(1))
    feat = nn.Sequential(*layers)
    if head is None:
        head = nn.Linear(filters, 7)
    return feat, head


def train_cnn(Xtr, ytr, feat, head, epochs=200, lr=1e-3, seed=0, device="cuda"):
    torch.manual_seed(seed)
    feat.to(device); head.to(device)
    opt = torch.optim.Adam(list(feat.parameters()) + list(head.parameters()), lr=lr)
    Xt = torch.from_numpy(Xtr.astype(np.float32)).to(device)
    yt = torch.from_numpy(ytr.astype(np.int64)).to(device)
    for e in range(epochs):
        feat.train(); head.train()
        perm = torch.randperm(len(Xt))
        for i in range(0, len(Xt), 128):
            idx = perm[i:i + 128]
            xb, yb = Xt[idx], yt[idx]
            opt.zero_grad()
            lo = nn.functional.cross_entropy(head(feat(xb.unsqueeze(1)).squeeze(-1)), yb)
            lo.backward(); opt.step()
    feat.eval(); head.eval()
    return feat, head


def feats_of(feat, X, device="cuda"):
    Xt = torch.from_numpy(X.astype(np.float32)).to(device)
    with torch.no_grad():
        return feat(Xt.unsqueeze(1)).squeeze(-1).cpu().numpy()


def main():
    d = load_data()
    Xe, ye, Xs, ys = d["X_exp"], d["y_exp"], d["X_theo"], d["y_theo"]
    skf = StratifiedKFold(5, shuffle=True, random_state=config.CV_SEED)
    tr, te = next(iter(skf.split(Xe, ye)))
    Xtr, ytr, Xte, yte = Xe[tr], ye[tr], Xe[te], ye[te]
    Xa = np.concatenate([Xtr, Xs]); ya = np.concatenate([ytr, ys])

    for fname, filters in [("f32", 32), ("f64", 64), ("f128", 128), ("f256", 256)]:
        feat, head = build_acnn([8, 5, 3], [1, 1, 1], filters)
        feat, head = train_cnn(Xa, ya, feat, head, epochs=200)
        Ftr = feats_of(feat, Xa)
        Fte = feats_of(feat, Xte)
        knn = KNeighborsClassifier(3).fit(Ftr, ya)
        acc_knn = knn.score(Fte, yte)
        with torch.no_grad():
            Xtt = torch.from_numpy(Xte.astype(np.float32)).to("cuda")
            p = head(torch.from_numpy(Fte.astype(np.float32)).to("cuda")).argmax(1).cpu().numpy()
        acc_head = (p == yte).mean()
        print(f"GAP-CNN {fname}: feature-kNN test acc {acc_knn:.3f} | head test acc {acc_head:.3f} | "
              f"F std {Fte.std():.4f}")

    # headless check: how separable are GAP features of f256?
    feat, head = build_acnn([8, 5, 3], [1, 1, 1], 256)
    feat, head = train_cnn(Xa, ya, feat, head, epochs=200)
    Ftr = feats_of(feat, Xa); Fte = feats_of(feat, Xte)
    Fte_norm = Fte / (np.linalg.norm(Fte, axis=1, keepdims=True) + 1e-9)
    print("GAP-f256 feature norms: mean %.3f std %.3f min %.3f max %.3f"
          % (Fte_norm.std(1).mean(), Fte_norm.std(1).std(), Fte_norm.std(1).min(), Fte_norm.std(1).max()))


if __name__ == "__main__":
    main()
