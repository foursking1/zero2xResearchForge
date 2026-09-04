"""Reconstruction-based likelihood autoencoders: GRU, TCN, Transformer,
TSMixer, each producing per-point Gaussian (mean, log-variance) so that the
anomaly score is a Gaussian negative log-likelihood (the "likelihood"
calibrated in this project).

All models share the same interface:

    model.forward(x)  # x: (B, L, 1) -> (mu, logvar), each (B, L, 1)
    model.score(x)    # Gaussian NLL per point

Training minimises the Gaussian NLL; every training script fixes the seed so
results are reproducible.
"""

from __future__ import annotations

import torch
import torch.nn as nn

CLIP = 1e-6


def gen_input(x):
    if x.ndim == 2 and x.shape[1] == 1:
        return x
    if x.ndim == 1:
        return x[:, None]
    return x


class BaseAE(nn.Module):
    def score(self, x):
        """Per-point anomaly score = squared reconstruction residual
        (Gaussian negative log-likelihood under a homoscedastic, fixed
        variance), a standard reconstruction-based anomaly score."""
        mu, _, _ = self.forward(x)
        return (x - mu) ** 2  # (B, L, 1)

    def forward(self, x):  # pragma: no cover - overridden
        raise NotImplementedError


class GRUAE(BaseAE):
    def __init__(self, wlen, hidden=32, layers=1, dropout=0.1):
        super().__init__()
        self.wlen = wlen
        self.hidden = hidden
        self.enc = nn.GRU(1, hidden, num_layers=layers, batch_first=True,
                          bidirectional=False,
                          dropout=dropout if layers > 1 else 0.0)
        self.dec = nn.GRU(1, hidden, num_layers=layers, batch_first=True,
                          dropout=dropout if layers > 1 else 0.0)
        self.head = nn.Linear(hidden, 2)

    def forward(self, x):
        x = gen_input(x)
        _, h = self.enc(x)  # h: (layers, B, hidden)
        h0 = h[-1].unsqueeze(0).expand(self.dec.num_layers, -1, -1).contiguous()
        seq = torch.zeros_like(x)
        out, _ = self.dec(seq, h0)
        out = self.head(out)
        return out[..., :1], out[..., 1:], out


class CausalConv1dBlock(nn.Module):
    def __init__(self, c_in, c_out, k, dilation):
        super().__init__()
        self.conv = nn.Conv1d(c_in, c_out, k, padding=(k - 1) * dilation, dilation=dilation)
        self.bn = nn.BatchNorm1d(c_out)
        self.act = nn.ReLU()

    def forward(self, x):
        y = self.conv(x)
        return self.act(self.bn(y[:, :, : x.shape[2]]))


class TCNAE(BaseAE):
    def __init__(self, wlen, channels=(32, 32, 32), k=3, dropout=0.1):
        super().__init__()
        self.wlen = wlen
        layers = []
        cin = 1
        for i, c in enumerate(channels):
            layers.append(CausalConv1dBlock(cin, c, k, dilation=2 ** i))
            layers.append(nn.Dropout(dropout))
            cin = c
        self.tcn = nn.Sequential(*layers)
        self.dense = nn.Linear(channels[-1], 2)

    def forward(self, x):
        x = gen_input(x)
        f = self.tcn(x.transpose(1, 2)).transpose(1, 2)
        out = self.dense(f)
        return out[..., :1], out[..., 1:], out


class TransformerAE(BaseAE):
    def __init__(self, wlen, dim=32, depth=2, nhead=4, dropout=0.1):
        super().__init__()
        self.wlen = wlen
        self.emb = nn.Linear(1, dim)
        enc = nn.TransformerEncoderLayer(dim, nhead, dim * 4, dropout=dropout,
                                         batch_first=True)
        self.encoder = nn.TransformerEncoder(enc, num_layers=depth)
        self.head = nn.Linear(dim, 2)

    def forward(self, x):
        x = gen_input(x)
        e = self.encoder(self.emb(x))
        out = self.head(e)
        return out[..., :1], out[..., 1:], out


class MixerLayer(nn.Module):
    """Token mixing (over sequence) + channel mixing (over features)."""

    def __init__(self, L, dim, hidden, dropout):
        super().__init__()
        self.token_norm = nn.LayerNorm(dim)
        self.token_mlp = nn.Sequential(nn.Linear(L, hidden), nn.GELU(),
                                       nn.Dropout(dropout), nn.Linear(hidden, L))
        self.channel_norm = nn.LayerNorm(dim)
        self.channel_mlp = nn.Sequential(nn.Linear(dim, hidden), nn.GELU(),
                                         nn.Dropout(dropout), nn.Linear(hidden, dim))

    def forward(self, x):
        z = self.token_norm(x)
        z = z.transpose(-1, -2)
        z = self.token_mlp(z).transpose(-1, -2) + x
        z = self.channel_mlp(self.channel_norm(z)) + z
        return z


class TSMixerAE(BaseAE):
    def __init__(self, wlen, dim=64, depth=4, expand=2, dropout=0.1):
        super().__init__()
        self.wlen = wlen
        self.emb = nn.Linear(1, dim)
        self.mixers = nn.ModuleList([
            MixerLayer(wlen, dim, dim * expand, dropout) for _ in range(depth)
        ])
        self.head = nn.Linear(dim, 2)

    def forward(self, x):
        x = gen_input(x)
        e = self.emb(x)  # (B, L, dim)
        for m in self.mixers:
            e = m(e)
        out = self.head(e)
        return out[..., :1], out[..., 1:], out


def build_model(name, wlen, seed=0):
    torch.manual_seed(seed)
    if name == "GRU":
        return GRUAE(wlen, hidden=32, layers=1)
    if name == "TCN":
        return TCNAE(wlen, channels=(24, 24, 24), k=3)
    if name == "Transformer":
        return TransformerAE(wlen, dim=24, depth=1, nhead=4)
    if name == "TSMixer":
        return TSMixerAE(wlen, dim=48, depth=2, expand=2)
    raise KeyError(name)