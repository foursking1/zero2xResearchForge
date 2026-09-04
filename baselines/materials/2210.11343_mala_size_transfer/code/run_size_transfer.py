"""
MALA cross-size-transfer inference for the beryllium model (arXiv:2210.11343).

Reproduces the paper's core claim: a model trained on 256 Be atoms
(equilibrium density 1.896 g/cm^3) is applied to 256 / 512 / 1,024 / 2,048
atom hcp supercells, and the per-atom band energy drift (proxy for the total
energy error) is evaluated at fixed grid spacing.

Pipeline (all stepwise, deterministic, seed 42, CPU):
  1. Load the frozen model (params.json, network.pth, iscaler/oscaler pkl).
  2. Build hcp supercells at 1.896 g/cm^3 and displace atoms (Gaussian, RMS
     0.1 A, seed 42) to emulate the 298 K training snapshot.
  3. Compute SNAP bispectrum descriptors on the real-space grid
     (numba-JIT core, validated against MALA to ~1e-16).
  4. Feed descriptors through the NN -> predicted LDOS (per voxel "1/eV").
  5. Integrate: Fermi energy (N = 2/atom), band energy, entropy, electron
     count (self-consistency check: 2 e-/atom).

Because the frozen rodare 1851 package does NOT ship any DFT reference
outputs (no QE .out files, no pseudopotentials, no reference density/energy),
absolute energy errors and density MAPE vs DFT are NOT computable; the
256-atom ANCHOR is used as the internal baseline and per-size drift is the
verified proxy metric (task direction hint #3).

Environment:
    pip install mala numpy scipy torch ase numba
    (MALA 1.4.0; legacy-params compatibility patches are applied locally)

Run:
    python run_size_transfer.py              # reads frozen model from
                                             # $MALA_MODEL_DIR (default: F:/dataset/... )
Output:
    ../results/size_transfer_results.json    # per-size observables + drift
"""
import json
import os
import tempfile
import time

import numpy as np
import torch
from ase.build import bulk
from scipy.optimize import brentq
from scipy.special import entr
from ase.units import kB

import mala
from mala.datahandling.snapshot import Snapshot
from mala.targets.calculation_helpers import fermi_function, analytical_integration

import numba_bispectrum as nb

# The frozen model directory (rodare 1851, size_transfer_cleaned).
MODEL_DIR = os.environ.get(
    "MALA_MODEL_DIR",
    "F:/dataset/materials/2210.11343_mala_size_transfer/trained_models/beryllium/",
)

SPACING = 0.25          # fixed grid spacing (Angstrom) across all sizes
DISPLACEMENT = 0.1      # Gaussian displacement RMS (Angstrom), seed 42
TEMPERATURE = 298.0     # K (paper training/validation temperature)
SEED = 42
SUPERCELLS = {
    256: (4, 4, 8),
    512: (4, 8, 8),
    1024: (8, 8, 8),
    2048: (8, 8, 16),
}


def load_legacy_params(path):
    """Load the legacy-format params.json through MALA 1.4 (drop debug block)."""
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
    d.pop("debug", None)
    tmp = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False,
                                      encoding="utf-8")
    json.dump(d, tmp)
    tmp.close()
    try:
        return mala.Parameters.load_from_file(tmp.name)
    finally:
        os.unlink(tmp.name)


def patch_legacy():
    """
    MALA 1.4 <-> legacy 1.1 compatibility patches.

    1) Snapshot.from_json: legacy snapshots lack "snapshot_type" -> "numpy".
    2) FeedForwardNet.__init__: legacy params store one activation for all
       hidden layers; MALA 1.4 expects one activation per layer.
    """
    _orig = Snapshot.from_json

    @classmethod
    def _patched(cls, json_dict):
        jd = dict(json_dict)
        jd.setdefault("snapshot_type", "numpy")
        return _orig(jd)

    Snapshot.from_json = _patched

    import mala.network.network as mnn
    _orig_ffn_init = mnn.FeedForwardNet.__init__

    def legacy_ffn_init(self, prm):
        o_acts = prm.network.layer_activations
        o_inc = prm.network.layer_activations_include_output_layer
        try:
            if isinstance(o_acts, list) and len(o_acts) == 1:
                n = len(prm.network.layer_sizes) - 1
                prm.network.layer_activations = [o_acts[0]] * n
                prm.network.layer_activations_include_output_layer = False
            _orig_ffn_init(self, prm)
        finally:
            prm.network.layer_activations = o_acts
            prm.network.layer_activations_include_output_layer = o_inc

    mnn.FeedForwardNet.__init__ = legacy_ffn_init


def build_be_primitive():
    """
    Be hcp primitive cell at the paper's 1.896 g/cm^3 training density.

    Lattice constants are scaled from the ambient experimental a0/c0 so the
    volume-per-atom gives 1.896 g/cm^3.
    """
    a0, c0 = 2.2866, 3.583
    V_prim = (np.sqrt(3) / 2) * a0 ** 2 * c0
    vol_per_atom = V_prim / 2
    rho_current = 9.0122 / (vol_per_atom * 6.02214076e23) * 1e24
    s = (rho_current / 1.896) ** (1 / 3)
    a, c = a0 * s, c0 * s
    return bulk("Be", "hcp", a=a, c=c)


def main():
    patch_legacy()
    params = load_legacy_params(MODEL_DIR + "beryllium.params.json")
    params.use_gpu = False
    params.use_lammps = False
    params.descriptors.descriptor_type = "SNAP"
    params.descriptors.twojmax = 10
    params.descriptors.rcutfac = 4.67637
    params.descriptors.bispectrum_cutoff = 4.67637
    params.descriptors.bispectrum_switchflag = 0
    params.targets.target_type = "LDOS"
    params.targets.ldos_gridsize = 250
    params.targets.ldos_gridspacing_ev = 0.1
    params.targets.ldos_gridoffset_ev = -5

    network = mala.Network.load_from_file(params, MODEL_DIR + "beryllium.network.pth")
    network.eval()
    iscaler = mala.DataScaler.load_from_file(MODEL_DIR + "beryllium.iscaler.pkl",
                                             auto_convert=False)
    oscaler = mala.DataScaler.load_from_file(MODEL_DIR + "beryllium.oscaler.pkl",
                                             auto_convert=False)
    for sc in [iscaler, oscaler]:
        if not hasattr(sc, "scale_minmax"):
            sc.scale_minmax = bool(getattr(sc, "scale_normal", False))

    be_prim = build_be_primitive()
    egrid = -5.0 + 0.1 * np.arange(250)

    def n_electrons(dos, ef, T=TEMPERATURE):
        return analytical_integration(dos, "F0", "F1", ef, egrid, T)

    def solve_ef(dos, N, T=TEMPERATURE):
        return brentq(lambda ef: n_electrons(dos, ef, T) - N,
                      egrid[0], egrid[-1], maxiter=200)

    results = {}
    resume_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "size_transfer_results.json")
    if os.path.exists(resume_path):
        try:
            prev = json.load(open(resume_path, encoding="utf-8")).get("results", {})
            results = {int(k): v for k, v in prev.items()}
            print("resuming; sizes done:", sorted(results), flush=True)
        except Exception:
            results = {}

    for natoms, supercell in sorted(SUPERCELLS.items()):
        if natoms in results:
            print(f"--- {natoms} atoms already in checkpoint, skipping ---", flush=True)
            continue

        be = be_prim * supercell
        rng = np.random.default_rng(SEED)
        be.positions += rng.normal(0, DISPLACEMENT, size=(len(be), 3))
        be.wrap()
        cell = be.get_cell()
        V_cell = abs(np.linalg.det(cell))
        L = [np.linalg.norm(cell[i]) for i in range(3)]
        grid = [max(2, int(round(L[i] / SPACING))) for i in range(3)]
        npts = int(np.prod(grid))

        t0 = time.perf_counter()
        dc = nb.prepare_bispectrum(params, be, grid)
        t_prep = time.perf_counter() - t0
        t0 = time.perf_counter()
        descs = nb.calculate_bispectrum_numba(dc, be, grid, batch_size=256)
        t_desc = time.perf_counter() - t0

        features = descs[..., 3:].reshape(-1, 91).astype(np.float32)
        inp = torch.from_numpy(features)
        iscaler.transform(inp)
        with torch.no_grad():
            out = network(inp)
        pred = oscaler.inverse_transform(out.to("cpu"), as_numpy=True).reshape(-1, 250)
        pred[pred < 0] = 0
        # DOS(E) = sum over grid points of per-voxel "1/eV" LDOS.
        dos = pred.sum(axis=0)

        N_target = 2 * len(be)
        ef = solve_ef(dos, N_target)
        fvals = fermi_function(egrid, ef, TEMPERATURE, suppress_overflow=True)
        fl = np.clip(fvals, 1e-20, 1.0 - 1e-15)
        band_energy = np.trapezoid(dos * egrid * fvals, egrid)
        shannon = entr(fl) + entr(1.0 - fl)
        entropy = kB * np.trapezoid(dos * shannon, egrid)
        density_pt = np.trapezoid(pred * fvals, egrid, axis=1)
        N_check = density_pt.sum()
        dos_integral = np.trapezoid(dos, egrid)

        results[natoms] = {
            "supercell": list(supercell),
            "n_atoms": len(be),
            "grid": grid,
            "n_grid_points": npts,
            "points_per_atom": npts / len(be),
            "spacing_actual": [L[i] / grid[i] for i in range(3)],
            "cell_volume": float(V_cell),
            "prep_time_s": float(t_prep),
            "desc_time_s": float(t_desc),
            "desc_per_point_ms": float(t_desc / npts * 1000),
            "fermi_energy_eV": float(ef),
            "band_energy_eV": float(band_energy),
            "band_energy_per_atom_eV": float(band_energy / len(be)),
            "entropy_eV": float(entropy),
            "entropy_per_atom_eV": float(entropy / len(be)),
            "total_electrons": float(N_check),
            "electrons_per_atom": float(N_check / len(be)),
            "dos_integral_eV": float(dos_integral),
        }
        print(f"--- {natoms} atoms done in {t_desc:.1f}s desc ---", flush=True)
        print(json.dumps(results[natoms], indent=1), flush=True)
        out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "size_transfer_results.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump({"results": results, "spacing": SPACING,
                       "temperature": TEMPERATURE, "seed": SEED}, f, indent=1)
        print("checkpoint written", out_path, flush=True)

    base = results[256]
    drift = {}
    for natoms in results:
        r = results[natoms]
        drift[natoms] = {
            "band_energy_per_atom_drift_eV":
                r["band_energy_per_atom_eV"] - base["band_energy_per_atom_eV"],
            "band_energy_per_atom_drift_meV":
                (r["band_energy_per_atom_eV"] - base["band_energy_per_atom_eV"]) * 1000,
            "fermi_energy_drift_eV": r["fermi_energy_eV"] - base["fermi_energy_eV"],
            "entropy_per_atom_drift_eV":
                r["entropy_per_atom_eV"] - base["entropy_per_atom_eV"],
        }
    print("DRIFT RELATIVE TO 256-ATOM BASELINE:")
    for natoms in drift:
        print(natoms, json.dumps(drift[natoms], indent=1), flush=True)

    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "size_transfer_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"results": results, "drift": drift, "spacing": SPACING,
                   "temperature": TEMPERATURE, "seed": SEED}, f, indent=1)
    print("wrote", out_path)


if __name__ == "__main__":
    main()