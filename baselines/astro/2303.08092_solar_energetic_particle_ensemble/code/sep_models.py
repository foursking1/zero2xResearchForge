# -*- coding: utf-8 -*-
"""CoNN / Committee / RH v1 / RH v2 classifiers (arXiv:2303.08092, Sec.3).

Architecture per the paper: input = selected features -> Dense(10) -> ReLU
-> Dropout(0.2) -> Dense(1) (logit).  Binary cross-entropy, Adam.

  - CoNN     : single network, all 12 features, epochs=500, lr=1e-3.
  - Committee: 10 networks, all 12 features, equal-weight probability average.
  - RH v1    : 10 networks, ceil(sqrt(12))=4 features sampled with prob. prop.
               to the feature weight (chi2+MI); epochs/lr scaled by 12/4.
  - RH v2    : 10 networks, 6 features sampled with prob. prop. to weight;
               epochs/lr scaled by 12/6; vote weighted by selected-feature
               weight sum.

All random seeds are managed so the run is reproducible.
"""
import numpy as np
import torch
import torch.nn as nn

# Pin to a single thread: the networks are tiny (12->10->1) and running many
# OMP threads under heavy shared-machine load causes severe thread-thrashing
# overhead (measured ~0.2 s/batch with 4 concurrent jobs).  A single thread is
# dramatically faster for these small dense nets.
torch.set_num_threads(1)


class Net(nn.Module):
    def __init__(self, n_in):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(n_in, 10),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(10, 1),
        )

    def forward(self, x):
        return self.net(x).squeeze(-1)


def train_estimator(X, y, feat_idx, epochs=500, lr=1e-3, seed=0,
                    batch_size=2048, log_interval=0, balanced=True):
    """Train a single network on the given feature indices.

    Returns (model, feat_idx, hist) where hist is the per-epoch BCE on the
    training set (if log_interval>0, on every `log_interval`-th epoch).

    `balanced=True` uses class-balanced BCE (pos_weight = n_neg/n_pos), which
    is what the paper uses to handle the ~1/285 SEP class imbalance (otherwise
    the network degenerates to predicting ~all-negative, giving TSS~0 at the
    0.5 decision threshold).
    """
    torch.manual_seed(seed)
    np.random.seed(seed)
    Xs = X[:, feat_idx].astype(np.float32)
    ys = y.astype(np.float32)
    model = Net(len(feat_idx))
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    if balanced:
        n_pos = max(float(ys.sum()), 1.0)
        n_neg = float(len(ys) - ys.sum())
        lossf = nn.BCEWithLogitsLoss(pos_weight=torch.tensor(n_neg / n_pos))
    else:
        lossf = nn.BCEWithLogitsLoss()
    n = len(Xs)
    hist = []
    Xt = torch.from_numpy(Xs)
    yt = torch.from_numpy(ys)
    for ep in range(epochs):
        # shuffle
        perm = torch.randperm(n)
        tot = 0.0
        nb = 0
        for i in range(0, n, batch_size):
            idx = perm[i:i + batch_size]
            xb, yb = Xt[idx], yt[idx]
            opt.zero_grad()
            out = model(xb)
            loss = lossf(out, yb)
            loss.backward()
            opt.step()
            tot += loss.item()
            nb += 1
        if log_interval and (ep % log_interval == 0 or ep == epochs - 1):
            hist.append((ep, tot / nb))
    return model, feat_idx, hist


@torch.no_grad()
def predict(model, X, feat_idx):
    model.eval()
    Xs = X[:, feat_idx].astype(np.float32)
    return torch.sigmoid(model(torch.from_numpy(Xs))).numpy()


def run_method(name, Xtr, ytr, Xte, w, seeds, epochs=500, lr=1e-3,
               log_interval=0, n_estimators=10):
    """Train a method on (Xtr, ytr) and return test probabilities + metadata.

    name: 'CoNN' | 'Committee' | 'RH_v1' | 'RH_v2'
    """
    n_feat = Xtr.shape[1]
    if name == "CoNN":
        feat_list = [np.arange(n_feat)]
        n_sel = n_feat
    elif name == "Committee":
        feat_list = [np.arange(n_feat) for _ in range(n_estimators)]
        n_sel = n_feat
    elif name == "RH_v1":
        n_sel = int(np.ceil(np.sqrt(n_feat)))          # 4
        feat_list = [sample_features(w, n_sel, seed=seeds[k])
                     for k in range(n_estimators)]
    elif name == "RH_v2":
        n_sel = n_feat // 2                            # 6
        feat_list = [sample_features(w, n_sel, seed=seeds[k])
                     for k in range(n_estimators)]
    else:
        raise ValueError(name)

    scale = n_feat / n_sel
    ep = int(epochs * scale)
    lr_eff = lr * scale

    probs = []
    probs_tr = []
    est_weights = []
    times = []
    for k, fi in enumerate(feat_list):
        import time
        t0 = time.time()
        model, _, _ = train_estimator(Xtr, ytr, fi, epochs=ep, lr=lr_eff,
                                      seed=seeds[k], log_interval=log_interval)
        times.append(time.time() - t0)
        p = predict(model, Xte, fi)
        probs.append(p)
        probs_tr.append(predict(model, Xtr, fi))
        if name in ("RH_v1", "RH_v2"):
            est_weights.append(float(fi_wsum(w, fi)))
        else:
            est_weights.append(1.0)

    probs = np.array(probs)                 # (n_est, n_test)
    probs_tr = np.array(probs_tr)           # (n_est, n_train)
    est_weights = np.array(est_weights)
    if name == "CoNN":
        p_avg = probs[0]
        p_tr_avg = probs_tr[0]
    else:
        p_avg = np.average(probs, axis=0, weights=est_weights)
        p_tr_avg = np.average(probs_tr, axis=0, weights=est_weights)

    return {
        "name": name,
        "p": p_avg,
        "p_train": p_tr_avg,
        "probs_est": probs,
        "feat_list": feat_list,
        "est_weights": est_weights,
        "n_selected": n_sel,
        "epochs_used": ep,
        "lr_used": lr_eff,
        "time_s": sum(times),
    }


def sample_features(w, k, seed=0):
    """Sample k features without replacement, with probability proportional to w."""
    rng = np.random.default_rng(seed)
    w = np.asarray(w, dtype=float)
    w = w / w.sum()
    chosen = []
    rem = list(range(len(w)))
    remw = w.copy()
    for _ in range(k):
        remw = remw / remw.sum()
        j = rng.choice(len(rem), p=remw)
        chosen.append(rem[j])
        rem.pop(j)
        remw = np.delete(remw, j)
    return np.array(sorted(chosen))


def fi_wsum(w, fi):
    return float(np.sum(w[fi]))
