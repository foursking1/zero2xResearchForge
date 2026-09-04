"""Extra figures: Mo accuracy-vs-DOF Pareto and Mo930 dataset-size convergence."""
import json
import os
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

RESULTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results")
FIGDIR = os.path.join(RESULTS, "figures")
os.makedirs(FIGDIR, exist_ok=True)


def fig_pareto():
    d = json.load(open(os.path.join(RESULTS, "mo_pareto_scan.json")))
    fig, ax = plt.subplots(figsize=(6.4, 4.6))
    kern = {k: v for k, v in d.items() if k.startswith("kernel_gap_proxy_n")}
    ks = sorted(kern, key=lambda k: kern[k]["n_params"])
    ax.plot([kern[k]["n_params"] for k in ks], [kern[k]["test_energy_mae"] for k in ks],
            "-o", lw=1.4, ms=5, label="kernel (GAP-proxy), n_basis scan")
    for name, m, off in [("linear_snap_proxy", "s", (30, 8)), ("quad_snap_proxy", "^", (-10, 12)),
                         ("mlp_nnp_proxy", "D", (-70, -4))]:
        if name in d:
            ax.scatter([d[name]["n_params"]], [d[name]["test_energy_mae"]], marker=m, s=55,
                       label=name.replace("_", " ").replace(" proxy", "-proxy"))
            ax.annotate(name.split("_proxy")[0], (d[name]["n_params"], d[name]["test_energy_mae"]),
                        xytext=(d[name]["n_params"] + off[0], d[name]["test_energy_mae"] + off[1]),
                        fontsize=7)
    ax.set_xscale("log")
    ax.set_xlabel("trainable parameters (model expense)", )
    ax.set_ylabel("test energy MAE (meV/atom)")
    ax.set_title("Mo: accuracy vs model expense (Pareto-style view)")
    ax.legend(fontsize=7, loc="upper right")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(FIGDIR, "fig_mo_pareto.png"), dpi=160)
    plt.close(fig)
    print("wrote fig_mo_pareto.png")


def fig_convergence():
    d = json.load(open(os.path.join(RESULTS, "mo930_convergence.json")))
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.2))
    nxs = [194, 930]
    for ax, key, lab, unt in [(axes[0], "test_energy_mae_aimd", "test energy MAE (AIMD subset)", "meV/atom"),
                              (axes[1], "test_force_mae_aimd", "test force MAE (AIMD subset)", "eV/A")]:
        for model in ["kernel_gap_proxy", "mlp_nnp_proxy"]:
            v = [d[f"{model}/n194"][key], d[f"{model}/n930"][key]]
            ax.plot(nxs, v, "-o", label=model.split("_proxy")[0])
        ax.set_xticks(nxs)
        ax.set_xlabel("training configurations (frozen Mo data)")
        ax.set_ylabel(f"{lab} ({unt})")
        ax.set_title(lab)
        ax.legend(fontsize=7)
        ax.grid(alpha=0.3)
    fig.suptitle("Mo: accuracy vs training-set size (in-domain AIMD-NVT test subset)")
    fig.tight_layout()
    fig.savefig(os.path.join(FIGDIR, "fig_mo_conv.png"), dpi=160)
    plt.close(fig)
    print("wrote fig_mo_conv.png")


if __name__ == "__main__":
    fig_pareto()
    fig_convergence()