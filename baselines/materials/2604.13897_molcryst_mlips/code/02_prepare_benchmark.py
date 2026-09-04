#!/usr/bin/env python3
"""
02_prepare_benchmark.py — Convert frozen h5 configs into ASE Atoms / extxyz
for lightweight MLIP training (proxy benchmark).

Chosen systems: resora (Resorcinol) and durene (Durene) — the endpoints of the
paper-reported polymorph energy-difference range (Resorcinol 4.64 kJ/mol,
Durene 0.09 kJ/mol).

Subsampling (seeded, deterministic):
  - train: deterministic stride sampling to cap at N_train_max per system
  - valid: all configs

Outputs (under results/benchmark/):
  {system}_train.xyz, {system}_valid.xyz
  {system}_metadata.json

Run: python 02_prepare_benchmark.py
"""
import os
import json
import h5py
import numpy as np
from ase import Atoms
from ase.io import write

DATA_DIR = r"F:\dataset\materials\2604.13897_molcryst_mlips"
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results", "benchmark")
os.makedirs(OUT_DIR, exist_ok=True)

SYSTEMS = ["resora", "durene"]
N_TRAIN_MAX = 2500  # cap training configs per system for CPU feasibility
SEED = 42


def load_configs(h5_path):
    atoms_list = []
    metas = []
    with h5py.File(h5_path, "r") as f:
        keys = sorted(f.keys(), key=lambda k: int(k.split("_")[-1]))
        for bk in keys:
            bg = f[bk]
            for ck in bg:
                c = bg[ck]
                pos = c["positions"][:]
                z = c["atomic_numbers"][:]
                cell = c["cell"][:]
                pbc = c["pbc"][:]
                E = float(c["properties/energy"][()])
                F = c["properties/forces"][:]
                a = Atoms(numbers=z, positions=pos, cell=cell, pbc=pbc)
                # Use MACE's default keys so the extxyz round-trip keeps the
                # values in Atoms.info / Atoms.arrays (ASE otherwise moves
                # 'energy'/'forces' into a SinglePointCalculator).
                a.info["REF_energy"] = E
                a.arrays["REF_forces"] = F
                atoms_list.append(a)
                metas.append({"batch": bk, "config": ck, "natoms": int(len(z))})
    return atoms_list, metas


def write_xyz(path, atoms_list):
    write(path, atoms_list, format="extxyz")


def main():
    rng = np.random.default_rng(SEED)
    summary = {}
    for sys_name in SYSTEMS:
        train_h5 = os.path.join(DATA_DIR, f"{sys_name}_train.h5")
        valid_h5 = os.path.join(DATA_DIR, f"{sys_name}_valid.h5")
        train_atoms, train_meta = load_configs(train_h5)
        valid_atoms, valid_meta = load_configs(valid_h5)
        n_train = len(train_atoms)
        n_valid = len(valid_atoms)

        # deterministic subsample (fixed seed, shuffled index list)
        idx = rng.permutation(n_train)
        if n_train > N_TRAIN_MAX:
            sel = idx[:N_TRAIN_MAX]
            train_atoms = [train_atoms[i] for i in sorted(sel)]
            train_meta = [train_meta[i] for i in sorted(sel)]

        train_xyz = os.path.join(OUT_DIR, f"{sys_name}_train.xyz")
        valid_xyz = os.path.join(OUT_DIR, f"{sys_name}_valid.xyz")
        write_xyz(train_xyz, train_atoms)
        write_xyz(valid_xyz, valid_atoms)

        summary[sys_name] = {
            "n_train_total": n_train,
            "n_train_used": len(train_atoms),
            "n_valid": n_valid,
            "natoms_train": sorted(set(m["natoms"] for m in train_meta)),
            "natoms_valid": sorted(set(m["natoms"] for m in valid_meta)),
            "train_xyz": train_xyz,
            "valid_xyz": valid_xyz,
        }
        print(f"{sys_name}: train total={n_train}, used={len(train_atoms)}, valid={n_valid}")

    with open(os.path.join(OUT_DIR, "metadata.json"), "w") as fh:
        json.dump(summary, fh, indent=2)
    print("Wrote benchmark xyz files to", OUT_DIR)


if __name__ == "__main__":
    main()
