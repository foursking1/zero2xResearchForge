#!/usr/bin/env python3
"""Model definitions used for the OGBG-MOLHIV reproduction.

All GNN models share the architecture family used in the OGB paper (Table 15):
5 message-passing layers + (optional) virtual node + global mean pooling +
an MLP readout head. Layer count / hidden size stay configurable.

Classes:
  GINModel    - GIN-0 style model (no learnable eps).
  GCNModel    - GCN (Kipf & Welling) variant used by OGB.
  VirtualNode - official-style virtual-node module (OGB implementations/graph/gin_gnn.py).
  MLPBaseline - non-graph baseline on per-graph aggregated atom features.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import GCNConv, GINConv, global_add_pool, global_mean_pool


class VirtualNode(nn.Module):
    """Appends a virtual node connected (implicitly) to all other nodes.

    Update rule follows the OGB reference implementation:
    v_new = BN(LIN(v) + SUM_OVER_NODES(h_i)),  h  gets 'v_new' broadcast back
    as a residual added before the next message-passing layer.
    """

    def __init__(self, dim):
        super().__init__()
        self.lin = nn.Linear(dim, dim, bias=False)
        self.bn = nn.BatchNorm1d(dim)

    def forward(self, h, vnode, batch, num_graphs):
        pooled = global_add_pool(h, batch, size=num_graphs)
        new_v = self.lin(vnode) + pooled
        new_v = self.bn(new_v)
        return F.relu(new_v)


class GINModel(nn.Module):
    def __init__(self, in_channels, hidden, num_layers, dropout=0.5,
                 virtual_node=False, out_channels=1):
        super().__init__()
        self.num_layers = num_layers
        self.virtual_node = virtual_node
        self.dropout = dropout

        self.convs = nn.ModuleList()
        self.bns = nn.ModuleList()
        self.vnodes = nn.ModuleList()
        for i in range(num_layers):
            self.convs.append(GINConv(nn.Linear(hidden if i else in_channels, hidden)))
            self.bns.append(nn.BatchNorm1d(hidden))
            if virtual_node and i < num_layers - 1:
                self.vnodes.append(VirtualNode(hidden))

        self.head = nn.Sequential(
            nn.Linear(hidden, hidden),
            nn.BatchNorm1d(hidden),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden, out_channels),
        )

    def forward(self, x, edge_index, batch):
        num_graphs = int(batch.max()) + 1
        vnode = torch.zeros(num_graphs, self.convs[0].nn.out_features,
                            device=x.device) if self.virtual_node else None

        for i, conv in enumerate(self.convs):
            if self.virtual_node and i > 0:
                x = x + vnode[batch]
            x = conv(x, edge_index)
            x = self.bns[i](x)
            x = F.relu(x)
            x = F.dropout(x, p=self.dropout, training=self.training)
            if self.virtual_node and i < self.num_layers - 1:
                vnode = self.vnodes[i](x, vnode, batch, num_graphs)

        x = global_mean_pool(x, batch)
        return self.head(x)


class GCNModel(nn.Module):
    def __init__(self, in_channels, hidden, num_layers, dropout=0.5,
                 virtual_node=False, out_channels=1):
        super().__init__()
        self.num_layers = num_layers
        self.virtual_node = virtual_node
        self.dropout = dropout

        self.convs = nn.ModuleList()
        self.bns = nn.ModuleList()
        self.vnodes = nn.ModuleList()
        for i in range(num_layers):
            self.convs.append(GCNConv(hidden if i else in_channels, hidden))
            self.bns.append(nn.BatchNorm1d(hidden))
            if virtual_node and i < num_layers - 1:
                self.vnodes.append(VirtualNode(hidden))

        self.head = nn.Sequential(
            nn.Linear(hidden, hidden),
            nn.BatchNorm1d(hidden),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden, out_channels),
        )

    def forward(self, x, edge_index, batch):
        num_graphs = int(batch.max()) + 1
        vnode = torch.zeros(num_graphs, self.convs[0].out_channels,
                            device=x.device) if self.virtual_node else None

        for i, conv in enumerate(self.convs):
            if self.virtual_node and i > 0:
                x = x + vnode[batch]
            x = conv(x, edge_index)
            x = self.bns[i](x)
            x = F.relu(x)
            x = F.dropout(x, p=self.dropout, training=self.training)
            if self.virtual_node and i < self.num_layers - 1:
                vnode = self.vnodes[i](x, vnode, batch, num_graphs)

        x = global_mean_pool(x, batch)
        return self.head(x)


class MLPBaseline(nn.Module):
    """Non-graph baseline: per-graph aggregated atom features -> MLP.

    'graph features' are computed outside (mean/max/std/sum of the 9-dim atom
    features over atoms); the model is a plain MLP with no message passing.
    """

    def __init__(self, in_channels, hidden=128, out_channels=1, dropout=0.3):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(in_channels, hidden),
            nn.BatchNorm1d(hidden),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden, hidden),
            nn.BatchNorm1d(hidden),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden, out_channels),
        )

    def forward(self, x):
        return self.net(x)


def graph_features(graphs):
    """Aggregate per-graph atom features into fixed-size vectors (no structure).

    Returns (feats, y) tensors for the list of PyG Data objects.
    Aggregation: mean, max, min, sum, std over nodes for each of the 9 dims,
    plus node counts. -> 5*9 + 1 = 46 dims.
    """
    feats, ys = [], []
    for g in graphs:
        x = g.x
        agg = torch.cat([
            x.mean(dim=0),
            x.max(dim=0).values,
            x.min(dim=0).values,
            x.sum(dim=0),
            x.std(dim=0) if x.shape[0] > 1 else torch.zeros_like(x[0]),
            torch.tensor([float(g.num_nodes)], dtype=torch.float32),
        ])
        feats.append(agg)
        ys.append(g.y.float().view(-1))
    feats = torch.stack(feats)
    ys = torch.cat(ys)
    return feats, ys