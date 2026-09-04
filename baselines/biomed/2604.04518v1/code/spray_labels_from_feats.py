"""Cluster battery + label derivation from SAVED SpRAy features.

Loads workspace/spray_features/{ds}_{poison}/l{layer}.npy and runs a battery
of clustering methods, reporting per-class q-accuracy and the per-group label
accuracy used in Table 4 / R08.  Also writes the canonical q_hat + metrics
using the selected method (default: kmeans2_z).

Usage:
    python spray_labels_from_feats.py <dataset> <poison> <layer> [method]
"""
import json
import os
import sys

import numpy as np

from config import SEED, WORKSPACE
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans, SpectralClustering, DBSCAN
from sklearn.metrics import accuracy_score

METHODS = ("km2", "km2raw", "km4", "spectral_nn", "spectral_rbf", "dbscan")


def cluster_and_map(a, qc, method):
    a_z = StandardScaler().fit_transform(a)
    n = len(a)
    if method == "km2":
        lab = KMeans(n_clusters=2, random_state=SEED, n_init=10).fit_predict(a_z)
    elif method == "km2raw":
        lab = KMeans(n_clusters=2, random_state=SEED, n_init=10).fit_predict(a)
    elif method == "km4":
        lab = KMeans(n_clusters=4, random_state=SEED, n_init=10).fit_predict(a_z)
    elif method == "spectral_nn":
        lab = SpectralClustering(n_clusters=2, random_state=SEED,
                                 affinity="nearest_neighbors",
                                 assign_labels="kmeans").fit_predict(a_z)
    elif method == "spectral_rbf":
        lab = SpectralClustering(n_clusters=2, random_state=SEED,
                                 affinity="rbf", assign_labels="kmeans").fit_predict(a_z)
    elif method == "dbscan":
        lab = DBSCAN(eps=3.0, min_samples=5).fit_predict(a_z)
    else:
        raise ValueError(method)
    q_hat = np.zeros(n, dtype=int)
    for c in np.unique(lab):
        if c == -1:
            continue
        sub = lab == c
        q_hat[sub] = 1 if qc[sub].mean() >= 0.5 else 0
    return q_hat, lab


def main(dataset, poison, layer, select=None):
    feat_dir = os.path.join(WORKSPACE, "spray_features", f"{dataset}_{poison}")
    attr = np.load(os.path.join(feat_dir, f"l{layer}.npy"))
    meta = np.load(os.path.join(feat_dir, f"l{layer}_meta.npy"))
    t = meta[:, 0].astype(int)
    g = meta[:, 1].astype(int)
    q_true = g % 2
    print(f"=== {dataset}-{poison} layer {layer} attr {attr.shape} ===", flush=True)
    for method in METHODS:
        qc_accs = []
        for cl in np.unique(t):
            idx = np.where(t == cl)[0]
            qc = q_true[idx]
            if qc.sum() == 0 or qc.sum() == len(qc):
                continue
            q_hat, _ = cluster_and_map(attr[idx], qc, method)
            qc_accs.append(accuracy_score(qc, q_hat))
        q_hat_all, _ = cluster_and_map(attr, q_true, method)
        pga = [float((q_hat_all[g == grp] == q_true[g == grp]).mean())
               if (g == grp).sum() else float("nan") for grp in range(4)]
        print(f"  {method:12s} q-acc-per-class={[round(a,3) for a in qc_accs]} "
              f"per_group={[round(v,3) for v in pga]} "
              f"mean={np.nanmean(pga):.3f}", flush=True)
    if select is None:
        select = "km2"
    q_hat, _ = cluster_and_map(attr, q_true, select)
    pga = [float((q_hat[g == grp] == q_true[g == grp]).mean())
           if (g == grp).sum() else float("nan") for grp in range(4)]
    out_dir = os.path.join(WORKSPACE, "spray_labels", f"{dataset}_{poison}")
    os.makedirs(out_dir, exist_ok=True)
    torch = __import__("torch")
    torch.save({"q_hat": torch.from_numpy(q_hat),
                "targets": torch.from_numpy(t),
                "groups": torch.from_numpy(g),
                "method": select},
               os.path.join(out_dir, f"labels_l{layer}.pt"))
    json.dump({"dataset": dataset, "poison": poison, "layer": layer,
               "method": select, "per_group_acc": pga,
               "mean_acc": float(np.nanmean(pga))},
              open(os.path.join(out_dir, f"metrics_l{layer}.json"), "w"),
              indent=2)
    print(f"WROTE labels_l{layer}.pt method={select} "
          f"per_group={[round(v,3) for v in pga]} mean={np.nanmean(pga):.3f}",
          flush=True)


if __name__ == "__main__":
    sel = sys.argv[4] if len(sys.argv) > 4 else None
    main(sys.argv[1], sys.argv[2], int(sys.argv[3]), sel)
