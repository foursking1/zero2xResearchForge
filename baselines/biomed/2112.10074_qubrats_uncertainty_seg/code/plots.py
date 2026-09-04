"""Create analysis figures from results:
  1. DSC / FTP / FTN curves vs uncertainty threshold (mean over test cases) per model.
  2. Example case slice visualization (prediction + uncertainty + GT).
  3. Ranking decoupling scatter: QU-BraTS score vs DSC.
"""
import json
import os
import sys

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt

sys.path.insert(0, os.path.dirname(__file__))
from qub_metrics import normalize_unc_0_100  # noqa: E402

ENTITIES = ["ET", "TC", "WT"]


def main():
    base = os.path.dirname(__file__)
    res_dir = os.path.join(base, "..", "results")
    fig_dir = os.path.join(res_dir, "figures")
    os.makedirs(fig_dir, exist_ok=True)

    with open(os.path.join(res_dir, "per_case_results.json")) as f:
        all_results = json.load(f)
    with open(os.path.join(base, "..", "config.json")) as f:
        cfg = json.load(f)
    models = cfg["models"] + [e["name"] for e in cfg["ensembles"]]

    colors = plt.rcParams["axes.prop_cycle"].by_key()["color"]
    lw = 1.8

    # ---- 1) curves per entity ----
    for e in ENTITIES:
        fig, axes = plt.subplots(1, 3, figsize=(14, 4), sharey=False)
        for i, (lab, key) in enumerate([("DSC vs tau", "dsc_curve"),
                                        ("FTP (filtered TP ratio) vs tau", "ftp_curve"),
                                        ("FTN (filtered TN ratio) vs tau", "ftn_curve")]):
            for j, m in enumerate(models):
                xs, ys = [], []
                for cid in all_results[m]:
                    r = all_results[m][cid][e]
                    xs.append(100 - np.array(r["thresholds"]))  # filtering level
                    ys.append(np.array(r[key]))
                x = xs[0]
                y = np.mean(ys, axis=0)
                axes[i].plot(x, y, color=colors[j % len(colors)], lw=lw,
                             label=f"{m} (AUC={y.mean() / 100: .3f})" if False else f"{m}")
            axes[i].set_xlabel("$100 - \\tau$ (filter level)")
            axes[i].set_title(f"{e}: {lab}")
            axes[i].set_xlim(0, 100)
            axes[i].set_ylim(0, 1.05)
            axes[i].legend(fontsize=7, framealpha=0.9)
        fig.tight_layout()
        fig.savefig(os.path.join(fig_dir, f"curves_{e}.png"), dpi=150)
        plt.close(fig)

    # ---- 2) box-ish summary of score and dice per model ----
    ev = pd.read_csv(os.path.join(res_dir, "evidence_table.csv"))
    fig, ax = plt.subplots(1, 2, figsize=(12, 4))
    for a, met in zip(ax, ["score", "dice"]):
        for e in ENTITIES:
            sub = ev[ev["entity"] == e]
            a.plot(sub["model"], sub[met], marker="o", label=e)
        a.set_ylabel(met)
        a.legend()
        a.tick_params(axis="x", rotation=30)
    fig.tight_layout()
    fig.savefig(os.path.join(fig_dir, "model_score_dice.png"), dpi=150)
    plt.close(fig)

    # ---- 3) ranking decoupling scatter ----
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.4))
    for a, e in zip(axes, ENTITIES):
        sub = ev[ev["entity"] == e].sort_values("dice")
        a.scatter(sub["dice"], sub["score"], s=90)
        for _, r in sub.iterrows():
            a.annotate(r["model"], (r["dice"], r["score"]), fontsize=8)
        a.set_title(f"{e} decoupling")
        a.set_xlabel("segmentation DSC")
        a.set_ylabel("QU-BraTS score")
    fig.tight_layout()
    fig.savefig(os.path.join(fig_dir, "ranking_decoupling.png"), dpi=150)
    plt.close(fig)

    print("figures written to", fig_dir)


if __name__ == "__main__":
    main()