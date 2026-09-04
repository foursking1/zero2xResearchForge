"""PA-RiskRanker (arXiv:2509.16616) and Rankformer-style baseline — PyTorch.

PA-RiskRanker  : per-trader feature embedder -> transformer encoder with
                 *self-cross-trader attention* within each ranking group
                 (each trader attends to every other trader in its group),
                 trained with *profit-aware BCE* (PA-BCE) in which every risky
                 trader's loss term is weighted by its financial impact
                 (Amount / profit), so misranks of high-impact traders are
                 penalised most.
Rankformer-bsl : identical backbone but WITHOUT inter-trader attention and
                 trained with a plain ListNet (softmax) listwise rank loss --
                 the contrast isolates the value of cross-trader attention +
                 profit-aware weighting.
"""
from __future__ import annotations
import numpy as np, torch, torch.nn as nn, torch.nn.functional as F
from torch.optim.lr_scheduler import CosineAnnealingLR


class PARiskRanker(nn.Module):
    def __init__(self, d_in, d_embed=128, n_layer=2, n_head=4, ff=256,
                 dropout=0.05, cross=True, aux=False, mode="seq"):
        super().__init__()
        self.cross = cross
        self.aux = aux
        self.mode = mode            # "seq": tokens over traders; "ft": tokens over features
        if mode == "ft":
            self.feat_emb = nn.Parameter(torch.zeros(d_in, d_embed))
            nn.init.normal_(self.feat_emb, std=0.1)
            self.cls = nn.Parameter(torch.zeros(1, 1, d_embed))
        else:
            self.embed = nn.Sequential(nn.Linear(d_in, d_embed), nn.ReLU(),
                                       nn.Linear(d_embed, d_embed), nn.LayerNorm(d_embed))
        if cross:
            enc = nn.TransformerEncoderLayer(d_model=d_embed, nhead=n_head, dim_feedforward=ff,
                                             dropout=dropout, batch_first=True,
                                             activation="gelu", norm_first=True)
            self.encoder = nn.TransformerEncoder(enc, num_layers=n_layer)
        else:
            # Rankformer-style: no inter-token attention, per-token MLP only
            self.encoder = nn.Sequential(
                nn.Sequential(nn.Linear(d_embed, ff), nn.GELU(), nn.Linear(ff, d_embed)),
                nn.LayerNorm(d_embed),
            )
        self.head = nn.Linear(d_embed, 1)
        if aux:
            self.head_aux = nn.Sequential(
                nn.Linear(d_embed, 64), nn.ReLU(), nn.Linear(64, 1))  # profit-proxy head
        else:
            self.head_aux = None

    def tokens(self, x):
        d = self.feat_emb.shape[1] if self.mode == "ft" else self.embed
        if self.mode == "ft":
            flat = x.reshape(-1, x.shape[-1]) if x.dim() == 3 else x      # (B, D)
            toks = flat.unsqueeze(-1) * self.feat_emb                      # (B, D, d)
            cls = self.cls.expand(len(flat), 1, -1)
            return torch.cat([cls, toks], dim=1)
        if x.dim() == 3:
            return self.embed(x)
        return self.embed(x.unsqueeze(1))

    def forward(self, x):
        """x: (B, G, D) ranking-group tensor. Returns (logits, aux) or logits."""
        toks = self.tokens(x)
        h = self.encoder(toks)                          # cross attention OR per-token MLP
        if self.mode == "ft":
            rep = h[:, 0]
        else:
            rep = h
        logits = self.head(rep).squeeze(-1)             # (B,G)
        if self.aux and self.head_aux is not None:
            return logits, self.head_aux(rep).squeeze(-1)
        return logits

    def encode(self, x):
        toks = self.tokens(x)
        h = self.encoder(toks)
        return h[:, 0] if self.mode == "ft" else h


def pabce_loss(logits, y, impact_pos, pos_lambda=20.0, w_cap=3.0):
    """Profit-aware BCE (paper Sec.3.4).
    w_i = pos_lambda * clip(impact_i / mean(impact over train positives), 0, w_cap)
          for risky traders; w_i = 1 for normals.
    Loss = mean over all samples of w_i * BCE_i.
    """
    p = torch.sigmoid(logits).clamp(1e-6, 1 - 1e-6)
    bce = -(y * torch.log(p) + (1 - y) * torch.log(1 - p))
    w = torch.full_like(y, fill_value=1.0, dtype=torch.float32)
    pos_mask = y > 0.5
    if pos_mask.any():
        w[pos_mask] = pos_lambda * torch.clamp(torch.clamp(impact_pos[pos_mask], min=0.0), max=w_cap)
    return (bce * w).mean()


def aux_huber_loss(aux_out, tgt, delta=1.0):
    """Profit-aware auxiliary: Huber loss on asinh(impact) proxy target."""
    return F.smooth_l1_loss(aux_out, tgt, beta=delta)


def listnet_loss(logits, y):
    """ListNet top-1 softmax listwise rank loss over each group."""
    yf = y.float()
    log_p = logits.log_softmax(dim=-1)
    l = -(yf / yf.sum(-1, keepdim=True).clamp(min=1e-9)) * log_p
    return l.sum(-1).mean()


@torch.no_grad()
def predict_scores(model, X_test):
    model.eval()
    out = []
    for i in range(0, len(X_test), 512):
        b = torch.tensor(X_test[i:i + 512], dtype=torch.float32)
        if b.dim() == 2:
            b = b.unsqueeze(1)
        out.append(torch.sigmoid(model(b)[:, 0]).numpy())
    return np.concatenate(out)


def to_tensor(a):
    return torch.tensor(a, dtype=torch.float32)


if __name__ == "__main__":
    m = PARiskRanker(29, cross=True)
    x = torch.randn(4, 100, 29)
    print("cross out:", m(x).shape)
    m2 = PARiskRanker(29, cross=False)
    print("no-cross out:", m2(x).shape)