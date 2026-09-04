"""02_baselines.py — PCA and 1-NN baselines (per-category AUROC).

Baselines follow paper Sec. V:
- PCA: linear subspace model on the z-scored 130-dim feature vectors pooled
  over training timesteps. Reconstruction error (per-sample mean over observed
  timesteps) is the anomaly score. Number of components chosen by
  explained-variance threshold on TRAINING data ONLY (no test labels used).
- 1-NN: nearest training sample under the '\u2113'_1 distance averaged over the
  observed timesteps (paper describes the 1-NN baseline with L1 distance).

Evaluation: per-category AUROC, 12-class mean, silver protocol from
paper Sec. V-A (each class's anomaly samples vs all 419 test-normal samples).

Usage: python 02_baselines.py   (reads the cached arrays from data/)
"""
import argparse
import json
import os
import time

import numpy as np

import common

OUT_RESULTS = os.path.join(common.BASE, "results")
os.makedirs(OUT_RESULTS, exist_ok=True)


def pca_scores(Xn, lengths, train_mask, test_mask, var_thresholds=(0.90, 0.95, 0.975)):
    """PCA with n_components from an explained-variance threshold.

    Returns dict threshold -> per-sample anomaly score (mean squared
    reconstruction error over observed timesteps).
    """
    tr = Xn[train_mask].reshape(-1, 130)
    Xt = Xn[test_mask]
    lt = lengths[test_mask]
    test_idx = np.where(test_mask)[0]

    # Center with training mean (already z-scored, but PCA centers its data).
    tr_c = tr - tr.mean(axis=0)
    Xtc = Xt - tr.mean(axis=0)

    U, s, Vt = np.linalg.svd(tr_c, full_matrices=False)
    var_expl = np.cumsum(s ** 2) / np.sum(s ** 2)

    scores = {}
    comps_used = {}
    for th in var_thresholds:
        k = int(np.searchsorted(var_expl, th) + 1)
        k = min(k, 130)
        comps_used[th] = k
        Vk = Vt[:k]
        # reconstruction error per timestep
        recon = (Xtc @ Vk.T) @ Vk
        err = ((Xtc - recon) ** 2).sum(axis=1)  # (n_test, T)
        full = np.full(Xn.shape[0], np.nan)
        for i, L in enumerate(lt):
            full[test_idx[i]] = err[i, :L].mean()
        scores[th] = full
    return scores, comps_used


def knn_scores(Xn, lengths, train_idx, test_idx, chunk_time=32, chunk_test=16):
    """1-NN anomaly score: distance to the nearest training sample.

    Distance = mean over observed timesteps of the L1 (sum over features) gap.
    Uses zero-padding aware masking; padded (unobserved) parts contribute 0.
    """
    Xtr = Xn[train_idx]
    Ltr = lengths[train_idx]
    n_train = Xtr.shape[0]
    scores = np.zeros(len(test_idx))
    for ii, ti in enumerate(test_idx):
        seg = Xn[ti]
        L = lengths[ti]
        acc = np.zeros(n_train, dtype=np.float64)
        n_obs = np.minimum(Ltr, L).astype(np.float64)
        for t0 in range(0, L, chunk_time):
            t1 = min(t0 + chunk_time, L)
            w = t1 - t0
            block = np.abs(seg[t0:t1, None, :].astype(np.float64) - Xtr[:, t0:t1, :].astype(np.float64))
            # mask unobserved train timesteps (padded zeros)
            mask = (np.arange(t0, t1)[None, :] < Ltr[:, None]).astype(np.float64)
            acc += (block.sum(axis=2) * mask).sum(axis=1)
        scores[ii] = float(np.min(acc / n_obs))
    return scores


def _knn_worker(args_in):
    """Compute 1-NN anomaly score for a subset of test samples."""
    idxs = args_in
    from joblib import Parallel, delayed
    scores = np.zeros(len(idxs))
    for b, ti in enumerate(idxs):
        segB = _Xn[ti]
        L = _lengths[ti]
        acc = np.zeros(_n_train, dtype=np.float64)
        n_obs = np.minimum(_Ltr, L).astype(np.float64)
        for t0 in range(0, L, 32):
            t1 = min(t0 + 32, L)
            diff = np.abs(segB[None, t0:t1, :].astype(np.float32)
                          - _Xtr[:, t0:t1, :].astype(np.float32))
            mask = (np.arange(t0, t1)[None, :] < _Ltr[:, None])
            acc += (diff.sum(axis=2) * mask).sum(axis=1)
        scores[b] = float(np.min(acc / n_obs))
    return idxs, scores


_Xn, _Xtr, _Ltr, _lengths, _n_train = [None] * 5


def knn_scores_batch(Xn, lengths, train_idx, test_idx, workers=8):
    """1-NN anomaly score (L1 over features, averaged over observed timesteps).

    Parallel over test samples using multiprocessing (fork).
    """
    global _Xn, _Xtr, _Ltr, _lengths, _n_train
    _Xn = Xn
    _Xtr = Xn[train_idx]
    _Ltr = lengths[train_idx]
    _lengths = lengths
    _n_train = _Xtr.shape[0]

    chunks = np.array_split(test_idx, workers)
    from concurrent.futures import ProcessPoolExecutor
    scores = np.full(Xn.shape[0], np.nan)
    with ProcessPoolExecutor(max_workers=workers) as ex:
        for idxs, s in ex.map(_knn_worker, chunks):
            for i, gi in enumerate(idxs):
                scores[gi] = s[i]
    return scores


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--var-threshold", type=float, default=0.975,
                    help="explained-variance threshold for PCA (train-data only)")
    ap.add_argument("--workers", type=int, default=8,
                    help="worker processes for 1-NN")
    args = ap.parse_args()

    d = common.load_cache()
    Xn = d["Xn"]
    lengths = d["lengths"]
    setting = d["setting"]
    anomaly = d["anomaly"].astype(bool)
    category = d["category"]
    train_mask, test_mask = common.get_train_test_masks(setting)
    train_idx = np.where(train_mask)[0]
    test_idx = np.where(test_mask)[0]

    t0 = time.time()
    scores_pca, comps = pca_scores(Xn, lengths, train_mask, test_mask,
                                   var_thresholds=(0.90, 0.95, 0.975))
    print(f"[pca] done in {time.time() - t0:.1f}s, n_components by var: {comps}")

    t1 = time.time()
    scores_knn = knn_scores_batch(Xn, lengths, train_idx, test_idx, workers=args.workers)
    print(f"[1-nn] done in {time.time() - t1:.1f}s")

    for th, s in scores_pca.items():
        print(f"[pca th={th}] mean per-cat AUROC: "
              f"{np.nanmean(list(common.evaluate_method(s, anomaly, category, test_mask).values())):.3f}")

    # final config: threshold from CLI
    th_use = args.var_threshold
    pick = min(comps, key=lambda k: abs(k - th_use))
    th_use = pick
    score_pca = scores_pca[th_use]
    score_knn = scores_knn

    auc_pca = common.evaluate_method(score_pca, anomaly, category, test_mask)
    auc_knn = common.evaluate_method(score_knn, anomaly, category, test_mask)

    print(f"\n[n_components used for REPORT] th={comps} (chosen {th_use} -> {comps[th_use]} comps)")

    rows = []
    for cat in range(12):
        pos = np.where(test_mask & anomaly & (category == cat))[0]
        rows.append({
            "category_id": cat,
            "category_name": common.CATEGORY_NAMES[cat],
            "n_anomaly": int(len(pos)),
            "auroc_pca": round(auc_pca[cat], 4),
            "auroc_1nn": round(auc_knn[cat], 4),
        })
    import pandas as pd
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(OUT_RESULTS, "baseline_table.csv"), index=False)
    print(df.to_string(index=False))

    res = {
        "pca_n_components_by_var": {str(k): int(v) for k, v in comps.items()},
        "pca_chosen_threshold": th_use,
        "pca_mean_auroc": round(float(np.nanmean(list(auc_pca.values()))), 4),
        "knn_mean_auroc": round(float(np.nanmean(list(auc_knn.values()))), 4),
        "per_category_pca": {int(k): round(float(v), 4) for k, v in auc_pca.items()},
        "per_category_1nn": {int(k): round(float(v), 4) for k, v in auc_knn.items()},
    }
    with open(os.path.join(OUT_RESULTS, "baseline_results.json"), "w") as f:
        json.dump(res, f, indent=2)
    print(f"\nsaved -> {OUT_RESULTS}/baseline_results.json")
    print(f"[time] total {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()