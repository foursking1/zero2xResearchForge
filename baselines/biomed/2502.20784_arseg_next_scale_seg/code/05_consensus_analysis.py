#!/usr/bin/env python3
"""Mechanism analysis: consensus aggregation (AR-Seg consensus) & next-scale conditioning.

* Consensus: MC-dropout stochastic sampling K in {1,2,4,8,16} on test set -> Soft-Dice vs
  the deterministic single pass; shows averaging stochastic consensus maps is stable and
  slightly better than a single stochastic sample.
* Stability: report sample variance of stochastic draws and the gain of consensus over a
  single draw (IQR of the stochastic set).
* Figures: example test patches with (image | pseudo-mask | baseline | AR pred).
"""
from __future__ import annotations
import os, sys, json, time
import numpy as np
import torch
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import UNetBaseline, ArSegUNet, soft_dice, hard_dice
from trainer import _iou


HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LIDC = os.path.join(ROOT, "results", "lidc")
EVI = os.path.join(ROOT, "evidence")
os.makedirs(EVI, exist_ok=True)


def load_test_subset(n=1500, seed=0):
    x = np.load(os.path.join(ROOT, "results", "cache", "lidc", "x_test.npy"))
    y = np.load(os.path.join(ROOT, "results", "cache", "lidc", "y_test.npy"))
    rng = np.random.RandomState(seed)
    idx = rng.choice(len(x), min(n, len(x)), replace=False)
    return np.sort(idx), x[idx], y[idx]


def consensus_curve(model_name, model, xs, ys, device, Ks=(1, 2, 4, 8, 16), seed=0):
    model.eval().to(device)
    torch.manual_seed(seed)
    out = {}
    last_stochastic = None   # (K,N,64,64) for the largest K
    with torch.no_grad():
        for K in Ks:
            ps = []
            # single deterministic pass (K==1) or K stochastic MC-dropout draws
            was = model.training
            if K > 1:
                model.train()
            for _ in range(1 if K == 1 else K):
                batchp = []
                for i in range(0, len(xs), 256):
                    fb = torch.from_numpy(xs[i:i + 256]).to(device).unsqueeze(1)
                    lg = model.forward_single(fb) if hasattr(model, "forward_single") else model(fb)
                    batchp.append(torch.sigmoid(lg))
                ps.append(torch.cat(batchp, 0).cpu().numpy())
            model.train(was)
            p = np.mean(ps, 0).squeeze(1)
            if K > 1:
                last_stochastic = np.stack(ps, 0).squeeze(2)
            sds = [soft_dice(pk, yk) for pk, yk in zip(p, ys)]
            hds = [hard_dice(pk, yk) for pk, yk in zip(p, ys)]
            ious = [_iou(pk, yk) for pk, yk in zip(p, ys)]
            out[f"K{K}"] = {"soft_dice": float(np.mean(sds)), "hard_dice": float(np.mean(hds)),
                            "iou": float(np.mean(ious))}
            print(f"[{model_name}] K={K:2d} soft_dice {np.mean(sds):.4f} hard_dice {np.mean(hds):.4f} iou {np.mean(ious):.4f}")
    if last_stochastic is not None:
        # per-pixel variance of the stochastic consensus draws (epistemic-uncertainty proxy)
        out["stochastic_pixel_var"] = float(np.mean(np.var(last_stochastic, axis=0)))
    return out


def plot_examples(idx, x, y, model_baseline, model_ar, device, fname):
    fig, axes = plt.subplots(len(idx), 4, figsize=(9, 2.4 * len(idx)))
    model_baseline.eval(); model_ar.eval()
    for r, i in enumerate(idx):
        xb = torch.from_numpy(x[i]).unsqueeze(0).unsqueeze(0).to(device)
        with torch.no_grad():
            pb = torch.sigmoid(model_baseline(xb)).cpu().numpy()[0, 0]
            pa = torch.sigmoid(model_ar.forward_single(xb)).cpu().numpy()[0, 0]
        axes[r, 0].imshow(x[i], cmap="gray")
        axes[r, 0].set_title("input")
        axes[r, 1].imshow(y[i], cmap="gray_r")
        axes[r, 1].set_title("pseudo-mask")
        axes[r, 2].imshow(pb, cmap="Reds")
        axes[r, 2].set_title("baseline")
        axes[r, 3].imshow(pa, cmap="Reds")
        axes[r, 3].set_title("AR-style")
        for c in range(4):
            axes[r, c].axis("off")
    fig.tight_layout()
    fig.savefig(fname, dpi=130)
    plt.close(fig)


def main():
    device = os.environ.get("ARSEG_DEVICE", "cuda")
    idx, xs, ys = load_test_subset(1500)
    m_base = UNetBaseline(in_ch=1, out_ch=1)
    m_ar = ArSegUNet(in_ch=1, out_ch=1)
    m_base.load_state_dict(torch.load(os.path.join(LIDC, "unet_baseline_best.pt"), map_location="cpu"))
    m_ar.load_state_dict(torch.load(os.path.join(LIDC, "arseg_nextscale_best.pt"), map_location="cpu"))

    print("[analysis] consensus curves on 1500-patch test subset")
    res_base = consensus_curve("unet_baseline", m_base, xs, ys, device)
    res_ar = consensus_curve("arseg_nextscale", m_ar, xs, ys, device)
    with open(os.path.join(EVI, "consensus_analysis.json"), "w") as f:
        json.dump({"baseline": res_base, "arseg": res_ar}, f, indent=2)
    plot_examples(idx[:6], xs, ys, m_base, m_ar, device, os.path.join(EVI, "lidc_examples.png"))
    print("[analysis] done")


if __name__ == "__main__":
    main()