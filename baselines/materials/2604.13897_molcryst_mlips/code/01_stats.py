#!/usr/bin/env python3
"""
01_stats.py — Parse all 20 frozen MolCryst-MLIPs h5 files and compute dataset statistics.

Task: 2604.13897_molcryst_mlips (L1 critical claim)
Data: F:\\dataset\\materials\\2604.13897_molcryst_mlips\\  (frozen, 20 h5 files)
Units:  energy = eV, forces = eV/Angstrom, positions = Angstrom
        conversion: 1 eV = 96.485 kJ/mol

Outputs:
  results/stats_per_system.csv   — per (system, split) summary table
  results/h5_structure_report.json — batch/config structure details
  results/evidence_table.csv     — long-form evidence table (system,split,metric,value)

Run: python 01_stats.py
"""
import os
import json
import glob
import h5py
import numpy as np
import pandas as pd

EV_PER_KJMOL = 96.485  # 1 eV = 96.485 kJ/mol

DATA_DIR = r"F:\dataset\materials\2604.13897_molcryst_mlips"
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results")
os.makedirs(OUT_DIR, exist_ok=True)

# system short-code -> full name used in the paper
SYSTEM_NAMES = {
    "acridine": "Acridine (extension, discussed in paper text)",
    "benzac": "Benzoic acid",
    "bzamid": "Benzamide",
    "coumar": "Coumarin",
    "durene": "Durene",
    "ehowih": "Ehowih-related extension (not in abstract list of 9)",
    "nicoac": "Nicotinic acid",
    "nicoam": "Niacinamide",
    "pyrizin": "Pyrazinamide",
    "resora": "Resorcinol",
}
PAPER_9 = {"benzac", "bzamid", "coumar", "durene", "nicoac", "nicoam", "pyrizin", "resora"}
# NOTE: the abstract lists 9 systems; the frozen filenames contain 10 short codes.
# 'ehowih' is not in the abstract's 9-system list; 'acridine' is described in the
# paper text as an extension system (HF repo claims 10 systems incl. acridine).


def list_h5(data_dir):
    files = sorted(glob.glob(os.path.join(data_dir, "*.h5")))
    assert len(files) == 20, f"expected 20 h5 files, found {len(files)}"
    return files


def scan_file(path):
    """Return per-config records for one h5 file."""
    rows = []
    structure = {"top_keys": [], "batch_sizes": {}, "n_batches": 0, "n_configs": 0}
    with h5py.File(path, "r") as f:
        keys = [k for k in f.keys()]
        structure["top_keys"] = keys
        structure["n_batches"] = len(keys)
        for bk in keys:
            bg = f[bk]
            cfg_keys = [k for k in bg.keys()]
            structure["batch_sizes"][len(cfg_keys)] = structure["batch_sizes"].get(len(cfg_keys), 0) + 1
            for ck in cfg_keys:
                c = bg[ck]
                pos = c["positions"][:]
                z = c["atomic_numbers"][:]
                cell = c["cell"][:]
                pbc = c["pbc"][:]
                E = float(c["properties/energy"][()])
                F = c["properties/forces"][:]
                ct = c["config_type"][()]
                if isinstance(ct, bytes):
                    ct = ct.decode()
                w = float(c["weight"][()])
                ew = float(c["property_weights/energy_weight"][()])
                fw = float(c["property_weights/forces_weight"][()])
                rows.append({
                    "batch": bk, "config": ck,
                    "natoms": int(pos.shape[0]),
                    "E": E, "E_per_atom": E / pos.shape[0],
                    "F": F, "F_norm": np.linalg.norm(F, axis=1),
                    "config_type": str(ct),
                    "weight": w, "energy_weight": ew, "forces_weight": fw,
                    "cell": cell, "pbc": pbc,
                    "species": sorted(set(int(x) for x in z)),
                })
                structure["n_configs"] += 1
    return rows, structure


def summarize(system, split, rows):
    n = len(rows)
    natoms = np.array([r["natoms"] for r in rows])
    E = np.array([r["E"] for r in rows])
    EpA = np.array([r["E_per_atom"] for r in rows])
    F = np.concatenate([r["F"].ravel() for r in rows]) if n else np.array([])
    Fn = np.concatenate([r["F_norm"] for r in rows]) if n else np.array([])
    cts = pd.Series([r["config_type"] for r in rows]).value_counts().to_dict()
    species = sorted(set().union(*[set(r["species"]) for r in rows])) if n else []
    return {
        "system": system, "split": split,
        "n_configs": n,
        "natoms_min": int(natoms.min()) if n else None,
        "natoms_max": int(natoms.max()) if n else None,
        "natoms_mean": float(natoms.mean()) if n else None,
        "natoms_median": float(np.median(natoms)) if n else None,
        "E_min_eV": float(E.min()) if n else None,
        "E_max_eV": float(E.max()) if n else None,
        "E_mean_eV": float(E.mean()) if n else None,
        "E_per_atom_min_eV": float(EpA.min()) if n else None,
        "E_per_atom_max_eV": float(EpA.max()) if n else None,
        "E_per_atom_mean_eV": float(EpA.mean()) if n else None,
        "F_component_absmin": float(np.abs(F).min()) if n else None,
        "F_component_absmax": float(np.abs(F).max()) if n else None,
        "F_norm_mean_eV_per_A": float(Fn.mean()) if n else None,
        "F_norm_max_eV_per_A": float(Fn.max()) if n else None,
        "total_force_components": int(F.size) if n else 0,
        "config_types": cts,
        "species_z": species,
        "weights": {"weight": sorted(set(round(r["weight"], 6) for r in rows)),
                     "energy_weight": sorted(set(round(r["energy_weight"], 6) for r in rows)),
                     "forces_weight": sorted(set(round(r["forces_weight"], 6) for r in rows))},
        "pbc": rows[0]["pbc"].tolist() if rows else None,
        "cell": rows[0]["cell"].tolist() if rows else None,
    }


def main():
    files = list_h5(DATA_DIR)
    all_stats = []
    structure_report = {}
    for fp in files:
        fname = os.path.basename(fp)
        system, split = fname.replace(".h5", "").rsplit("_", 1)
        rows, structure = scan_file(fp)
        stats = summarize(system, split, rows)
        all_stats.append(stats)
        structure_report[fname] = {
            "n_batches": structure["n_batches"],
            "n_configs": structure["n_configs"],
            "batch_size_distribution": structure["batch_sizes"],
            "top_key_sample_first3": structure["top_keys"][:3],
            "top_key_sample_last3": structure["top_keys"][-3:],
        }
        print(f"{fname}: {structure['n_batches']} batches, {structure['n_configs']} configs")

    df = pd.DataFrame(all_stats)
    df.to_csv(os.path.join(OUT_DIR, "stats_per_system.csv"), index=False, encoding="utf-8-sig")

    with open(os.path.join(OUT_DIR, "h5_structure_report.json"), "w") as fh:
        json.dump(structure_report, fh, indent=2)

    # ---- evidence_table.csv: long format (system, split, metric, value) ----
    rows_ev = []
    for s in all_stats:
        system = s["system"]; split = s["split"]
        ev = [
            ("n_configs", s["n_configs"]),
            ("natoms_min", s["natoms_min"]),
            ("natoms_max", s["natoms_max"]),
            ("natoms_mean", s["natoms_mean"]),
            ("E_min_eV", s["E_min_eV"]),
            ("E_max_eV", s["E_max_eV"]),
            ("E_per_atom_mean_eV", s["E_per_atom_mean_eV"]),
            ("E_per_atom_min_eV", s["E_per_atom_min_eV"]),
            ("E_per_atom_max_eV", s["E_per_atom_max_eV"]),
            ("F_component_absmax_eV_per_A", s["F_component_absmax"]),
            ("F_norm_mean_eV_per_A", s["F_norm_mean_eV_per_A"]),
        ]
        for metric, value in ev:
            rows_ev.append({"system": system, "split": split, "metric": metric, "value": value})
    ev_df = pd.DataFrame(rows_ev)
    ev_df.to_csv(os.path.join(OUT_DIR, "evidence_table.csv"), index=False, encoding="utf-8-sig")
    print("\nWrote results/evidence_table.csv, stats_per_system.csv, h5_structure_report.json")

    # Print a compact overview
    print("\n=== Overview ===")
    for s in all_stats:
        print(f"{s['system']:9s} {s['split']:5s} n={s['n_configs']:6d} "
              f"natoms {s['natoms_min']}-{s['natoms_max']} "
              f"EpA[{s['E_per_atom_min_eV']:.4f},{s['E_per_atom_max_eV']:.4f}] eV "
              f"config_type={s['config_types']}")


if __name__ == "__main__":
    main()
