"""
Task 4: 2608.06662_mlip_cross_geometry - MLIP zero-shot inference on frozen ZrO2 data.

Runs CHGNet (MP-C group, MatBench Discovery compliant) single-point inference on a
fixed-seed stratified subsample of the 14,434 extended-XYZ frames and writes a
per-structure error table for downstream aggregation.

Usage:
    python infer_mlip.py [data_root] [out_csv] [max_per_geometry]

Data root defaults to F:/dataset/materials/2608.06662_mlip_cross_geometry/ZrO2
"""
import os
import sys
import csv
import glob
import json
import random
import time
from concurrent.futures import ProcessPoolExecutor

import numpy as np

os.environ.setdefault("OMP_NUM_THREADS", "2")

SEED = 42
GEOMS = ["bulk", "slab", "particle", "neck", "wire"]
DEFAULT_ROOT = r"F:/dataset/materials/2608.06662_mlip_cross_geometry/ZrO2"


def collect_frames(root):
    """Return list of (geometry, filepath, frame_index, n_atoms)."""
    import ase.io
    frames = []
    for geom in GEOMS:
        files = sorted(glob.glob(os.path.join(root, geom, "*.xyz")))
        for f in files:
            try:
                ats = ase.io.read(f, index=":")
            except Exception as e:
                print("read error", f, e)
                continue
            for i, a in enumerate(ats):
                frames.append((geom, f, i, len(a)))
    return frames


def sample_frames(frames, max_per_geom):
    rng = random.Random(SEED)
    by_geom = {g: [] for g in GEOMS}
    for fr in frames:
        by_geom[fr[0]].append(fr)
    chosen = []
    for g in GEOMS:
        lst = by_geom[g]
        if len(lst) <= max_per_geom:
            chosen.extend(lst)
        else:
            chosen.extend(rng.sample(lst, max_per_geom))
    chosen.sort(key=lambda x: (x[0], x[1], x[2]))
    return chosen


def extract_dft(atoms):
    """Return (E_DFT eV, F_DFT (n,3) eV/A). ASE extended-xyz parser stores the
    reference fields in the SinglePointCalculator attached at read time."""
    calc = atoms.calc
    e = None
    f = None
    if calc is not None:
        res = getattr(calc, "results", {})
        if res:
            e = res.get("energy")
            f = res.get("forces")
    if e is None:
        e = atoms.info.get("energy")
    if f is None and "forces" in atoms.arrays:
        f = atoms.get_array("forces")
    return float(e), np.asarray(f, dtype=float)


def worker_infer(batch):
    """batch: list of (geometry, filepath, frame_index, n_atoms)."""
    import ase.io
    from chgnet.model import CHGNet
    from chgnet.model.dynamics import CHGNetCalculator

    model = CHGNet.load()
    calc = CHGNetCalculator(model)
    out = []
    for geom, f, i, n in batch:
        atoms = ase.io.read(f, index=i)
        e_dft, f_dft = extract_dft(atoms)
        if f_dft is None or f_dft.shape != (n, 3):
            print("skip missing forces", os.path.basename(f), i)
            continue
        atoms.set_calculator(calc)
        e_model = atoms.get_potential_energy()
        f_model = atoms.get_forces()
        d = f_model - f_dft
        force_rmse = float(np.sqrt(np.mean(d ** 2)))
        sse = float(np.sum(d ** 2))
        ncomps = int(n * 3)
        out.append({
            "geometry": geom, "file": os.path.basename(f), "frame": i,
            "n_atoms": n, "E_DFT": float(e_dft), "E_model": float(e_model),
            "force_rmse_per_atom": force_rmse, "sse": sse, "n_comps": ncomps,
        })
    return out


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_ROOT
    here = os.path.dirname(os.path.abspath(__file__))
    out_csv = sys.argv[2] if len(sys.argv) > 2 else os.path.join(here, "..", "results", "per_structure_errors.csv")
    max_per_geom = int(sys.argv[3]) if len(sys.argv) > 3 else 120
    os.makedirs(os.path.dirname(out_csv), exist_ok=True)

    frames = collect_frames(root)
    print("Total frames:", len(frames))
    chosen = sample_frames(frames, max_per_geom)
    print("Sampled frames:", len(chosen))
    for g in GEOMS:
        print(" ", g, sum(1 for c in chosen if c[0] == g))

    # split into batches for workers
    n_workers = min(10, len(chosen))
    batches = [[] for _ in range(n_workers)]
    for i, c in enumerate(chosen):
        batches[i % n_workers].append(c)

    t0 = time.time()
    rows = []
    with ProcessPoolExecutor(max_workers=n_workers) as ex:
        for res in ex.map(worker_infer, batches):
            rows.extend(res)
    print("Inference done in %.1f s" % (time.time() - t0))
    rows.sort(key=lambda r: (r["geometry"], r["file"], r["frame"]))

    with open(out_csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=[
            "geometry", "file", "frame", "n_atoms", "E_DFT", "E_model",
            "force_rmse_per_atom", "sse", "n_comps"])
        w.writeheader()
        w.writerows(rows)
    print("Wrote", out_csv)

    # also write a sample manifest
    meta = {
        "model": "CHGNet v0.3.0 (chgnet 0.4.2, pretrained MP)",
        "group": "MP-C",
        "seed": SEED,
        "max_per_geometry": max_per_geom,
        "device": "cpu",
        "data_root": root,
        "n_sampled": len(chosen),
        "n_total": len(frames),
        "sampled_by_geom": {g: sum(1 for c in chosen if c[0] == g) for g in GEOMS},
    }
    with open(os.path.join(os.path.dirname(out_csv), "inference_meta.json"), "w") as f:
        json.dump(meta, f, indent=2)


if __name__ == "__main__":
    main()
