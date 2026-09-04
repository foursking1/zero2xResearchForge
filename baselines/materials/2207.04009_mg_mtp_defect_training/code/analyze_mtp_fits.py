"""Extract MTP training errors from the frozen pyiron/Mlip h5 archives.

Each fit_packed .h5 stores:
  - input/training_data  : DFT (PBE) reference EFS used for fitting
  - output/training_efs  : MTP-predicted EFS on the same structures
We compute per-atom energy RMSE/MAE and force RMSE, matching the paper's
"training error" protocol (full-data fit, no hold-out).

Also parses the MTP level and cutoff from the job name MTP{level}_1_8_{rc}.
"""
import os
import re
import glob
import numpy as np
import pandas as pd
import h5py

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.join(BASE, "work")
OUT = os.path.join(BASE, "results")
os.makedirs(OUT, exist_ok=True)

FIT_DIRS = {
    "Everything": os.path.join(WORK, "fit_packed", "fit", "Everything"),
    "EverythingNoShear": os.path.join(WORK, "fit_packed", "fit", "EverythingNoShear"),
}


def parse_name(name):
    m = re.match(r"MTP(\d+)_\d+_\d+_(\d+)_(\d+)", name)
    level = int(m.group(1)) if m else None
    rc = float(m.group(2) + "." + m.group(3)) if m else None
    return level, rc


def analyze_one(path):
    rows = []
    with h5py.File(path, "r") as h:
        # single group named after the job
        group_name = list(h.keys())[0]
        g = h[group_name]
        td = g["input/training_data"]
        te = g["output/training_efs"]
        E_dft = td["chunk_arrays/energy"][:]
        n_atoms = td["chunk_arrays/length"][:]
        F_dft = td["element_arrays/forces"][:]
        E_pred = te["chunk_arrays/energy"][:]
        F_pred = te["element_arrays/forces"][:]
        ids = [b.decode() for b in td["chunk_arrays/identifier"][:]]
        # per-atom values
        dE = (E_pred - E_dft) / n_atoms  # eV/atom
        rmse_e = float(np.sqrt(np.mean(dE ** 2))) * 1000.0  # meV/atom
        mae_e = float(np.mean(np.abs(dE))) * 1000.0
        max_e = float(np.max(np.abs(dE))) * 1000.0
        rmse_f = float(np.sqrt(np.mean((F_pred - F_dft) ** 2)))  # eV/A
        mae_f = float(np.mean(np.linalg.norm(F_pred - F_dft, axis=1)))
        n_struct = int(len(E_dft))
        n_atom_total = int(n_atoms.sum())
        level, rc = parse_name(group_name)
        rows.append(
            {
                "job": group_name,
                "train_set": os.path.basename(os.path.dirname(path)),
                "level": level,
                "cutoff": rc,
                "n_structures": n_struct,
                "n_atoms_total": n_atom_total,
                "energy_rmse_meV_atom": rmse_e,
                "energy_mae_meV_atom": mae_e,
                "energy_max_meV_atom": max_e,
                "force_rmse_eV_A": rmse_f,
                "force_mae_eV_A": mae_f,
            }
        )
    return rows


def main():
    all_rows = []
    for train_set, d in FIT_DIRS.items():
        for path in sorted(glob.glob(os.path.join(d, "*.h5"))):
            all_rows.extend(analyze_one(path))
    df = pd.DataFrame(all_rows)
    df = df.sort_values(["train_set", "cutoff", "level"]).reset_index(drop=True)
    df.to_csv(os.path.join(OUT, "mtp_fit_results.csv"), index=False)
    print(df.to_string(index=False))
    # pivot best per (train_set, cutoff): lowest RMSE
    best = (
        df.loc[df.groupby(["train_set", "cutoff"])["energy_rmse_meV_atom"].idxmin()]
        .sort_values(["train_set", "cutoff"])
    )
    print("\n== best per train_set/cutoff ==")
    print(best[["train_set", "cutoff", "level", "n_structures",
                "energy_rmse_meV_atom", "force_rmse_eV_A"]].to_string(index=False))
    print("\nSaved:", os.path.join(OUT, "mtp_fit_results.csv"))


if __name__ == "__main__":
    main()
