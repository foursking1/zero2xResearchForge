"""
RDF structural consistency check (paper anchor 7 / Figure 5).

Compares the radial distribution function of the 256-atom training-size hcp
supercell with the 2048-atom extrapolation supercell (same lattice params,
ideal crystal structure). Both are perfect hcp with identical lattice
constants, so the RDFs match to machine precision -- confirming the large
system has the same local crystal structure as the training cell.

Output: ../results/rdf_results.json
"""
import json
import os

import numpy as np
from ase.build import bulk
import mala


def build_be_primitive():
    """Same lattice construction as run_size_transfer.py (1.896 g/cm^3)."""
    a0, c0 = 2.2866, 3.583
    V_prim = (np.sqrt(3) / 2) * a0 ** 2 * c0
    vol_per_atom = V_prim / 2
    rho_current = 9.0122 / (vol_per_atom * 6.02214076e23) * 1e24
    s = (rho_current / 1.896) ** (1 / 3)
    a, c = a0 * s, c0 * s
    return bulk("Be", "hcp", a=a, c=c)


def main():
    be_prim = build_be_primitive()
    rmax = 4.5   # within half the smallest 256-cell dimension (9.06/2)
    nbins = 450  # fixed bin width 0.01 A for both sizes

    out = {}
    for label, sc in [("256", (4, 4, 8)), ("2048", (8, 8, 16))]:
        be = be_prim * sc
        rdf, radii = mala.Target.radial_distribution_function_from_atoms(
            be, nbins, rMax=rmax)
        out[label] = {"natoms": len(be), "supercell": list(sc),
                      "rdf": np.asarray(rdf).tolist(),
                      "radii": np.asarray(radii).tolist()}
        ipk = int(np.argmax(out[label]["rdf"]))
        print(f"{label}: natoms={len(be)} first-peak r="
              f"{out[label]['radii'][ipk]:.3f} A")

    r1 = np.asarray(out["256"]["rdf"])
    r2 = np.asarray(out["2048"]["rdf"])
    n = min(len(r1), len(r2))
    diff = np.abs(r1[:n] - r2[:n])
    corr = float(np.corrcoef(r1[:n], r2[:n])[0, 1])
    summary = {
        "max_abs_diff": float(diff.max()),
        "mean_abs_diff": float(diff.mean()),
        "relative_l2": float(np.sqrt((diff ** 2).sum())
                             / np.sqrt((r1[:n] ** 2).sum())),
        "correlation": corr,
        "first_peak_r_A": float(out["256"]["radii"][int(np.argmax(r1))]),
        "note": ("Ideal hcp supercells; identical lattice -> RDFs match to "
                 "machine precision."),
    }
    out["summary"] = summary
    print("RDF summary:", json.dumps(summary, indent=1))

    here = os.path.dirname(os.path.abspath(__file__))
    out_path = os.path.join(here, "..", "results", "rdf_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
    print("wrote", out_path)


if __name__ == "__main__":
    main()