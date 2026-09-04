"""Deep anomaly detector: GRU autoencoder trained on sliding windows.

Encoder: single-layer GRU maps the z-scored input window to a final hidden
state. Decoder: single-layer GRU seeded with the code and fed zeros, predicts
the input step-by-step. Reconstruction MSE is the anomaly score; per-window
scores are aggregated to per-point scores (mean over covering windows).

A deliberately *moderate-capacity* representative of the 'fancy deep-learning'
family (like the AT/NCAD detectors benchmarked in arXiv:2308.13068) --- the
scientific question is whether such models actually beat a simple PCA baseline
under an honest point-wise protocol.
"""
from __future__ import annotations

import numpy as np
import torch
import torch.nn as nn

torch.set_num_threads(4)   # avoid thread-thrash speed collapse under contention

from scripts.common import (zscore_fit, zscore_transform, make_windows,
                            window_aggregate, smooth_ma)


class GRUAutoencoder(nn.Module):
    def __init__(self, n_features: int, hidden: int = 32, num_layers: int = 1,
                 dropout: float = 0.0):
        super().__init__()
        self.hidden = hidden
        self.encoder = nn.GRU(n_features, hidden, num_layers=num_layers,
                              batch_first=True, dropout=0.0)
        self.decoder = nn.GRU(n_features, hidden, num_layers=num_layers,
                              batch_first=True, dropout=0.0)
        self.head = nn.Linear(hidden, n_features)

    def forward(self, x):
        # x: (B, L, F)
        _, h = self.encoder(x)                      # h: (nl, B, H)
        h = h[-1].unsqueeze(0)                      # last layer last time code
        B, L, F = x.shape
        inp = torch.zeros(B, L, F, device=x.device)
        out, _ = self.decoder(inp, h)
        recon = self.head(out)
        return recon


class GRUAutoencoderDetector:
    """Window-based deep detector; train on training segment only."""

    def __init__(self, length: int = 100, train_stride: int = 10,
                 test_stride: int = 25, hidden: int = 32,
                 epochs: int = 8, batch_size: int = 256, lr: float = 1e-3,
                 smooth: int = 5, seed: int = 0, max_train_windows: int | None = None,
                 device: str = "cpu"):
        self.length = length
        self.train_stride = train_stride
        self.test_stride = test_stride
        self.hidden = hidden
        self.epochs = epochs
        self.batch_size = batch_size
        self.lr = lr
        self.smooth = smooth
        self.seed = seed
        self.max_train_windows = max_train_windows
        self.device = torch.device(device)
        self.mean_ = None
        self.std_ = None
        self.model_ = None
        self.channel_scale_ = None

    def fit(self, train: np.ndarray, verbose: bool = True):
        torch.manual_seed(self.seed)
        np.random.seed(self.seed)
        self.mean_, self.std_ = zscore_fit(train)
        X = zscore_transform(train, self.mean_, self.std_)
        W = make_windows(X, self.length, self.train_stride)
        if self.max_train_windows and W.shape[0] > self.max_train_windows:
            rng = np.random.default_rng(self.seed)
            keep = rng.choice(W.shape[0], self.max_train_windows, replace=False)
            keep = np.sort(keep)
            W = W[keep]
        Wt = torch.tensor(W, dtype=torch.float32)
        n, L, F = Wt.shape

        self.model_ = GRUAutoencoder(F, hidden=self.hidden, num_layers=1).to(self.device)
        opt = torch.optim.Adam(self.model_.parameters(), lr=self.lr)
        mse = nn.MSELoss()
        steps = 0
        for ep in range(self.epochs):
            perm = torch.randperm(n, generator=torch.Generator().manual_seed(self.seed + ep))
            self.model_.train()
            tot = 0.0
            nb = 0
            for i in range(0, n, self.batch_size):
                bidx = perm[i:i + self.batch_size]
                xb = Wt[bidx].to(self.device)
                opt.zero_grad()
                recon = self.model_(xb)
                loss = mse(recon, xb)
                loss.backward()
                opt.step()
                tot += loss.item()
                nb += 1
                steps += 1
            if verbose:
                print(f"  [GRU-AE] epoch {ep + 1}/{self.epochs} loss={tot / nb:.6f}")
        return self

    def score_raw_channels(self, x: np.ndarray, stride: int | None = None):
        """Per-point per-channel squared reconstruction error (before channel agg)."""
        Xz = zscore_transform(x, self.mean_, self.std_)
        stride = stride or self.test_stride
        W = make_windows(Xz, self.length, stride)
        self.model_.eval()
        with torch.no_grad():
            Wt = torch.tensor(W, dtype=torch.float32)
            recon = self.model_(Wt.to(self.device)).cpu().numpy()
        err = np.mean((W - recon) ** 2, axis=1)          # (n_windows, F)
        n, F = err.shape
        acc = np.zeros((x.shape[0], F))
        cnt = np.zeros(x.shape[0])
        starts = np.arange(0, x.shape[0] - self.length + 1, stride)
        for i, s in enumerate(starts):
            acc[s : s + self.length] += err[i]
            cnt[s : s + self.length] += 1
        cnt[cnt == 0] = 1
        return acc / cnt[:, None]

    def score(self, x: np.ndarray, stride: int | None = None,
              per_channel_std: bool = False):
        Xz = zscore_transform(x, self.mean_, self.std_)
        stride = stride or self.test_stride
        if per_channel_std:
            if self.channel_scale_ is None:
                # calibration scale fit on the FIRST call (caller passes train first);
                # per-channel in-window residual RMSE of the training segment.
                rc = self.score_raw_channels(x, stride)
                s = np.sqrt(np.clip(rc.mean(axis=0), 0, None)); s[s == 0] = 1.0
                self.channel_scale_ = s
            ch = self.score_raw_channels(x, stride)
            err = np.mean((ch / self.channel_scale_) ** 2, axis=1)
        else:
            W = make_windows(Xz, self.length, stride)
            self.model_.eval()
            with torch.no_grad():
                Wt = torch.tensor(W, dtype=torch.float32)
                recon = self.model_(Wt.to(self.device)).cpu().numpy()
            mse = np.mean((W - recon) ** 2, axis=(1, 2))   # (n_windows,)
            err = window_aggregate(mse, x.shape[0], self.length, stride)
        if self.smooth and self.smooth > 1:
            err = smooth_ma(err, self.smooth)
        return err