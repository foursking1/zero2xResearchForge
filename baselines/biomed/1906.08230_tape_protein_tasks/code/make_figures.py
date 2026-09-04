"""Generate summary figures for the report (evidence/figures/*.png).

Run AFTER regression_head.py so results/evidence_table.csv exists.
"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import RESULTS_DIR, EVIDENCE_DIR, find_data_dir  # noqa: E402

plt.rcParams.update({"font.size": 9, "figure.dpi": 150})
DATA_HAND = {"#2e86ab": "pretrained / learned", "#d1495b": "hand-crafted (one-hot / composition)"}


def main():
    figdir = os.path.join(EVIDENCE_DIR, "figures")
    os.makedirs(figdir, exist_ok=True)
    table = pd.read_csv(os.path.join(RESULTS_DIR, "evidence_table.csv"))
    data_dir = find_data_dir()

    for task in ["fluorescence", "stability"]:
        # ---- grouped bar chart of Spearman rho ----
        sub = table[table.task == task].sort_values("spearman_rho", ascending=True)
        fig, ax = plt.subplots(figsize=(7, 3.4))
        colors = ["#d1495b" if (r.startswith("one-hot") or r.startswith("aa-"))
                  else "#2e86ab" for r in sub["representation"]]
        bars = ax.barh(sub["model"], sub["spearman_rho"], color=colors)
        for b, r in zip(bars, sub["spearman_rho"]):
            ax.text(b.get_width() + 0.005, b.get_y() + b.get_height() / 2,
                    f"{r:.3f}", va="center", fontsize=8)
        ax.set_xlabel("Spearman rho on test split")
        ax.set_title(f"{task}: test Spearman correlation by representation")
        ax.set_xlim(0, float(sub["spearman_rho"].max()) + 0.12)
        ax.axvline(0, color="k", lw=0.5)
        ax.legend(handles=[Patch(color="#2e86ab", label="pretrained (ESM-2, frozen)"),
                           Patch(color="#d1495b", label="hand-crafted (one-hot / comp.)")],
                  fontsize=8, loc="lower right")
        fig.tight_layout()
        fig.savefig(os.path.join(figdir, f"rho_{task}.png"))
        plt.close(fig)
        print("saved rho_%s.png" % task, flush=True)

        # ---- label distribution by split ----
        df = pd.read_csv(os.path.join(data_dir, f"{task}_dataset.csv"))
        fig, ax = plt.subplots(figsize=(6, 3))
        for st, col in [("train", "#2e86ab"), ("valid", "#f2c14e"), ("test", "#d1495b")]:
            g = df[df.stage == st].label
            ax.hist(g, bins=60, histtype="step", density=True, color=col,
                    label=f"{st} (n={len(g)})")
        ax.set_title(f"{task}: label distribution by split")
        ax.set_xlabel("label")
        ax.legend(fontsize=8)
        fig.tight_layout()
        fig.savefig(os.path.join(figdir, f"labels_{task}.png"))
        plt.close(fig)
        print("saved labels_%s.png" % task, flush=True)


if __name__ == "__main__":
    main()