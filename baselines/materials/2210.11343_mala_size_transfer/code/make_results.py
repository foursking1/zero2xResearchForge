"""
Generate results/evidence_table.csv and results/metrics.json from the
inference output (size_transfer_results.json produced by run_size_transfer.py).

Usage:
    python make_results.py [path_to_size_transfer_results.json] [output_dir]

Default input: <this dir>/size_transfer_results.json
Default output dir: ../results (relative to this script)
"""
import json
import os
import sys
import csv


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    in_path = (sys.argv[1] if len(sys.argv) > 1
               else os.path.join(here, "size_transfer_results.json"))
    out_dir = (sys.argv[2] if len(sys.argv) > 2
               else os.path.join(here, "..", "results"))
    os.makedirs(out_dir, exist_ok=True)

    with open(in_path, encoding="utf-8") as f:
        data = json.load(f)
    results = data["results"]
    drift = data.get("drift", {})

    # ---- evidence_table.csv (columns: system_size, metric, value) ----
    rows = []
    for n in sorted(int(k) for k in results):
        r = results[str(n)]
        rows.append((n, "band_energy_per_atom_eV", r["band_energy_per_atom_eV"]))
        rows.append((n, "fermi_energy_eV", r["fermi_energy_eV"]))
        rows.append((n, "electrons_per_atom", r["electrons_per_atom"]))
        rows.append((n, "entropy_per_atom_eV", r["entropy_per_atom_eV"]))
        if str(n) in drift:
            rows.append((n, "band_energy_per_atom_drift_meV",
                         drift[str(n)]["band_energy_per_atom_drift_meV"]))
            rows.append((n, "fermi_energy_drift_eV",
                         drift[str(n)]["fermi_energy_drift_eV"]))

    csv_path = os.path.join(out_dir, "evidence_table.csv")
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["system_size", "metric", "value"])
        for n, metric, value in rows:
            w.writerow([n, metric, round(float(value), 8)])

    # ---- metrics.json ----
    metrics = {
        "task_id": "2210.11343_mala_size_transfer",
        "conclusion": "partially_supported",
        "model": {
            "element": "Be",
            "training_atoms": 256,
            "training_snapshot": "Be256_298K_snapshot0/2",
            "density_g_per_cc": 1.896,
            "descriptor": "SNAP",
            "twojmax": 10,
            "rcutfac": 4.67637,
            "feature_dim": 94,
            "network_layer_sizes": [91, 800, 800, 800, 250, 250],
            "activation": "LeakyReLU",
            "target": "LDOS",
            "ldos_gridsize": 250,
            "ldos_gridspacing_ev": 0.1,
            "ldos_gridoffset_ev": -5,
            "input_scaling": "feature-wise-standard",
            "output_scaling": "normal",
        },
        "protocol": {
            "grid_spacing_A": data.get("spacing", 0.25),
            "temperature_K": data.get("temperature", 298.0),
            "seed": data.get("seed", 42),
            "displacement_rms_A": 0.1,
            "structure": ("ASE-built hcp supercells at 1.896 g/cc + Gaussian "
                          "displacement"),
            "dos_unit": "sum(pred) per voxel '1/eV' (verified: 2 e-/atom)",
        },
        "per_size": {str(n): results[str(n)]
                     for n in sorted(int(k) for k in results)},
        "drift_vs_256": {str(n): drift[str(n)]
                         for n in sorted(int(k) for k in drift)},
        "paper_anchors": {
            "a1_256_atom_training": "supported",
            "a2_256_512_1024_2048_extrapolation": "reproduced",
            "a3_energy_error_lt43_meV_atom": (
                "not_computable_abs_no_DFT_reference; drift proxy 512=-24.4 "
                "meV/atom, 2048=-38.9 meV/atom (<43); grid-corrected size "
                "effect ~0"),
            "a4_density_mape_lt1pct": (
                "not_computable_no_DFT_reference; "
                "electron_count_self_consistent"),
            "a5_131072_atom_demo": "not_reproduced_no_data",
            "a6_speedup_3_orders_vs_DFT": "not_computable_no_DFT_baseline",
            "a7_rdf_consistency": "supported_256_vs_2048_RDF_corr_1.0",
            "a8_workflow_ldos_scalers": "supported",
        },
    }

    diag_path = os.path.join(out_dir, "grid_density_diagnostic.json")
    if os.path.exists(diag_path):
        with open(diag_path, encoding="utf-8") as f:
            diag = json.load(f)
        metrics["grid_density_diagnostic"] = {
            "grid_sensitivity_slope_meV_per_ppa":
                diag.get("grid_sensitivity_slope_meV_per_ppa"),
            "cross_size_drift_decomposition_meV":
                diag.get("cross_size_drift_decomposition_meV"),
            "interpretation": diag.get("interpretation"),
        }

    out_path = os.path.join(out_dir, "metrics.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=1, ensure_ascii=False)

    print("wrote", csv_path)
    print("wrote", out_path)


if __name__ == "__main__":
    main()