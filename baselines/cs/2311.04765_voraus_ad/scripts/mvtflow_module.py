"""mvtflow_module.py — shared MVT-Flow-style conditional RealNVP implementation.

Used by 03_mvtflow.py (main training) and 05_flow_variants.py (sweep).
Imported at module level; auto-selects CUDA if available (tiny model).
"""
import os

import numpy as np
import torch
import torch.nn as nn

import common

torch.set_num_threads(min(20, os.cpu_count()))
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
if device.type == "cuda":
    free_mb = int(torch.cuda.mem_get_info()[0] // (1024 * 1024))
    print(f"[device] using CUDA ({torch.cuda.get_device_name(0)}), "
          f"free mem {free_mb} MiB", flush=True)
    assert free_mb > 2000, "insufficient GPU memory, refusing to start"
else:
    print(f"[device] using CPU, threads={torch.get_num_threads()}", flush=True)

D = 130
N_ACTIONS = 15


# -------------------------------------------------------------------- flow
class AffineBlock(nn.Module):
    """One affine coupling block over a fixed 50/50 channel split."""

    def __init__(self, d, ctx_dim, hidden=256):
        super().__init__()
        n_half = d // 2
        self.n_half = n_half
        self.subnet = nn.Sequential(
            nn.Linear(n_half + ctx_dim, hidden),
            nn.ReLU(),
            nn.Linear(hidden, hidden),
            nn.ReLU(),
            nn.Linear(hidden, 2 * n_half),
        )

    def forward(self, x, ctx):
        n = self.n_half
        a, b = x[:, :n], x[:, n:]
        net = self.subnet(torch.cat([a, ctx], dim=1))
        log_s, t = net[:, :n], net[:, n:]
        log_s = torch.tanh(log_s) * 3.0
        b = b * torch.exp(log_s) + t
        return torch.cat([a, b], dim=1), log_s.sum(dim=1)

    def inverse(self, z, ctx):
        n = self.n_half
        a, b = z[:, :n], z[:, n:]
        net = self.subnet(torch.cat([a, ctx], dim=1))
        log_s, t = net[:, :n], net[:, n:]
        log_s = torch.tanh(log_s) * 3.0
        b = (b - t) * torch.exp(-log_s)
        return torch.cat([a, b], dim=1)


class Permute(nn.Module):
    def __init__(self, d, seed=0):
        super().__init__()
        rng = np.random.RandomState(seed)
        self.perm = torch.as_tensor(rng.permutation(d), dtype=torch.long)
        inv = np.empty(d, dtype=np.int64)
        inv[self.perm.numpy()] = np.arange(d)
        self.inv = torch.as_tensor(inv, dtype=torch.long)

    def forward(self, x):
        return x[:, self.perm], 0.0

    def inverse(self, z):
        return z[:, self.inv]


class CondRealNVP(nn.Module):
    def __init__(self, d=D, n_blocks=4, ctx_dim=32, hidden=256, seed=0):
        super().__init__()
        self.d = d
        n_half = d // 2
        self.n_half = n_half
        blocks = []
        for i in range(n_blocks):
            blocks.append(nn.ModuleList([
                Permute(d, seed=(seed + 1) * (i + 1)),
                AffineBlock(d, ctx_dim, hidden),
            ]))
        self.blocks = nn.ModuleList(blocks)
        self.context_emb = nn.Embedding(N_ACTIONS, ctx_dim)

    def to_latent(self, x, action):
        ctx = self.context_emb(action)
        ldj = 0.0
        for perm, blk in self.blocks:
            x, l = perm(x)
            x, l2 = blk(x, ctx)
            ldj = ldj + l + l2
        return x, ldj

    def log_prob(self, x, action):
        z, ldj = self.to_latent(x, action)
        logp = -0.5 * (z ** 2).sum(dim=1) - 0.5 * self.d * np.log(2 * np.pi)
        return logp + ldj


# ---------------------------------------------------------------- training
def build_timestep_pool(Xn, lengths, action, train_idx):
    """Flatten all observed training timesteps into a (N, 130) pool."""
    n_total = int(np.sum(lengths[train_idx]))
    Xp = np.empty((n_total, D), dtype=np.float32)
    Ap = np.empty(n_total, dtype=np.int64)
    off = 0
    for gi in train_idx:
        L = int(lengths[gi])
        Xp[off : off + L] = Xn[gi][:L]
        Ap[off : off + L] = action[gi]
        off += L
    return Xp, Ap


def train_epoch(model, opt, Xp, Ap, args, epoch, d_feat=D):
    model.train()
    rng = np.random.RandomState(args.seed + epoch * 99991)
    n = Xp.shape[0]
    keep = int(round(n * args.subsample))
    order = rng.permutation(n)[:keep]
    total, cnt = 0.0, 0
    bs = args.batch_size
    for start in range(0, keep, bs):
        idx = order[start : start + bs]
        x = torch.from_numpy(Xp[idx]).to(device)
        a = torch.from_numpy(Ap[idx]).to(device)
        opt.zero_grad()
        loss = -model.log_prob(x, a).mean()
        loss.backward()
        opt.step()
        total += loss.item() * len(idx)
        cnt += len(idx)
    return total / cnt


@torch.no_grad()
def evaluate(model, Xn, lengths, action, test_mask, anomaly, category, d_feat=D, pool=None, pool_action=None, rows2global=None):
    """Score all test samples: mean NLL over observed timesteps.

    With pool/rows2global (used for delta features) the score uses the
    precomputed feature pool rows instead of slicing Xn timesteps.
    """
    model.eval()
    test_idx = np.where(test_mask)[0]
    if pool is not None:
        pass
    scores = np.zeros(len(test_idx))
    for i, gi in enumerate(test_idx):
        L = int(lengths[gi])
        if pool is not None:
            r0, r1 = rows2global[gi]
            feat = pool[r0:r1]
            x = torch.as_tensor(feat[None], dtype=torch.float32).to(device)
            act = torch.as_tensor([action[gi]], dtype=torch.long).to(device)
            logp = model.log_prob(x.reshape(-1, d_feat), act.repeat_interleave(L))
            scores[i] = -float(logp.mean())
        else:
            x = torch.as_tensor(Xn[gi][:L][None], dtype=torch.float32).to(device)
            act = torch.as_tensor([action[gi]], dtype=torch.long).to(device)
            logp = model.log_prob(x.reshape(-1, d_feat), act.repeat_interleave(L))
            scores[i] = -float(logp.mean())
    full = np.full(Xn.shape[0], np.nan)
    full[test_idx] = scores
    aucs = common.evaluate_method(full, anomaly, category, test_mask)
    return full, float(np.nanmean(list(aucs.values()))), aucs