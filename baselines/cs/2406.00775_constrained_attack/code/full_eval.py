"""
Full evaluation: for every combination of (seed, model), train the model on
the frozen training split and evaluate CPGD / CAPGD on the frozen test split
(attack set = correctly-classified phishing test samples; L2, eps=0.5).

Produces:
  results/evidence_table.csv
  results/metrics.json
with the columns required by the task/rubric.
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

sys.path.insert(0, os.path.dirname(__file__))

from datautils import load_url, Preprocessor, accuracy, train_validation_test_split
from evaluate import evaluate_model
from train import train_model
from constraints import URLConstraintSet
from attacks import ConstrainedAttack


def _train_and_save(name, out_dir, seed):
    torch.manual_seed(seed)
    np.random.seed(seed)
    df = load_url()
    (x_tr, y_tr), (x_va, y_va), (_, _) = train_validation_test_split(df, seed=seed)
    prep = Preprocessor()
    Z_tr = prep.transform(x_tr.to_numpy())
    Z_va = prep.transform(x_va.to_numpy())
    model, best_ep = train_model(name, Z_tr, y_tr, Z_va, y_va, seed=seed,
                                 epochs=250, patience=40)
    os.makedirs(f"{out_dir}/models_{seed}", exist_ok=True)
    torch.save(model.state_dict(), f"{out_dir}/models_{seed}/{name}.pt")
    np.savez(f"{out_dir}/models_{seed}/prep.npz", fmin=prep.fmin, frange=prep.range)
    return best_ep


def run(seeds=(0,), n_iter=10, models=("mlp", "resmlp"), out_dir="agent_solution/results",
        device="cpu", retrain=True):
    rows = []
    for seed in seeds:
        for name in models:
            if retrain:
                _train_and_save(name, out_dir, seed)
            r = evaluate_model(name, seed=seed, n_iter=n_iter, normalize_grad=True,
                               device=device, out_dir=out_dir)
            rows.append({"seed": seed, **r})
            print("done", seed, name, r["capgd_robust_acc"], flush=True)
    df = pd.DataFrame(rows)
    # rubric-compatible column names
    df["clean_acc"] = df["clean_acc_critical"]
    df["robust_acc_cpgd"] = df["robust_acc"]
    df["robust_acc_capgd"] = df["capgd_robust_acc"]
    df["constraint_satisfaction_rate"] = df["capgd_constraint_satisfaction_rate"]
    df.to_csv(f"{out_dir}/evidence_table.csv", index=False)
    # also expose the aliases in per-row metrics
    for r, (_i, row) in zip(rows, df.iterrows()):
        for k in ("clean_acc", "robust_acc_cpgd", "robust_acc_capgd",
                  "constraint_satisfaction_rate"):
            r[k] = float(row[k])
    metrics = {
        "task": "2406.00775_constrained_attack",
        "attack": {"norm": "L2", "eps": 0.5, "n_iter": int(n_iter),
                   "space": "per-feature [min,max] range scaling",
                   "critical_class": 1, "only_correctly_classified": True,
                   "robust_acc_definition": "share of attacked clean critical "
                                            "samples that remain correctly "
                                            "classified or whose generated "
                                            "example is invalid"},
        "results": rows,
    }
    with open(f"{out_dir}/metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)
    print(df.to_string())


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--seeds", type=int, nargs="+", default=[0])
    p.add_argument("--n_iter", type=int, default=10)
    p.add_argument("--models", nargs="+", default=["mlp", "resmlp"])
    p.add_argument("--out", default="agent_solution/results")
    p.add_argument("--no_retrain", action="store_true")
    p.add_argument("--device", default="cpu")
    a = p.parse_args()
    run(seeds=a.seeds, n_iter=a.n_iter, models=tuple(a.models), out_dir=a.out,
        device=a.device, retrain=not a.no_retrain)