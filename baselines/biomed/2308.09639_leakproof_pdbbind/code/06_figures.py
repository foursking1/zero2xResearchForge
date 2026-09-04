"""Produce result figures in agent_solution/evidence/:
  fig1_leakage.png        leakage (ligand/target) time vs random split
  fig2_rmse_compare.png    test RMSE bars, time vs random, per model
  fig3_predictions.png     2x2 scatter of predicted-vs-true on LP test
"""
import os
import sys

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common  # noqa: E402

OUT = os.path.join(common.ROOT, "agent_solution", "results")
EV = os.path.join(common.ROOT, "agent_solution", "evidence")


def fig1_leakage():
    leak = pd.read_csv(os.path.join(OUT, "leakage_stats.csv"))
    leak = leak[leak["tag"] != "identity"]
    cats = ["train->test ligand", "train->test target(seq)", "train->test ligand OR target"]
    time_v = [leak.loc[leak.tag == "time", "train->test_lig_ratio"].iloc[0],
              leak.loc[leak.tag == "time", "train->test_seq_ratio"].iloc[0],
              leak.loc[leak.tag == "time", "train->test_lig_or_seq_ratio"].iloc[0]]
    rand_v = [leak.loc[leak.tag == "random", "train->test_lig_ratio"].iloc[0],
              leak.loc[leak.tag == "random", "train->test_seq_ratio"].iloc[0],
              leak.loc[leak.tag == "random", "train->test_lig_or_seq_ratio"].iloc[0]]
    x = np.arange(len(cats))
    w = 0.35
    fig, ax = plt.subplots(figsize=(7, 4.6))
    ax.bar(x - w / 2, time_v, w, label="LP time-based split", color="#4C72B0")
    ax.bar(x + w / 2, rand_v, w, label="Random split (seed=0)", color="#DD8452")
    ax.set_xticks(x); ax.set_xticklabels(cats, fontsize=10)
    ax.set_ylabel("fraction of test complexes leaked into train")
    ax.set_ylim(0, 0.65)
    for xi, (a, b) in enumerate(zip(time_v, rand_v)):
        ax.text(xi - w / 2, a, f"{a:.1%}", ha="center", va="bottom", fontsize=9)
        ax.text(xi + w / 2, b, f"{b:.1%}", ha="center", va="bottom", fontsize=9)
    ax.legend(fontsize=10)
    ax.set_title("Cross-train/test identity leakage in the LP-PDBBind frozen data")
    fig.tight_layout()
    fig.savefig(os.path.join(EV, "fig1_leakage.png"), dpi=150)
    plt.close(fig)


def fig2_rmse_compare():
    ev = pd.read_csv(os.path.join(OUT, "evidence_table.csv"))
    ev = ev[ev["model"].isin(["rf_ecfp_dipep", "cnn_deepdta"])]
    models = pd.Categorical(ev["model"], categories=["rf_ecfp_dipep", "cnn_deepdta"])
    order = ev.sort_values("model").reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(6.4, 4.2))
    labels = {"rf_ecfp_dipep": "Random Forest\n(ECFP + dipeptide)",
              "cnn_deepdta": "DeepDTA-like CNN"}
    pos = np.arange(len(order))
    colors = ["#4C72B0" if s == "time" else "#DD8452" for s in order["split_type"]]
    ax.bar(pos, order["rmse_test_cl2_noncov"], 0.55, color=colors)
    for p, r in zip(pos, order["rmse_test_cl2_noncov"]):
        ax.text(p, r, f"{r:.2f}", ha="center", va="bottom", fontsize=9)
    ax.set_xticks(pos)
    ax.set_xticklabels([f"{labels[m]}\n{split}" for m, split in zip(order["model"], order["split_type"])], fontsize=9)
    ax.set_ylabel("Test RMSE (kcal/mol)")
    ax.set_title("LP test set (CL2 non-covalent, n=2171)")
    ax.legend([plt.Rectangle((0, 0), 1, 1, fc="#4C72B0"), plt.Rectangle((0, 0), 1, 1, fc="#DD8452")],
              ["time-based split", "random split"])
    fig.tight_layout()
    fig.savefig(os.path.join(EV, "fig2_rmse_compare.png"), dpi=150)
    plt.close(fig)


def fig3_predictions():
    fig, axes = plt.subplots(2, 2, figsize=(8, 8))
    titles = [("RF / time", "rf", "time"), ("RF / random", "rf", "random"),
              ("CNN / time", "cnn", "time"), ("CNN / random", "cnn", "random")]
    for ax, (t, mod, sp) in zip(axes.ravel(), titles):
        p = pd.read_csv(os.path.join(OUT, f"predictions_{mod}_{sp}.csv"))
        ax.scatter(p["y_true"], p["y_pred"], s=6, alpha=0.4, c="#4C72B0")
        lo = min(p["y_true"].min(), p["y_pred"].min())
        hi = max(p["y_true"].max(), p["y_pred"].max())
        ax.plot([lo, hi], [lo, hi], "k--", lw=0.8)
        r = p["y_true"].corr(p["y_pred"])
        ax.set_title(f"{t}  (R={r:.2f})")
        ax.set_xlabel("true pK"); ax.set_ylabel("pred pK")
    fig.suptitle("LP test CL2 non-covalent predictions")
    fig.tight_layout()
    fig.savefig(os.path.join(EV, "fig3_predictions.png"), dpi=150)
    plt.close(fig)


def main():
    os.makedirs(EV, exist_ok=True)
    fig1_leakage()
    fig2_rmse_compare()
    fig3_predictions()
    print("figures saved to", EV)


if __name__ == "__main__":
    main()