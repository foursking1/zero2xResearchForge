"""
Training pipeline for the three deep classifiers.

Fixed random seed; stratified 75/25 split; z-score scaling from the
training split only; early stopping on the validation split. The test split
is used ONLY for final evaluation / attacks (fully frozen).
"""

from __future__ import annotations

import json
import os
import sys

import numpy as np
import torch

sys.path.insert(0, os.path.dirname(__file__))

from datautils import Preprocessor, accuracy, load_url, train_validation_test_split
from models import build_model


def train_model(name, X_tr, y_tr, X_va, y_va, epochs=300, lr=1e-3, seed=0,
                device="cpu", patience=40, verbose=False):
    torch.manual_seed(seed)
    np.random.seed(seed)
    model = build_model(name)
    model.to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    sch = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=epochs)
    X_tr_t = torch.tensor(X_tr, dtype=torch.float32, device=device)
    y_tr_t = torch.tensor(y_tr, dtype=torch.float32, device=device)
    X_va_t = torch.tensor(X_va, dtype=torch.float32, device=device)
    y_va_t = torch.tensor(y_va, dtype=torch.float32, device=device)

    best_loss = float("inf")
    best_state = None
    best_epoch = 0

    for ep in range(1, epochs + 1):
        model.train()
        opt.zero_grad()
        logits = model(X_tr_t)
        loss = torch.nn.functional.binary_cross_entropy_with_logits(logits, y_tr_t)
        loss.backward()
        opt.step()
        sch.step()

        if ep % 2 == 0 or ep == epochs:
            model.eval()
            with torch.no_grad():
                val_loss = torch.nn.functional.binary_cross_entropy_with_logits(
                    model(X_va_t), y_va_t).item()
            if val_loss < best_loss:
                best_loss = val_loss
                best_state = {k: v.detach().clone() for k, v in model.state_dict().items()}
                best_epoch = ep
            elif ep - best_epoch > patience:
                break
            if verbose and ep % 20 == 0:
                print(f"  [{name}] ep {ep}: train CE {loss.item():.4f} val CE {val_loss:.4f}")

    if best_state is not None:
        model.load_state_dict(best_state)
    return model, best_epoch


def main(out_dir="agent_solution/results", seed=0, device="cpu"):
    torch.manual_seed(seed)
    np.random.seed(seed)
    df = load_url()
    (x_tr, y_tr), (x_va, y_va), (x_te, y_te) = train_validation_test_split(df, seed=seed)

    prep = Preprocessor()  # frozen-bound range scaling
    Z_tr = prep.transform(x_tr.to_numpy())
    Z_va = prep.transform(x_va.to_numpy())
    Z_te = prep.transform(x_te.to_numpy())

    os.makedirs(out_dir, exist_ok=True)
    stats = {"split": {"train": len(y_tr), "val": len(y_va), "test": len(y_te)},
             "phishing_frac": {"train": float(y_tr.mean()), "test": float(y_te.mean())}}

    for name in ["mlp", "resmlp", "fttransformer"]:
        model, best_ep = train_model(name, Z_tr, y_tr, Z_va, y_va, seed=seed, device=device)
        os.makedirs(f"{out_dir}/models_{seed}", exist_ok=True)
        torch.save(model.state_dict(), f"{out_dir}/models_{seed}/{name}.pt")
        np.savez(f"{out_dir}/models_{seed}/prep.npz", fmin=prep.fmin, frange=prep.range)
        stats[name] = {"best_epoch": best_ep}
        print(f"{name}: saved (best epoch {best_ep})")

    with open(f"{out_dir}/split_stats.json", "w") as f:
        json.dump(stats, f, indent=2)
    print("done.")


if __name__ == "__main__":
    main(device="cpu")