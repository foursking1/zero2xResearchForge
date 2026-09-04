# -*- coding: utf-8 -*-
"""Conditional normalizing flow (RealNVP) for the PTA posterior.

Learns p_phi(theta | summary) from forward-simulated (theta, summary) pairs
(paper's amortised-inference protocol, Shih et al. 2024 / PTAflow-style).
Conditioning summary = b (280-dim Fourier projection) + c (scalar), the exact
sufficient statistics of the Gaussian likelihood for fixed white noise.

Parameters are scaled to [0,1] (linearly from the prior box) before being fed
to the flow. Base distribution is a standard Normal N(0,1)^22 (a standard
RealNVP choice; the paper uses Uniform[-1,1] as base, but a normal base keeps
q_phi > 0 everywhere, which is required for the importance-reweighting step
Eq.G1 and gives a well-defined likelihood-free posterior).
"""
import numpy as np
import torch
import torch.nn as nn


class CondMLP(nn.Module):
    def __init__(self, dim_in, dim_out, hidden=128):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(dim_in, hidden), nn.ReLU(),
            nn.Linear(hidden, hidden), nn.ReLU(),
            nn.Linear(hidden, dim_out),
        )

    def forward(self, x):
        return self.net(x)


class CouplingLayer(nn.Module):
    def __init__(self, dim, context_dim, mask, hidden=128, scale_beta=4.0):
        super().__init__()
        self.dim = dim
        self.scale_beta = scale_beta
        self.register_buffer("mask", torch.tensor(mask, dtype=torch.float32))
        self.mlp = CondMLP(dim + context_dim, 2 * dim, hidden)

    def forward(self, theta, context):
        """theta -> z (affine coupling)."""
        masked = theta * self.mask
        h = self.mlp(torch.cat([masked, context], dim=-1))
        scale, shift = h.chunk(2, dim=-1)  # each [..., dim]
        scale = torch.tanh(scale) * self.scale_beta  # bounded
        z = masked + (1 - self.mask) * (theta * torch.exp(scale) + shift)
        logdet = ((1 - self.mask) * scale).sum(dim=-1)
        return z, logdet

    def inverse(self, z, context):
        """z -> theta."""
        masked = z * self.mask
        h = self.mlp(torch.cat([masked, context], dim=-1))
        scale, shift = h.chunk(2, dim=-1)
        scale = torch.tanh(scale) * self.scale_beta
        theta = masked + (1 - self.mask) * ((z - shift) * torch.exp(-scale))
        return theta


class RealNVP(nn.Module):
    def __init__(self, dim=22, context_dim=281, n_layers=5, hidden=192, scale_beta=4.0):
        super().__init__()
        self.dim = dim
        masks = []
        for i in range(n_layers):
            # alternating half-masks
            if i % 2 == 0:
                masks.append(np.concatenate([np.ones(dim // 2), np.zeros(dim - dim // 2)]))
            else:
                masks.append(np.concatenate([np.zeros(dim // 2), np.ones(dim - dim // 2)]))
        self.layers = nn.ModuleList(
            [CouplingLayer(dim, context_dim, masks[i], hidden, scale_beta) for i in range(n_layers)]
        )

    def forward(self, theta, context):
        z = theta
        logdet = 0.0
        for layer in self.layers:
            z, ld = layer.forward(z, context)
            logdet = logdet + ld
        return z, logdet

    def log_prob(self, theta, context):
        """log q_phi(theta | context); base = Standard Normal."""
        z, logdet = self.forward(theta, context)
        # base N(0,1)^dim
        lp = -0.5 * z.pow(2).sum(dim=-1) - 0.5 * self.dim * np.log(2 * np.pi) + logdet
        return lp

    def sample(self, n, context):
        """Draw n samples from q_phi(theta | context). context: [n, context_dim]."""
        with torch.no_grad():
            z = torch.randn(n, self.dim)
            theta = z
            for layer in reversed(self.layers):
                theta = layer.inverse(theta, context)
        return theta.numpy()


def to_torch(x):
    return torch.from_numpy(np.asarray(x, dtype=np.float32))


def train_nf(theta_train, summary_train, n_epochs=30, batch_size=256, lr=8e-4,
             context_dim=None, dim=22, seed=0, hidden=192, n_layers=5):
    """Train the conditional flow. Returns (model, loss_history)."""
    torch.manual_seed(seed)
    np.random.seed(seed)
    model = RealNVP(dim=dim, context_dim=context_dim, n_layers=n_layers, hidden=hidden)
    opt = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-5)
    sched = torch.optim.lr_scheduler.ReduceLROnPlateau(opt, factor=0.5, patience=4)
    n = len(theta_train)
    hist = []
    for epoch in range(n_epochs):
        perm = np.random.permutation(n)
        tot_loss = 0.0
        nb = 0
        for i in range(0, n, batch_size):
            idx = perm[i:i + batch_size]
            th = to_torch(theta_train[idx])
            ct = to_torch(summary_train[idx])
            opt.zero_grad()
            loss = -model.log_prob(th, ct).mean()
            loss.backward()
            opt.step()
            tot_loss += loss.item()
            nb += 1
        avg = tot_loss / nb
        hist.append(avg)
        sched.step(avg)
    return model, hist
