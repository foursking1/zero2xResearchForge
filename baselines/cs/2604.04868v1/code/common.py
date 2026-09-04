"""Common helpers for the frozen-data analysis of arXiv 2604.04868v1.

This module loads the FROZEN reproduction outputs (results/*.json) produced by the
reference reproduction pipeline, and provides utilities to (a) locate the frozen
files, (b) regenerate the deterministic synthetic baseline data (sklearn
make_classification with the same seed/method as the reference) to recover the
TRUE informative-feature positions, and (c) shared metric helpers.

No internet access, no external datasets, no TabPFN model weights are required:
every number used for claim verification is either read from a frozen JSON file
or recomputed from a frozen figure / deterministic data generator.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np
from sklearn.datasets import make_classification
from sklearn.metrics import roc_auc_score

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
# Frozen data root (in-place; do NOT copy large files)
FROZEN_ROOT = Path(r"F:/dataset/2604.04868v1")
RESULTS_DIR = FROZEN_ROOT / "results"

# Output location of this solution (agent_solution/)
SOLUTION_ROOT = Path(__file__).resolve().parents[1]
OUT_RESULTS = SOLUTION_ROOT / "results"
OUT_FIGURES = OUT_RESULTS / "figures"

# Reference data-generation configuration used by the reproduction pipeline
# (see code/src/data/synthetic_generator.py)
DATA_KW = dict(
    n_samples=1500,
    n_features=8,
    n_informative=2,
    n_redundant=0,
    n_repeated=0,
    n_classes=2,
    n_clusters_per_class=1,
    class_sep=1.0,
    flip_y=0.01,
    random_state=42,
)


def load_json(rel_path: str | os.PathLike) -> dict:
    """Load a frozen JSON result file relative to the results/ directory."""
    p = RESULTS_DIR / rel_path
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Ground-truth informative feature positions
# ---------------------------------------------------------------------------
class _RecordingRS(np.random.RandomState):
    """RandomState subclass that records every in-place ``shuffle`` argument.

    sklearn's make_classification performs a final ``generator.shuffle(indices)``
    to randomly permute the feature columns; the post-shuffle ``indices`` array
    tells us exactly which raw feature columns are the informative ones
    (``indices[i] < n_informative`` means feature column ``i`` is informative).
    """

    def __init__(self, seed: int):
        super().__init__(seed)
        self.shuffles: list[np.ndarray] = []

    def shuffle(self, x):
        out = super().shuffle(x)
        self.shuffles.append(np.array(x, copy=True))
        return out


def informative_positions(
    n_features: int = 8,
    n_informative: int = 2,
    n_redundant: int = 0,
    n_samples: int = 1500,
    random_state: int = 42,
) -> list[int]:
    """Recover the TRUE informative feature columns for a make_classification call.

    This mirrors exactly the data generator used by the reference reproduction
    (shuffle=True, default), i.e. the column order returned by
    ``make_classification`` is ``X[:, indices]`` where ``indices`` is the final
    feature permutation.  Features ``i`` with ``indices[i] < n_informative`` are
    informative.

    NOTE: ``n_samples`` MUST match the experiment's sample count because the
    number of RNG draws consumed before the final feature shuffle depends on it
    (with a fixed seed, different n_samples yield different informative
    positions).
    """
    rs = _RecordingRS(random_state)
    make_classification(
        n_samples=n_samples,
        n_features=n_features,
        n_informative=n_informative,
        n_redundant=n_redundant,
        n_repeated=0,
        n_classes=2,
        n_clusters_per_class=1,
        class_sep=1.0,
        flip_y=0.01,
        shuffle=True,
        random_state=rs,
    )
    indices = rs.shuffles[-1]  # last shuffle = feature permutation
    return sorted(int(i) for i in range(n_features) if indices[i] < n_informative)


def baseline_data(n_train: int = 1200, n_test: int = 300):
    """Regenerate the deterministic baseline data (same seed as reference)."""
    kw = dict(DATA_KW)
    kw.pop("n_samples", None)
    X, y = make_classification(
        n_samples=n_train + n_test,
        n_features=kw["n_features"],
        n_informative=kw["n_informative"],
        n_redundant=kw["n_redundant"],
        n_repeated=kw["n_repeated"],
        n_classes=kw["n_classes"],
        n_clusters_per_class=kw["n_clusters_per_class"],
        class_sep=kw["class_sep"],
        flip_y=kw["flip_y"],
        random_state=kw["random_state"],
    )
    return X[:n_train], X[n_train:], y[:n_train], y[n_train:]


# ---------------------------------------------------------------------------
# Metric helpers
# ---------------------------------------------------------------------------
def kl_vs_uniform(p: np.ndarray) -> float:
    """KL( p || uniform ) for a normalized distribution p."""
    p = np.asarray(p, dtype=float)
    p = p / p.sum()
    k = len(p)
    u = np.full(k, 1.0 / k)
    return float(np.sum(p * np.log(p / (u + 1e-12) + 1e-12)))


def gini(p: np.ndarray) -> float:
    """Gini coefficient of a non-negative distribution (0 = uniform, 1 = concentrated)."""
    p = np.asarray(p, dtype=float)
    p = p / p.sum()
    s = np.sort(p)
    n = len(p)
    cum = np.cumsum(s)
    return float((n + 1 - 2 * np.sum(cum) / cum[-1]) / n)


def share_of(p: np.ndarray, indices: list[int]) -> float:
    """Fraction of total mass contained in the given indices."""
    p = np.asarray(p, dtype=float)
    return float(p[list(indices)].sum() / p.sum())


def univariate_aucs(X: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Per-column univariate ROC-AUC (robust; handles ties via try/except)."""
    aucs = []
    for i in range(X.shape[1]):
        try:
            aucs.append(roc_auc_score(y, X[:, i]))
        except ValueError:
            aucs.append(float("nan"))
    return np.asarray(aucs)
