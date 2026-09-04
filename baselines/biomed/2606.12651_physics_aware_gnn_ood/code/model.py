"""Pure-PyTorch GINE instantiation (no torch_geometric dependency).

GINE (Graph Isomorphism Network with edge features, Hu et al. 2020):
    h_v^{l+1} = MLP^l((1+eps) h_v^l + sum_{u in N(v)} ReLU(h_u^l + e_{uv}))

Implemented with raw index_add_ scatter so it runs anywhere with PyTorch.
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
from config import TRAIN, MODEL


class GINELayer(nn.Module):
    def __init__(self, in_dim, out_dim, edge_dim, eps=0.0, bn=True):
        super().__init__()
        self.eps = eps
        self.mlp = nn.Sequential(
            nn.Linear(in_dim, out_dim), nn.ReLU(inplace=False), nn.Linear(out_dim, out_dim))
        self.edge_proj = nn.Linear(edge_dim, in_dim, bias=False)
        self.bn = nn.BatchNorm1d(out_dim) if bn else nn.Identity()

    def forward(self, x, edge_index, edge_attr):
        # edge_index: [2,E], src = edge_index[0], dst = edge_index[1]
        src, dst = edge_index
        e = torch.relu(self.edge_proj(edge_attr))              # [E, in_dim]
        msg_in = x[src] + e                                    # [E, in_dim]
        msg = torch.relu(msg_in)
        agg = torch.zeros_like(x)
        agg.index_add_(0, dst, msg)                            # scatter-add to dst
        h = (1.0 + self.eps) * x + agg
        h = self.mlp(h)
        return self.bn(h)


class AuxHead(nn.Module):
    def __init__(self, in_dim):
        super().__init__()
        self.net = nn.Sequential(nn.Linear(in_dim, in_dim), nn.ReLU(), nn.Linear(in_dim, 1))

    def forward(self, h):
        return self.net(h).squeeze(-1)


class GINE(nn.Module):
    def __init__(self, atom_dim, edge_dim, hidden=64, layers=3, num_aux=0):
        super().__init__()
        self.emb = nn.Linear(atom_dim, hidden)
        self.convs = nn.ModuleList()
        for _ in range(layers):
            self.convs.append(GINELayer(hidden, hidden, edge_dim, eps=0.0))
        self.head = nn.Linear(2 * hidden, 1)
        self.aux_heads = nn.ModuleList([AuxHead(2 * hidden) for _ in range(num_aux)])

    def forward(self, x, edge_index, edge_attr, node_batch):
        x = torch.relu(self.emb(x))
        for conv in self.convs:
            x = conv(x, edge_index, edge_attr)
        mu = _seg_mean(x, node_batch)
        mx = _seg_max(x, node_batch)
        g = torch.cat([mu, mx], dim=1)
        logit = self.head(g)                     # [N,1]
        aux = [h(g) for h in self.aux_heads]
        return logit, aux


def _seg_mean(x, b):
    n = b.max().long().item() + 1
    s = torch.zeros(n, x.size(1), device=x.device)
    s.index_add_(0, b, x)
    cnt = torch.bincount(b, minlength=n).clamp(min=1).unsqueeze(1).float()
    return s / cnt


def _seg_max(x, b):
    n = b.max().long().item() + 1
    if n <= 0:
        return x.new_zeros((0, x.size(1)))
    # x >= 0 (ReLU everywhere), so include_self=True keeps empty graphs at 0
    mx = x.new_zeros((n, x.size(1)))
    mx.index_reduce_(0, b, x, reduce="amax", include_self=True)
    return mx


def build_model(num_aux, atom_dim, edge_dim):
    return GINE(atom_dim, edge_dim, hidden=MODEL["hidden"], layers=MODEL["layers"],
                num_aux=num_aux)


def loss_fn(logit, y, aux, aux_targets, pos_weights, aux_w):
    """Returns main BCE + weighted aux MSE."""
    if pos_weights is not None:
        loss_main = F.binary_cross_entropy_with_logits(logit, y, pos_weight=pos_weights)
    else:
        loss_main = F.binary_cross_entropy_with_logits(logit, y)
    aux_losses = []
    for h, (t, m) in zip(aux, aux_targets):
        valid = m
        hh, tt = h[valid], t[valid]
        aux_loss = F.mse_loss(hh, tt) if hh.numel() else torch.tensor(0.0, device=h.device)
        aux_losses.append(aux_loss)
    loss_aux = aux_losses[0] if aux_losses else torch.tensor(0.0, device=logit.device)
    return loss_main + aux_w * loss_aux, loss_main, aux_losses


def get_pos_weights(y):
    neg = float((y == 0).sum())
    pos = float((y == 1).sum())
    return torch.tensor([neg / max(pos, 1e-6)], dtype=torch.float)