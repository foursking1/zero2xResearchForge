#!/usr/bin/env python3
"""
03_train_mace.py — Train a lightweight MACE potential (from scratch) on frozen
MolCryst h5-derived data for the proxy benchmark.

The paper's production models are *fine-tunes of the MACE-MH-1 foundation model*
(omol head).  We cannot reproduce that without the foundation weights (not part
of the frozen data package), so this script trains a *from-scratch, small* MACE
model on the same frozen training data for two systems (resora, durene) as a
lightweight proxy to check whether the reported accuracy magnitude
(energy MAE ~0.141 kJ/mol/atom, force MAE ~0.648 kJ/mol/Å) is plausible and to
quantify how a modest model performs on the same DFT data.

Run (CPU):  python 03_train_mace.py resora   # e.g.
             python 03_train_mace.py durene
"""
import os
import sys
import time
import argparse

import numpy as np

from mace.cli.run_train import main as mace_train_main

BENCH_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results", "benchmark")
SEED = 42


def build_args(system: str, max_epochs: int, hidden_irreps: str,
               max_ell: int, batch_size: int, swa: bool, forces_weight: float):
    work_dir = os.path.join(BENCH_DIR, f"{system}_mace_work")
    os.makedirs(work_dir, exist_ok=True)
    train_file = os.path.join(BENCH_DIR, f"{system}_train.xyz")
    valid_file = os.path.join(BENCH_DIR, f"{system}_valid.xyz")
    return [
        "mace_run_train",
        f"--name={system}_proxy",
        f"--train_file={train_file}",
        f"--valid_file={valid_file}",
        "--energy_key=REF_energy",
        "--forces_key=REF_forces",
        "--E0s=average",
        "--model=MACE",
        "--num_interactions=2",
        f"--hidden_irreps={hidden_irreps}",
        f"--max_ell={max_ell}",
        "--r_max=5.0",
        "--num_radial_basis=8",
        "--num_cutoff_basis=5",
        "--interaction=RealAgnosticResidualInteractionBlock",
        "--interaction_first=RealAgnosticResidualInteractionBlock",
        "--correlation=2",
        "--MLP_irreps=16x0e",
        "--radial_MLP=[64, 64, 64]",
        f"--batch_size={batch_size}",
        "--valid_batch_size=10",
        f"--max_num_epochs={max_epochs}",
        "--patience=1000",
        f"--forces_weight={forces_weight}",
        "--energy_weight=1.0",
        "--lr=0.005",
        "--weight_decay=5e-07",
        "--scheduler=ReduceLROnPlateau",
        "--lr_factor=0.8",
        "--scheduler_patience=20",
        "--default_dtype=float64",
        "--device=cpu",
        f"--seed={SEED}",
        "--error_table=PerAtomRMSE",
        "--eval_interval=1",
        "--plot=False",
        f"--work_dir={work_dir}",
        f"--model_dir={work_dir}",
        f"--log_dir={work_dir}",
        f"--checkpoints_dir={work_dir}",
    ]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("system", choices=["resora", "durene"])
    ap.add_argument("--max_epochs", type=int, default=60)
    ap.add_argument("--hidden_irreps", type=str, default="64x0e+64x1e")
    ap.add_argument("--max_ell", type=int, default=2)
    ap.add_argument("--batch_size", type=int, default=10)
    ap.add_argument("--forces_weight", type=float, default=100.0)
    args = ap.parse_args()

    argv = build_args(args.system, args.max_epochs, args.hidden_irreps,
                      args.max_ell, args.batch_size, False, args.forces_weight)
    sys.argv = argv
    t0 = time.time()
    print(f"[03_train_mace] training {args.system} for up to {args.max_epochs} epochs...")
    mace_train_main()
    print(f"[03_train_mace] done in {time.time() - t0:.1f} s")


if __name__ == "__main__":
    main()
