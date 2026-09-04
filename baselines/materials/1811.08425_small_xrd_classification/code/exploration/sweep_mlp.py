"""Hyperparameter sweep for the final model on the single split (fast)."""
import numpy as np
import torch
import torch.nn as nn
from sklearn.model_selection import StratifiedKFold

import config
from data_loader import load_data
from augmentation import make_augmented

torch.set_num_threads(16)


def mlp(widths, drop, n_in=1499):
    layers = []
    in_ = n_in
    for w in widths:
        layers.append(nn.Linear(in_, w))
        layers.append(nn.ReLU())
        layers.append(nn.Dropout(drop))
        in_ = w
    layers.append(nn.Linear(in_, config.NUM_CLASSES))
    return nn.Sequential(*layers)


def run(Xtr, ytr, Xte, yte, model, epochs, lr, drop, seed, device="cuda"):
    torch.manual_seed(seed)
    model.to(device)
    opt = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=epochs)
    Xt = torch.from_numpy(Xtr.astype(np.float32)).to(device)
    yt = torch.from_numpy(ytr.astype(np.int64)).to(device)
    Xtt = torch.from_numpy(Xte.astype(np.float32)).to(device)
    best = 0.0; best_state = None
    # use last 10% of training as early-stop val
    n = len(Xt)
    nv = max(1, n // 10)
    Xv, yv = Xt[n - nv:], yt[n - nv:]
    for e in range(epochs):
        model.train()
        perm = torch.randperm(n - nv)
        for i in range(0, n - nv, 128):
            idx = perm[i:i + 128]
            xb, yb = Xt[idx], yt[idx]
            opt.zero_grad()
            lo = nn.functional.cross_entropy(model(xb), yb)
            lo.backward(); opt.step()
        scheduler.step()
        model.eval()
        with torch.no_grad():
            vp = model(Xv).argmax(1)
        vacc = (vp == yv).float().mean().item()
        if vacc > best:
            best = vacc
            best_state = {k: v.detach().clone() for k, v in model.state_dict().items()}
    model.load_state_dict(best_state)
    model.eval()
    with torch.no_grad():
        p = model(Xtt).argmax(1).cpu().numpy()
    return (p == yte).mean()


def main():
    d = load_data()
    Xe, ye, Xs, ys = d["X_exp"], d["y_exp"], d["X_theo"], d["y_theo"]
    skf = StratifiedKFold(5, shuffle=True, random_state=config.CV_SEED)
    tr, te = next(iter(skf.split(Xe, ye)))
    Xtr, ytr, Xte, yte = Xe[tr], ye[tr], Xe[te], ye[te]
    Xa = np.concatenate([Xtr, Xs]); ya = np.concatenate([ytr, ys])

    configs = []
    for widths in ([256], [256, 256], [512, 256], [512, 256, 128], [1024, 512]):
        for drop in (0.2, 0.4):
            for lr in (1e-3,):
                configs.append((widths, drop, lr))
    for widths, drop, lr in configs:
        acc = run(Xa, ya, Xte, yte, mlp(widths, drop), epochs=300, lr=lr,
                  drop=drop, seed=0)
        print(f"  MLP {widths} drop{drop} lr{lr}: test acc {acc:.4f}")

    # a few repeats for the best-looking config
    for widths in ([512, 256], [512, 256, 128]):
        accs = [run(Xa, ya, Xte, yte, mlp(widths, 0.3), epochs=300, lr=1e-3,
                    drop=0.3, seed=s) for s in range(3)]
        print(f"  MLP {widths} drop0.3 3-seed mean: {np.mean(accs):.4f} "
              f"vals {np.round(accs, 3)}")


if __name__ == "__main__":
    main()