"""
Task 1: 2509.07417_zeolite_mlip_bench
Recompute Table 3 (pure silica) and Table 4 (guest-containing) relative-energy
RMSE values from the frozen official Zenodo dataset ZeoBenchmark.zip.

Usage:
    python analyze_zeo.py [zip_path] [out_dir]

zip_path defaults to F:/dataset/materials/2509.07417_zeolite_mlip_bench/ZeoBenchmark.zip
out_dir  defaults to the script's ../results directory.

Pipeline:
  1. SHA-256 checksum verification of the frozen zip.
  2. Extract to a temporary directory (no modification of frozen files).
  3. Load Puresilica.json / Cu_CHA.json / KSDA_ERI.json.
  4. Count atoms per structure from the pymatgen 'structure' dict embedded in the
     DFT entry (Si count for pure silica, total atoms for guests).
  5. Compute relative energies and RMSE vs DFT per paper's definition.

Units: 1 eV = 96.48533212 kJ/mol.
"""
import hashlib
import json
import math
import os
import sys
import tempfile
import zipfile
import shutil

EV_TO_KJ = 96.48533212

# Expected SHA-256 of the frozen zip (from data/checksums.sha256)
ZIP_SHA256 = "f8214b63e39c6d3e3f84bfe6bcf7cf5c44140074de5d12de4085921131a7f3d1"

# Paper-model key mapping for reporting
MODEL_KEYS = {
    # pure silica keys (17)
    "chgnet": "CHGNet",
    "orb": "ORB",  # not reported in Table 3 (ORB v1)
    "orb_v3": "ORB-v3",
    "mattersim": "MatterSim",
    "uff": "UFF",
    "dreiding": "Dreiding",
    "gfn": "GFN-FF",
    "slc": "SLC",
    "clayff": "ClayFF",
    "bsff": "BSFF",
    "eSEN-30M-OAM": "eSEN-30M-OAM",
    "eqV2-L-OAM": "eqV2-L-OAM",
    "eqV2-L-OMat": "eqV2-L-OMat",
    "EquiformerV2-lE4-lF100-S2EFS-OC22": "EqV2-OC22",
    "pfp": "PFP-v7",
    "pfp_shifted": "PFP-v7(shifted)",
    "dft": "DFT",
}


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def count_si(structure):
    """Count number of Si atoms from a pymatgen-style structure dict."""
    n = 0
    for site in structure["sites"]:
        for sp in site["species"]:
            if sp.get("element") == "Si":
                n += sp.get("occu", 1.0)
    return n


def count_atoms(structure):
    """Count total atoms (sum of occupancies) from a pymatgen-style structure dict."""
    n = 0.0
    for site in structure["sites"]:
        for sp in site["species"]:
            n += sp.get("occu", 1.0)
    return n


def get_ref_structure(data):
    """Return the structure key whose DFT per-atom energy is the lowest."""
    best = None
    best_e = float("inf")
    for sname, sdata in data.items():
        e = sdata["dft"]["energy"]
        n = count_atoms(sdata["dft"]["structure"])
        if n <= 0:
            continue
        per = e / n
        if per < best_e:
            best_e = per
            best = sname
    return best


def compute_pure_silica(data):
    """Table 3: rel(s) = [E(s)/nSi(s) - E(quartz)/nSi(quartz)] * 96.485 kJ/molSi.
    RMSE vs same-criteria DFT, over all topologies except quartz.
    Each potential uses its own alpha-quartz energy as reference.
    """
    quartz_energy = {}
    quartz_nsi = {}
    for model in list(MODEL_KEYS) + ["dft"]:
        if model in data.get("quartz", {}):
            st = data["quartz"][model].get("structure")
            if st is None:
                # use dft structure's Si count as proxy (same framework)
                st = data["quartz"]["dft"]["structure"]
            quartz_energy[model] = data["quartz"][model]["energy"]
            quartz_nsi[model] = count_si(st) if st else None

    models = [m for m in ["dft"] + list(MODEL_KEYS) if m in quartz_energy]
    # Build per-structure, per-model relative energies
    # rows = list of topologies (excluding quartz)
    topologies = [k for k in data.keys() if k != "quartz"]
    rel = {m: {} for m in models}
    nsi = {}
    for t in topologies:
        nsi[t] = count_si(data[t]["dft"]["structure"])
    for t in topologies:
        for m in models:
            if m not in data[t]:
                continue
            e = data[t][m]["energy"]
            rel[m][t] = (e / nsi[t] - quartz_energy[m] / quartz_nsi[m]) * EV_TO_KJ
    # RMSE vs DFT
    rmse = {}
    for m in models:
        if m == "dft":
            continue
        errs = [(rel[m][t] - rel["dft"][t]) ** 2 for t in topologies if t in rel[m]]
        rmse[m] = math.sqrt(sum(errs) / len(errs))
    return rmse, topologies, rel, nsi


def compute_guests(data):
    """Table 4: rel(s) = [E(s)/N(s) - E(ref)/N(ref)] * 96.485 kJ/molatom.
    ref = structure with lowest DFT per-atom energy.
    RMSE vs DFT over all structures.
    """
    ref = get_ref_structure(data)
    N = {}
    for sname in data:
        N[sname] = count_atoms(data[sname]["dft"]["structure"])
    models = [m for m in MODEL_KEYS if m != "dft" and m in data[ref]]
    # only MLIP keys for guests (no analytic potentials)
    rel = {m: {} for m in models + ["dft"]}
    for sname in data:
        for m in rel:
            if m in data[sname]:
                e = data[sname][m]["energy"]
                rel[m][sname] = (e / N[sname] - data[ref][m]["energy"] / N[ref]) * EV_TO_KJ
    rmse = {}
    for m in models:
        errs = [(rel[m][s] - rel["dft"][s]) ** 2 for s in data if s in rel[m]]
        rmse[m] = math.sqrt(sum(errs) / len(errs))
    return rmse, ref, N, rel


def main():
    zip_path = sys.argv[1] if len(sys.argv) > 1 else (
        r"F:/dataset/materials/2509.07417_zeolite_mlip_bench/ZeoBenchmark.zip")
    here = os.path.dirname(os.path.abspath(__file__))
    out_dir = sys.argv[2] if len(sys.argv) > 2 else os.path.join(here, "..", "results")
    out_dir = os.path.abspath(out_dir)
    os.makedirs(out_dir, exist_ok=True)

    print(f"Zip: {zip_path}")
    actual = sha256_file(zip_path)
    print(f"Checksum: {actual}")
    assert actual == ZIP_SHA256, f"CHECKSUM MISMATCH: {actual}"
    print("Checksum OK.")

    tmpdir = tempfile.mkdtemp(prefix="zeo_bench_")
    try:
        with zipfile.ZipFile(zip_path) as z:
            z.extractall(tmpdir)
        base = os.path.join(tmpdir, "Zenodo")
        print("Extracted to", base)

        with open(os.path.join(base, "Puresilica.json"), "rb") as f:
            pure = json.load(f)
        with open(os.path.join(base, "Cu_CHA.json"), "rb") as f:
            cu = json.load(f)
        with open(os.path.join(base, "KSDA_ERI.json"), "rb") as f:
            eri = json.load(f)

        print("Sizes: pure=%d cu=%d eri=%d" % (len(pure), len(cu), len(eri)))

        # ---- Table 3: pure silica ----
        rmse3, tops, rel3, nsi = compute_pure_silica(pure)
        order3 = sorted(rmse3.items(), key=lambda kv: kv[1])
        print("\n=== Table 3 (pure silica, kJ/molSi) ===")
        for m, v in order3:
            print(f"  {MODEL_KEYS.get(m, m):<24s} {v:.4f}")

        # ---- Table 4: guests ----
        cu_rmse, cu_ref, cu_N, _ = compute_guests(cu)
        eri_rmse, eri_ref, eri_N, _ = compute_guests(eri)
        print("\n=== Table 4 Cu/CHA (kJ/molatom) ===")
        for m, v in sorted(cu_rmse.items(), key=lambda kv: kv[1]):
            print(f"  {MODEL_KEYS.get(m, m):<24s} {v:.4f}")
        print("  ref =", cu_ref)
        print("\n=== Table 4 K-OSDA/ERI (kJ/molatom) ===")
        for m, v in sorted(eri_rmse.items(), key=lambda kv: kv[1]):
            print(f"  {MODEL_KEYS.get(m, m):<24s} {v:.4f}")
        print("  ref =", eri_ref)

        # C3 check: eSEN min in all three systems
        # Paper-reported universal MLIP set (Table 3/4): CHGNet, ORB-v3, MatterSim,
        # eSEN-30M-OAM, PFP-v7 (pfp_shifted), EqV2(OC22).
        paper_mlips = ["CHGNet", "ORB-v3", "MatterSim", "eSEN-30M-OAM", "PFP-v7", "EqV2-OC22"]
        c3_ranks = {}
        c3_ranks_restricted = {}
        # raw rank among all models that have a RMSE in that system
        for name, r in [("pure", rmse3), ("cu", cu_rmse), ("eri", eri_rmse)]:
            if "eSEN-30M-OAM" in r:
                ranked = sorted(r.items(), key=lambda kv: kv[1])
                c3_ranks[name] = [i for i, (m, _) in enumerate(ranked) if m == "eSEN-30M-OAM"][0] + 1
                # restricted to paper-reported MLIPs
                rest = {m: v for m, v in r.items() if m in paper_mlips}
                ranked_r = sorted(rest.items(), key=lambda kv: kv[1])
                c3_ranks_restricted[name] = [i for i, (m, _) in enumerate(ranked_r) if m == "eSEN-30M-OAM"][0] + 1
        print("\nC3 eSEN ranks (all models):", c3_ranks)
        print("C3 eSEN ranks (paper-reported MLIPs only):", c3_ranks_restricted)

        # ---- Write outputs ----
        # evidence table CSV
        import csv
        csv_path = os.path.join(out_dir, "evidence_table.csv")
        with open(csv_path, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["system", "model", "rmse_kj_mol", "note"])
            for m, v in sorted(rmse3.items()):
                w.writerow(["puresilica", MODEL_KEYS.get(m, m), round(v, 4), "Table3 kJ/molSi"])
            for m, v in sorted(cu_rmse.items()):
                w.writerow(["Cu_CHA", MODEL_KEYS.get(m, m), round(v, 4), "Table4 kJ/molatom"])
            for m, v in sorted(eri_rmse.items()):
                w.writerow(["KSDA_ERI", MODEL_KEYS.get(m, m), round(v, 4), "Table4 kJ/molatom"])
        print("Wrote", csv_path)

        # metrics.json
        metrics = {
            "task_id": "2509.07417_zeolite_mlip_bench",
            "checksum_verified": actual,
            "n_puresilica": len(pure),
            "n_cu_cha": len(cu),
            "n_ksda_eri": len(eri),
            "table3_rmse_puresilica_kj_molSi": {MODEL_KEYS.get(m, m): round(v, 4) for m, v in sorted(rmse3.items())},
            "table4_rmse_cu_cha_kj_molatom": {MODEL_KEYS.get(m, m): round(v, 4) for m, v in sorted(cu_rmse.items())},
            "table4_rmse_ksda_eri_kj_molatom": {MODEL_KEYS.get(m, m): round(v, 4) for m, v in sorted(eri_rmse.items())},
            "cu_cha_ref_structure": cu_ref,
            "ksda_eri_ref_structure": eri_ref,
            "c3_esen_rank_by_system": c3_ranks,
            "c3_esen_rank_by_system_paper_mlips_only": c3_ranks_restricted,
            "cu_cha_harder_than_eri_all_models": {
                MODEL_KEYS.get(m, m): (cu_rmse[m] > eri_rmse[m])
                for m in cu_rmse if m in eri_rmse
            },
        }
        with open(os.path.join(out_dir, "metrics.json"), "w") as f:
            json.dump(metrics, f, indent=2)
        print("Wrote", os.path.join(out_dir, "metrics.json"))
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    main()
