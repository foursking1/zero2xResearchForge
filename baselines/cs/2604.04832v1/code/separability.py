"""FDR / F2 / F3 separability metrics (one-vs-one) and FDR normalisation."""
from __future__ import annotations

import numpy as np
from scipy import stats

EPS = 1e-10

PAIR_DEFS = [
    ("paper_vs_scissors", 1, 2),
    ("rock_vs_paper", 0, 1),
    ("rock_vs_scissors", 0, 2),
]

# Paper Stage-1 targets (Fig. 4a).  Used only to *select* the normalisation
# method; the reproduced values are always our own computations.
PAPER_FDR_TARGETS = {
    "paper_vs_scissors": 0.073,
    "rock_vs_paper": 0.842,
    "rock_vs_scissors": 1.000,
}


def fdr_per_feature(fa: np.ndarray, fb: np.ndarray) -> np.ndarray:
    """Per-dimension one-vs-one FDR = (mu_a-mu_b)^2 / (var_a + var_b)."""
    ma = fa.mean(axis=0)
    mb = fb.mean(axis=0)
    va = fa.var(axis=0)
    vb = fb.var(axis=0)
    return (ma - mb) ** 2 / (va + vb + EPS)


def pairwise_fdr(fa: np.ndarray, fb: np.ndarray, agg: str = "max") -> float:
    """One-vs-one FDR aggregated over feature dimensions."""
    fdr = fdr_per_feature(fa, fb)
    if agg == "max":
        return float(np.max(fdr))
    if agg == "mean":
        return float(np.mean(fdr))
    raise ValueError(agg)


def f2_overlap_volume(fa: np.ndarray, fb: np.ndarray) -> float:
    """Product over dims of overlap/range (lower = better separability)."""
    min_a, max_a = fa.min(axis=0), fa.max(axis=0)
    min_b, max_b = fb.min(axis=0), fb.max(axis=0)
    overlap = np.maximum(0, np.minimum(max_a, max_b) - np.maximum(min_a, min_b))
    span = np.maximum(max_a, max_b) - np.minimum(min_a, min_b) + EPS
    return float(np.prod(overlap / span))


def f3_max_feature_efficiency(fa: np.ndarray, fb: np.ndarray) -> float:
    """max_k (1 - overlap_k/range_k) (higher = better separability)."""
    min_a, max_a = fa.min(axis=0), fa.max(axis=0)
    min_b, max_b = fb.min(axis=0), fb.max(axis=0)
    overlap = np.maximum(0, np.minimum(max_a, max_b) - np.maximum(min_a, min_b))
    span = np.maximum(max_a, max_b) - np.minimum(min_a, min_b) + EPS
    return float(np.max(1.0 - overlap / span))


# ---------------------------------------------------------------------------
# Normalisation
# ---------------------------------------------------------------------------
def normalize_minmax(values: dict[str, float]) -> dict[str, float]:
    v = np.array(list(values.values()), dtype=float)
    lo, hi = v.min(), v.max()
    if hi - lo < EPS:
        return {k: 0.5 for k in values}
    return {k: (x - lo) / (hi - lo) for k, x in values.items()}


def normalize_divide_max(values: dict[str, float]) -> dict[str, float]:
    hi = max(values.values())
    if hi < EPS:
        return {k: 0.0 for k in values}
    return {k: x / hi for k, x in values.items()}


def normalize_cap_at_1(values: dict[str, float]) -> dict[str, float]:
    return {k: min(x, 1.0) for k, x in values.items()}


NORMALIZERS = {
    "minmax": normalize_minmax,
    "divide_max": normalize_divide_max,
    "cap_at_1": normalize_cap_at_1,
}


def select_normalization(raw_fdr: dict[str, float]) -> dict:
    """Trial all 3 normalisations against the paper's Stage-1 targets.

    Returns a dict with each method's output, MAE, and the selected method.
    """
    out = {"raw": {k: float(v) for k, v in raw_fdr.items()}}
    for name, fn in NORMALIZERS.items():
        normed = fn(raw_fdr)
        mae = float(np.mean([abs(normed[k] - PAPER_FDR_TARGETS[k]) for k in PAPER_FDR_TARGETS]))
        out[name] = normed
        out[f"{name}_mae"] = mae
    out["selected_method"] = min(NORMALIZERS, key=lambda n: out[f"{n}_mae"])
    out["selected_values"] = out[out["selected_method"]]
    return out


# ---------------------------------------------------------------------------
# Full separability analysis
# ---------------------------------------------------------------------------
def analyze_separability(F: np.ndarray, Y: np.ndarray, pids: np.ndarray | None = None):
    """Compute all separability metrics for the three gesture pairs.

    Parameters
    ----------
    F : (N, D) feature matrix
    Y : (N,) labels (0=rock, 1=paper, 2=scissors)
    pids : optional (N,) participant ids for per-participant FDR
    """
    results = {}
    raw_fdr_max = {}
    raw_fdr_mean = {}
    best_feature = {}
    f2, f3 = {}, {}
    per_participant = {}

    for pair, la, lb in PAIR_DEFS:
        fa, fb = F[Y == la], F[Y == lb]

        fdr_max = pairwise_fdr(fa, fb, "max")
        fdr_mean = pairwise_fdr(fa, fb, "mean")
        raw_fdr_max[pair] = fdr_max
        raw_fdr_mean[pair] = fdr_mean

        per_feat = fdr_per_feature(fa, fb)
        best_idx = int(np.argmax(per_feat))
        best_feature[pair] = {"index": best_idx, "fdr": float(per_feat[best_idx])}

        f2[pair] = f2_overlap_volume(fa, fb)
        f3[pair] = f3_max_feature_efficiency(fa, fb)

        if pids is not None:
            per_participant[pair] = {}
            for pid in sorted(np.unique(pids)):
                ma = (Y == la) & (pids == pid)
                mb = (Y == lb) & (pids == pid)
                if ma.sum() > 1 and mb.sum() > 1:
                    per_participant[pair][str(pid)] = pairwise_fdr(F[ma], F[mb], "max")

    results["pairwise_fdr_max_raw"] = raw_fdr_max
    results["pairwise_fdr_mean_raw"] = raw_fdr_mean
    results["pairwise_fdr_best_feature"] = best_feature
    results["f2_overlap_volume"] = f2
    results["f3_max_feature_efficiency"] = f3
    results["normalization_max"] = select_normalization(raw_fdr_max)
    results["normalization_mean"] = select_normalization(raw_fdr_mean)
    results["per_participant_fdr_max"] = per_participant
    return results


def fdr_mcc_correlation(delta_fdr: list[float], delta_mcc: list[float]):
    """Pearson correlation between two lists."""
    a = np.asarray(delta_fdr, dtype=float)
    b = np.asarray(delta_mcc, dtype=float)
    if len(a) < 3 or np.std(a) < EPS or np.std(b) < EPS:
        return {"pearson_r": 0.0, "p_value": 1.0, "n": len(a)}
    r, p = stats.pearsonr(a, b)
    return {"pearson_r": float(r), "p_value": float(p), "n": len(a)}
