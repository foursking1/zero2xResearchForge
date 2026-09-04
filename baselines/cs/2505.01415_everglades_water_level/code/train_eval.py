"""Main pipeline: train DLinear / NLinear / NBEATS and evaluate them with the
official Everglades protocol (paper arXiv:2505.01415 Sec. 3.1).

  python train_eval.py [--model MODEL] [--seed SEED] [--cpu/--gpu] [--epochs E] [--quick]

Outputs (relative to agent_solution/results/):
  metrics_{model}.csv         per (station x lead) MAE/RMSE
  evidence_table.csv          aggregated Overall MAE/RMSE by (model, lead)
  predictions_{model}.npz     raw forecasts on the test segment + metadata
  model_states/{model}.pt     best trained weights (seeded, reproducible)
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

import numpy as np
import pandas as pd
import torch
import torch.nn as nn

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common  # noqa: E402
from common import (CONTEXT_LEN, HORIZON, LEADS, N_DAYS, TARGETS, TEST_LO,
                    TEST_HI, TRAIN, VAL)
from models import DLinear, NBEATS, ModelPredictor, NLinear, init_target_idx  # noqa: E402

DEVICE = torch.device("cpu")
RESULTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")


def make_model(name: str, mc_dropout: float = 0.0) -> nn.Module:
    """Instantiate a model by name. Hyper-parameters are the ones reported in
    the paper's frame (neuralforecast-style; defaults unless noted)."""
    if name == "DLinear":
        return DLinear(kernel=25)
    if name == "NLinear":
        return NLinear()
    if name == "NBEATS":
        return NBEATS(n_blocks=(2, 2), mlp_units=([512, 512], [512, 512]), activ="gelu")
    if name == "MLPResidual":
        from models_extra import MLPResidual
        return MLPResidual(hidden=1536, depth=5, dropout=mc_dropout)
    if name == "TSMixer":
        from models_extra import TSMixer
        return TSMixer(d_model=128, n_layers=2, mlp_time=256, mlp_feat=256)
    if name == "PatchTST":
        from models_extra import PatchTST
        return PatchTST(patch_len=20, stride=20, d_model=128, n_heads=4, n_layers=2, d_ff=256)
    raise ValueError(name)


# extra CLI args per model family (lr/patience differing between linear/MLP)
MODEL_HP = {
    "DLinear":      dict(lr=1e-3, batch_size=64, patience=12),
    "NLinear":      dict(lr=1e-3, batch_size=64, patience=12),
    "NBEATS":       dict(lr=3e-4, batch_size=64, patience=12),
    "MLPResidual":  dict(lr=3e-4, batch_size=64, patience=25),
    "TSMixer":      dict(lr=5e-4, batch_size=64, patience=15),
    "PatchTST":     dict(lr=5e-4, batch_size=64, patience=15),
}


def train_model(model: nn.Module, x_tr, y_tr, x_val, y_val, seed: int,
                epochs: int, batch_size: int = 64, lr: float = 1e-3,
                patience: int = 10, wd: float = 0.0, verbose: bool = False) -> dict:
    torch.manual_seed(seed)
    np.random.seed(seed)
    device = next(model.parameters()).device
    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=wd)
    loss_fn = nn.MSELoss()

    xt = torch.from_numpy(x_tr).to(device)
    yt = torch.from_numpy(y_tr).to(device)
    xv = torch.from_numpy(x_val).to(device)
    yv = torch.from_numpy(y_val).to(device)
    n = xt.size(0)
    best_val = float("inf")
    best_state = None
    bad = 0
    hist = []
    t0 = time.time()
    for ep in range(epochs):
        model.train()
        perm = torch.randperm(n)
        tot = 0.0
        nb = 0
        for i in range(0, n, batch_size):
            idx = perm[i:i + batch_size]
            opt.zero_grad()
            pred = model(xt[idx])
            loss = loss_fn(pred, yt[idx])
            loss.backward()
            opt.step()
            tot += loss.item() * idx.size(0)
            nb += idx.size(0)
        tr_loss = tot / max(nb, 1)
        model.eval()
        with torch.no_grad():
            vloss = loss_fn(model(xv), yv).item()
        hist.append((ep + 1, tr_loss, vloss))
        if vloss < best_val:
            best_val = vloss
            best_state = {k: v.detach().clone() for k, v in model.state_dict().items()}
            bad = 0
        else:
            bad += 1
        if bad >= patience:
            if verbose:
                print(f"  early stop at epoch {ep+1} (best val {best_val:.5f})")
            break
    model.load_state_dict(best_state)
    return {"best_val_loss": best_val, "epochs_run": len(hist),
            "epochs_trained": ep + 1, "history": hist,
            "time_s": time.time() - t0}


def eval_roll(model: nn.Module, Xs: np.ndarray, Ys: np.ndarray, scaler_x, scaler_y,
              t_start: int = TEST_LO, t_stop: int = TEST_HI - 1,
              mc_passes: int = 0) -> pd.DataFrame:
    """Daily-rolling evaluation over test days.

    For each origin t (context = X[t-100 : t], past only), one 28-step forecast.
    If mc_passes > 1 the model is run in train mode `mc_passes` times and the
    average is taken (Monte-Carlo dropout inference).
    """
    device = next(model.parameters()).device
    predictor = ModelPredictor(model, scaler_x, device)
    rows = []
    preds_all = np.zeros((t_stop - t_start + 1, HORIZON, len(TARGETS)), dtype=np.float32)
    for i, t in enumerate(range(t_start, t_stop + 1)):
        ctx = Xs[t - CONTEXT_LEN: t]  # scaled, past only
        if mc_passes > 1 and any(d.p > 0 for d in model.modules()
                                 if isinstance(d, torch.nn.Dropout)):
            model.train()
            acc = None
            with torch.no_grad():
                for _ in range(mc_passes):
                    y = model(torch.from_numpy(ctx.astype(np.float32)).unsqueeze(0).to(device))
                    acc = y if acc is None else acc + y
            pred = (acc / mc_passes)[0].cpu().numpy()
        else:
            pred = predictor.predict_window(ctx)  # (H, out) scaled
        preds_all[i] = pred
    for step_idx in range(HORIZON):
        lead = step_idx + 1
        if lead not in LEADS:
            continue
        # forecast valid where target day t+step_idx < N_DAYS
        avail = np.where(t_start + np.arange(t_stop - t_start + 1) + step_idx < N_DAYS)[0]
        if avail.size == 0:
            continue
        f = preds_all[avail, step_idx, :]
        target_days = t_start + avail + step_idx
        f_true = scaler_y.inverse_transform(f)
        y = scaler_y.inverse_transform(Ys[target_days])
        err = f_true - y  # (n_dates, 5), raw units
        for j, st in enumerate(TARGETS):
            e = err[:, j]
            rows.append({
                "model": None, "lead": lead, "station": st,
                "mae": float(np.abs(e).mean()), "rmse": float(np.sqrt((e ** 2).mean())),
                "n": int(len(e)),
            })
    return pd.DataFrame(rows), preds_all


def aggregate(frame: pd.DataFrame, model_name: str) -> pd.DataFrame:
    out = []
    for lead in LEADS:
        sub = frame[frame["lead"] == lead]
        out.append({
            "model": model_name, "lead_time": lead,
            "overall_mae": float(sub.groupby("station")["mae"].mean().mean()),
            "overall_rmse": float(sub.groupby("station")["rmse"].mean().mean()),
            "n_dates": int(sub["n"].min()),
        })
    return pd.DataFrame(out)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", choices=list(MODEL_HP), required=True)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--epochs", type=int, default=120)
    ap.add_argument("--patience", type=int, default=None)
    ap.add_argument("--mc", type=float, default=0.0, help="dropout rate for MC-dropout inference (e.g. 0.05)")
    ap.add_argument("--mc-passes", type=int, default=20, help="number of MC samples averaged at eval")
    ap.add_argument("--device", choices=["cpu", "gpu"], default="cpu")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()
    global DEVICE
    DEVICE = torch.device("cuda" if args.device == "gpu" and torch.cuda.is_available() else "cpu")
    torch.set_num_threads(max(1, min(8, os.cpu_count() or 1)))
    print(f"[train_eval] device={DEVICE}", flush=True)

    hp = MODEL_HP[args.model]
    if args.patience is None:
        args.patience = hp["patience"]

    df = common.load_data()
    feat_cols = common.verify_dataframe(df)
    init_target_idx(feat_cols)  # column positions of the 5 target stations in X
    X, Y = common.build_matrix(df)
    Xs = torch.tensor(X).float()
    Ys = torch.tensor(Y).float()

    # --- scalers fitted on TRAIN ONLY ---------------------------------------
    scaler_x = common.StandardScaler().fit(X[:TRAIN])
    scaler_y = common.StandardScaler().fit(Y[:TRAIN])
    Xsc = scaler_x.transform(X)
    Ysc = scaler_y.transform(Y)

    # --- build windows (all within train segment, test never touched) -------
    max_orig = TRAIN - HORIZON  # output must end <= TRAIN-1
    all_orig = np.arange(CONTEXT_LEN, max_orig + 1)
    # validation slice: last fraction of windows (from the intra-train val block)
    n_val_w = max(VAL - HORIZON, 32)     # ~183 windows at the end of train
    val_orig = all_orig[-n_val_w:]
    tr_orig = all_orig[:-n_val_w]
    x_tr, y_tr = common.make_windows(Xsc, Ysc, tr_orig)
    x_val, y_val = common.make_windows(Xsc, Ysc, val_orig)

    torch.manual_seed(args.seed)
    model = make_model(args.model, mc_dropout=args.mc)
    model = model.to(DEVICE)
    torch.manual_seed(args.seed)
    info = train_model(model, x_tr, y_tr, x_val, y_val, seed=args.seed,
                       epochs=args.epochs, patience=args.patience,
                       batch_size=hp["batch_size"], lr=hp["lr"],
                       verbose=args.verbose)
    if args.verbose:
        print(f"[{args.model}] {info['epochs_run']} epochs, best_val_loss={info['best_val_loss']:.6f}, "
              f"{info['time_s']:.1f}s")

    # --- daily-rolling evaluation on test segment ---------------------------
    tag = args.model if args.mc <= 0 else f"{args.model}_mc{args.mc}"
    frame, preds_all = eval_roll(model, Xsc, Ysc, scaler_x, scaler_y,
                                 TEST_LO, TEST_HI - 1,
                                 mc_passes=args.mc_passes if args.mc > 0 else 0)
    frame["model"] = tag

    os.makedirs(RESULTS_DIR, exist_ok=True)
    os.makedirs(os.path.join(RESULTS_DIR, "model_states"), exist_ok=True)
    torch.save({"state_dict": model.state_dict(), "info": info},
               os.path.join(RESULTS_DIR, "model_states", f"{tag}.pt"))
    metric_file = os.path.join(RESULTS_DIR, f"metrics_{tag}.csv")
    frame.to_csv(metric_file, index=False)
    np.savez_compressed(
        os.path.join(RESULTS_DIR, f"predictions_{tag}.npz"),
        preds=preds_all, dates=df["date"].values[TEST_LO:TEST_HI],
        targets=TARGETS, scaler_mean=scaler_y.mean_, scaler_std=scaler_y.std_,
    )
    agg = aggregate(frame, tag)
    agg.to_csv(os.path.join(RESULTS_DIR, f"evidence_{tag}.csv"), index=False)

    if args.verbose:
        print(f"[{tag}]")
        print(agg.to_string(index=False))
        print(frame.pivot_table(index="station", columns="lead", values="mae"))


if __name__ == "__main__":
    main()