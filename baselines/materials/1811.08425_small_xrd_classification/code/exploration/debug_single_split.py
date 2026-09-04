"""Quick single-split debug experiments to tune the pipeline.

Tests model configs / preprocessing / augmentation on ONE fixed 80/20 split
(same split as fold 0 of the CV) to iterate fast.
"""

import numpy as np
import torch
from sklearn.model_selection import StratifiedKFold

import config
from data_loader import load_data
from augmentation import make_augmented
from model import build_model
from train_eval import train_model, _evaluate

torch.set_num_threads(16)


def run_one(Xtr, ytr, Xte, yte, kernels, strides, epochs=60, loss="bce",
            device="cuda", verbose=True, lr=1e-3, seed=0):
    class M(torch.nn.Module):
        def __init__(self):
            super().__init__()
            layers = []
            in_ch = 1
            for k, s in zip(kernels, strides):
                layers.append(torch.nn.Conv1d(in_ch, 32, kernel_size=k,
                                              stride=s, padding=k // 2))
                layers.append(torch.nn.ReLU())
                in_ch = 32
            self.features = torch.nn.Sequential(*layers)
            self.pool = torch.nn.AdaptiveAvgPool1d(1)
            self.head = torch.nn.Linear(32, 7)
        def forward(self, x):
            h = self.features(x.unsqueeze(1))
            return self.head(self.pool(h).squeeze(-1))
        def loss(self, logits, target):
            if loss == "bce":
                oh = torch.nn.functional.one_hot(target, 7).float()
                return torch.nn.functional.binary_cross_entropy_with_logits(
                    logits, oh)
            return torch.nn.functional.cross_entropy(logits, target)
    torch.manual_seed(seed)
    model = M().to(device)
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    Xt = torch.from_numpy(Xtr.astype(np.float32)).to(device)
    yt = torch.from_numpy(ytr.astype(np.int64)).to(device)
    n = len(Xt)
    for e in range(epochs):
        model.train()
        perm = torch.randperm(n)
        for i in range(0, n, config.BATCH_SIZE):
            idx = perm[i:i + config.BATCH_SIZE]
            xb, yb = Xt[idx], yt[idx]
            opt.zero_grad()
            lo = model.loss(model(xb), yb)
            lo.backward()
            opt.step()
    acc, f1mi, f1ma, cm, pred = _evaluate(model, Xte, yte, device=device)
    if verbose:
        print(f"  k{sorted(set(kernels))} s{sorted(set(strides))} {loss} "
              f"{epochs}ep lr{lr}: test acc {acc:.4f} f1macro {f1ma:.4f}")
    return acc, f1ma, pred


def get_split(seed=config.CV_SEED):
    d = load_data()
    skf = StratifiedKFold(5, shuffle=True, random_state=seed)
    for tr, te in skf.split(d["X_exp"], d["y_exp"]):
        return (tr, te, d)


def main():
    tr, te, d = get_split()
    Xe, ye, Xs, ys, tw = d["X_exp"], d["y_exp"], d["X_theo"], d["y_theo"], d["tw"]
    Xtr, ytr = Xe[tr], ye[tr]
    Xte, yte = Xe[te], ye[te]
    print(f"split: train {len(tr)} test {len(te)}")
    print("test class counts:", np.bincount(yte, minlength=7))

    configs = [
        ([8, 5, 3], [8, 5, 3], "bce", 60),
        ([8, 5, 3], [1, 1, 1], "bce", 60),
        ([8, 5, 3], [1, 1, 1], "ce", 60),
        ([8, 5, 3], [2, 2, 2], "bce", 60),
        ([16, 8, 4], [2, 2, 2], "bce", 60),
        ([8, 5, 3], [1, 1, 1], "bce", 150),
    ]
    # no augmentation, exp only
    print("--- exp only, no aug ---")
    for k, s, loss, ep in configs:
        run_one(Xtr, ytr, Xte, yte, k, s, ep, loss)
    # exp + sim, no aug
    print("--- exp + sim, no aug ---")
    Xa = np.concatenate([Xtr, Xs]); ya = np.concatenate([ytr, ys])
    for k, s, loss, ep in configs:
        run_one(Xa, ya, Xte, yte, k, s, ep, loss)
    # exp + sim + aug, best configs
    rng = np.random.default_rng(config.AUG_SEED)
    Xas, yas = make_augmented(Xs, tw, 2000, rng, label=None); yas = ys[yas]
    Xae, yae = make_augmented(Xtr, tw, 2000, rng, label=None); yae = ytr[yae]
    for tag, (Xb, yb) in [("exp+sim+aug", (np.concatenate([Xtr, Xs, Xas, Xae]),
                                           np.concatenate([ytr, ys, yas, yae])))]:
        print(f"--- {tag}, train size {len(Xb)} ---")
        for k, s, loss, ep in configs:
            run_one(Xb, yb, Xte, yte, k, s, loss, ep)


if __name__ == "__main__":
    main()
