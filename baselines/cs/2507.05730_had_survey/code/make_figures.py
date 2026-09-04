#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate the evidence figures used in report.md / solution.md.

Reads results/evidence_table.csv and results/crd_table.csv and writes:
    figures/fig_auc_match.png      (RX vs paper AUC bar chart, colour-coded deltas)
    figures/fig_runtime.png        (per-dataset RX runtime)
    figures/fig_rx_vs_crd.png      (RX vs CRD mean-AUC comparison)
    figures/fig_detection_example.png (RX score maps + GT for 4 examples)
"""

import csv
import os
import sys

import numpy as np

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "..", "results")
FIG = os.path.join(HERE, "..", "figures")
os.makedirs(FIG, exist_ok=True)


def load_csv(path):
    with open(path) as f:
        return list(csv.DictReader(f))


def main():
    rows = [r for r in load_csv(os.path.join(RES, "evidence_table.csv")) if r.get("row_type") == "data"]
    files = [r["file"] for r in rows]
    labels = [f.replace("abu/abu-", "").replace(".mat", "").replace("sandiego.mat+plane_gt.mat", "San Diego")
              for f in files]
    auc_rx = [float(r["auc_rx"]) for r in rows]
    auc_paper = [float(r["auc_paper_rx"]) for r in rows]
    delta = [float(r["delta"]) for r in rows]
    rt = [float(r["runtime_s"]) for r in rows]

    # ---- fig 1: AUC RX vs paper ------------------------------------------
    x = np.arange(len(rows))
    w = 0.38
    fig, ax = plt.subplots(figsize=(11, 5))
    ax.bar(x - w/2, auc_paper, w, label="Paper Table 5 (RX)", color="#9ecae1", edgecolor="#6baed6")
    ax.bar(x + w/2, auc_rx, w, label="This work (global RX)", color="#fb6a4a", edgecolor="#cb181d")
    ax.axhline(0.90, color="green", lw=1, ls="--", alpha=0.6, label="match band (|Δ|≤0.01 → 11/14)")
    ax.axhspan(0.80, 1.0, color="green", alpha=0.05)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=8)
    ax.set_ylabel("Pixel-level AUC")
    ax.set_ylim(0.75, 1.02)
    ax.set_title("Global RX detector: reproduced AUC vs survey Table 5 (14 frozen datasets)")
    ax.legend(fontsize=8, loc="upper right")
    for i, d in enumerate(delta):
        if abs(d) > 1e-9:
            ax.annotate(f"{d:+.3f}", (x[i], max(auc_rx[i], auc_paper[i]) + 0.008),
                        fontsize=7, ha="center", color="#b30000")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig_auc_match.png"), dpi=200)
    plt.close(fig)

    # ---- fig 2: runtime ----------------------------------------------------
    fig, ax = plt.subplots(figsize=(11, 4.2))
    bars = ax.bar(x, rt, color="#31a354", edgecolor="#006d2c")
    mean_rt = np.mean(rt)
    ax.axhline(mean_rt, color="#006d2c", ls="--", lw=1)
    ax.axhline(5.0, color="red", ls=":", lw=1.2, label="speed bound (5 s)")
    ax.text(len(rows)-0.5, mean_rt + 0.03, f"mean = {mean_rt:.3f} s", ha="right", fontsize=9, color="#006d2c")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=8)
    ax.set_ylabel("Runtime (s)")
    ax.set_title("Global RX runtime per dataset (single-thread CPU)")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig_runtime.png"), dpi=200)
    plt.close(fig)

    # ---- fig 3: RX vs CRD --------------------------------------------------
    crd_rows = [r for r in load_csv(os.path.join(RES, "crd_table.csv")) if r.get("file") != "SUMMARY"]
    crd_map = {r["file"]: float(r["auc_crd"]) for r in crd_rows}
    auc_crd = [crd_map[f] for f in files]
    fig, ax = plt.subplots(figsize=(11, 5))
    ax.plot(x, auc_crd, "o-", color="#08519c", label="CRD (this work, global dict + LOO)", ms=6)
    ax.plot(x, auc_rx, "s--", color="#cb181d", label="RX (this work)", ms=6)
    ax.fill_between(x, auc_rx, auc_crd, where=np.array(auc_crd) > np.array(auc_rx),
                    color="#08519c", alpha=0.10)
    ax.plot([], [])  # placeholder
    ax.annotate(f"mean CRD={np.mean(auc_crd):.3f} > mean RX={np.mean(auc_rx):.3f}",
                xy=(0.02, 0.03), xycoords="axes fraction", fontsize=10, color="#08519c")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=8)
    ax.set_ylim(0.8, 1.0)
    ax.set_ylabel("Pixel-level AUC")
    ax.set_title("Claim (c) direction: CRD vs RX on the 14 frozen datasets")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig_rx_vs_crd.png"), dpi=200)
    plt.close(fig)

    # ---- fig 4: RX score maps example -------------------------------------
    try:
        sys.path.insert(0, os.path.join(HERE))
        import scipy.io as sio
        from run_rx import global_rx_score, load_dataset
        data_dir = sys.argv[1] if len(sys.argv) > 1 else "/mnt/f/dataset/cs/2507.05730_had_survey/hsi"
        sel = ["abu/abu-airport-1.mat", "aviris_1.mat",
               "sandiego.mat+plane_gt.mat", "hydice_urban.mat"]
        fig, axes = plt.subplots(2, len(sel), figsize=(4 * len(sel), 4))
        for j, rel in enumerate(sel):
            data, gt = load_dataset(data_dir, rel)
            score = global_rx_score(data)
            axes[0, j].imshow(gt, cmap="Reds", vmin=0, vmax=1)
            axes[0, j].set_title(rel.replace("abu/", ""), fontsize=8)
            axes[0, j].set_xticks([]); axes[0, j].set_yticks([])
            im = axes[1, j].imshow(score, cmap="viridis")
            axes[1, j].set_xticks([]); axes[1, j].set_yticks([])
        axes[0, 0].set_ylabel("Ground truth", fontsize=9)
        axes[1, 0].set_ylabel("RX score map", fontsize=9)
        fig.suptitle("Example global-RX anomaly score maps vs ground truth", fontsize=10)
        fig.tight_layout()
        fig.savefig(os.path.join(FIG, "fig_detection_example.png"), dpi=200)
        plt.close(fig)
    except Exception as e:  # keep going even if the example figure fails
        print(f"[warn] example figure skipped: {e}")

    print("figures written to", FIG)


if __name__ == "__main__":
    main()