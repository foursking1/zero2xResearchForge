"""
Task 4: 2608.06662_mlip_cross_geometry - ORB-V3 zero-shot inference (MP-NC group).

ORB-V3 is the paper's best zero-shot model (anchor: 6 meV/atom, 197.3 meV/A).
Uses the SAME stratified subsample (seed 42, max_per_geometry=200) as CHGNet/MACE.

Usage:
    python infer_orb.py [data_root] [out_csv] [max_per_geometry]
"""
import os
import sys
import csv
import time
from concurrent.futures import ProcessPoolExecutor

import numpy as np

os.environ.setdefault("OMP_NUM_THREADS", "2")

SEED = 42
GEOMS = ["bulk", "slab", "particle", "neck", "wire"]
DEFAULT_ROOT = r"F:/dataset/materials/2608.06662_mlip_cross_geometry/ZrO2"
HERE = os.path.dirname(os.path.abspath(__file__))

from infer_mlip import collect_frames, sample_frames, extract_dft  # noqa: E402


def worker_infer(batch):
    """batch: list of (geometry, filepath, frame_index, n_atoms)."""
    import ase.io
    from orb_models.forcefield import pretrained

    calc = pretrained.orb_v3(device="cpu")
    out = []
    for geom, f, i, n in batch:
        atoms = ase.io.read(f, index=i)
        e_dft, f_dft = extract_dft(atoms)
        if f_dft is None or f_dft.shape != (n, 3):
            print("skip missing forces", os.path.basename(f), i)
            continue
        atoms.calc = calc
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
    out_csv = sys.argv[2] if len(sys.argv) > 2 else os.path.join(here, "..", "results", "per_structure_errors_orb.csv")
    max_per_geom = int(sys.argv[3]) if len(sys.argv) > 3 else 200
    os.makedirs(os.path.dirname(out_csv), exist_ok=True)

    frames = collect_frames(root)
    chosen = sample_frames(frames, max_per_geom)
    print("Sampled frames:", len(chosen))

    n_workers = min(8, len(chosen))
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


if __name__ == "__main__":
    main()
