#!/usr/bin/env python3
"""Mechanism ablation + figures.

(1) Next-scale-conditioning ablation: from the *trained* AR-style checkpoint, replace the
    coarse-mask conditioning with a constant map (ablate_coarse=True) and re-measure test
    Soft-Dice / IoU on LIDC.  The performance drop isolates the contribution of the
    cross-scale (coarse->fine) conditioning channel.
(2) Training-curve & bar figures for results/.

Evidence goes to results/evidence/.
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
EVI = os.path.join(ROOT, "evidence")
os.makedirs(EVI, exist_ok=True)


@torch.no_grad()
def test_metrics(model, x, y, device, batch=512, ar=False, ablate=False):
    model.eval().to(device)
    if hasattr(model, "ablate_coarse"):
        model.ablate_coarse = ablate
    sds, hds, ious = [], [], []
    for i in range(0, len(x), batch):
        xi = torch.from_numpy(x[i:i + batch]).to(device).unsqueeze(1)
        lg = model.forward_single(xi) if ar else model(xi)
        p = torch.sigmoid(lg).cpu().numpy()[:, 0]
        for pk, yk in zip(p, y[i:i + batch]):
            sds.append(soft_dice(pk, yk)); hds.append(hard_dice(pk, yk)); ious.append(_iou(pk, yk))
    return {"soft_dice": float(np.mean(sds)), "hard_dice": float(np.mean(hds)),
            "iou": float(np.mean(ious)), "n": len(x)}


def main():
    device = os.environ.get("ARSEG_DEVICE", "cuda")
    x_te = np.load(os.path.join(ROOT, "results", "cache", "lidc", "x_test.npy"))
    y_te = np.load(os.path.join(ROOT, "results", "cache", "lidc", "y_test.npy"))

    m_ar = ArSegUNet(in_ch=1, out_ch=1)
    m_ar.load_state_dict(torch.load(os.path.join(ROOT, "results", "lidc", "arseg_nextscale_best.pt"), map_location="cpu"))

    full = test_metrics(m_ar, x_te, y_te, device, ar=True, ablate=False)
    ablated = test_metrics(m_ar, x_te, y_te, device, ar=True, ablate=True)
    ablation = {
        "with_coarse_conditioning": full,
        "coarse_ablated(const_0.5)": ablated,
        "soft_dice_delta": round(full["soft_dice"] - ablated["soft_dice"], 4),
        "iou_delta": round(full["iou"] - ablated["iou"], 4),
    }
    with open(os.path.join(EVI, "nextscale_ablation.json"), "w") as f:
        json.dump(ablation, f, indent=2)
    print(json.dumps(ablation, indent=1))

    # ---- training curves figure ----
    figs = []
    for ds in ("lidc", "brats"):
        for model_name, fn in (
            ("unet_baseline", "unet_baseline.json" if ds == "lidc" else "unet_baseline_wt.json"),
            ("arseg_nextscale", "arseg_nextscale.json" if ds == "lidc" else "arseg_nextscale_wt.json")):
            p = os.path.join(ROOT, "results", ds, fn)
            if os.path.exists(p):
                d = json.load(open(p))
                figs.append((ds, model_name, d["history"]))
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    for ds in ("lidc", "brats"):
        ax = axes[0] if ds == "lidc" else axes[1]
        for model_name, h in [(n, h) for (d2, n, h) in figs if d2 == ds]:
            key = "val_soft_dice" if ds == "lidc" else "val_soft_dice"
            ax.plot([e["epoch"] for e in h], [e[key] for e in h], label=model_name)
        ax.set_title(f"{ds} validation (soft Dice)" if ds == "lidc" else "brats WT validation (soft Dice)")
        ax.set_xlabel("epoch"); ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(EVI, "training_curves.png"), dpi=130)
    plt.close(fig)
    print("figures written")


if __name__ == "__main__":
    main()