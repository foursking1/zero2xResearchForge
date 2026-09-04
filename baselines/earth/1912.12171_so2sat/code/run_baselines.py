"""Shallow baselines: RBF-SVM / Random Forest / kNN on hand-crafted per-band
statistics and on a randomized-PCA projection of the raw spectral pixels.

These mirror the paper's SVM baseline (Table V, OA=0.54 S2) using only the
held-out 20% eval subset from the frozen validation split.
"""
import argparse
import json
import os
import time

import numpy as np
from sklearn.decomposition import PCA
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, cohen_kappa_score
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

from metrics import compute_metrics

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "results")
SEED = 42


def load(bands):
    tr_y = np.load(os.path.join(DATA, "train_y.npy"))
    va_y = np.load(os.path.join(DATA, "val_y.npy"))
    if bands == "s2":
        tr = np.load(os.path.join(DATA, "train_s2.npy"))
        va = np.load(os.path.join(DATA, "val_s2.npy"))
    else:
        tr = np.concatenate([np.load(os.path.join(DATA, "train_s2.npy")),
                             np.load(os.path.join(DATA, "train_s1.npy"))], axis=-1)
        va = np.concatenate([np.load(os.path.join(DATA, "val_s2.npy")),
                             np.load(os.path.join(DATA, "val_s1.npy"))], axis=-1)
    return tr, va, tr_y, va_y


def band_stats(x):
    n, h, w, c = x.shape
    xf = x.reshape(n, h * w, c)  # n x 1024 x c
    feat = np.concatenate([
        xf.mean(axis=1),
        xf.std(axis=1),
        xf.min(axis=1),
        xf.max(axis=1),
        np.quantile(xf, 0.25, axis=1),
        np.quantile(xf, 0.75, axis=1),
    ], axis=1)  # n x (6*c)
    return feat


def flatten_stats(x):
    # concatenation of mean/std only (n x 2c) used by the fast kNN/RF sanity check
    n, h, w, c = x.shape
    xf = x.reshape(n, h * w, c)
    return np.concatenate([xf.mean(axis=1), xf.std(axis=1)], axis=1)


def run_pca_svm(bands):
    tr, va, tr_y, va_y = load(bands)
    c = tr.shape[-1]
    trf = tr.reshape(len(tr), -1)
    vaf = va.reshape(len(va), -1)
    t0 = time.time()
    pca = PCA(n_components=min(120, trf.shape[1]), random_state=SEED, svd_solver="randomized")
    trp = pca.fit_transform(trf)
    vap = pca.transform(vaf)
    sc = StandardScaler().fit(trp)
    trp, vap = sc.transform(trp), sc.transform(vap)
    print(f"pca {bands}: {(time.time()-t0):.0f}s fit, explained var {pca.explained_variance_ratio_.sum():.3f}")
    clf = SVC(C=1.0, kernel="rbf", gamma="scale", class_weight="balanced", cache_size=500)
    t0 = time.time()
    clf.fit(trp, tr_y)
    print(f"svm fit {bands}: {(time.time()-t0):.0f}s", flush=True)
    preds = clf.predict(vap)
    oa = accuracy_score(va_y, preds)
    kappa = cohen_kappa_score(va_y, preds)
    print(f"[pca-svm {bands}] OA={oa:.4f} Kappa={kappa:.4f}")
    return "pca_svm_" + bands, preds


def run_stats_svm(bands):
    tr, va, tr_y, va_y = load(bands)
    trf = band_stats(tr)
    vaf = band_stats(va)
    sc = StandardScaler().fit(trf)
    clf = SVC(C=1.0, kernel="rbf", gamma="scale", class_weight="balanced", cache_size=500)
    t0 = time.time()
    clf.fit(sc.transform(trf), tr_y)
    print(f"stats-svm fit {bands}: {(time.time()-t0):.0f}s", flush=True)
    preds = clf.predict(sc.transform(vaf))
    oa = accuracy_score(va_y, preds)
    print(f"[stats-svm {bands}] OA={oa:.4f}")
    return "stats_svm_" + bands, preds


def run_rf(bands):
    tr, va, tr_y, va_y = load(bands)
    trf = band_stats(tr)
    vaf = band_stats(va)
    clf = RandomForestClassifier(n_estimators=300, max_features="sqrt", n_jobs=6,
                                 random_state=SEED, oob_score=False)
    t0 = time.time()
    clf.fit(trf, tr_y)
    print(f"rf fit {bands}: {(time.time()-t0):.0f}s", flush=True)
    preds = clf.predict(vaf)
    oa = accuracy_score(va_y, preds)
    print(f"[rf {bands}] OA={oa:.4f}")
    return "rf_" + bands, preds


def run_knn(bands):
    tr, va, tr_y, va_y = load(bands)
    trf = flatten_stats(tr)
    vaf = flatten_stats(va)
    sc = StandardScaler().fit(trf)
    clf = KNeighborsClassifier(n_neighbors=7, n_jobs=6)
    clf.fit(sc.transform(trf), tr_y)
    preds = clf.predict(sc.transform(vaf))
    oa = accuracy_score(va_y, preds)
    print(f"[knn {bands}] OA={oa:.4f}")
    return "knn_" + bands, preds


def main():
    os.makedirs(OUT, exist_ok=True)
    all_metrics = {}
    for name, fn in [("pca_svm_s2", lambda: run_pca_svm("s2")),
                     ("pca_svm_s1s2", lambda: run_pca_svm("s1s2")),
                     ("stats_svm_s2", lambda: run_stats_svm("s2")),
                     ("rf_s2", lambda: run_rf("s2")),
                     ("rf_s1s2", lambda: run_rf("s1s2")),
                     ("knn_s2", lambda: run_knn("s2"))]:
        tag, preds = fn()
        _, va, _, va_y = load(tag.split("_")[-1])
        od = os.path.join(OUT, tag)
        os.makedirs(od, exist_ok=True)
        bandsrc = "s1s2" if "s1s2" in tag else "s2"
        m, _ = compute_metrics(va_y, preds, split="eval", bands=bandsrc,
                               seed=SEED, train_size=int(np.load(os.path.join(DATA, "train_y.npy")).shape[0]),
                               out_dir=od)
        all_metrics[tag] = m
    with open(os.path.join(OUT, "baselines.json"), "w") as fh:
        json.dump(all_metrics, fh, indent=2)


if __name__ == "__main__":
    main()