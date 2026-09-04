"""Test GAP-CNN on richer input reps (standardized) to break feature collapse.

Also test flattened-CNN variants properly. Reports test acc + feature norm.
"""
import numpy as np
import torch
import torch.nn as nn
from sklearn.model_selection import StratifiedKFold
from sklearn.neighbors import KNeighborsClassifier

import config
from data_loader import load_data
from augmentation import make_augmented

torch.set_num_threads(16)


def make_cnn(kerns, strids, filters, gap=True, bn=True):
    layers = []
    in_ch = 1
    for k, s in zip(kerns, strids):
        layers.append(nn.Conv1d(in_ch, filters, k, s, padding=k // 2))
        if bn:
            layers.append(nn.BatchNorm1d(filters))
        layers.append(nn.ReLU())
        in_ch = filters
    if gap:
        layers.append(nn.AdaptiveAvgPool1d(1))
        return nn.Sequential(*layers), nn.Linear(filters, 7)
    return nn.Sequential(*layers), None


def train(Xtr, ytr, feat, head, epochs=300, lr=1e-3, seed=0, device="cuda",
          gap=True):
    torch.manual_seed(seed)
    feat.to(device)
    if head is not None:
        head.to(device)
    params = (list(feat.parameters()) + (list(head.parameters())
              if head is not None else []))
    opt = torch.optim.Adam(params, lr=lr, weight_decay=1e-4)
    Xt = torch.from_numpy(Xtr.astype(np.float32)).to(device)
    yt = torch.from_numpy(ytr.astype(np.int64)).to(device)
    for e in range(epochs):
        feat.train()
        if head is not None:
            head.train()
        perm = torch.randperm(len(Xt))
        for i in range(0, len(Xt), 128):
            idx = perm[i:i + 128]
            xb, yb = Xt[idx], yt[idx]
            z = feat(xb.unsqueeze(1))
            if gap:
                z = z.squeeze(-1)
                lo = nn.functional.cross_entropy(head(z), yb)
            else:
                lo = nn.functional.cross_entropy(z, yb)
            opt.zero_grad(); lo.backward(); opt.step()
    feat.eval()
    return feat, head


def evaluate(Xte, yte, feat, head, device="cuda", gap=True):
    Xtt = torch.from_numpy(Xte.astype(np.float32)).to(device)
    with torch.no_grad():
        z = feat(Xtt.unsqueeze(1))
        if gap:
            z = z.squeeze(-1)
            logits = head(z)
        else:
            logits = z
        p = logits.argmax(1).cpu().numpy()
        znorm = z.view(z.shape[0], -1).norm(dim=1).cpu().numpy()
    return (p == yte).mean(), znorm.std(), p


def main():
    d = load_data(preprocessed=False)
    Xe_raw, ye, Xs_raw, ys = d["X_exp"], d["y_exp"], d["X_theo"], d["y_theo"]
    tw = d["tw"]
    from data_loader import preprocess

    def raw_std(X):
        return (X - X.mean(1, keepdims=True)) / (X.std(1, keepdims=True) + 1e-8)
    reps = {"preproc": preprocess, "raw_std": raw_std,
            "raw_max": lambda X: X / X.max(1, keepdims=True)}
    skf = StratifiedKFold(5, shuffle=True, random_state=config.CV_SEED)
    tr, te = next(iter(skf.split(Xe_raw, ye)))
    for rep_name, repf in reps.items():
        Xe = repf(Xe_raw); Xs = repf(Xs_raw)
        rng = np.random.default_rng(config.AUG_SEED)
        Xae, yae = make_augmented(Xe[tr], tw, 2000, rng); yae = ye[tr][yae]
        Xas, yas = make_augmented(Xs, tw, 2000, rng); yas = ys[yas]
        Xb = np.concatenate([Xe[tr], Xs, Xae, Xas]); yb = np.concatenate([ye[tr], ys, yae, yas])
        for fname, filters in [("f64", 64), ("f128", 128)]:
            feat, head = make_cnn([8, 5, 3], [1, 1, 1], filters, gap=True)
            feat, head = train(Xb, yb, feat, head, epochs=300, gap=True)
            acc, nstd, p = evaluate(Xe[te], ye[te], feat, head, gap=True)
            print(f"{rep_name} GAP-CNN f{filters}: test acc {acc:.4f} "
                  f"feat-norm std {nstd:.4f}")


if __name__ == "__main__":
    main()
