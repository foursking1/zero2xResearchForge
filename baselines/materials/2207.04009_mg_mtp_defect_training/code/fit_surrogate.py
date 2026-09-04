"""Lightweight many-body surrogate potential (linear regression on 2+3 body
descriptors) trained on the frozen DFT reference data.

Goal: demonstrate that a simple, transparent descriptor regression trained on
the frozen DFT energies reaches the ~1-50 meV/atom ballpark on the
EverythingNoShear training set, i.e. within an order of magnitude of the
frozen MTP results (4-35 meV/atom) and 1-2 orders better than a pure pair
(2-body) potential (~0.85 eV/atom RMSE).

Descriptors (summed over atoms):
  2-body : sum_j g_k(r_ij)                      (k = Gaussian basis)
  3-body : sum_{j<l} g_k(r_ij) g_l(r_il)        (radial-angular, cos^0)
  3-body : sum_{j<l} g_k(r_ij) g_l(r_il) cos_theta_jil  (cos^1)
Linear model  E_pred = w . phi(structure); ridge regression.

Outputs: results/surrogate_rmse.csv
"""
import os
import numpy as np
import pandas as pd
from ase import Atoms
from ase.neighborlist import neighbor_list

from load_structures import load_cfg_structures

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.join(BASE, "work")
OUT = os.path.join(BASE, "results")
os.makedirs(OUT, exist_ok=True)

RC = 5.2
NB = 6
SIGMA = 0.30
SEED = 42
LAM = 1e-3


def gauss_centers():
    return np.linspace(2.0, RC, NB)


def structure_features(rec, centers):
    cell = np.asarray(rec["cell"], dtype=float)
    pos = np.asarray(rec["positions"], dtype=float)
    n = len(pos)
    nb = len(centers)
    f0 = np.array([n])                       # per-atom constant (reference energy)
    f2 = np.zeros(nb)
    f3_0 = np.zeros((nb, nb))
    f3_1 = np.zeros((nb, nb))
    if n == 0:
        return np.concatenate([f0, f2, f3_0.ravel(), f3_1.ravel()])
    atoms = Atoms(["Mg"] * n, positions=pos, cell=cell, pbc=True)
    i, j, d, D = neighbor_list("ijdD", atoms, RC)
    # unique pairs for 2-body
    mask = i < j
    if mask.any():
        d2 = d[mask]
        G2 = np.exp(-((d2[:, None] - centers[None, :]) ** 2) / SIGMA ** 2)
        f2 = G2.sum(axis=0)
    # 3-body: loop over central atoms, neighbours from i (sorted)
    for a in range(n):
        sel = np.where(i == a)[0]
        if len(sel) < 2:
            continue
        dv = D[sel]              # displacement vectors of neighbours of a
        dd = d[sel]
        G = np.exp(-((dd[:, None] - centers[None, :]) ** 2) / SIGMA ** 2)  # (m, nb)
        c = np.dot(dv, dv.T)
        nrm = np.linalg.norm(dv, axis=1)
        C = c / np.outer(nrm, nrm)          # cosines (m, m)
        diag_mask = ~np.eye(len(sel), dtype=bool)
        # cos^0
        M0 = G.T @ G
        np.fill_diagonal(M0, 0.0)          # remove j==l
        f3_0 += 0.5 * M0
        # cos^1
        M1 = G.T @ (C * diag_mask) @ G     # zero out j==l on C
        f3_1 += 0.5 * M1
    return np.concatenate([f0, f2, f3_0.ravel(), f3_1.ravel()])


def main():
    subset = "EverythingNoShear"
    recs = load_cfg_structures(os.path.join(WORK, "structure_files", subset + ".cfg"))
    rng = np.random.default_rng(SEED)
    perm = rng.permutation(len(recs))
    n_tr = int(0.8 * len(recs))
    tr_idx, te_idx = perm[:n_tr], perm[n_tr:]
    print(f"Loaded {len(recs)}; train={len(tr_idx)} test={len(te_idx)}")

    centers = gauss_centers()
    E = np.array([r["energy"] for r in recs])
    nat = np.array([r["n_atoms"] for r in recs])

    # build features (deterministic order)
    nfeat = 1 + NB + 2 * NB * NB
    X = np.zeros((len(recs), nfeat))
    for k in range(len(recs)):
        X[k] = structure_features(recs[k], centers)
    print("feature dim:", X.shape[1])

    A = X[tr_idx].T @ X[tr_idx] + LAM * np.eye(X.shape[1])
    b = X[tr_idx].T @ E[tr_idx]
    w = np.linalg.solve(A, b)
    Ep = X @ w

    def report(tag, idx):
        e = (Ep[idx] - E[idx]) / nat[idx]
        rmse = np.sqrt(np.mean(e ** 2)) * 1000.0
        mae = np.mean(np.abs(e)) * 1000.0
        print(f"{tag:8s} n={len(idx):6d}  energy RMSE={rmse:9.2f} meV/atom  MAE={mae:8.2f}")
        return rmse, mae

    r_tr, a_tr = report("train", tr_idx)
    r_te, a_te = report("test", te_idx)
    r_all, a_all = report("all", np.arange(len(recs)))

    row = {
        "model": "linear_2b3b_surrogate",
        "train_set": subset,
        "n_features": int(X.shape[1]),
        "cutoff_A": RC,
        "n_train": int(len(tr_idx)),
        "n_test": int(len(te_idx)),
        "energy_rmse_train_meV_atom": r_tr,
        "energy_mae_train_meV_atom": a_tr,
        "energy_rmse_test_meV_atom": r_te,
        "energy_mae_test_meV_atom": a_te,
        "energy_rmse_all_meV_atom": r_all,
        "energy_mae_all_meV_atom": a_all,
        "note": "2+3 body linear ridge surrogate (simplified MTP-like descriptor)",
    }
    df = pd.DataFrame([row])
    df.to_csv(os.path.join(OUT, "surrogate_rmse.csv"), index=False)
    np.save(os.path.join(OUT, "surrogate_weights.npy"), w)
    np.save(os.path.join(OUT, "surrogate_centers.npy"), centers)
    print("\nSaved", os.path.join(OUT, "surrogate_rmse.csv"))


if __name__ == "__main__":
    main()
