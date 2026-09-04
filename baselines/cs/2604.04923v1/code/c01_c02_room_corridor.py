"""C01 / C02: VGT on the room-with-corridor stratified space (paper Fig. 5-7).

C01 - VGT captures the intrinsic dimension drop 2 (room) -> 1 (corridor).
C02 - VGT curves: slope ~2 for probe points a (junction) and b (room centre),
      slope ~1 for probe point c (corridor middle minimum) with a transition
      to slope ~2 when the ball reaches the adjacent room (paper: r ~ 0.3).

The frozen data does NOT ship the synthetic room-with-corridor point cloud, so
it is reconstructed from the paper's description (Fig. 5: a square room plus a
winding sine corridor attached at one point).  The VGT implementation used is
the frozen reference implementation `VolumeGrowthTransform`.
"""
import os
import json
import sys

import numpy as np
from scipy import stats

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import CODE_ROOT  # noqa: E402
import vgt as vgt_impl  # corrected VGT implementation  # noqa: E402

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")


# ---------------------------------------------------------------------------
# Space construction
# ---------------------------------------------------------------------------
def build_room_corridor(seed=42, n_room_grid=160, n_corridor=500, noise=0.005):
    """Reconstruct the 'room with corridor' stratified space of paper Fig. 5.

    Room:  square [-0.5, 0.5] x [-0.5, 0.5]  (2D stratum)
    Corridor: thin strip of half-width 0.015 around the winding centre-line
              (0.5 + t, 0.15*sin(pi*t/0.6)),  t in [0, 0.6]  (1D stratum).
              The strip is thin compared with the smallest VGT radius used
              (r>=0.03), so the corridor behaves as a 1D line at those scales.
    Probe points:
        a = (0.5, 0)      room-corridor connection point
        b = (0, 0)        centre of the room
        c = (0.8, -0.15)  middle minimum of the corridor
    """
    rng = np.random.default_rng(seed)

    # Room: regular grid (mimics dense agent-position sampling)
    xs = np.linspace(-0.5, 0.5, n_room_grid)
    ys = np.linspace(-0.5, 0.5, n_room_grid)
    gx, gy = np.meshgrid(xs, ys)
    room = np.stack([gx.ravel(), gy.ravel()], axis=1)

    # Corridor: sample (t, s) uniformly, s in [-w, w] perpendicular offset
    w = 0.015
    L = 0.6
    A = 0.15
    t = rng.uniform(0.0, L, n_corridor)
    s = rng.uniform(-w, w, n_corridor)
    cx = 0.5 + t
    cy = -A * np.sin(np.pi * t / L)   # minus sign -> valley (minimum) at t=L/2
    tx = 1.0
    ty = A * (np.pi / L) * np.cos(np.pi * t / L)
    norm = np.hypot(tx, ty)
    # unit normal to the centre-line
    nx, ny = -ty / norm, tx / norm
    corr = np.stack([cx + s * nx, cy + s * ny], axis=1)

    X = np.vstack([room, corr])
    labels = np.zeros(len(X), dtype=int)          # 0 = room (2D)
    labels[len(room):] = 1                        # 1 = corridor (1D)

    # small isotropic noise -> "noisy variation" of Fig. 5
    X = X + rng.normal(0.0, noise, size=X.shape)
    return X, labels


def probe_points():
    return {
        "a": np.array([0.5, 0.0]),
        "b": np.array([0.0, 0.0]),
        "c": np.array([0.8, -0.15]),
    }


# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------
def local_dim_room_vs_corridor(X, labels, n_subset=4000, seed=1):
    """C01: VGT local dimension in room vs corridor (corrected VGT)."""
    rng = np.random.default_rng(seed)
    room_idx = np.where(labels == 0)[0]
    corr_idx = np.where(labels == 1)[0]
    n_r = min(n_subset // 2, len(room_idx))
    n_c = min(n_subset // 2, len(corr_idx))
    idx = np.concatenate([
        rng.choice(room_idx, n_r, replace=False),
        rng.choice(corr_idx, n_c, replace=False),
    ])

    # corrected VGT with a scale-appropriate radius grid
    radii, dia = vgt_impl.compute_radii(X, n_radii=28, r_min_frac=1e-3,
                                        r_max_frac=1.0, seed=0)
    # local dim fit window: above the corridor half-width (0.015) so the 1D
    # regime is probed, and below the corridor->room reach (~0.33)
    r_lo = 0.03
    r_hi = 0.16
    lds, res = vgt_impl.local_dim_all(X, radii=radii, r_lo=r_lo, r_hi=r_hi,
                                      center_indices=idx, seed=0)

    # exclude points very close to the room-corridor junction from the
    # "pure" stratum comparison (boundary transition is expected)
    keep = np.ones(len(idx), dtype=bool)
    xcorr = X[idx, 0]
    corr_close = (labels[idx] == 1) & (xcorr < 0.65)
    room_edge = (labels[idx] == 0) & (xcorr > 0.45)
    keep &= ~corr_close & ~room_edge

    res_dict = {
        "n_room": int((labels[idx] == 0).sum()),
        "n_corr": int((labels[idx] == 1).sum()),
        "radius_grid_min": float(radii.min()),
        "radius_grid_max": float(radii.max()),
        "diameter_estimate": float(dia),
        "ld_fit_window": [r_lo, r_hi],
        "room_ld_mean": float(np.nanmean(lds[(labels[idx] == 0) & keep])),
        "room_ld_median": float(np.nanmedian(lds[(labels[idx] == 0) & keep])),
        "room_ld_std": float(np.nanstd(lds[(labels[idx] == 0) & keep])),
        "corr_ld_mean": float(np.nanmean(lds[(labels[idx] == 1) & keep])),
        "corr_ld_median": float(np.nanmedian(lds[(labels[idx] == 1) & keep])),
        "corr_ld_std": float(np.nanstd(lds[(labels[idx] == 1) & keep])),
        "global_ld_mean": float(np.nanmean(lds)),
        "dim_drop": float(np.nanmean(lds[(labels[idx] == 0) & keep])
                          - np.nanmean(lds[(labels[idx] == 1) & keep])),
    }
    return res_dict, lds, idx, radii


def probe_vgt_curves(X, seed=1):
    """C02: VGT curves for probe points a/b/c (corrected VGT)."""
    rng = np.random.default_rng(seed)
    probes = probe_points()
    centers = {}
    for name, p in probes.items():
        d2 = ((X - p) ** 2).sum(axis=1)
        centers[name] = int(np.argmin(d2))

    idx = np.array([centers[k] for k in ("a", "b", "c")])
    radii, dia = vgt_impl.compute_radii(X, n_radii=32, r_min_frac=1e-3,
                                        r_max_frac=1.0, seed=0)
    res = vgt_impl.compute_vgt(X, center_indices=idx, radii=radii)
    log_r = res["log_radii"]
    curves = res["vgt_curves"]

    slopes_small = {}
    slopes_large = {}
    slopes_mid = {}
    transition = {}
    small_mask = (radii >= 0.03) & (radii < 0.16)   # 1D regime for corridor c
    mid_mask = (radii >= 0.16) & (radii <= 0.6)
    large_mask = radii > 0.6
    for k, name in enumerate(("a", "b", "c")):
        y = curves[k]
        slopes_small[name] = (float(np.polyfit(log_r[small_mask], y[small_mask], 1)[0])
                              if small_mask.sum() >= 3 else float("nan"))
        slopes_mid[name] = (float(np.polyfit(log_r[mid_mask], y[mid_mask], 1)[0])
                            if mid_mask.sum() >= 3 else float("nan"))
        slopes_large[name] = (float(np.polyfit(log_r[large_mask], y[large_mask], 1)[0])
                              if large_mask.sum() >= 3 else float("nan"))

    # transition radius for point c: first radius (>=0.16, i.e. after the
    # initial 1D regime) where the *segment* slope of the VGT curve exceeds
    # 1.5 (midpoint between slope 1 and 2).  Segment slopes avoid the
    # smearing caused by smoothing the derivative.
    yc = curves[2]
    seg = np.diff(yc) / np.diff(log_r)          # slope of each log-r segment
    seg_r = np.sqrt(radii[:-1] * radii[1:])     # geometric mean radius of segment
    search = np.where(seg_r >= 0.16)[0]
    above = search[seg[search] > 1.5]
    r_trans = float(seg_r[above[0]]) if len(above) > 0 else float("nan")

    return {
        "centers": centers,
        "probe_coords": {k: probe_points()[k].tolist() for k in ("a", "b", "c")},
        "slopes_small": slopes_small,
        "slopes_mid": slopes_mid,
        "slopes_large": slopes_large,
        "transition_radius_c": r_trans,
        "radii": radii.tolist(),
        "curves": curves.tolist(),
        "log_radii": log_r.tolist(),
    }


def main():
    X, labels = build_room_corridor()
    ld_res, lds, idx, radii = local_dim_room_vs_corridor(X, labels)
    vgt_res = probe_vgt_curves(X)

    summary = {
        "n_points": int(len(X)),
        "n_room": int((labels == 0).sum()),
        "n_corridor": int((labels == 1).sum()),
        "local_dim": ld_res,
        "probe": vgt_res,
    }

    with open(os.path.join(OUT_DIR, "c01_c02_room_corridor.json"), "w") as f:
        json.dump(summary, f, indent=2)

    # ---- console report ----
    print("=== C01: VGT local dimension, room vs corridor ===")
    for k, v in ld_res.items():
        print(f"  {k}: {v}")
    print()
    print("=== C02: VGT probe curves ===")
    print("  probe centers (data index):", vgt_res["centers"])
    print("  slopes (small r < 0.16):", vgt_res["slopes_small"])
    print("  slopes (large r > 0.4):", vgt_res["slopes_large"])
    print("  transition radius for c:", vgt_res["transition_radius_c"])

    # ---- figures ----
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    # left: local dimension scatter on the space
    sc = axes[0].scatter(X[idx, 0], X[idx, 1], c=lds,
                         s=3, cmap="viridis")
    axes[0].set_title("VGT local dimension (room-with-corridor)")
    axes[0].set_xlabel("x"); axes[0].set_ylabel("y")
    plt.colorbar(sc, ax=axes[0])
    # mark probe points
    for name, p in probe_points().items():
        axes[0].plot(*p, marker="x", color="red", ms=10, mew=2)
        axes[0].annotate(name, p, textcoords="offset points", xytext=(6, 6), color="red")

    # right: VGT curves at probes
    for k, name in enumerate(("a", "b", "c")):
        axes[1].plot(vgt_res["log_radii"], vgt_res["curves"][k],
                     label=f"point {name}")
    axes[1].set_title("VGT curves at probe points a/b/c")
    axes[1].set_xlabel("log r"); axes[1].set_ylabel("log volume")
    axes[1].legend()
    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, "c01_c02_room_corridor.png"), dpi=140)
    plt.close(fig)
    print("\nSaved results/ -> c01_c02_room_corridor.json / .png")


if __name__ == "__main__":
    main()
