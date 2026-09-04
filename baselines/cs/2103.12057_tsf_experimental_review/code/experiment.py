"""Train + evaluate one (architecture, config) pair on frozen M3 monthly.

Protocol (aligned with Lara-Benitez et al. 2021, arXiv 2103.12057):
- fixed origin: last 18 observations of each series = test, rest = train
- per-series min-max normalization, statistics fit on train segment ONLY
- MIMO sliding windows: input = last `past_history` values, output = next 18
- WAPE per series = mean(|y-o|) / mean(y); averaged over all test series
"""
import argparse
import hashlib
import json
import os
import time

import numpy as np
import pandas as pd
import torch
import torch.nn as nn

torch.set_num_threads(int(os.environ.get("TORCH_THREADS", "4")))

from models import build_model

HORIZON = 18
DATA_ROOT = os.environ.get(
    "M3_DATA",
    "/mnt/f/dataset/cs/2103.12057_tsf_experimental_review/tsf",
)
CSV_PATH = os.path.join(DATA_ROOT, "m3_monthly_series.csv")

BEST_STATE = {}


def set_seed(seed):
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def load_series():
    df = pd.read_csv(CSV_PATH)
    series = []
    for sid, g in df.groupby("series_id", sort=True):
        series.append(g["value"].to_numpy(np.float64))
    return series


def fit_normalize(train, method="minmax"):
    """fit normalization stats on train, return (inv_tf, func) or None if degenerate."""
    if method == "minmax":
        mn, mx = float(train.min()), float(train.max())
        if mx - mn < 1e-12:
            return None
        return (mn, mx)
    elif method == "zscore":
        mu, sd = float(train.mean()), float(train.std())
        if sd < 1e-12:
            return None
        return (mu, sd)
    elif method == "zscore_paper":
        mu = float(train.mean())
        rng = float(train.max()) - float(train.min())
        if rng < 1e-12:
            return None
        return (mu, rng)
    raise ValueError(method)


def apply_normalize(v, stats, method="minmax"):
    if method == "minmax":
        mn, mx = stats
        return (v - mn) / (mx - mn)
    else:
        mu, spread = stats
        return (v - mu) / spread


def de_normalize(v, stats, method="minmax"):
    if method == "minmax":
        mn, mx = stats
        return v * (mx - mn) + mn
    else:
        mu, spread = stats
        return v * spread + mu


def build_instances(train_norm, ph):
    """MIMO sliding windows over the normalized train segment (step=1)."""
    total = ph + HORIZON
    n = len(train_norm)
    if n < total:
        return None
    x = []
    y = []
    for i in range(0, n - total + 1):
        x.append(train_norm[i : i + ph])
        y.append(train_norm[i + ph : i + total])
    return np.stack(x).astype(np.float32), np.stack(y).astype(np.float32)


def train_model(model, X, Y, config, device):
    dataset = torch.utils.data.TensorDataset(torch.from_numpy(X), torch.from_numpy(Y))
    loader = torch.utils.data.DataLoader(
        dataset, batch_size=config["batch_size"], shuffle=True, drop_last=False,
        num_workers=0,
    )
    loss_fn = nn.MSELoss()
    opt = torch.optim.Adam(model.parameters(), lr=config["lr"])
    model.to(device)
    model.train()
    for epoch in range(config["epochs"]):
        total_loss = 0.0
        n_batches = 0
        for xb, yb in loader:
            xb, yb = xb.to(device), yb.to(device)
            opt.zero_grad()
            out = model(xb)
            loss = loss_fn(out, yb)
            loss.backward()
            opt.step()
            total_loss += float(loss.item())
            n_batches += 1
        if config.get("verbose"):
            print(f"  epoch {epoch+1}: loss={total_loss/max(n_batches,1):.6f}")
    return total_loss / max(n_batches, 1)


def predict_series(model, normalized_trains, ph, stats_list, device, valid_ids, normalization="minmax"):
    """One-shot MIMO prediction: last ph normalized train values -> 18."""
    model.eval()
    preds = {}
    X = np.stack(
        [normalized_trains[sid][-ph:] for sid in valid_ids]
    ).astype(np.float32)
    with torch.no_grad():
        out = model(torch.from_numpy(X).to(device)).cpu().numpy()
    for i, sid in enumerate(valid_ids):
        preds[sid] = de_normalize(out[i], stats_list[sid], normalization)
    return preds


def wape_per_series(y_true, y_pred):
    denom = y_true.mean()
    if denom <= 1e-12:
        return None
    return float(np.mean(np.abs(y_true - y_pred))) / denom


def run_config(kind, config, base_seed=0):
    ph = config["past_history"]
    norm = config.get("normalization", "minmax")
    series = load_series()
    n_series = len(series)

    normalized_trains = {}
    stats_list = {}
    for sid, s in enumerate(series):
        tr = s[:-HORIZON]
        stats = fit_normalize(tr, norm)
        if stats is None:
            raise RuntimeError(f"constant train segment in series {sid}")
        stats_list[sid] = stats
        normalized_trains[sid] = apply_normalize(tr, stats, norm)

    xs, ys = [], []
    for sid, s in enumerate(series):
        inst = build_instances(normalized_trains[sid], ph)
        if inst is None:
            continue
        xs.append(inst[0])
        ys.append(inst[1])
    X = np.concatenate(xs)
    Y = np.concatenate(ys)
    n_train = len(X)

    seed = (base_seed + int(hashlib.md5(f"{kind}-{json.dumps(config, sort_keys=True)}".encode()).hexdigest()[:8], 16)) % 2**31
    set_seed(seed)

    device = torch.device(config.get("device", "cpu"))
    model = build_model(kind, config)
    n_params = sum(p.numel() for p in model.parameters())

    t0 = time.time()
    train_loss = train_model(model, X, Y, config, device)

    # test predictions: use all series with len_train >= ph
    valid_ids = [sid for sid in range(n_series) if len(normalized_trains[sid]) >= ph]
    preds = predict_series(model, normalized_trains, ph, stats_list, device, valid_ids, norm)

    t_train = time.time() - t0

    wapes = []
    per_series = []
    for sid in valid_ids:
        y_true = series[sid][-HORIZON:]
        y_pred = preds[sid]
        w = wape_per_series(y_true, y_pred)
        if w is None:
            continue
        wapes.append(w)
        per_series.append((sid, w, float(y_true.mean()), float(np.mean(np.abs(y_true - y_pred)))))
    wapes = np.array(wapes)
    ps = pd.DataFrame(per_series, columns=["series_id", "wape", "target_mean", "mae"])

    result = dict(
        model=kind,
        past_history=ph,
        horizon=HORIZON,
        normalization=norm,
        n_series=len(valid_ids),
        n_config=json.dumps(config, sort_keys=True),
        n_train_windows=int(n_train),
        n_params=int(n_params),
        train_loss=float(train_loss),
        wape=float(wapes.mean()) * 100.0,
        wape_std=float(wapes.std(ddof=1)) * 100.0,
        wape_median=float(np.median(wapes)) * 100.0,
        mae_mean=float(ps["mae"].mean()),
        target_mean_mean=float(ps["target_mean"].mean()),
        train_seconds=float(t_train),
        seed=seed,
        device=str(device),
    )
    return result, ps


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--config", required=True, help="json string")
    ap.add_argument("--out-prefix", default=None)
    ap.add_argument("--no-save", action="store_true")
    args = ap.parse_args()

    config = json.loads(args.config)
    result, ps = run_config(args.model, config)

    if not args.no_save:
        prefix = args.out_prefix or f"res_{args.model}"
        os.makedirs(prefix, exist_ok=True)
        pd.DataFrame([result]).to_csv(os.path.join(prefix, "summary.csv"), index=False)
        ps.to_csv(os.path.join(prefix, "per_series.csv"), index=False)
    print(json.dumps(result, indent=1))


if __name__ == "__main__":
    main()