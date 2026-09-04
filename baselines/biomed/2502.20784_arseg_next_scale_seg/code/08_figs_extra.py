#!/usr/bin/env python3
"""Extra evidence figures: BraTS axial example + summary bar chart."""
from __future__ import annotations
import os, sys, json
import numpy as np
import torch
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import UNetBaseline, ArSegUNet

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
EVI = os.path.join(ROOT, "evidence")
os.makedirs(EVI, exist_ok=True)


def brats_example():
    device = os.environ.get("ARSEG_DEVICE", "cuda")
    x = np.load(os.path.join(ROOT, "results", "cache", "brats", "x_test.npy"))
    y = np.load(os.path.join(ROOT, "results", "cache", "brats", "y_test.npy"))
    m_base = UNetBaseline(in_ch=1, out_ch=1)
    m_ar = ArSegUNet(in_ch=1, out_ch=1)
    m_base.load_state_dict(torch.load(os.path.join(ROOT, "results", "brats", "unet_baseline_wt_best.pt"), map_location="cpu"))
    m_ar.load_state_dict(torch.load(os.path.join(ROOT, "results", "brats", "arseg_nextscale_wt_best.pt"), map_location="cpu"))
    m_base.to(device); m_ar.to(device)
    m_base.eval(); m_ar.eval()
    # pick test slices with some foreground, spread across the two test patients
    with open(os.path.join(ROOT, "results", "cache", "brats", "meta_test.txt")) as f:
        meta = f.readlines()
    fg = y.sum((1, 2))
    sel = [i for i in np.argsort(fg)[-2:][::-1]]
    sel += [i for i in range(len(y)) if 200 < fg[i] < 2000][:2]
    fig, axes = plt.subplots(len(sel), 4, figsize=(9, 2.2 * len(sel)))
    with torch.no_grad():
        for r, i in enumerate(sel):
            xi = torch.from_numpy(x[i]).unsqueeze(0).unsqueeze(0).to(device)
            pb = torch.sigmoid(m_base(xi)).cpu().numpy()[0, 0]
            pa = torch.sigmoid(m_ar.forward_single(xi)).cpu().numpy()[0, 0]
            gt = (y[i] > 0).astype(np.float32)
            axes[r, 0].imshow(x[i], cmap="gray"); axes[r, 0].set_title(meta[i].strip())
            axes[r, 1].imshow(gt, cmap="gray_r"); axes[r, 1].set_title("GT WT")
            axes[r, 2].imshow(pb, cmap="Reds"); axes[r, 2].set_title("baseline")
            axes[r, 3].imshow(pa, cmap="Reds"); axes[r, 3].set_title("AR-style")
            for c in range(4):
                axes[r, c].axis("off")
    fig.tight_layout()
    fig.savefig(os.path.join(EVI, "brats_wt_examples.png"), dpi=130)
    plt.close(fig)
    print("brats example figure written")


def bar_chart():
    lidc = json.load(open(os.path.join(ROOT, "results", "lidc", "arseg_nextscale.json")))
    lidc_b = json.load(open(os.path.join(ROOT, "results", "lidc", "unet_baseline.json")))
    br = json.load(open(os.path.join(ROOT, "results", "brats", "arseg_nextscale_wt.json")))
    br_b = json.load(open(os.path.join(ROOT, "results", "brats", "unet_baseline_wt.json")))
    fig, axes = plt.subplots(1, 2, figsize=(9, 4))
    labels = ["baseline", "AR-style"]
    vals1 = [lidc_b["test"]["single"]["soft_dice"], lidc["test"]["single"]["soft_dice"]]
    axes[0].bar(labels, vals1, color=["#888", "#c4463a"])
    axes[0].set_ylim(0.9, 1.0); axes[0].set_title("LIDC test Soft-Dice (higher better)")
    for i, v in enumerate(vals1):
        axes[0].text(i, v + 0.002, f"{v:.4f}", ha="center")
    vals2 = [br_b["test"]["single"]["hard_dice"] * 100, br["test"]["single"]["hard_dice"] * 100]
    axes[1].bar(labels, vals2, color=["#888", "#c4463a"])
    axes[1].set_ylim(70, 90); axes[1].set_title("BraTS-2021-mini WT hard-Dice (higher better)")
    for i, v in enumerate(vals2):
        axes[1].text(i, v + 0.5, f"{v:.1f}", ha="center")
    fig.tight_layout()
    fig.savefig(os.path.join(EVI, "summary_bars.png"), dpi=130)
    plt.close(fig)
    print("bar chart written")


if __name__ == "__main__":
    brats_example()
    bar_chart()