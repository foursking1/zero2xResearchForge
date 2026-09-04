"""Stage-timing benchmark for experiment.py internals (cpu)."""
import json
import time

import numpy as np
import torch
import torch.nn as nn

from models import build_model

HORIZON = 18
import pandas as pd


def load_series():
    df = pd.read_csv(
        "/mnt/f/dataset/cs/2103.12057_tsf_experimental_review/tsf/m3_monthly_series.csv"
    )
    series = []
    for sid, g in df.groupby("series_id", sort=True):
        series.append(g["value"].to_numpy(np.float64))
    return series


def build_instances(train_norm, ph):
    total = ph + HORIZON
    n = len(train_norm)
    x = []
    y = []
    for i in range(0, n - total + 1):
        x.append(train_norm[i : i + ph])
        y.append(train_norm[i + ph : i + total])
    return np.stack(x).astype(np.float32), np.stack(y).astype(np.float32)


t0 = time.time()
series = load_series()
print(f"load_series: {time.time()-t0:.1f}s n={len(series)}", flush=True)

ph = 22
t0 = time.time()
xs, ys = [], []
for s in series:
    mn, mx = s[:-HORIZON].min(), s[:-HORIZON].max()
    tr = (s[:-HORIZON] - mn) / (mx - mn)
    x, y = build_instances(tr, ph)
    xs.append(x)
    ys.append(y)
X = np.concatenate(xs)
Y = np.concatenate(ys)
print(f"windows: {time.time()-t0:.1f}s X={X.shape}", flush=True)

torch.set_num_threads(20)
t0 = time.time()
model = build_model("gru", {"past_history": 22, "horizon": 18, "hidden": 64, "n_layers": 1, "dropout": 0.0})
print(f"build_model: {time.time()-t0:.3f}s params={sum(p.numel() for p in model.parameters())}", flush=True)

ds = torch.utils.data.TensorDataset(torch.from_numpy(X), torch.from_numpy(Y))
t0 = time.time()
loader = torch.utils.data.DataLoader(ds, batch_size=64, shuffle=True, num_workers=0)
print(f"dataloader: {time.time()-t0:.2f}s", flush=True)

loss_fn = nn.MSELoss()
opt = torch.optim.Adam(model.parameters(), lr=0.001)
t0 = time.time()
model.train()
for batch_i, (xb, yb) in enumerate(loader):
    opt.zero_grad()
    out = model(xb)
    loss = loss_fn(out, yb)
    loss.backward()
    opt.step()
    if batch_i % 2000 == 0:
        print(f"  batch {batch_i}: {time.time()-t0:.1f}s", flush=True)
print(f"ONE-EPOCH TRAIN: {time.time()-t0:.1f}s", flush=True)