"""Cluster battery: compare clustering methods for SpRAy label derivation.

Computes grad*act attributions for layers 6 and 12 in ONE forward+backward
pass per batch (same math as spray.py but multi-layer), saves the features,
then evaluates several clustering strategies against true q labels:

  * KMeans on z-scored features (n_clusters=2)
  * KMeans on raw features (n_clusters=2)
  * KMeans over-clustering (n_clusters=4) + merge by majority
  * SpectralClustering (nearest_neighbors, assign_labels=kmeans) on z-features
  * SpectralClustering (rbf affinity) on z-features
  * DBSCAN on z-features

Reports per-class q accuracy (like debug_spray2) AND the per-group label
accuracy used in Table 4 / R08 (like spray.py).
"""
import os
import numpy as np
import torch

from config import SEED, WORKSPACE
from corrections import load_split, split_root
from models import make_resnet18
from debug_spray2 import all_layers_attr, featurize

from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans, SpectralClustering, DBSCAN
from sklearn.metrics import accuracy_score


def cluster_and_map(a, qc, method):
    """Return q_hat by clustering features a (rows=samples) and mapping each
    cluster to q by majority vote of true qc."""
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
            # noise -> leave as 0 (not used for mapping in paper pipeline)
            continue
        sub = lab == c
        if qc[sub].mean() >= 0.5:
            q_hat[sub] = 1
    return q_hat, lab


def per_group_acc(q_hat, g, q_true):
    vals = []
    for grp in range(4):
        m = g == grp
        vals.append(float((q_hat[m] == q_true[m]).mean()) if m.sum() else float("nan"))
    return vals


def main():
    root = split_root("squares", "symmetric")
    train, val, test = load_split(root)
    model = make_resnet18(2, SEED)
    model.load_state_dict(torch.load(
        os.path.join(WORKSPACE, "models", "students", "squares_symmetric",
                     "best.pt"), weights_only=False))
    x = torch.cat([train["images"], val["images"]])
    targets = torch.cat([train["targets"], val["targets"]])
    groups = torch.cat([train["groups"], val["groups"]])
    t = targets.numpy(); g = groups.numpy(); q_true = g % 2
    print("computing attributions...", flush=True)
    attrs, preds = all_layers_attr(model, x)
    feat_dir = os.path.join(WORKSPACE, "spray_features", "squares_symmetric")
    os.makedirs(feat_dir, exist_ok=True)
    for layer in (6, 12):
        attr = featurize(attrs[layer - 1])
        np.save(os.path.join(feat_dir, f"l{layer}.npy"), attr)
        np.save(os.path.join(feat_dir, f"l{layer}_meta.npy"),
                np.stack([t, g, q_true], 1))
        print(f"=== layer {layer} attr {attr.shape} ===", flush=True)
        for method in ("km2", "km2raw", "km4", "spectral_nn", "spectral_rbf", "dbscan"):
            qc_accs, pga = [], []
            for cl in np.unique(t):
                idx = np.where(t == cl)[0]
                qc = q_true[idx]
                if qc.sum() == 0 or qc.sum() == len(qc):
                    continue
                q_hat, lab = cluster_and_map(attr[idx], qc, method)
                qc_accs.append(accuracy_score(qc, q_hat))
            q_hat_all, _ = cluster_and_map(attr, q_true, method)
            pga = per_group_acc(q_hat_all, g, q_true)
            print(f"  {method:12s} q-acc-per-class={[round(a,3) for a in qc_accs]} "
                  f"per_group={[round(v,3) for v in pga]} "
                  f"mean={np.nanmean(pga):.3f}", flush=True)


if __name__ == "__main__":
    main()
