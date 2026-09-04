"""
Attack evaluation pipeline.

Loads trained models, builds the attack set (correctly-classified phishing
test samples), runs CPGD and CAPGD on the frozen test split, and reports
robust accuracy (percentage of attacked samples that remain correctly
classified / valid-but-not-flipped) plus the constraint satisfaction rate.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time

import numpy as np
import torch

sys.path.insert(0, os.path.dirname(__file__))

from constraints import URLConstraintSet
from datautils import Preprocessor, accuracy, load_url, train_validation_test_split
from models import build_model
from attacks import ConstrainedAttack, cpgd_eval, capgd_eval

RESULTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "results")


def predict(model, z, device="cpu"):
    model.eval()
    with torch.no_grad():
        logits = model(torch.tensor(z, dtype=torch.float32, device=device)).cpu().numpy()
    return (logits >= 0).astype(int)


def evaluate_model(name, seed=0, n_iter=10, normalize_grad=True, device="cpu",
                   out_dir=RESULTS_DIR):
    prep = Preprocessor()  # frozen-bound range scaling (data-independent)

    model = build_model(name, device=device)
    model.load_state_dict(torch.load(f"{out_dir}/models_{seed}/{name}.pt",
                                     map_location=device, weights_only=True))
    model.eval()

    df = load_url()
    (_, _), (_, _), (x_te, y_te) = train_validation_test_split(df, seed=seed)
    X_te_raw = x_te.to_numpy()
    y_te = np.asarray(y_te)
    Z_te = prep.transform(X_te_raw)

    preds = predict(model, Z_te, device).reshape(-1)
    acc_all = accuracy(y_te, preds)
    crit = y_te == 1
    acc_crit = accuracy(y_te[crit], preds[crit])

    attack_mask = crit & (preds == y_te)  # critical + correctly classified
    attack_idx = np.where(attack_mask)[0]
    Z0 = torch.tensor(Z_te[attack_idx], dtype=torch.float64, device=device)
    Y = torch.tensor(y_te[attack_idx], dtype=torch.float64, device=device)
    y_attack = y_te[attack_idx]

    fmin, fmax, frange = prep.to_torch()
    cset = URLConstraintSet()
    ctx = ConstrainedAttack(model, fmin, frange, cset, eps=0.5, device=device,
                            normalize_grad=normalize_grad)

    results = {"n_attacked": int(len(attack_idx))}
    for attack_name, fn in [("cpgd", cpgd_eval), ("capgd", capgd_eval)]:
        t0 = time.time()
        Zadv = fn(ctx, Z0, Y, n_iter=n_iter, seed=seed)
        dur = time.time() - t0

        model.eval()
        with torch.no_grad():
            logits_adv = model(Zadv.float())
        pred_adv = (logits_adv.detach().cpu().numpy() >= 0).astype(int).reshape(-1)

        raw_adv_np = prep.inverse(Zadv.cpu().numpy())
        feasible = cset.is_feasible(torch.tensor(raw_adv_np)).float().mean().item()
        pert_std = (Zadv - Z0).norm(dim=-1).cpu().numpy()
        within_eps_arr = pert_std <= ctx.eps + 1e-9

        # validity semantics: a successful adversarial example must be
        # feasible AND within the L2 budget AND misclassified
        n_adv = 0
        for i in range(len(attack_idx)):
            x = torch.tensor(raw_adv_np[i][None])
            if cset.is_feasible(x)[0] and within_eps_arr[i] and pred_adv[i] != y_attack[i]:
                n_adv += 1
        n_flipped = int((pred_adv != y_attack).sum())
        robust_acc = 100.0 * (1 - n_adv / len(attack_idx))
        results[attack_name] = {
            "robust_acc": float(robust_acc),
            "constraint_satisfaction_rate": float(feasible),
            "within_eps_rate": float(within_eps_arr.mean()),
            "n_flipped": int(n_flipped),
            "n_successful_adv": int(n_adv),
            "mean_L2": float(pert_std.mean()),
            "duration_s": float(dur),
        }

    return {
        "model": name,
        "clean_acc_all": float(100.0 * acc_all),
        "clean_acc_critical": float(100.0 * acc_crit),
        "n_attacked": int(len(attack_idx)),
        **results["cpgd"], **{f"capgd_{k}": v for k, v in results["capgd"].items()},
    }


def run_all(seed=0, n_iter=10, normalize_grad=True, device="cpu",
            models=("mlp", "resmlp", "fttransformer")):
    out = []
    for name in models:
        r = evaluate_model(name, seed=seed, n_iter=n_iter,
                           normalize_grad=normalize_grad, device=device)
        print(json.dumps(r, indent=1))
        out.append(r)
    return out


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--n_iter", type=int, default=10)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--no_normalize", action="store_true")
    p.add_argument("--device", default="cpu")
    p.add_argument("--models", nargs="+", default=["mlp", "resmlp", "fttransformer"])
    a = p.parse_args()
    run_all(seed=a.seed, n_iter=a.n_iter,
            normalize_grad=not a.no_normalize, device=a.device,
            models=tuple(a.models))
    p_ = p.add_argument("--models", nargs="+", default=["mlp", "resmlp", "fttransformer"])