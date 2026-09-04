"""MLP validation oracle with participant-aware GroupKFold CV.

Uses scikit-learn's MLPClassifier and MCC as in the paper.  Feature
standardisation is fitted on the training folds only (no leakage).
"""
from __future__ import annotations

import numpy as np
from sklearn.model_selection import GroupKFold
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import matthews_corrcoef

from separability import PAIR_DEFS

# Paper Stage-1 MLP targets (Fig. 4b).  Used only to pick the architecture.
PAPER_MCC_TARGETS = {
    "paper_vs_scissors": 0.872,
    "rock_vs_paper": 0.990,
    "rock_vs_scissors": 1.000,
}

ARCHITECTURES = [(64,), (32, 16), (16, 8), (128, 64, 32)]


def pairwise_mcc(y_true: np.ndarray, y_pred: np.ndarray, la: int, lb: int) -> float:
    mask = (y_true == la) | (y_true == lb)
    if mask.sum() < 4:
        return 0.0
    yt = (y_true[mask] == la).astype(int)
    yp = (y_pred[mask] == la).astype(int)
    if len(np.unique(yt)) < 2 or len(np.unique(yp)) < 2:
        return 0.0
    return float(matthews_corrcoef(yt, yp))


def group_kfold_mlp(F: np.ndarray, Y: np.ndarray, pids: np.ndarray,
                    hidden_layers: tuple = (32, 16), n_splits: int = 10,
                    max_iter: int = 1000, random_state: int = 42,
                    standardize: bool = True) -> dict:
    """GroupKFold (10 participants) MLP; returns fold and aggregate MCC.

    Returns
    -------
    dict with 'fold_results' (list), 'overall_pairwise_mcc',
    'mean_pairwise_mcc' / 'std_pairwise_mcc' (over folds) and more.
    """
    gkf = GroupKFold(n_splits=n_splits)
    fold_results = []
    all_preds = np.zeros(len(Y), dtype=int)

    for fold_idx, (tr_idx, te_idx) in enumerate(gkf.split(F, Y, groups=pids)):
        tr_pids, te_pids = np.unique(pids[tr_idx]), np.unique(pids[te_idx])
        overlap = len(set(tr_pids) & set(te_pids))
        assert overlap == 0, "participant overlap in train/test!"

        X_tr, X_te = F[tr_idx], F[te_idx]
        if standardize:
            scaler = StandardScaler().fit(X_tr)
            X_tr = scaler.transform(X_tr)
            X_te = scaler.transform(X_te)

        clf = MLPClassifier(
            hidden_layer_sizes=hidden_layers, activation="relu", solver="adam",
            max_iter=max_iter, random_state=random_state + fold_idx,
            early_stopping=True, validation_fraction=0.15, n_iter_no_change=20,
        )
        clf.fit(X_tr, Y[tr_idx])
        y_pred = clf.predict(X_te)
        all_preds[te_idx] = y_pred

        pairwise = {p: pairwise_mcc(Y[te_idx], y_pred, la, lb)
                    for p, la, lb in PAIR_DEFS}
        fold_results.append({
            "fold": fold_idx,
            "test_participants": [int(x) for x in te_pids],
            "n_test": int(len(te_idx)),
            "overall_mcc": float(matthews_corrcoef(Y[te_idx], y_pred)),
            "pairwise_mcc": pairwise,
        })

    mean_pairwise = {p: float(np.mean([f["pairwise_mcc"][p] for f in fold_results]))
                     for p, _, _ in PAIR_DEFS}
    std_pairwise = {p: float(np.std([f["pairwise_mcc"][p] for f in fold_results]))
                    for p, _, _ in PAIR_DEFS}

    return {
        "architecture": list(hidden_layers),
        "n_splits": n_splits,
        "overall_mcc": float(matthews_corrcoef(Y, all_preds)),
        "overall_pairwise_mcc": {p: pairwise_mcc(Y, all_preds, la, lb)
                                 for p, la, lb in PAIR_DEFS},
        "mean_pairwise_mcc": mean_pairwise,
        "std_pairwise_mcc": std_pairwise,
        "fold_results": fold_results,
    }


def architecture_sweep(F: np.ndarray, Y: np.ndarray, pids: np.ndarray,
                       architectures: list[tuple] | None = None,
                       random_state: int = 42) -> dict:
    """Sweep MLP architectures; best = lowest MAE vs paper MCC targets."""
    architectures = architectures or ARCHITECTURES
    out = {}
    for arch in architectures:
        res = group_kfold_mlp(F, Y, pids, arch, random_state=random_state)
        res["mae_vs_paper"] = float(np.mean([
            abs(res["mean_pairwise_mcc"][k] - PAPER_MCC_TARGETS[k])
            for k in PAPER_MCC_TARGETS
        ]))
        out[str(arch)] = res
    best = min(out, key=lambda a: out[a]["mae_vs_paper"])
    return {"architectures": out, "best_architecture": best,
            "best_results": out[best]}
