"""N-HiTS (Challu et al., 2023) — deep global model, PyTorch implementation.

A faithful-but-lean N-HiTS used as the *deep global* forecaster. One model is
trained per sampling frequency (monthly / quarterly / yearly) over *all* series
of that frequency jointly (both M3 and Tourism — global training), as allowed
by TASK.md with explicit declaration.

Training data: *only* the pre-test segment of every series (train =
``values[:-H]``). The test segment (last H observations) never enters training,
validation windows, or early stopping. A small random validation split (fresh
windows from the same pre-test segment, fixed seed) is used for early stopping.
"""

from __future__ import annotations

import os

import numpy as np
import torch
import torch.nn as nn

# Device selection: CPU by default (offline multi-task benchmark). Set
# NHITS_DEVICE=cuda to train on GPU when free VRAM is available.
DEVICE = os.environ.get("NHITS_DEVICE", "cpu")
if DEVICE == "cuda" and not torch.cuda.is_available():
    DEVICE = "cpu"

# Small tensors thrash under OpenMP; a single thread is far faster here.
torch.set_num_threads(1)


# ---------------------------------------------------------------------------
# interpolation helpers
# ---------------------------------------------------------------------------
def _interp_resize_matrix(target_len, source_len, device=None):
    """[target_len, source_len] linear-interpolation matrix."""
    device = device or torch.device("cpu")
    if target_len == source_len:
        return torch.eye(source_len, device=device)
    src = torch.linspace(0, source_len - 1, steps=target_len, device=device)
    lo = torch.floor(src).long().clamp(0, source_len - 2)
    hi = (lo + 1).clamp(max=source_len - 1)
    w = (src - lo).unsqueeze(1)  # [target, 1]
    rows_lo = torch.zeros(target_len, source_len, device=device)
    rows_hi = torch.zeros(target_len, source_len, device=device)
    rows_lo.scatter_(1, lo.unsqueeze(1), 1.0)
    rows_hi.scatter_(1, hi.unsqueeze(1), 1.0)
    return rows_lo * (1.0 - w) + rows_hi * w


# ---------------------------------------------------------------------------
# N-HiTS building blocks
# ---------------------------------------------------------------------------
class IdentityBasis(nn.Module):
    """Maps pooled backcast/forecast coefficients to full length via a linear
    (identity) interpolation basis, the multi-rate component of N-HiTS."""

    def __init__(self, in_len, out_len, pooled_in, pooled_out):
        super().__init__()
        self.backcast = _interp_resize_matrix(in_len, pooled_in)
        self.forecast = _interp_resize_matrix(out_len, pooled_out)

    def forward(self, theta_backcast, theta_forecast):
        device = theta_backcast.device
        b = theta_backcast @ self.backcast.to(device).T   # [B, in_len]
        f = theta_forecast @ self.forecast.to(device).T   # [B, out_len]
        return b, f


class NHiTSBlock(nn.Module):
    def __init__(self, in_len, out_len, width=32, pooling_kernel=2):
        super().__init__()
        self.in_len = in_len
        self.out_len = out_len
        self.k = max(1, int(pooling_kernel))
        self.pooled_in = (in_len - self.k) // self.k + 1 if in_len >= self.k else in_len
        self.pooled_out = int(np.ceil(out_len / self.k))

        self.pool = nn.MaxPool1d(kernel_size=self.k, stride=self.k)
        self.mlp = nn.Sequential(
            nn.Linear(self.pooled_in, width), nn.ReLU(),
            nn.Linear(width, width), nn.ReLU(),
            nn.Linear(width, width), nn.ReLU(),
            nn.Linear(width, self.pooled_in + self.pooled_out),
        )
        self.basis = IdentityBasis(in_len, out_len, self.pooled_in, self.pooled_out)

    def forward(self, insample_x):
        # insample_x: [B, in_len]
        x_pooled = self.pool(insample_x.unsqueeze(1)).squeeze(1)  # [B, pooled_in]
        theta = self.mlp(x_pooled)                                # [B, pooled_in + pooled_out]
        theta_b, theta_f = theta.split([self.pooled_in, self.pooled_out], dim=-1)
        return self.basis(theta_b, theta_f)                       # backcast, forecast


class NHiTS(nn.Module):
    """N-HiTS predicting ``out_len`` steps from ``in_len`` inputs.

    Stacks use increasing max-pooling kernels [k^1, k^2, ...] across stacks
    (multi-rate sampling): fine stacks capture fast dynamics, coarse stacks the
    slow trend. Stack forecasts are combined with a learnable soft-softmax
    weighting ('learning-rate reduction' of the paper).
    """

    def __init__(self, in_len, out_len, n_stacks=3, n_blocks_per_stack=1,
                 width=32, n_pool_kernel_size=2):
        super().__init__()
        self.in_len = in_len
        self.out_len = out_len
        self.n_stacks = n_stacks
        self.blocks_per_stack = n_blocks_per_stack
        self.blocks = nn.ModuleList()
        for s_idx in range(n_stacks):
            k = int(n_pool_kernel_size) ** (s_idx + 1)
            for _ in range(n_blocks_per_stack):
                self.blocks.append(NHiTSBlock(in_len, out_len, width, k))
        if n_stacks > 1:
            self.stack_weights = nn.Parameter(torch.zeros(n_stacks))
        else:
            self.register_buffer("stack_weights", torch.ones(1))

    def forward(self, insample_x):
        residual = insample_x
        stack_forecasts = []
        for s_idx in range(self.n_stacks):
            first = s_idx * self.blocks_per_stack
            last = (s_idx + 1) * self.blocks_per_stack - 1
            fc_stack = None
            for bi in range(first, last + 1):
                backcast, fc = self.blocks[bi](residual)
                residual = residual - backcast
                if bi == last:
                    fc_stack = fc
            stack_forecasts.append(fc_stack)
        ws = torch.softmax(self.stack_weights, dim=0)
        forecast = torch.zeros(insample_x.shape[0], self.out_len, device=insample_x.device)
        for si, fc in enumerate(stack_forecasts):
            if fc.shape[-1] != self.out_len:
                fc = fc @ _interp_resize_matrix(self.out_len, fc.shape[-1]).to(fc.device).T
            forecast = forecast + ws[si] * fc
        return forecast


# ---------------------------------------------------------------------------
# data preparation
# ---------------------------------------------------------------------------
def build_windows(series_values, in_len, out_len, train_horizon, max_windows, rng):
    """Windows from the *pre-test* part of a series (leak-free)."""
    train = np.asarray(series_values[:-train_horizon], dtype=np.float64)
    n = len(train) - in_len - out_len
    if n < 1:
        return None, None
    stride = max(1, int(np.ceil(n / max_windows)))
    xs, ys = [], []
    for t in range(0, n, stride):
        xs.append(train[t:t + in_len])
        ys.append(train[t + in_len:t + in_len + out_len])
    return np.stack(xs), np.stack(ys)


def standardize_window(x, y):
    m, sd = x.mean(), x.std() + 1e-8
    return ((x - m) / sd).astype(np.float32), ((y - m) / sd).astype(np.float32)


TARGET_CLIP = float(os.environ.get("NHITS_TARGET_CLIP", "5.0"))


class _WindowDataset(torch.utils.data.Dataset):
    def __init__(self, X, Y):
        self.X = X.astype(np.float32)
        self.Y = Y.astype(np.float32)

    def __len__(self):
        return len(self.X)

    def __getitem__(self, i):
        x, mx, sx = self.X[i], self.X[i].mean(), self.X[i].std() + 1e-8
        x = ((x - mx) / sx).astype(np.float32)
        y = np.clip((self.Y[i] - mx) / sx, -TARGET_CLIP, TARGET_CLIP).astype(np.float32)
        return x, y


# ---------------------------------------------------------------------------
# training loop
# ---------------------------------------------------------------------------
def train_nhits(series_list, freq, cfg, outdir=None, seed=42):
    """Train one global N-HiTS on all series of frequency ``freq``.

    Returns (model, stats).
    """
    in_len = cfg["input_window"]
    out_len = cfg["output_horizon"]

    rng = np.random.default_rng(seed)
    all_x, all_y = [], []
    needed = [s for s in series_list if s.frequency == freq]
    for s in needed:
        xw, yw = build_windows(s.values, in_len, out_len, s.horizon,
                               cfg.get("max_windows_per_series", 200), rng)
        if xw is not None and len(xw):
            all_x.append(xw)
            all_y.append(yw)
    X = np.concatenate(all_x)
    Y = np.concatenate(all_y)
    print(f"[nhits:{freq}] windows: {X.shape}, series: {len(needed)}")

    rng2 = np.random.default_rng(seed)
    n_val = max(1, int(cfg.get("val_fraction", 0.1) * len(X)))
    idx = rng2.permutation(len(X))
    val_idx, tr_idx = idx[:n_val], idx[n_val:]
    ds_tr, ds_val = _WindowDataset(X[tr_idx], Y[tr_idx]), _WindowDataset(X[val_idx], Y[val_idx])
    dl_tr = torch.utils.data.DataLoader(ds_tr, batch_size=cfg.get("batch_size", 256),
                                        shuffle=True,
                                        generator=torch.Generator().manual_seed(seed))
    dl_val = torch.utils.data.DataLoader(ds_val, batch_size=1024, shuffle=False)

    torch.manual_seed(seed)
    model = NHiTS(in_len, out_len, cfg["n_stacks"], cfg["n_blocks_per_stack"],
                  cfg["width"], cfg["n_pool_kernel_size"])
    model.to(DEVICE)
    opt = torch.optim.Adam(model.parameters(), lr=cfg.get("lr", 1e-3), weight_decay=cfg.get("weight_decay", 1e-4))
    sched = torch.optim.lr_scheduler.ReduceLROnPlateau(opt, factor=0.5, patience=3)
    lossf = nn.MSELoss()
    epochs, patience = cfg.get("epochs", 30), cfg.get("patience", 5)
    best_val, best_state, bad = float("inf"), None, 0

    for epoch in range(epochs):
        model.train()
        running = 0.0
        cnt = 0
        for x, y in dl_tr:
            x, y = x.to(DEVICE), y.to(DEVICE)
            opt.zero_grad()
            loss = lossf(model(x), y)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            running += loss.item() * x.shape[0]
            cnt += x.shape[0]
        model.eval()
        vsum = 0.0
        vcnt = 0
        with torch.no_grad():
            for x, y in dl_val:
                x, y = x.to(DEVICE), y.to(DEVICE)
                vsum += ((model(x) - y) ** 2).sum().item()
                vcnt += y.shape[0]
        vloss = vsum / vcnt
        sched.step(vloss)
        if vloss < best_val - 1e-6:
            best_val = vloss
            best_state = {k: v.detach().clone() for k, v in model.state_dict().items()}
            bad = 0
        else:
            bad += 1
        print(f"[nhits:{freq}] epoch {epoch + 1:2d} tr {running / max(cnt, 1):.4f} "
              f"val {vloss:.4f} best {best_val:.4f}")
        if bad >= patience:
            print(f"[nhits:{freq}] early stop at epoch {epoch + 1}")
            break

    model.load_state_dict(best_state)
    stats = {"best_val_mse": float(best_val), "windows": X.shape[0]}
    if outdir:
        os.makedirs(outdir, exist_ok=True)
        torch.save({"state_dict": best_state, "config": cfg},
                   os.path.join(outdir, f"nhits_{freq}.pt"))
    return model, stats


def predict_nhits(model, series, in_len, out_len):
    """Forecast one test segment using the last ``in_len`` pre-test observations."""
    train = np.asarray(series.values[:-series.horizon], dtype=np.float64)
    if len(train) == 0:
        return None
    x = train[-in_len:] if len(train) >= in_len else np.pad(
        train, (in_len - len(train), 0), mode="edge")
    m, sd = x.mean(), x.std() + 1e-8
    xin = torch.from_numpy(((x - m) / sd).astype(np.float32)).unsqueeze(0).to(DEVICE)
    model.eval()
    with torch.no_grad():
        pred = model(xin)[0].cpu().numpy()[:series.horizon] * sd + m
    return pred