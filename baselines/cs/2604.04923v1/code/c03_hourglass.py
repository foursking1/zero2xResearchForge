"""C03: Stratification detection on an hourglass space (paper Fig. 8).

Claim: HADES detects singularities accurately; DIC misses the hourglass neck;
VGT-dot provides a more informative local-to-global clustering.

Methods compared on a reconstructed hourglass space (two 2D lobes joined by a
thin 1D neck):
  * DIC      - Dimension Induced Clustering: k-means on the local intrinsic
               dimension (small-scale VGT slope).  A 1D scalar feature.
  * VGT-dot  - k-means on the *curve* of the (smoothed) VGT derivative over a
               restricted scale window (local-to-global signature).
  * HADES    - a reconstruction of HADES' local-measure comparison: for each
               point the k-NN distance profile is compared against a single
               power-law (manifold) growth model; the change of the power-law
               slope across the neighbour range is the singularity score.
               (Official HADES is NOT shipped in the frozen workspace; this is
               a clearly-labelled reconstruction based on the description in
               [18].)

Design intent: at a junction/singularity point the intrinsic dimension
*changes with scale* (1D neck -> 2D lobe).  A scalar local-dimension estimate
(DIC) fitted at a *small* scale sees only ~1 (same as the neck), so the
singularity is absorbed into the neck cluster ("DIC misses the hourglass
neck").  The VGT-dot curve records the 1->2 transition, giving the junction a
distinct signature, and HADES' multiscale measure comparison flags exactly the
points where the power-law slope changes.
"""
import os
import json
import sys

import numpy as np
from scipy.spatial import cKDTree
from scipy.spatial.distance import cdist
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score, precision_recall_fscore_support

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vgt as vgt_impl  # noqa: E402

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")


# ---------------------------------------------------------------------------
# Space construction
# ---------------------------------------------------------------------------
def build_hourglass(seed=42, lobe_n=4000, R=0.5, cx=2.0, w=0.005,
                    neck_len=1.5, neck_lambda=200, noise=0.002,
                    junction_radius=0.25):
    """Two 2D disks (lobes) joined by a thin 1D neck strip.

    Disks of radius R are centred at (+-cx, 0); the neck strip spans
    x in [-neck_len, neck_len] with half-width w.  The neck meets each disk at
    its leftmost/rightmost point (+-(cx-R), 0), forming a cusp / singularity.
    Junction labels are assigned to the neck points within junction_radius of
    the attachment points, i.e. the neck segment where a ball of moderate
    radius crosses from the 1D neck into the 2D lobe.
    """
    rng = np.random.default_rng(seed)

    lobes = []
    for c in (-cx, cx):
        pts = []
        while len(pts) < lobe_n:
            cand = rng.uniform(-R, R, (int(lobe_n * 1.35), 2))
            pts.append(cand[(cand ** 2).sum(axis=1) <= R ** 2])
        p = np.concatenate(pts)[:lobe_n]
        p[:, 0] += c
        lobes.append(p)
    lobes = np.concatenate(lobes, axis=0)

    # neck strip: linear point density neck_lambda per unit length
    neck_n = max(100, int(neck_len * 2 * neck_lambda))
    nx = rng.uniform(-neck_len, neck_len, neck_n)
    ny = rng.uniform(-w, w, neck_n)
    neck = np.stack([nx, ny], axis=1)

    X = np.vstack([lobes, neck])
    labels = np.zeros(len(X), dtype=int)          # 0 = lobe (2D)
    labels[len(lobes):] = 1                       # 1 = neck (1D)
    attach = np.array([[-cx + R, 0.0], [cx - R, 0.0]])
    dmin = cdist(X, attach).min(axis=1)
    labels[(labels == 1) & (dmin < junction_radius)] = 2   # 2 = junction

    X = X + rng.normal(0.0, noise, size=X.shape)
    return X, labels


# ---------------------------------------------------------------------------
# Features
# ---------------------------------------------------------------------------
def dic_feature(X, r_lo=0.02, r_hi=0.06, n_radii=28, seed=0):
    """DIC feature: local intrinsic dimension = small-scale VGT slope."""
    radii, _ = vgt_impl.compute_radii(X, n_radii=n_radii, r_min_frac=1e-3,
                                      r_max_frac=1.0, seed=seed)
    lds, _ = vgt_impl.local_dim_all(X, radii=radii, r_lo=r_lo, r_hi=r_hi,
                                    seed=seed)
    return lds


def vgt_dot_curve_feature(X, n_radii=48, smoothing_window=3, seed=0,
                          scale_lo=0.03, scale_hi=0.30):
    """VGT-dot feature vector = smoothed derivative over a scale window."""
    res = vgt_impl.vgt_dot_features(X, n_radii=n_radii,
                                    smoothing_window=smoothing_window, seed=seed)
    derivs = res["derivatives"]                     # (N, n_radii)
    radii = res["radii"]
    mask = (radii >= scale_lo) & (radii <= scale_hi)
    feat = derivs[:, mask]                          # (N, n_scales)
    # standardise each scale channel
    feat = (feat - feat.mean(axis=0)) / (feat.std(axis=0) + 1e-12)
    return feat, res


def vgt_dot_2d_summary(X, n_radii=48, smoothing_window=3, seed=0,
                       small=(0.03, 0.08), large=(0.20, 0.30)):
    """VGT-dot 2D summary: mean derivative over a small- and a large-scale band."""
    res = vgt_impl.vgt_dot_features(X, n_radii=n_radii,
                                    smoothing_window=smoothing_window, seed=seed)
    derivs = res["derivatives"]
    radii = res["radii"]
    m_small = (radii >= small[0]) & (radii <= small[1])
    m_large = (radii >= large[0]) & (radii <= large[1])
    feat = np.stack([derivs[:, m_small].mean(axis=1),
                     derivs[:, m_large].mean(axis=1)], axis=1)
    return feat, res


def hades_singularity_score(X, k=150, split_frac=0.5):
    """HADES-inspired local-measure-comparison score.

    For each point take the distances r_1<=...<=r_k to its k nearest
    neighbours.  Under the null of a uniform d-manifold the order statistics
    satisfy log r_j = (1/d) log j + const, i.e. a *single* power law with
    slope 1/d.  We fit the slope on the first half of the neighbour range and
    on the second half; the absolute slope difference is the singularity
    score.  A point whose intrinsic dimension changes with scale (1D neck ->
    2D lobe, i.e. a junction) has different small-scale and large-scale
    slopes -> large score; a point on a clean d-manifold has equal slopes
    (up to noise) -> score ~ 0.
    """
    tree = cKDTree(X)
    dists, _ = tree.query(X, k=min(k + 1, len(X)))
    dists = dists[:, 1:]
    n2 = int((dists.shape[1]) * split_frac)
    scores = np.zeros(len(X))
    for i in range(len(X)):
        r = dists[i]
        r = r[r > 1e-12]
        if len(r) < 2 * n2:
            scores[i] = 0.0
            continue
        j = np.arange(1, len(r) + 1)
        x = np.log(j)
        y = np.log(r)
        s1 = np.polyfit(x[:n2], y[:n2], 1)[0]
        s2 = np.polyfit(x[n2:], y[n2:], 1)[0]
        scores[i] = float(abs(s1 - s2))
    return scores


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------
def _km(feature2d, labels, n_clusters, seed=0):
    valid = ~np.isnan(feature2d[:, 0])
    km = KMeans(n_clusters=n_clusters, n_init=10, random_state=seed)
    pred = np.full(len(feature2d), -1)
    pred[valid] = km.fit_predict(feature2d[valid])
    return pred, valid


def cluster_eval(feature2d, labels, n_clusters=3, seed=0):
    """k-means on a feature matrix; metrics vs 3-group ground truth."""
    pred, valid = _km(feature2d, labels, n_clusters, seed)
    gt = labels
    ari = adjusted_rand_score(gt[valid], pred[valid])

    junction = (gt == 2)
    best_prec = best_rec = best_f1 = -1.0
    best_cl = -1
    for cl in range(n_clusters):
        cl_mask = (pred == cl)
        n_in = (junction & cl_mask).sum()
        if n_in == 0:
            continue
        prec = n_in / cl_mask.sum()
        rec = n_in / junction.sum()
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0
        if f1 > best_f1:
            best_f1, best_prec, best_rec, best_cl = f1, prec, rec, cl

    return {
        "n_clusters": n_clusters,
        "ari_vs_3group_gt": float(ari),
        "junction_cluster": int(best_cl),
        "junction_precision": float(best_prec),
        "junction_recall": float(best_rec),
        "junction_f1": float(best_f1),
        "cluster_sizes": [int((pred == cl).sum()) for cl in range(n_clusters)],
    }


def main():
    X, labels = build_hourglass()
    n_lobe = int((labels == 0).sum())
    n_neck = int((labels == 1).sum())
    n_junc = int((labels == 2).sum())

    ld = dic_feature(X)
    vdf, vd_res = vgt_dot_curve_feature(X)
    vd2d, _ = vgt_dot_2d_summary(X)
    had = hades_singularity_score(X)

    # per-group feature summaries
    groups = {"lobe": 0, "neck": 1, "junction": 2}
    feat_summary = {}
    for gname, g in groups.items():
        m = labels == g
        feat_summary[gname] = {
            "n": int(m.sum()),
            "dic_mean": float(np.nanmean(ld[m])),
            "dic_std": float(np.nanstd(ld[m])),
            "vgt_dot_curve_norm_mean": float(np.mean(np.linalg.norm(vdf[m], axis=1))),
            "hades_mean": float(np.mean(had[m])),
        }

    # clustering evaluations
    ld_2d = ld.reshape(-1, 1)
    dic2 = cluster_eval(ld_2d, labels, n_clusters=2)
    dic3 = cluster_eval(ld_2d, labels, n_clusters=3)
    vd2 = cluster_eval(vdf, labels, n_clusters=2)
    vd3 = cluster_eval(vdf, labels, n_clusters=3)
    vd2d3 = cluster_eval(vd2d, labels, n_clusters=3)

    # HADES detection: choose threshold as the score level giving the best F1
    # (reported threshold and metrics at that operating point)
    best = (0.0, 0.0, 0.0, -1.0)
    for thr in np.linspace(0.0, 1.0, 201):
        p, r, f, _ = precision_recall_fscore_support(
            labels == 2, had >= thr, average="binary", zero_division=0)
        if f > best[3]:
            best = (float(thr), float(p), float(r), float(f))
    thr, prec, rec, f1 = best
    had_metrics = {
        "best_threshold": thr,
        "n_flagged": int((had >= thr).sum()),
        "n_true_junction": n_junc,
        "precision": prec,
        "recall": rec,
        "f1": f1,
        "score_lobe_mean": float(had[labels == 0].mean()),
        "score_neck_mean": float(had[labels == 1].mean()),
        "score_junction_mean": float(had[labels == 2].mean()),
    }

    summary = {
        "space": {"n_points": int(len(X)), "n_lobe": n_lobe,
                  "n_neck": n_neck, "n_junction": n_junc},
        "feature_summary": feat_summary,
        "dic_2clusters": dic2,
        "dic_3clusters": dic3,
        "vgt_dot_2clusters": vd2,
        "vgt_dot_3clusters": vd3,
        "vgt_dot_2d_3clusters": vd2d3,
        "hades": had_metrics,
    }

    with open(os.path.join(OUT_DIR, "c03_hourglass.json"), "w") as f:
        json.dump(summary, f, indent=2)

    # ---- console ----
    print("=== C03: hourglass space ===")
    print("space:", summary["space"])
    print("\nfeature means by group:")
    for g in groups:
        fs = feat_summary[g]
        print(f"  {g:8s} n={fs['n']:5d} DIC={fs['dic_mean']:.3f} "
              f"HADES={fs['hades_mean']:.3f}")
    print("\nDIC k=2:", json.dumps({k: (round(v, 3) if isinstance(v, float) else v)
                                    for k, v in dic2.items()}))
    print("DIC k=3:", json.dumps({k: (round(v, 3) if isinstance(v, float) else v)
                                   for k, v in dic3.items()}))
    print("VGT-dot k=2:", json.dumps({k: (round(v, 3) if isinstance(v, float) else v)
                                       for k, v in vd2.items()}))
    print("VGT-dot k=3:", json.dumps({k: (round(v, 3) if isinstance(v, float) else v)
                                       for k, v in vd3.items()}))
    print("VGT-dot 2D k=3:", json.dumps({k: (round(v, 3) if isinstance(v, float) else v)
                                          for k, v in vd2d3.items()}))
    print("HADES:", json.dumps({k: (round(v, 3) if isinstance(v, float) else v)
                                for k, v in had_metrics.items()}))

    # ---- figures ----
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(2, 3, figsize=(15, 9))
    plots = [
        ("ground truth", labels, None, None),
        ("DIC local dim", ld, "viridis", None),
        ("HADES score", had, "magma", None),
    ]
    for ax, (title, c, cmap, _) in zip(axes.ravel()[:3], plots):
        sc = ax.scatter(X[:, 0], X[:, 1], c=c, s=2, cmap=cmap)
        ax.set_title(title); ax.set_aspect("equal")
        plt.colorbar(sc, ax=ax, fraction=0.046)

    def km_pred(feat2d, k):
        pred, _ = _km(feat2d, labels, k)
        return pred
    for ax, (name, feat, k) in zip(
            axes.ravel()[3:],
            [("DIC k=3", ld_2d, 3), ("VGT-dot k=3 (curve)", vdf, 3),
             ("HADES flagged", had, None)]):
        if k is None:
            sc = ax.scatter(X[:, 0], X[:, 1], c=had >= thr, s=2, cmap="bwr")
            ax.set_title(f"HADES flagged (thr={thr:.2f})")
        else:
            pred = km_pred(feat, k)
            sc = ax.scatter(X[:, 0], X[:, 1], c=pred, s=2, cmap="tab10")
            ax.set_title(name)
        ax.set_aspect("equal")
        plt.colorbar(sc, ax=ax, fraction=0.046)

    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, "c03_hourglass.png"), dpi=140)
    plt.close(fig)
    print("\nSaved results/ -> c03_hourglass.json / .png")


if __name__ == "__main__":
    main()
