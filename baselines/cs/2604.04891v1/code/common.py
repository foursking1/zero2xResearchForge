"""Shared utilities for the claim-verification analysis of arXiv:2604.04891v1.

Data is read in place from the frozen dataset at F:\\dataset\\2604.04891v1
(no copying of large files).  This module only defines pure helpers used by
verify_static.py and verify_flow.py.
"""
from __future__ import annotations

import os
from pathlib import Path

import numpy as np

# Frozen dataset root (original location, read in place).
DATA_ROOT = Path(os.environ.get("PAPER_DATA_ROOT", r"F:\dataset\2604.04891v1"))
STATIC_NPZ = DATA_ROOT / "results" / "static_couplings.npz"
FLOW_NPZ = DATA_ROOT / "results" / "mmd_flows.npz"

SEED = 1234
N = 200


def load_static() -> dict[str, np.ndarray]:
    """Load the frozen static-coupling artifacts."""
    with np.load(STATIC_NPZ, allow_pickle=True) as z:
        return {k: z[k] for k in z.files}


def load_flow() -> dict[str, np.ndarray]:
    """Load the frozen MMD-flow artifacts (initial/target clouds + loss curves)."""
    with np.load(FLOW_NPZ, allow_pickle=True) as z:
        return {k: z[k] for k in z.files}


def displacement_covariance(P: np.ndarray, X: np.ndarray, Y: np.ndarray) -> np.ndarray:
    """Sigma(P) = sum_{ij} P_ij (y_j - x_i)(y_j - x_i)^T in R^{2x2}."""
    n, m = P.shape
    diff = Y[None, :, :] - X[:, None, :]  # (n, m, 2)
    S = np.zeros((2, 2))
    for a in range(2):
        for b in range(2):
            S[a, b] = np.sum(P * diff[:, :, a] * diff[:, :, b])
    return S


def schatten_norm(S: np.ndarray, p) -> float:
    """Schatten p-norm of a symmetric 2x2 PSD matrix S.

    p=1 -> trace, p=2 -> Frobenius, p=inf -> largest eigenvalue (operator norm).
    """
    if p == 1:
        return float(np.trace(S))
    if p == 2:
        return float(np.linalg.norm(S, "fro"))
    if p in (np.inf, float("inf")):
        # lambda_max of a symmetric matrix
        return float(np.linalg.eigvalsh(S)[-1])
    raise ValueError(f"unsupported p={p}")


def plan_feasibility(P: np.ndarray, n: int, m: int) -> dict:
    """Check whether P is a feasible coupling: P>=0, P 1 = a, P^T 1 = b."""
    a = np.full(n, 1.0 / n)
    b = np.full(m, 1.0 / m)
    row = P.sum(axis=1)
    col = P.sum(axis=0)
    return {
        "min_entry": float(P.min()),
        "max_row_err": float(np.abs(row - a).max()),
        "max_col_err": float(np.abs(col - b).max()),
        "total_mass": float(P.sum()),
    }


def perm_from_plan(P: np.ndarray) -> np.ndarray:
    """Extract a permutation from a coupling by greedy assignment on -P."""
    from scipy.optimize import linear_sum_assignment

    rows, cols = linear_sum_assignment(-P)
    perm = np.empty(len(rows), dtype=int)
    perm[rows] = cols
    return perm


def plan_agreement(P1: np.ndarray, P2: np.ndarray, tol: float = 1e-9) -> dict:
    """Quantify how different two couplings are."""
    diff = P1 - P2
    return {
        "max_abs_diff": float(np.abs(diff).max()),
        "fro_diff": float(np.linalg.norm(diff, "fro")),
        "l1_diff": float(np.abs(diff).sum()),
        "mass_agree_tol": float(np.sum(np.abs(diff) <= tol) / diff.size),
    }
