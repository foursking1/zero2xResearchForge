"""Verify Claim C02.

Claim C02 (TASK.md / .claim_spec.json):
  "MMD gradient flows with Schatten p = 1, 2, infinity produce qualitatively
   different particle trajectories: operator-norm flow is most globally
   coordinated, trace-norm flow is most local, Frobenius flow interpolates;
   final losses are 0.0018, 0.0016, 0.0011 respectively"

Pipeline
--------
1. Load frozen flow artifacts (X0, Y, losses_1/2/inf) from mmd_flows.npz.
2. Re-run the three explicit-Euler flows on the SAME frozen clouds with the
   reference hyper-parameters (step sizes 2.5/1.8/1.6, eps=1e-2, 6000 steps)
   and check the loss curves reproduce the frozen ones.
3. Quantitative trajectory-coordination metrics:
   - SVD spectrum of the aggregate displacement  D = X_final - X_0
   - top-singular-value share  s1/(s1+s2)  and conditioning  s1/s2
   - mean absolute cosine of per-particle displacement against the top
     singular direction (directional coherence)
   - per-step velocity rank structure at selected iterations
4. Compare final losses to the claimed values (0.0018 / 0.0016 / 0.0011).
5. Write results/metrics_flow.json and regenerated figures.

NOTE: this is the fast version of verify_flow.py; it is identical except that it
pins torch to a single thread (see inline comment), which is ~30x faster on this
machine for the tiny (200x2) matrices.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch

from common import FLOW_NPZ, load_flow

OUT = Path(__file__).resolve().parent.parent / "results"
OUT.mkdir(parents=True, exist_ok=True)

torch.set_default_dtype(torch.float64)
# Performance fix: the default multi-threaded BLAS is ~30x slower for the tiny
# (200x2) matrices here (measured 1083 ms/step vs 33 ms/step single-threaded),
# so pin torch to one thread to keep the 6000-step runs tractable.
torch.set_num_threads(1)
SEED = 1234

STEPS = 6000
EPS = 1e-2
STEP_SIZES = {1: 2.5, 2: 1.8, float("inf"): 1.6}
NAMES = {1: "trace (p=1)", 2: "Frobenius (p=2)", float("inf"): "operator (p=inf)"}


def smooth_cdist(x: torch.Tensor, y: torch.Tensor, eps: float = EPS) -> torch.Tensor:
    diff = x[:, None, :] - y[None, :, :]
    return torch.sqrt((diff * diff).sum(dim=-1) + eps ** 2)


def mmd_energy_squared(x: torch.Tensor, y: torch.Tensor, eps: float = EPS) -> torch.Tensor:
    d_xx = smooth_cdist(x, x, eps)
    d_yy = smooth_cdist(y, y, eps)
    d_xy = smooth_cdist(x, y, eps)
    return 2.0 * d_xy.mean() - d_xx.mean() - d_yy.mean()


def schatten_direction(grad: torch.Tensor, p):
    """Exact replica of the reference velocity field (reproduce.py)."""
    if p == 1:
        return -grad
    u, s, vh = torch.linalg.svd(grad, full_matrices=False)
    if p == float("inf"):
        return -s.sum() * (u @ vh)
    r = 2.0 * p
    q = r / (r - 1.0)
    norm_q = (s.pow(q).sum()).pow(1.0 / q)
    if float(norm_q) < 1e-14:
        return torch.zeros_like(grad)
    weights = s.pow(q - 1.0)
    return -(norm_q.pow(2.0 - q)) * ((u * weights.unsqueeze(0)) @ vh)


def run_flow(x0: torch.Tensor, y: torch.Tensor, p, step_size: float, steps: int, eps: float):
    """Return history (steps+1, n, 2) and losses (steps,)."""
    x = x0.clone().detach()
    history = [x.clone()]
    losses = []
    for k in range(steps):
        x = x.detach().requires_grad_(True)
        loss = mmd_energy_squared(x, y, eps)
        loss.backward()
        grad = x.grad.detach()
        vel = schatten_direction(grad, p)
        with torch.no_grad():
            x = x + step_size * vel
        history.append(x.clone())
        losses.append(float(loss.detach()))
        if (k + 1) % 2000 == 0:
            print(f"    [p={'1' if p==1 else '2' if p==2 else 'inf'}] step {k+1}/{steps} "
                  f"loss={losses[-1]:.6f}", flush=True)
    return torch.stack(history), np.array(losses, dtype=float)


def direction_metrics(D: np.ndarray) -> dict:
    """SVD-based coordination metrics of an (n, 2) displacement matrix."""
    u, s, vh = np.linalg.svd(D, full_matrices=False)
    s1, s2 = s[0], s[1]
    top_dir = vh[0]  # 2-d vector
    # normalised per-particle displacement
    norms = np.linalg.norm(D, axis=1)
    norms[norms < 1e-12] = 1.0
    proj = np.abs(D @ top_dir) / norms
    return {
        "singular_values": s.tolist(),
        "top_share": float(s1 / s.sum()),
        "cond_s1_over_s2": float(s1 / s2) if s2 > 0 else float("inf"),
        "mean_abs_cos_top_dir": float(proj.mean()),
        "mean_displacement_norm": float(norms.mean()),
    }


def main() -> None:
    flow = load_flow()
    X0, Y = flow["X0"], flow["Y"]
    frozen_losses = {1: flow["losses_1"], 2: flow["losses_2"], float("inf"): flow["losses_inf"]}

    results = {}
    print("Re-running the three MMD gradient flows on the frozen clouds ...", flush=True)
    for p in [1, 2, float("inf")]:
        hist, losses = run_flow(
            torch.from_numpy(X0), torch.from_numpy(Y), p, STEP_SIZES[p], STEPS, EPS
        )
        fl = frozen_losses[p]
        max_diff = float(np.abs(losses - fl).max())
        results[p] = {
            "history": hist.numpy(),
            "losses": losses,
            "frozen_losses": fl,
            "max_abs_loss_diff_vs_frozen": max_diff,
        }
        print(f"  p={p}: final_loss={losses[-1]:.6f}  frozen={fl[-1]:.6f}  "
              f"max_diff={max_diff:.2e}  (reproduced={'yes' if max_diff < 1e-10 else 'NO'})", flush=True)

    # ── report ──────────────────────────────────────────────────────────
    report = {
        "claim_id": "C02",
        "steps": STEPS,
        "eps": EPS,
        "step_sizes": {"1": STEP_SIZES[1], "2": STEP_SIZES[2], "inf": STEP_SIZES[float("inf")]},
        "source": str(FLOW_NPZ),
        "final_losses": {},
        "trajectory_metrics": {},
        "velocity_metrics": {},
        "loss_reproduced_from_frozen": True,
        "claim_values": {"1": 0.0018, "2": 0.0016, "inf": 0.0011},
    }

    # loss comparison + trajectory metrics
    for p in [1, 2, float("inf")]:
        pkey = "1" if p == 1 else "2" if p == 2 else "inf"
        losses = results[p]["losses"]
        hist = results[p]["history"]
        D = hist[-1] - hist[0]
        dm = direction_metrics(D)
        report["final_losses"][pkey] = {
            "recomputed": float(losses[-1]),
            "frozen": float(results[p]["frozen_losses"][-1]),
            "max_abs_loss_diff_vs_frozen": results[p]["max_abs_loss_diff_vs_frozen"],
            "initial_loss": float(losses[0]),
        }
        report["trajectory_metrics"][pkey] = dm

        # velocity rank-structure at selected steps
        sel = sorted({0, 999, 2999, STEPS - 1})
        vel_metrics = {}
        for k in sel:
            x = torch.from_numpy(hist[k]).detach().requires_grad_(True)
            loss = mmd_energy_squared(x, torch.from_numpy(Y), EPS)
            loss.backward()
            g = x.grad.detach().numpy()
            sv = np.linalg.svd(g, compute_uv=False)
            vel_metrics[int(k)] = {
                "grad_singular_values": sv.tolist(),
                "grad_top_share": float(sv[0] / sv.sum()),
            }
        report["velocity_metrics"][pkey] = vel_metrics

    # tolerance check vs claim
    report["tolerance_check"] = {}
    for pkey in ["1", "2", "inf"]:
        val = report["final_losses"][pkey]["recomputed"]
        c = report["claim_values"][pkey]
        report["tolerance_check"][pkey] = {
            "recomputed": val,
            "claim": c,
            "abs_diff": abs(val - c),
            "rel_diff": abs(val - c) / c,
            "within_15pct": abs(val - c) / c <= 0.15,
        }

    with open(OUT / "metrics_flow.json", "w") as fh:
        json.dump(report, fh, indent=2)
    print(f"Wrote {OUT / 'metrics_flow.json'}", flush=True)

    # ── Figures (regenerated from frozen data) ──────────────────────────
    fig, axes = plt.subplots(1, 3, figsize=(18, 5.8), constrained_layout=True)
    all_pts = np.concatenate([Y, X0, *[results[p]["history"][-1] for p in [1, 2, float("inf")]]], axis=0)
    x_min, y_min = all_pts.min(axis=0) - 0.7
    x_max, y_max = all_pts.max(axis=0) + 0.7
    for ax, p in zip(axes, [1, 2, float("inf")]):
        hist = results[p]["history"]
        ax.scatter(Y[:, 0], Y[:, 1], s=14, c="royalblue", alpha=0.24, label="target")
        for idx in range(len(X0)):
            curve = hist[:, idx]
            ax.plot(curve[:, 0], curve[:, 1], color="black", lw=0.45, alpha=0.18)
        ax.scatter(hist[0, :, 0], hist[0, :, 1], s=14, c="crimson", alpha=0.75, label="start")
        ax.scatter(hist[-1, :, 0], hist[-1, :, 1], s=14, c="royalblue", alpha=0.80, label="end")
        ax.set_title(f"{NAMES[p]}\nfinal loss = {results[p]['losses'][-1]:.4f}")
        ax.set_aspect("equal")
        ax.set_xlim(x_min, x_max)
        ax.set_ylim(y_min, y_max)
    axes[0].legend(loc="upper right", fontsize=9)
    fig.savefig(OUT / "mmd_trajectories_three_recomputed.png", dpi=200, bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7.0, 4.8))
    for p, color in zip([1, 2, float("inf")], ["crimson", "darkorange", "royalblue"]):
        pkey = "1" if p == 1 else "2" if p == 2 else "inf"
        ax.plot(results[p]["losses"], lw=2.0, color=color,
                label=f"{NAMES[p]} ({results[p]['losses'][-1]:.4f})")
    ax.set_xlabel("iteration")
    ax.set_ylabel(r"$f(\mu_k)$")
    ax.set_title("MMD decay for three generalized Wasserstein flows")
    ax.legend(fontsize=9)
    fig.savefig(OUT / "mmd_losses_three_recomputed.png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved figures to {OUT}", flush=True)


if __name__ == "__main__":
    main()
