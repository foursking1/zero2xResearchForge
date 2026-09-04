"""C03b: VGT-dot clustering on the real agent token embeddings.

The reproduction workspace ships 500 token embeddings (64-d) extracted from a
Transformer-XL agent playing the SimpleGrid-STL-v0 "eventually" task.  The
frozen `stratification_analysis.py` clustered these with a scalar VGT-dot
feature (mean of the derivative), and stored `cluster_labels.npy`.  That
reference implementation has a buggy radius grid (see `vgt.py` header), and the
scalar feature is shown here to be essentially constant over the cloud
(mean ~0.32, std ~0.01), i.e. not discriminative.

We reproduce the analysis with the *corrected* VGT (from `vgt.py`) using the
derivative *curve* over a restricted scale window as the clustering feature,
and compare against the frozen cluster labels.  We also measure the intrinsic
dimension of each stratum to characterise the local-to-global structure.

Question: does VGT-dot provide an informative clustering of the real
embeddings (C03)?
"""
import os
import json
import sys

import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score
from sklearn.decomposition import PCA

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import load_embeddings, load_cluster_labels  # noqa: E402
import vgt as vgt_impl  # noqa: E402

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")


def vgt_dot_curve_feature(X, n_radii=48, smoothing_window=5, seed=0,
                          scale_lo=None, scale_hi=None):
    """Standardised VGT-dot derivative curve over a scale window."""
    res = vgt_impl.vgt_dot_features(X, n_radii=n_radii,
                                    smoothing_window=smoothing_window, seed=seed)
    derivs = res["derivatives"]
    radii = res["radii"]
    if scale_lo is None:
        scale_lo = radii[2]
    if scale_hi is None:
        scale_hi = radii[40]
    mask = (radii >= scale_lo) & (radii <= scale_hi)
    feat = derivs[:, mask]
    feat = (feat - feat.mean(axis=0)) / (feat.std(axis=0) + 1e-12)
    return feat, res, mask


def cluster_by_time_stats(cl, ts):
    return {int(c): {
        "n": int((cl == c).sum()),
        "time_mean": float(ts[cl == c].mean()),
        "time_min": int(ts[cl == c].min()),
        "time_max": int(ts[cl == c].max()),
    } for c in np.unique(cl)}


def main():
    emb, ts = load_embeddings()
    cl_frozen = load_cluster_labels()

    radii, dia = vgt_impl.compute_radii(emb, n_radii=48, r_min_frac=1e-3,
                                        r_max_frac=1.0, seed=0)

    # scalar VGT-dot (the frozen feature)
    res_scalar = vgt_impl.vgt_dot_features(emb, n_radii=48, smoothing_window=5, seed=0)
    f_scalar = res_scalar["features"]

    # corrected curve feature
    feat, res, mask = vgt_dot_curve_feature(emb, n_radii=48, smoothing_window=5,
                                            scale_lo=radii[4], scale_hi=radii[40])

    # local intrinsic dimension (corrected VGT)
    lds, _ = vgt_impl.local_dim_all(emb, radii=radii, r_lo=radii[4], r_hi=radii[20],
                                    seed=0)

    # ---- k-means on the curve feature (k=3) ----
    km = KMeans(n_clusters=3, n_init=10, random_state=0)
    cl_vgt = km.fit_predict(feat)
    ari_vs_frozen = adjusted_rand_score(cl_frozen, cl_vgt)

    # temporal structure of the VGT-dot clusters
    ts_by_cl = cluster_by_time_stats(cl_vgt, ts)

    # overlap with the frozen early-time cluster (cluster 1, 60 pts, t<=9)
    frozen_early = (cl_frozen == 1)
    overlap = None
    best_ov = -1
    for c in np.unique(cl_vgt):
        ov = int((frozen_early & (cl_vgt == c)).sum())
        if ov > best_ov:
            best_ov = ov
            overlap = int(c)
    jaccard = best_ov / int((frozen_early | (cl_vgt == overlap)).sum())

    # per-cluster local dimension
    ld_by_cl = {int(c): {
        "local_dim_mean": float(np.nanmean(lds[cl_vgt == c])),
        "local_dim_std": float(np.nanstd(lds[cl_vgt == c])),
    } for c in np.unique(cl_vgt)}

    # scalar feature is almost constant -> not discriminative
    summary = {
        "n_embeddings": int(len(emb)),
        "embedding_dim": int(emb.shape[1]),
        "diameter": float(dia),
        "radius_grid_min": float(radii.min()),
        "radius_grid_max": float(radii.max()),
        "local_dim_global_mean": float(np.nanmean(lds)),
        "local_dim_global_std": float(np.nanstd(lds)),
        "frozen_cluster_counts": [int((cl_frozen == c).sum()) for c in range(3)],
        "vgt_dot_cluster_counts": [int((cl_vgt == c).sum()) for c in range(3)],
        "ari_vs_frozen_clusters": float(ari_vs_frozen),
        "early_cluster_overlap": {
            "frozen_early_cluster": 1,
            "n_frozen_early": int(frozen_early.sum()),
            "vgt_dot_cluster_containing_them": overlap,
            "overlap_n": best_ov,
            "jaccard": float(jaccard),
        },
        "scalar_vgt_dot": {
            "mean": float(np.mean(f_scalar)),
            "std": float(np.std(f_scalar)),
            "range": [float(f_scalar.min()), float(f_scalar.max())],
        },
        "cluster_time_stats": ts_by_cl,
        "cluster_local_dim": ld_by_cl,
    }

    with open(os.path.join(OUT_DIR, "c03b_embeddings_vgtdot.json"), "w") as f:
        json.dump(summary, f, indent=2)

    # ---- console ----
    print("=== C03b: VGT-dot clustering of real token embeddings ===")
    print(f"embeddings {emb.shape}, diameter {dia:.3f}, local dim mean {np.nanmean(lds):.3f}")
    print(f"scalar VGT-dot: mean={np.mean(f_scalar):.4f} std={np.std(f_scalar):.4f} "
          f"(near-constant -> frozen scalar feature not discriminative)")
    print(f"frozen clusters: {summary['frozen_cluster_counts']}")
    print(f"VGT-dot k-means clusters: {summary['vgt_dot_cluster_counts']}")
    print(f"ARI vs frozen: {ari_vs_frozen:.3f}")
    print(f"frozen early cluster (n=60, t<=9) contained in VGT-dot cluster {overlap} "
          f"(n={best_ov}), Jaccard={jaccard:.3f}")
    print("cluster time stats:", json.dumps(ts_by_cl))
    print("cluster local dim:", json.dumps(ld_by_cl))

    # ---- figures ----
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    pca = PCA(n_components=2, random_state=0)
    xy = pca.fit_transform(emb)
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.6))
    sc = axes[0].scatter(xy[:, 0], xy[:, 1], c=ts, s=8, cmap="viridis")
    axes[0].set_title("time step"); plt.colorbar(sc, ax=axes[0])
    axes[1].scatter(xy[:, 0], xy[:, 1], c=cl_frozen, s=8, cmap="tab10")
    axes[1].set_title("frozen cluster labels")
    axes[2].scatter(xy[:, 0], xy[:, 1], c=cl_vgt, s=8, cmap="tab10")
    axes[2].set_title("VGT-dot curve k-means")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, "c03b_embeddings_vgtdot.png"), dpi=140)
    plt.close(fig)
    print("\nSaved results/ -> c03b_embeddings_vgtdot.json / .png")


if __name__ == "__main__":
    main()
