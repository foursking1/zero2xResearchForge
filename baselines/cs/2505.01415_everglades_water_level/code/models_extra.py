"""Extra MLP/Transformer class models for the MLP < linear ordering check.

Besides the anchor NBEATS we support:
  * MLPResidual : level-residual MLP  (y_hat = last_target_level + MLP(x - last_obs))
  * TSMixer     : MLP-Mixer over time/feature channels (arXiv:2303.06053)
  * PatchTST    : patch + self-attention encoder with flattened head (arXiv:2307.11619)
"""
from __future__ import annotations

import numpy as np
import torch
import torch.nn as nn

from common import CONTEXT_LEN, HORIZON, N_DAYS, TARGETS
from models import TARGET_IDX

N_FEATURES = 37
N_OUTPUTS = len(TARGETS)


class MLPResidual(nn.Module):
    """Small MLP on (x - last_value) with additive level residual on targets.

    Guarantees a persistence-ish baseline; the MLP only models the deviation,
    which strongly regularizes the short-horizon behavior.
    """

    def __init__(self, hidden: int = 512, depth: int = 3,
                 dropout: float = 0.0, activ: str = "relu"):
        super().__init__()
        act = {"relu": nn.ReLU(), "gelu": nn.GELU()}[activ]
        layers = [nn.Linear(CONTEXT_LEN * N_FEATURES, hidden), act]
        for _ in range(depth - 2):
            layers += [nn.Linear(hidden, hidden), act]
        layers += [nn.Linear(hidden, HORIZON * N_OUTPUTS)]
        if dropout > 0.0:  # dropout after every hidden linear
            body = []
            for layer in layers:
                body.append(layer)
                if isinstance(layer, nn.Linear) and layer is not layers[-1]:
                    body.append(nn.Dropout(dropout))
            layers = body
        self.net = nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:   # (B, C, F)
        last = x[:, -1, TARGET_IDX]                        # (B, out)
        xd = x - x[:, -1:, :]
        y = self.net(xd.reshape(x.size(0), -1))            # (B, H*out)
        y = y.reshape(x.size(0), -1, N_OUTPUTS).transpose(1, 2) + last.unsqueeze(-1)
        return y.transpose(1, 2)                           # (B, H, out)


class TSMixer(nn.Module):
    """Channel-mixing + time-mixing MLP, token-per-time-step (lighter config)."""

    def __init__(self, d_model: int = 128, n_layers: int = 2,
                 mlp_time: int = 256, mlp_feat: int = 256, dropout: float = 0.0):
        super().__init__()
        # project 37 features -> d_model
        self.in_proj = nn.Linear(N_FEATURES, d_model)
        self.blocks = nn.ModuleList()
        for _ in range(n_layers):
            self.blocks.append(nn.ModuleList([
                nn.Sequential(nn.Linear(CONTEXT_LEN, mlp_time), nn.GELU(),
                              nn.Linear(mlp_time, CONTEXT_LEN)),   # time mixing
                nn.Sequential(nn.Linear(d_model, mlp_feat), nn.GELU(),
                              nn.Linear(mlp_feat, d_model)),       # feature mixing
            ]))
        self.out_proj = nn.Linear(d_model * CONTEXT_LEN, HORIZON * N_OUTPUTS)

    def _norm(self, t: torch.Tensor) -> torch.Tensor:   # layer-norm-like
        return (t - t.mean(dim=-1, keepdim=True)) / (t.std(dim=-1, keepdim=True) + 1e-6)

    def forward(self, x: torch.Tensor) -> torch.Tensor:  # (B, C, F)
        z = self.in_proj(x)                              # (B, C, d)
        for time_mlp, feat_mlp in self.blocks:
            zt = z + time_mlp(self._norm(z).transpose(1, 2)).transpose(1, 2)
            zs = zt + feat_mlp(self._norm(zt))
            z = zs
        y = self.out_proj(z.reshape(z.size(0), -1))
        return y.reshape(x.size(0), N_OUTPUTS, -1).transpose(1, 2)  # (B,H,out)


class PatchTST(nn.Module):
    """Patch embedding + transformer encoder + flat head over all variates."""

    def __init__(self, patch_len: int = 20, stride: int = 20, d_model: int = 128,
                 n_heads: int = 8, n_layers: int = 2, d_ff: int = 256, dropout: float = 0.0,
                 pe: str = "zeros"):
        super().__init__()
        self.patch_len = patch_len
        self.stride = stride
        n_patch = (CONTEXT_LEN - patch_len) // stride + 1
        self.n_patch = n_patch
        self.d_model = d_model
        # per-feature patch embedding, then concat across features -> mixed-head
        self.patch_emb = nn.Conv1d(N_FEATURES, d_model, kernel_size=patch_len, stride=stride)
        self.pos = nn.Parameter(torch.zeros(1, n_patch, d_model))
        layer = nn.TransformerEncoderLayer(
            d_model=d_model, nhead=n_heads, dim_feedforward=d_ff, dropout=dropout,
            activation="gelu", batch_first=True, norm_first=True)
        self.encoder = nn.TransformerEncoder(layer, num_layers=n_layers)
        self.head = nn.Linear(n_patch * d_model, HORIZON * N_OUTPUTS)

    def forward(self, x: torch.Tensor) -> torch.Tensor:  # (B, C, F)
        B = x.size(0)
        z = self.patch_emb(x.transpose(1, 2))            # (B, d, n_patch)
        z = z.transpose(1, 2) + self.pos                # (B, n_patch, d)
        z = self.encoder(z)                              # (B, n_patch, d)
        y = self.head(z.reshape(B, -1))
        return y.reshape(B, N_OUTPUTS, -1).transpose(1, 2)  # (B,H,out)