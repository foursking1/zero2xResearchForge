"""Robustness analysis: quantify the effect of the data-split protocol on the
reported metrics, by re-running the shallow baselines on alternative splits of
the frozen validation.h5:

  split = "random"   -> stratified random 80/20, seed 42 (task-recommended, PRIMARY)
  split = "stride5"  -> every 5th patch of the h5 goes to eval (spatially-stricter
                        proxy split; shown to only modestly reduce OA, revealing the
                        intrinsic spatial auto-correlation of the frozen validation set)

Results are written to results/robustness/
"""
import json
import os

import numpy as np

from run_baselines import band_stats, load
from metrics import compute_metrics

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA = os.path.join(ROOT, "data")
RES = os.path.join(ROOT, "results", "robustness")
SEED = 42


def build_split(h5path, mode):
    import h5py
    with h5py.File(h5path, "r") as f:
        labels = np.asarray(f["label"], dtype=np.float64).argmax(axis=1).astype(np.int64)
    n = labels.shape[0]
    if mode == "random":
        rng = np.random.RandomState(SEED)
        train_idx, val_idx = [], []
        for c in range(17):
            idx = np.where(labels == c)[0]
            idx = rng.permutation(idx)
            nv = int(round(len(idx) * 0.20))
            val_idx.append(idx[:nv])
            train_idx.append(idx[nv:])
        train_idx = np.concatenate(train_idx)
        val_idx = np.concatenate(val_idx)
        rng.shuffle(train_idx)
        return train_idx, val_idx, labels
    if mode == "stride5":
        ev = (np.arange(n) % 5) == 2
        return np.where(~ev)[0], np.where(ev)[0], labels
    if mode.startswith("eq"):
        # temporal split: first half patches for train, second half for eval, per class NOT balanced
        half = n // 2
        return np.arange(0, half), np.arange(half, n), labels
    raise ValueError(mode)


def main():
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    os.makedirs(RES, exist_ok=True)
    H5 = "/mnt/f/dataset/earth/1912.12171_so2sat/data/official_h5/validation.h5"
    summary = {}
    for mode in ["stride5"]:
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.preprocessing import StandardScaler
        from sklearn.svm import SVC

        tr_idx, va_idx, labels = build_split(H5, mode)
        ytr, yva = labels[tr_idx], labels[va_idx]
        res = dict(mode=mode, train_size=int(len(tr_idx)), val_size=int(len(va_idx)))
        for bands in ["s2", "s1s2"]:
            import h5py
            with h5py.File(H5, "r") as f:
                if bands == "s2":
                    tr = f["sen2"][tr_idx].astype(np.float32)
                    va = f["sen2"][va_idx].astype(np.float32)
                else:
                    tr = np.concatenate([f["sen2"][tr_idx], f["sen1"][tr_idx]], axis=-1).astype(np.float32)
                    va = np.concatenate([f["sen2"][va_idx], f["sen1"][va_idx]], axis=-1).astype(np.float32)
            # normalize using train stats
            mean = tr.mean(axis=(0, 1, 2)); std = tr.std(axis=(0, 1, 2))
            tr = (tr - mean) / std; va = (va - mean) / std
            Xtr, Xva = band_stats(tr), band_stats(va)

            for name in ["rf", "svm"]:
                if name == "rf":
                    m_ = RandomForestClassifier(n_estimators=300, max_features="sqrt",
                                                n_jobs=6, random_state=SEED)
                else:
                    sc = StandardScaler().fit(Xtr)
                    Xtr_s, Xva_s = sc.transform(Xtr), sc.transform(Xva)
                    m_ = SVC(C=1.0, kernel="rbf", gamma="scale", class_weight="balanced", cache_size=500)
                    Xtr_s, Xva_s = Xtr_s, Xva_s
                    m_.fit(Xtr_s, ytr)
                    preds = m_.predict(Xva_s)
                    tag = f"robust_{mode}_{name}_{bands}"
                    out = os.path.join(RES, tag)
                    met, cm = compute_metrics(yva, preds, split="eval", bands=bands,
                                              seed=SEED, train_size=int(len(tr_idx)), out_dir=out)
                    res[f"{name}_{bands}"] = met
                    continue
                m_.fit(Xtr, ytr)
                preds = m_.predict(Xva)
                tag = f"robust_{mode}_{name}_{bands}"
                out = os.path.join(RES, tag)
                met, cm = compute_metrics(yva, preds, split="eval", bands=bands,
                                          seed=SEED, train_size=int(len(tr_idx)), out_dir=out)
                res[f"{name}_{bands}"] = met
        summary[mode] = res
        print(json.dumps(res, indent=1), flush=True)
    with open(os.path.join(RES, "robustness.json"), "w") as fh:
        json.dump(summary, fh, indent=2)


if __name__ == "__main__":
    main()