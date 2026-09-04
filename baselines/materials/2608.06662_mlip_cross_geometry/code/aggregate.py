"""
Task 4: 2608.06662_mlip_cross_geometry - aggregate per-structure errors into
the evidence table.

Reads one or more per-structure error CSVs (columns:
geometry,file,frame,n_atoms,E_DFT,E_model,force_rmse_per_atom,sse,n_comps) plus
the frozen extended-XYZ files (for Zr/O counts), fits element-level reference
energy offsets {dmu_Zr, dmu_O} by least squares on the reported reference set
(all sampled frames by default), then computes per-geometry and global aligned
energy/force RMSE.

Usage:
    python aggregate.py <data_root> [csv1 csv2 ...]

    data_root : directory containing bulk/slab/particle/neck/wire/*.xyz
    csvs      : per-structure error tables. Defaults to the CHGNet, MACE and
                ORB CSVs produced by the inference scripts.
"""
import os
import sys
import csv
import json
from collections import defaultdict

import numpy as np

GEOMS = ["bulk", "slab", "particle", "neck", "wire"]
HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "..", "results")


def read_rows(csv_path):
    with open(csv_path, newline="") as f:
        return list(csv.DictReader(f))


def composition_from_xyz(data_root, geom, fname, frames, n_atoms_by_frame):
    """Return list of (n_Zr, n_O) for the requested frames of one xyz file."""
    import ase.io
    path = os.path.join(data_root, geom, fname)
    ats_list = ase.io.read(path, index=":")
    out = {}
    for a in ats_list:
        syms = a.get_chemical_symbols()
        n_zr = sum(1 for s in syms if s == "Zr")
        n_o = sum(1 for s in syms if s == "O")
        out[len(a)] = (n_zr, n_o)
    res = []
    for i, n in zip(frames, n_atoms_by_frame):
        n = int(n)
        res.append(out.get(n, (n, 0)))
    return res


def load_model(data_root, csv_path, name, group):
    rows = read_rows(csv_path)
    # group rows by (geometry, file) to attach Zr/O counts
    by_file = defaultdict(list)
    for r in rows:
        by_file[(r["geometry"], r["file"])].append(r)

    comp_cache = {}
    for (geom, fname), sub in by_file.items():
        key = (geom, fname)
        if key in comp_cache:
            comps = comp_cache[key]
        else:
            comps = composition_from_xyz(
                data_root, geom, fname,
                [r["frame"] for r in sub], [r["n_atoms"] for r in sub])
            comp_cache[key] = comps
        for r, (nz, no) in zip(sub, comps):
            r["n_Zr"] = nz
            r["n_O"] = no

    # numeric conversion
    for r in rows:
        for k in ["n_atoms", "E_DFT", "E_model", "force_rmse_per_atom", "sse", "n_comps", "n_Zr", "n_O"]:
            r[k] = float(r[k])

    # ---- reference energy alignment: fit {dmu_Zr, dmu_O} on all frames ----
    A = np.array([[r["n_Zr"], r["n_O"]] for r in rows], dtype=float)
    y = np.array([r["E_DFT"] - r["E_model"] for r in rows], dtype=float)
    dmu, *_ = np.linalg.lstsq(A, y, rcond=None)
    dmu_zr, dmu_o = float(dmu[0]), float(dmu[1])

    for r in rows:
        r["E_aligned"] = r["E_model"] + r["n_Zr"] * dmu_zr + r["n_O"] * dmu_o
        r["e_per_atom_eV"] = (r["E_DFT"] - r["E_aligned"]) / r["n_atoms"]

    def energy_rmse(subset):
        if not subset:
            return float("nan")
        e = np.array([r["e_per_atom_eV"] for r in subset])
        return float(np.sqrt(np.mean(e ** 2))) * 1000.0  # meV/atom

    def force_rmse(subset):
        if not subset:
            return float("nan")
        sse = sum(r["sse"] for r in subset)
        ncomps = sum(r["n_comps"] for r in subset)
        return float(np.sqrt(sse / ncomps)) * 1000.0  # meV/A

    per_geom = {}
    for g in GEOMS:
        sub = [r for r in rows if r["geometry"] == g]
        per_geom[g] = {"energy_rmse": energy_rmse(sub), "force_rmse": force_rmse(sub)}

    return {
        "name": name,
        "group": group,
        "n_frames": len(rows),
        "dmu_zr": dmu_zr,
        "dmu_o": dmu_o,
        "energy_rmse_global": energy_rmse(rows),
        "force_rmse_global": force_rmse(rows),
        "per_geom": per_geom,
    }


def main():
    data_root = sys.argv[1] if len(sys.argv) > 1 else r"F:/dataset/materials/2608.06662_mlip_cross_geometry/ZrO2"
    csvs = sys.argv[2:]
    if not csvs:
        csvs = [
            os.path.join(RESULTS, "per_structure_errors_chgnet.csv"),
            os.path.join(RESULTS, "per_structure_errors_mace.csv"),
            os.path.join(RESULTS, "per_structure_errors_orb.csv"),
        ]
    names = [os.path.basename(c).replace("per_structure_errors_", "").replace(".csv", "").upper() for c in csvs]
    groups = {"CHGNET": "MP-C", "MACE": "MP-C", "MPA0": "MP-NC", "ORB": "MP-NC"}

    models = []
    for c, nm in zip(csvs, names):
        if not os.path.exists(c):
            print("skip missing", c)
            continue
        print("Loading", c)
        models.append(load_model(data_root, c, nm, groups.get(nm, "?")))

    out_rows = []
    for m in models:
        for g in GEOMS + ["global"]:
            if g == "global":
                e, f = m["energy_rmse_global"], m["force_rmse_global"]
            else:
                e, f = m["per_geom"][g]["energy_rmse"], m["per_geom"][g]["force_rmse"]
            out_rows.append({
                "model": m["name"], "group": m["group"], "geometry": g,
                "energy_rmse_meV_atom": round(e, 3) if e == e else None,
                "force_rmse_meV_A": round(f, 3) if f == f else None,
            })

    # across-model mean (only for models sharing a geometry) + group means
    def geom_mean(predicate, g):
        vals_e = [m["energy_rmse_global"] if g == "global" else m["per_geom"][g]["energy_rmse"]
                  for m in models if predicate(m)]
        vals_f = [m["force_rmse_global"] if g == "global" else m["per_geom"][g]["force_rmse"]
                  for m in models if predicate(m)]
        vals_e = [v for v in vals_e if v == v]
        vals_f = [v for v in vals_f if v == v]
        if not vals_e:
            return None, None
        return float(np.mean(vals_e)), float(np.mean(vals_f))

    for g in GEOMS + ["global"]:
        for label, pred in [("MEAN_ALL", lambda m: True),
                            ("MEAN_MP_C", lambda m: m["group"] == "MP-C"),
                            ("MEAN_MP_NC", lambda m: m["group"] == "MP-NC")]:
            e, f = geom_mean(pred, g)
            if e is None:
                continue
            out_rows.append({
                "model": label, "group": "", "geometry": g,
                "energy_rmse_meV_atom": round(e, 3),
                "force_rmse_meV_A": round(f, 3),
            })

    # paper-anchor reference rows (PAPER_ANCHOR.md; not computed from frozen data)
    paper_refs = [
        ("PAPER_ORB_V3_best", "", "global", 6.0, 197.3),
        ("PAPER_MEAN_26", "", "global", 20.0, 400.0),
        ("PAPER_ORB_V2_MPtrj_MPC_best", "", "global", 107.67, 309.1),
    ]
    for name, grp, geom, e, f in paper_refs:
        out_rows.append({"model": name, "group": grp, "geometry": geom,
                         "energy_rmse_meV_atom": e, "force_rmse_meV_A": f})

    # directionality: neck+wire vs bulk+slab force rmse
    direction = {}
    for m in models:
        def comb(gs, key):
            vals = [m["per_geom"][g][key] for g in gs]
            vals = [v for v in vals if v == v]
            return float(np.mean(vals)) if vals else None
        direction[m["name"]] = {
            "force_neck_wire": comb(["neck", "wire"], "force_rmse"),
            "force_bulk_slab": comb(["bulk", "slab"], "force_rmse"),
            "energy_lowcoord": comb(["particle", "wire", "neck"], "energy_rmse"),
            "energy_bulk_slab": comb(["bulk", "slab"], "energy_rmse"),
        }

    out_csv = os.path.join(RESULTS, "evidence_table.csv")
    with open(out_csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["model", "group", "geometry",
                                          "energy_rmse_meV_atom", "force_rmse_meV_A"])
        w.writeheader()
        w.writerows(out_rows)
    print("Wrote", out_csv)

    metrics = {
        "models": models,
        "directionality": direction,
        "evidence_rows": out_rows,
    }
    with open(os.path.join(RESULTS, "metrics.json"), "w") as f:
        json.dump(metrics, f, indent=2, default=float)
    print("Wrote", os.path.join(RESULTS, "metrics.json"))

    # console summary
    for m in models:
        print("\n== %s (%s) n=%d dmu=(%.5f, %.5f)" % (m["name"], m["group"], m["n_frames"], m["dmu_zr"], m["dmu_o"]))
        print("  global energy RMSE %.2f meV/atom, force RMSE %.2f meV/A" % (
            m["energy_rmse_global"], m["force_rmse_global"]))
        for g in GEOMS:
            print("   %-9s E %8.2f  F %8.2f" % (
                g, m["per_geom"][g]["energy_rmse"], m["per_geom"][g]["force_rmse"]))
    if direction:
        print("\nDirectionality (neck+wire vs bulk+slab):")
        for k, v in direction.items():
            print("  %s: F neck/wire=%.1f vs bulk/slab=%.1f ; E lowcoord=%.1f vs bulk/slab=%.1f" % (
                k, v["force_neck_wire"] or -1, v["force_bulk_slab"] or -1,
                v["energy_lowcoord"] or -1, v["energy_bulk_slab"] or -1))


if __name__ == "__main__":
    main()
