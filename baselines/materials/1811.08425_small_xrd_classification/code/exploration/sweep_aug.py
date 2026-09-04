"""Tune augmentation + class weighting on the single split (MLP)."""
import numpy as np
import torch
import torch.nn as nn
from sklearn.model_selection import StratifiedKFold

import config
from data_loader import load_data
from augmentation import make_augmented

torch.set_num_threads(16)


def mlp(widths=(512, 256), drop=0.4, n_in=1499):
    layers = []
    in_ = n_in
    for w in widths:
        layers.append(nn.Linear(in_, w)); layers.append(nn.ReLU())
        layers.append(nn.Dropout(drop)); in_ = w
    layers.append(nn.Linear(in_, config.NUM_CLASSES))
    return nn.Sequential(*layers)


def run(Xtr, ytr, Xte, yte, model, epochs=300, lr=1e-3, seed=0, w=1.0):
    torch.manual_seed(seed)
    model.to("cuda")
    opt = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=epochs)
    Xt = torch.from_numpy(Xtr.astype(np.float32)).to("cuda")
    yt = torch.from_numpy(ytr.astype(np.int64)).to("cuda")
    if isinstance(w, np.ndarray):
        weights = torch.from_numpy(w.astype(np.float32)).to("cuda")
    else:
        weights = None
    Xtt = torch.from_numpy(Xte.astype(np.float32)).to("cuda")
    n = len(Xt); nv = max(1, n // 10)
    Xv, yv = Xt[n - nv:], yt[n - nv:]
    best, best_state = 0.0, None
    for e in range(epochs):
        model.train()
        perm = torch.randperm(n - nv)
        for i in range(0, n - nv, 128):
            idx = perm[i:i + 128]
            xb, yb = Xt[idx], yt[idx]
            opt.zero_grad()
            lo = nn.functional.cross_entropy(model(xb), yb,
                                             weight=weights if w != 1.0 else None)
            lo.backward(); opt.step()
        sched.step()
        model.eval()
        with torch.no_grad():
            vp = model(Xv).argmax(1)
        vacc = (vp == yv).float().mean().item()
        if vacc > best:
            best, best_state = vacc, {k: v.detach().clone()
                                       for k, v in model.state_dict().items()}
    model.load_state_dict(best_state)
    model.eval()
    with torch.no_grad():
        p = model(Xtt).argmax(1).cpu().numpy()
    from sklearn.metrics import f1_score
    return (p == yte).mean(), f1_score(yte, p, average="macro")


def make_aug(Xsrc, ysrc, tw, n, rng):
    Xa, ya_src = make_augmented(Xsrc, tw, n, rng)
    return Xa, ysrc[ya_src]


def main():
    d = load_data()
    Xe, ye, Xs, ys, tw = d["X_exp"], d["y_exp"], d["X_theo"], d["y_theo"], d["tw"]
    skf = StratifiedKFold(5, shuffle=True, random_state=config.CV_SEED)
    tr, te = next(iter(skf.split(Xe, ye)))
    Xtr, ytr, Xte, yte = Xe[tr], ye[tr], Xe[te], ye[te]
    rng = np.random.default_rng(config.AUG_SEED)
    base = np.concatenate([Xtr, Xs]); basey = np.concatenate([ytr, ys])
    print("test counts:", np.bincount(yte, minlength=7))
    print("baseline exp+sim:", run(base, basey, Xte, yte, mlp(), seed=0)[:1])

    # augmentation ratios
    for n_exp, n_sim in [(500, 500), (1000, 1000), (2000, 2000), (2000, 500)]:
        Xae, yae = make_aug(Xtr, ytr, tw, n_exp, rng)
        Xas, yas = make_aug(Xs, ys, tw, n_sim, rng)
        Xb = np.concatenate([Xtr, Xs, Xae, Xas]); yb = np.concatenate([ytr, ys, yae, yas])
        acc, f1 = run(Xb, yb, Xte, yte, mlp(), seed=0)
        print(f"aug {n_exp}+{n_sim}: acc {acc:.4f} f1macro {f1:.4f}")

    # class weighting (inverse frequency)
    from collections import Counter
    cnt = Counter(ytr.tolist())
    w = np.array([1.0 / cnt.get(i, 1) for i in range(7)])
    w = w / w.mean()
    print("class weights:", np.round(w, 2))
    Xae, yae = make_aug(Xtr, ytr, tw, 2000, rng)
    Xas, yas = make_aug(Xs, ys, tw, 2000, rng)
    Xb = np.concatenate([Xtr, Xs, Xae, Xas]); yb = np.concatenate([ytr, ys, yae, yas])
    acc, f1 = run(Xb, yb, Xte, yte, mlp(), seed=0, w=w)
    print(f"aug + classweight: acc {acc:.4f} f1macro {f1:.4f}")


if __name__ == "__main__":
    main()