"""Parse MTP/ATOMSK extended-xyz .cfg files from the frozen Edmond dataset.

The .cfg files (structure_files.tar.gz) contain the DFT reference data used for
MTP fitting: one block per structure with lattice vectors, atom positions,
forces, total energy and stress tensor (VASP/PBE via pyiron).

Outputs a tidy CSV `structures_all.csv` (one row per structure) plus a per-file
summary used for statistics.
"""
import os
import re
import sys
import glob
import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.join(BASE, "work")
OUT = os.path.join(BASE, "results")
os.makedirs(OUT, exist_ok=True)

CFG_DIR = os.path.join(WORK, "structure_files")


def parse_cfg(path):
    """Parse a .cfg file; return list of dicts (one per structure)."""
    recs = []
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        lines = f.read().splitlines()
    i = 0
    n = len(lines)
    while i < n:
        if lines[i].strip() != "BEGIN_CFG":
            i += 1
            continue
        j = i + 1
        # Size
        size = None
        while j < n and "Size" not in lines[j]:
            j += 1
        j += 1  # skip 'Size'
        if j < n:
            size = int(lines[j].strip())
        # SuperCell (3 lines)
        cell = None
        while j < n and "SuperCell" not in lines[j]:
            j += 1
        if j + 3 < n:
            cell = np.array(
                [list(map(float, lines[k].split())) for k in range(j + 1, j + 4)]
            )
        j += 4
        # AtomData header
        while j < n and "AtomData:" not in lines[j]:
            j += 1
        j += 1  # skip header line
        pos = np.zeros((size, 3))
        forces = np.zeros((size, 3))
        types = np.zeros(size, dtype=int)
        ids = np.zeros(size, dtype=int)
        for a in range(size):
            toks = lines[j].split()
            ids[a] = int(toks[0])
            types[a] = int(toks[1])
            pos[a] = [float(toks[2]), float(toks[3]), float(toks[4])]
            forces[a] = [float(toks[5]), float(toks[6]), float(toks[7])]
            j += 1
        # Energy
        energy = None
        while j < n and "Energy" not in lines[j]:
            j += 1
        if j < n:
            energy = float(lines[j].split("\t")[-1].split()[-1])
            j += 1
        # PlusStress (6 components, kBar in VASP convention -> keep as stored)
        stress = np.full(6, np.nan)
        has_stress = False
        while j < n and "PlusStress" not in lines[j]:
            j += 1
        if j < n and j + 1 < n:
            toks = lines[j + 1].split()
            if len(toks) >= 6:
                stress = np.array(list(map(float, toks[:6])))
                has_stress = True
            j += 2
        # Feature
        feature = None
        while j < n and "Feature" not in lines[j]:
            j += 1
        if j < n:
            feature = lines[j].split()[-1].strip()
            j += 1
        recs.append(
            {
                "n_atoms": size,
                "cell": cell,
                "positions": pos,
                "forces": forces,
                "types": types,
                "energy": energy,
                "stress": stress,
                "has_stress": has_stress,
                "feature": feature,
            }
        )
        # advance to END_CFG
        while i < n and lines[i].strip() != "END_CFG":
            i += 1
        i += 1
    return recs


def main():
    categories = sorted(
        os.path.basename(p)[:-4]
        for p in glob.glob(os.path.join(CFG_DIR, "*.cfg"))
    )
    all_rows = []
    per_file = []
    for cat in categories:
        path = os.path.join(CFG_DIR, cat + ".cfg")
        recs = parse_cfg(path)
        natoms = np.array([r["n_atoms"] for r in recs])
        energies = np.array([r["energy"] for r in recs])
        # per-atom energies
        epa = energies / natoms
        per_file.append(
            {
                "dataset": "structures",
                "subset": cat,
                "n_structures": len(recs),
                "n_atoms_total": int(natoms.sum()),
                "n_atoms_min": int(natoms.min()),
                "n_atoms_max": int(natoms.max()),
                "n_atoms_mean": float(natoms.mean()),
                "energy_min": float(energies.min()),
                "energy_max": float(energies.max()),
                "epa_mean": float(epa.mean()),
                "epa_min": float(epa.min()),
                "epa_max": float(epa.max()),
                "n_with_stress": int(sum(r["has_stress"] for r in recs)),
            }
        )
        for k, r in enumerate(recs):
            all_rows.append(
                {
                    "subset": cat,
                    "index_in_subset": k,
                    "feature": r["feature"],
                    "n_atoms": r["n_atoms"],
                    "energy_eV": r["energy"],
                    "energy_per_atom_eV": r["energy"] / r["n_atoms"],
                    "stress_xx": r["stress"][0],
                    "stress_yy": r["stress"][1],
                    "stress_zz": r["stress"][2],
                    "stress_yz": r["stress"][3],
                    "stress_xz": r["stress"][4],
                    "stress_xy": r["stress"][5],
                    "cell_flat": r["cell"].ravel().tolist(),
                    "positions_flat": r["positions"].ravel().tolist(),
                    "forces_flat": r["forces"].ravel().tolist(),
                    "types_flat": r["types"].ravel().tolist(),
                }
            )
    df = pd.DataFrame(all_rows)
    df.to_csv(os.path.join(OUT, "structures_all.csv"), index=False)
    psum = pd.DataFrame(per_file)
    psum.to_csv(os.path.join(OUT, "structures_summary.csv"), index=False)
    print("== per-category summary ==")
    print(psum.to_string(index=False))
    print("\nTOTAL structures:", len(df))
    print("Saved:", os.path.join(OUT, "structures_all.csv"))


if __name__ == "__main__":
    sys.exit(main())
