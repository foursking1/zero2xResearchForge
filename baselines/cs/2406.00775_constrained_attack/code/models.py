"""
Deep tabular classifiers used in this reproduction.

Three distinct deep architectures (equivalent-class deep models to the
architectures studied in the paper -- TabTransformer/TabNet/RLN/etc.), all
trained with a fixed random seed on the frozen URL data:

* MLP        : a plain deep fully-connected network (e.g. TabNet/RLN-like)
* ResMLP     : a deeper residual network with LayerNorm + dropout
* FT-Transf  : a Feature Tokenizer Transformer (transformer-style surface
               model, analogous to the transformer family of the paper)

All models consume z-score standardized features and output a single logit
(binary classifier: phishing = 1).
"""

from __future__ import annotations

import torch
import torch.nn as nn


class MLP(nn.Module):
    """Plain deep MLP, 4 hidden layers."""

    def __init__(self, d_in=63, widths=(256, 128, 64, 32), act="relu", seed=0):
        super().__init__()
        gens = torch.Generator().manual_seed(seed)
        layers = []
        prev = d_in
        for w in widths:
            layers.append(nn.Linear(prev, w))
            layers.append({"relu": nn.ReLU, "leaky": nn.LeakyReLU(0.1),
                           "tanh": nn.Tanh}[act]())
            prev = w
        layers.append(nn.Linear(prev, 1))
        self.net = nn.Sequential(*layers)
        self._init(gens)

    def _init(self, gens):
        for m in self.net:
            if isinstance(m, nn.Linear):
                torch.nn.init.xavier_uniform_(m.weight, generator=gens)
                nn.init.zeros_(m.bias)

    def forward(self, x):
        return self.net(x).squeeze(-1)


class ResMLP(nn.Module):
    """Deeper residual MLP with LayerNorm + Dropout."""

    def __init__(self, d_in=63, hidden=256, depth=4, dropout=0.1, seed=1):
        super().__init__()
        gens = torch.Generator().manual_seed(seed)
        self.in_proj = nn.Linear(d_in, hidden)
        blocks = []
        for _ in range(depth):
            blocks.append(nn.Sequential(
                nn.LayerNorm(hidden),
                nn.Linear(hidden, hidden),
                nn.GELU(),
                nn.Dropout(dropout),
            ))
        self.blocks = nn.ModuleList(blocks)
        self.head = nn.Linear(hidden, 1)
        self._init(gens)

    def _init(self, gens):
        for m in self.modules():
            if isinstance(m, nn.Linear):
                torch.nn.init.xavier_uniform_(m.weight, generator=gens)
                nn.init.zeros_(m.bias)

    def forward(self, x):
        h = torch.tanh(self.in_proj(x))
        for blk in self.blocks:
            h = h + blk(h)
        return self.head(h).squeeze(-1)


class FTTransformer(nn.Module):
    """Feature-tokenization transformer (FT-Transformer) deep tabular model."""

    def __init__(self, d_in=63, d_token=64, n_layers=3, n_heads=4, n_out=1,
                 d_ff=128, dropout=0.1, seed=2):
        super().__init__()
        gens = torch.Generator().manual_seed(seed)
        self.feature_tokenizer = nn.Linear(1, d_token)  # shared per-token MLP
        num_tokens = d_in + 1  # +[CLS]
        self.first_layer = nn.LayerNorm(d_token)
        encoder = []
        for _ in range(n_layers):
            encoder.append(nn.TransformerEncoderLayer(
                d_model=d_token, nhead=n_heads, dim_feedforward=d_ff,
                dropout=dropout, activation="gelu", batch_first=True, norm_first=True))
        self.encoder = nn.ModuleList(encoder)
        self.cls_projection = nn.Linear(d_token, n_out)
        self._init(gens)

    def _init(self, gens):
        for m in self.modules():
            if isinstance(m, nn.Linear):
                torch.nn.init.xavier_uniform_(m.weight, generator=gens)
                nn.init.zeros_(m.bias)

    def forward(self, x):
        # x: [B, F] -> tokens [B, F, d_token]
        tokens = self.feature_tokenizer(x.unsqueeze(-1))
        cls = torch.zeros(x.shape[0], 1, tokens.shape[-1], dtype=tokens.dtype,
                          device=tokens.device)
        t = torch.cat([cls, tokens], dim=1)
        t = self.first_layer(t)
        for layer in self.encoder:
            t = layer(t)
        cls_out = t[:, 0]
        return self.cls_projection(cls_out).squeeze(-1)


def build_model(name: str, d_in: int = 63, device=None):
    name = name.lower()
    if name == "mlp":
        model = MLP(d_in=d_in, widths=(256, 128, 64, 32), act="relu", seed=0)
    elif name == "resmlp":
        model = ResMLP(d_in=d_in, hidden=256, depth=4, dropout=0.15, seed=1)
    elif name in ("ft", "fttransformer", "ft-transformer", "fttrans"):
        model = FTTransformer(d_in=d_in, d_token=64, n_layers=3, n_heads=4,
                              n_out=1, d_ff=128, dropout=0.15, seed=2)
    else:
        raise ValueError(f"unknown model {name}")
    if device is not None:
        model = model.to(device)
    return model