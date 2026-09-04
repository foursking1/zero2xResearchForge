"""GRU / GRU-Time-Aware (GRU-TA) sequence models for TJH early-mortality.

Architecture (PyTorch, CPU-friendly, thousands of samples => trains in tens of
seconds):
  * input  : per-patient binned series (n_bins=12 x 6ch: [ldh, mask, crp, mask,
              lymph, mask]) built by SequenceBuilder (LOCF + train-mean fill).
  * encoder: 1-layer GRU (hidden=48) over the bins.
  * head   : per-step linear projection -> logit_t; training supervises every
              step; test score = sigmoid(logit at the last bin).

Losses
  * GRU      : plain per-step binary cross-entropy.
  * GRU-TA   : time-aware weighted BCE. For *deceased* patients the earlier,
               harder-to-predict steps are up-weighted (linear ramp w_t = 1 +
               gamma*(n_bins - t)/n_bins); survivors keep uniform weight.
               This implements the paper's 'time-aware loss' idea -- push the
               model to fire early, before information that trivially reveals
               the outcome accumulates.

Anti-leakage: feature means for imputation come from the training cohort only;
a fixed train/validation split (by patient) is used solely for checkpointing;
the frozen test set is scored once per seed.
"""
from __future__ import annotations

import os
import time

import numpy as np
import torch
import torch.nn as nn

from common import SHARED_FEATURES, load_raw
from preprocess import SequenceBuilder

DEVICE = torch.device("cpu")
N_BINS = 12
WINDOW_HOURS = 72.0
HIDDEN = 48
N_EPOCHS = 80
BATCH = 32
LR = 1e-3
WD = 1e-4
VAL_FRAC = 0.20
SEEDS = [0, 1, 2, 3, 4]


class GRUModel(nn.Module):
    def __init__(self, n_bins, input_ch, hidden=HIDDEN):
        super().__init__()
        self.gru = nn.GRU(input_ch, hidden, num_layers=1, batch_first=True)
        self.head = nn.Linear(hidden, 1)

    def forward(self, x):
        # x: (B, T, C)
        out, _ = self.gru(x)
        logits = self.head(out).squeeze(-1)   # (B, T)
        return logits


def time_aware_weight(y, n_bins, gamma=1.0):
    """Weights per (sample, step). y: (B,) 0/1 labels.

    Dead patients: w_t = 1 + gamma*(n_bins-1-t)/max(1, n_bins-1)  (early high).
    Survivors   : w_t = 1.
    """
    t = torch.arange(n_bins, dtype=torch.float32)                 # 0..n_bins-1
    ramp = 1.0 + gamma * (n_bins - 1 - t) / max(1.0, n_bins - 1)  # high at t=0
    w = ramp[None, :].expand(y.shape[0], n_bins).clone()          # (B, T)
    w[y == 0, :] = 1.0
    return w


def make_sequences(train_df, test_df):
    """Return normalised tensors ready for the GRU."""
    sb = SequenceBuilder(feats=SHARED_FEATURES, window_hours=WINDOW_HOURS,
                         n_bins=N_BINS)
    Xtr, ytr, pids_tr, Xte, yte, pids_te = sb.fit_transform(train_df, test_df)

    # per-channel train normalisation (values channels only)
    vch = list(range(0, Xtr.shape[2], 2))
    mean = Xtr[..., vch].mean(axis=(0, 1))
    std = Xtr[..., vch].std(axis=(0, 1)) + 1e-8
    for X in (Xtr, Xte):
        X[..., vch] = (X[..., vch] - mean) / std
        X = X.astype(np.float32)

    return (torch.from_numpy(Xtr.astype(np.float32)), torch.from_numpy(ytr.astype(np.int64)),
            pids_tr,
            torch.from_numpy(Xte.astype(np.float32)), torch.from_numpy(yte.astype(np.int64)),
            pids_te)


def train_seq(Xtr, ytr, Xte, yte, use_ta, gamma=1.0, seed=0,
              epochs=N_EPOCHS, val_frac=VAL_FRAC, score_mode="mean"):
    """Train one GRU(-TA) model. Returns test probability array."""
    torch.manual_seed(seed)
    np.random.seed(seed)

    n = Xtr.shape[0]
    rng = np.random.RandomState(seed)
    perm = rng.permutation(n)
    n_val = int(n * val_frac)
    val_idx, tr_idx = perm[:n_val], perm[n_val:]
    Xv, yv = Xtr[val_idx], ytr[val_idx]
    Xt2, yt2 = Xtr[tr_idx], ytr[tr_idx]
    yv_f = yv.float()

    model = GRUModel(N_BINS, Xtr.shape[2], hidden=HIDDEN)
    opt = torch.optim.Adam(model.parameters(), lr=LR, weight_decay=WD)
    lossf = nn.BCEWithLogitsLoss(reduction="none")

    def loss_fn(logits, y, w):
        bce = lossf(logits, y[:, None].float().expand_as(logits))
        return (bce * w).mean()

    best = None
    for ep in range(epochs):
        model.train()
        order = np.random.default_rng(seed + ep).permutation(len(yt2))
        for i in range(0, len(yt2), BATCH):
            idxb = order[i:i + BATCH]
            xb = Xt2[idxb]; yb = yt2[idxb]
            logits = model(xb)
            if use_ta:
                w = time_aware_weight(yb, N_BINS, gamma)
            else:
                w = torch.ones_like(logits)
            loss = loss_fn(logits, yb, w)
            opt.zero_grad()
            loss.backward()
            opt.step()

        if (ep + 1) % 5 == 0 or ep == epochs - 1:
            model.eval()
            with torch.no_grad():
                lv = model(Xv)
                bce_v = lossf(lv, yv_f[:, None].expand_as(lv)).mean(dim=1).mean()
            if best is None or bce_v.item() < best[0]:
                best = (bce_v.item(), {k: v.detach().clone() for k, v in model.state_dict().items()})

    model.load_state_dict(best[1])
    model.eval()
    with torch.no_grad():
        ltest = model(Xte)
        pv = torch.sigmoid(ltest)
        if score_mode == "last":
            p = pv[:, -1].numpy()
        elif score_mode == "max":
            p = pv.max(dim=1).values.numpy()
        else:  # mean pooling over all steps (default)
            p = pv.mean(dim=1).numpy()
    return p


def run_seeds(train_df, test_df, use_ta, gamma=1.0, seeds=SEEDS,
              score_mode="mean"):
    """Train each seed and return (test probs per seed, (Xte, yte, pids_te))."""
    Xtr, ytr, pids_tr, Xte, yte, pids_te = make_sequences(train_df, test_df)
    proba = np.zeros((len(seeds), Xte.shape[0]))
    for k, sd in enumerate(seeds):
        proba[k] = train_seq(Xtr, ytr, Xte, yte, use_ta, gamma=gamma,
                             seed=sd, score_mode=score_mode)
    return proba, (Xte, yte, pids_te)


if __name__ == "__main__":
    from sklearn.metrics import roc_auc_score, average_precision_score
    train, test = load_raw()
    print("building sequences ...")
    for ta, gamma in [(False, None), (True, 1.0)]:
        t0 = time.time()
        proba, (Xte, yte, pids) = run_seeds(train, test, ta, gamma)
        for k, sd in enumerate(SEEDS):
            print(f"TA={ta} seed={sd}: AUROC={roc_auc_score(yte, proba[k]):.4f} "
                  f"AUPRC={average_precision_score(yte, proba[k]):.4f}")
        print(f"  TA={ta} mean AUROC=%.4f mean AUPRC=%.4f  ({time.time()-t0:.0f}s)"
              % (np.mean([roc_auc_score(yte, p) for p in proba]),
                 np.mean([average_precision_score(yte, p) for p in proba])))