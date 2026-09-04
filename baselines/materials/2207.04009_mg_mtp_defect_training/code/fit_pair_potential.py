"""Classical pair-potential baseline fit on the frozen DFT data.

Fits a flexible 2-body potential f(r) = sum_k c_k * exp(-(r-r_k)^2/sigma^2)
(linear in coefficients -> ridge regression) to the per-structure total
energies of the EverythingNoShear training set.  This is the best a *pure
pair potential* (classical-style) can do, and serves as the "classical
potential" reference for the 1-2 orders-of-magnitude comparison against the
MTP energy errors recovered from the frozen Mlip h5 archives.

Outputs:
  results/classical_pair_rmse.csv
"""
import os
import numpy as np
import pandas as pd
from scipy import sparse
from ase import Atoms
from ase.neighborlist import neighbor_list

from load_structures import load_cfg_structures, parse_cfg_file

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.join(BASE, "work")
OUT = os.path.join(BASE, "results")
os.makedirs(OUT, exist_ok=True)

RC = 5.2          # pair cutoff in Angstrom (same as MTP min-cutoff default)
N_BASIS = 12      # number of Gaussian basis functions
SIGMA = 0.20      # Gaussian width
SEED = 42


def pair_features(rec, centers):
    """Return feature vector = sum over pairs of Gaussian basis evaluated at r.

    rec: dict with cell, positions, n_atoms from load_structures
    """
    cell = np.asarray(rec["cell"], dtype=float)
    pos = np.asarray(rec["positions"], dtype=float)
    n = len(pos)
    if n == 0:
        return np.zeros(len(centers))
    atoms = Atoms("Mg%d" % n if False else ["Mg"] * n, positions=pos, cell=cell, pbc=True)
    i, j, d, _ = neighbor_list("ijdD", atoms, RC)
    mask = i < j  # unique pairs
    i, j, d = i[mask], j[mask], d[mask]
    if len(d) == 0:
        return np.zeros(len(centers))
    # Gaussian design matrix G[pair, basis]
    G = np.exp(-((d[:, None] - centers[None, :]) ** 2) / SIGMA ** 2)
    feat = G.sum(axis=0)
    return feat


def main():
    subset = "EverythingNoShear"
    recs = load_cfg_structures(os.path.join(WORK, "structure_files", subset + ".cfg"))
    rng = np.random.default_rng(SEED)
    # deterministic 80/20 split
    perm = rng.permutation(len(recs))
    n_tr = int(0.8 * len(recs))
    tr_idx = perm[:n_tr]
    te_idx = perm[n_tr:]
    print(f"Loaded {len(recs)} structures; train={len(tr_idx)}, test={len(te_idx)}")

    centers = np.linspace(2.0, RC, N_BASIS)
    E = np.array([r["energy"] for r in recs])
    nat = np.array([r["n_atoms"] for r in recs])

    # build feature matrix
    X = np.zeros((len(recs), N_BASIS))
    for k, idx in enumerate(range(len(recs))):
        X[k] = pair_features(recs[idx], centers)
    # ridge regression on training set
    lam = 1e-4
    A = X[tr_idx].T @ X[tr_idx] + lam * np.eye(N_BASIS)
    b = X[tr_idx].T @ E[tr_idx]
    c = np.linalg.solve(A, b)
    Ep = X @ c

    def report(tag, idx):
        e_dft = E[idx]
        e_pred = Ep[idx]
        n = nat[idx]
        rmse = np.sqrt(np.mean(((e_pred - e_dft) / n) ** 2)) * 1000.0
        mae = np.mean(np.abs((e_pred - e_dft) / n)) * 1000.0
        print(f"{tag:8s} n={len(idx):6d}  energy RMSE={rmse:9.2f} meV/atom  MAE={mae:8.2f}")
        return rmse, mae

    rmse_tr, mae_tr = report("train", tr_idx)
    rmse_te, mae_te = report("test", te_idx)
    rmse_all, mae_all = report("all", np.arange(len(recs)))

    row = {
        "model": "pair_Gaussian_basis",
        "train_set": subset,
        "n_basis": N_BASIS,
        "cutoff_A": RC,
        "n_train": int(len(tr_idx)),
        "n_test": int(len(te_idx)),
        "energy_rmse_train_meV_atom": rmse_tr,
        "energy_mae_train_meV_atom": mae_tr,
        "energy_rmse_test_meV_atom": rmse_te,
        "energy_mae_test_meV_atom": mae_te,
        "energy_rmse_all_meV_atom": rmse_all,
        "energy_mae_all_meV_atom": mae_all,
        "note": "2-body only (classical-style pair potential), ridge fit",
    }
    df = pd.DataFrame([row])
    df.to_csv(os.path.join(OUT, "classical_pair_rmse.csv"), index=False)
    np.save(os.path.join(OUT, "pair_coeffs.npy"), c)
    np.save(os.path.join(OUT, "pair_centers.npy"), centers)
    print("\nSaved", os.path.join(OUT, "classical_pair_rmse.csv"))


if __name__ == "__main__":
    main()
