"""Test MLP and improved CNN variants on the single 80/20 split."""
import numpy as np
import torch
import torch.nn as nn

import config
from data_loader import load_data
from augmentation import make_augmented

torch.set_num_threads(16)


def run(Xtr, ytr, Xte, yte, model, epochs=150, lr=1e-3, device="cuda",
        seed=0, verbose=False, is_cnn=False):
    torch.manual_seed(seed)
    model.to(device)
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    Xt = torch.from_numpy(Xtr.astype(np.float32)).to(device)
    yt = torch.from_numpy(ytr.astype(np.int64)).to(device)
    for e in range(epochs):
        model.train()
        perm = torch.randperm(len(Xt))
        for i in range(0, len(Xt), 128):
            idx = perm[i:i + 128]
            xb, yb = Xt[idx], yt[idx]
            if is_cnn:
                xb = xb.unsqueeze(1)
            opt.zero_grad()
            lo = nn.functional.cross_entropy(model(xb), yb)
            lo.backward(); opt.step()
    model.eval()
    Xtt = torch.from_numpy(Xte.astype(np.float32)).to(device)
    if is_cnn:
        Xtt = Xtt.unsqueeze(1)
    with torch.no_grad():
        p = model(Xtt).argmax(1).cpu().numpy()
    acc = (p == yte).mean()
    if verbose:
        print(f"  test acc {acc:.4f}")
    return acc


def mlp(hidden=256, n_in=1499, drop=0.3):
    return nn.Sequential(
        nn.Linear(n_in, hidden), nn.ReLU(), nn.Dropout(drop),
        nn.Linear(hidden, hidden), nn.ReLU(), nn.Dropout(drop),
        nn.Linear(hidden, 7))


def cnn(kerns, strids, filters=32, bn=False, flatten=False, n_in=1499,
        drop=0.0):
    layers = []
    in_ch = 1
    for k, s in zip(kerns, strids):
        layers.append(nn.Conv1d(in_ch, filters, k, s, padding=k // 2))
        if bn:
            layers.append(nn.BatchNorm1d(filters))
        layers.append(nn.ReLU())
        if drop:
            layers.append(nn.Dropout(drop))
        in_ch = filters
    if flatten:
        return nn.Sequential(*layers, nn.Flatten())
    layers.append(nn.AdaptiveAvgPool1d(1))
    return nn.Sequential(*layers, nn.Flatten(), nn.Linear(filters, 7))


def main():
    d = load_data()
    Xe, ye, Xs, ys, tw = d["X_exp"], d["y_exp"], d["X_theo"], d["y_theo"], d["tw"]
    from sklearn.model_selection import StratifiedKFold
    skf = StratifiedKFold(5, shuffle=True, random_state=config.CV_SEED)
    tr, te = next(iter(skf.split(Xe, ye)))
    Xtr, ytr, Xte, yte = Xe[tr], ye[tr], Xe[te], ye[te]
    print("test class counts:", np.bincount(yte, minlength=7))
    print("majority baseline", yte.mean() if False else np.bincount(yte, minlength=7).max()/len(yte))

    # augmentation only from training exp
    rng = np.random.default_rng(config.AUG_SEED)
    Xae, yae = make_augmented(Xtr, tw, 2000, rng, label=None)
    yae = ytr[yae]
    Xas, yas = make_augmented(Xs, tw, 2000, rng, label=None)
    yas = ys[yas]

    combos = [
        ("exp-only", Xtr, ytr),
        ("exp+aug-exp", np.concatenate([Xtr, Xae]), np.concatenate([ytr, yae])),
        ("exp+sim", np.concatenate([Xtr, Xs]), np.concatenate([ytr, ys])),
        ("exp+sim+aug", np.concatenate([Xtr, Xs, Xae, Xas]),
                        np.concatenate([ytr, ys, yae, yas])),
    ]
    models = [
        ("MLP-256", mlp(256), False),
        ("CNN-s1-f32", cnn([8, 5, 3], [1, 1, 1], 32), True),
        ("CNN-s1-f64", cnn([8, 5, 3], [1, 1, 1], 64), True),
        ("CNN-s1-f64-BN", cnn([8, 5, 3], [1, 1, 1], 64, bn=True), True),
        ("CNN-s44-f64", cnn([8, 5, 3], [4, 4, 4], 64), True),
        ("CNN-s1-flat-f64", cnn([8, 5, 3], [1, 1, 1], 64, flatten=True), True),
    ]
    for cname, Xc, yc in combos:
        print(f"=== {cname} (n={len(Xc)}) ===")
        for mname, m, iscnn in models:
            acc = run(Xc, yc, Xte, yte, m, epochs=120, is_cnn=iscnn)
            print(f"  {mname:16s} test acc {acc:.4f}")


if __name__ == "__main__":
    main()
