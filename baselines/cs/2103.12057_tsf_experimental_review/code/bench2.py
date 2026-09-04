"""Quick profiling: threads x batch_size x model for CPU training speed."""
import time
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from models import build_model

HORIZON = 18
CSV = "/mnt/f/dataset/cs/2103.12057_tsf_experimental_review/tsf/m3_monthly_series.csv"


def load_windows(ph=22):
    df = pd.read_csv(CSV)
    xs, ys = [], []
    for sid, g in df.groupby("series_id", sort=True):
        v = g["value"].to_numpy(np.float64)
        tr = v[:-HORIZON]
        mn, mx = tr.min(), tr.max()
        tr = (tr - mn) / (mx - mn)
        total = ph + HORIZON
        n = len(tr)
        xs.append(np.stack([tr[i : i + ph] for i in range(0, n - total + 1)]).astype(np.float32))
        ys.append(np.stack([tr[i + ph : i + total] for i in range(0, n - total + 1)]).astype(np.float32))
    return np.concatenate(xs), np.concatenate(ys)


X, Y = load_windows()


def bench(nthreads, batch_size, model, kwargs, epochs=1):
    torch.set_num_threads(nthreads)
    m = build_model(model, dict(kwargs, past_history=22, horizon=18))
    ds = torch.utils.data.TensorDataset(torch.from_numpy(X), torch.from_numpy(Y))
    loader = torch.utils.data.DataLoader(ds, batch_size=batch_size, shuffle=True, num_workers=0)
    loss_fn = nn.MSELoss()
    opt = torch.optim.Adam(m.parameters(), lr=0.001)
    m.train()
    t0 = time.time()
    nbatches = 0
    for _ in range(epochs):
        for xb, yb in loader:
            opt.zero_grad()
            loss = loss_fn(m(xb), yb)
            loss.backward()
            opt.step()
            nbatches += 1
    dt = time.time() - t0
    print(f"model={model} threads={nthreads} bs={batch_size}: {dt/epochs:.2f}s/epoch  {np.round(1000*dt/nbatches,1)}ms/batch  n_batches={nbatches}")


for nt in (20, 4, 8):
    for bs in (256, 1024, 2048):
        bench(nt, bs, "mlp", {"hidden_sizes": [64, 64]})
    bench(nt, 512, "gru", {"hidden": 64, "n_layers": 1, "dropout": 0.0})
    bench(nt, 512, "cnn", {"channels": 64, "n_layers": 3, "kernel": 3})