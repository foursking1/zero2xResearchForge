"""Pick final settings: threads=4, batch sizes for each model."""
import time
import numpy as np
import pandas as pd
import torch
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


def bench(nthreads, batch_size, model, kwargs):
    torch.set_num_threads(nthreads)
    m = build_model(model, dict(kwargs, past_history=22, horizon=18))
    ds = torch.utils.data.TensorDataset(torch.from_numpy(X), torch.from_numpy(Y))
    loader = torch.utils.data.DataLoader(ds, batch_size=batch_size, shuffle=True, num_workers=0)
    loss_fn = torch.nn.MSELoss()
    opt = torch.optim.Adam(m.parameters(), lr=0.001)
    m.train()
    t0 = time.time()
    nb = 0
    for xb, yb in loader:
        opt.zero_grad()
        loss = loss_fn(m(xb), yb)
        loss.backward()
        opt.step()
        nb += 1
    dt = time.time() - t0
    print(f"model={model:4s} threads={nthreads} bs={batch_size}: {dt:.2f}s/epoch {1000*dt/nb:.1f}ms/batch n_batches={nb}")


bench(4, 512, "lstm", {"hidden": 64, "n_layers": 1, "dropout": 0.0})
bench(4, 512, "tcn", {"channels": 32, "n_blocks": 3, "kernel": 3, "dropout": 0.0})
bench(4, 512, "tcn", {"channels": 64, "n_blocks": 4, "kernel": 3, "dropout": 0.0})
bench(4, 512, "gru", {"hidden": 64, "n_layers": 1, "dropout": 0.0})
bench(4, 512, "gru", {"hidden": 128, "n_layers": 2, "dropout": 0.0})
bench(4, 1024, "mlp", {"hidden_sizes": [256, 256]})
bench(4, 1024, "mlp", {"hidden_sizes": [32, 64, 128, 64, 32]})