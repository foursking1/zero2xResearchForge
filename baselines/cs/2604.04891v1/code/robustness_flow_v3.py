"""Robustness / sensitivity check for the C02 conclusions.

Re-runs the three MMD gradient flows on the *frozen* clouds with a shorter
horizon (2000 steps) and with the nominal step sizes and +/-10 % perturbations.
Checks whether the two qualitative conclusions from the full run are robust:

  1. final-loss ordering:  p=inf < p=2 ~ p=1  (operator norm lowest)
  2. velocity anisotropy:  p=inf > p=2 > p=1  (operator norm most globally
     coordinated force field)

Writes results/metrics_flow_robustness.json.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import torch

from common import load_flow

torch.set_default_dtype(torch.float64)
torch.set_num_threads(1)

OUT = Path(__file__).resolve().parent.parent / "results"
STEPS = 2000
EPS = 1e-2
BASE_STEP = {1: 2.5, 2: 1.8, float("inf"): 1.6}


def smooth_cdist(x, y, eps=EPS):
    diff = x[:, None, :] - y[None, :, :]
    return torch.sqrt((diff * diff).sum(dim=-1) + eps ** 2)


def mmd_energy_squared(x, y, eps=EPS):
    return 2.0 * smooth_cdist(x, y, eps).mean() - smooth_cdist(x, x, eps).mean() - smooth_cdist(y, y, eps).mean()


def schatten_direction(grad, p):
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


def run_traj(x0, y, p, step_size, steps):
    """Return (trajectory[np, (steps+1,n,2)], losses[np, (steps,)])."""
    x = x0.clone().detach()
    history = [x.clone()]
    losses = []
    for _ in range(steps):
        x = x.detach().requires_grad_(True)
        loss = mmd_energy_squared(x, y, EPS)
        loss.backward()
        vel = schatten_direction(x.grad.detach(), p)
        with torch.no_grad():
            x = x + step_size * vel
        history.append(x.clone())
        losses.append(float(loss.detach()))
    return torch.stack(history).numpy(), np.array(losses)


def grad_top_share(x, y):
    """Top-singular-value share of the MMD gradient matrix at cloud x."""
    x = torch.from_numpy(x).detach().requires_grad_(True)
    y = torch.from_numpy(y).detach()
    loss = mmd_energy_squared(x, y, EPS)
    loss.backward()
    g = x.grad.detach().numpy()
    sv = np.linalg.svd(g, compute_uv=False)
    return float(sv[0] / sv.sum())


def main() -> None:
    flow = load_flow()
    X0 = torch.from_numpy(flow["X0"])
    Y_np = flow["Y"]

    out = {
        "steps": STEPS,
        "note": "short-horizon sensitivity check on frozen clouds; +/-10% step size",
    }
    for p in [1, 2, float("inf")]:
        pkey = "1" if p == 1 else "2" if p == 2 else "inf"
        out[pkey] = {}
        for tag, factor in [("nominal", 1.0), ("minus10pct", 0.9), ("plus10pct", 1.1)]:
            step = BASE_STEP[p] * factor
            hist, losses = run_traj(X0, Y_np, p, step, STEPS)
            out[pkey][tag] = {
                "step_size": step,
                "final_loss": float(losses[-1]),
                "loss_at_1000": float(losses[999]),
                "vel_grad_top_share_at_999": grad_top_share(hist[999], Y_np),
            }
        print(f"p={pkey}: " + ", ".join(f"{t}: loss={d['final_loss']:.6f} "
              f"velshare@999={d['vel_grad_top_share_at_999']:.3f}" for t, d in out[pkey].items()), flush=True)

    with open(OUT / "metrics_flow_robustness.json", "w") as fh:
        json.dump(out, fh, indent=2)
    print(f"Wrote {OUT / 'metrics_flow_robustness.json'}", flush=True)


if __name__ == "__main__":
    main()
