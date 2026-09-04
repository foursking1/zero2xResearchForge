"""
Generate figures from results (radial risk + sparsity risk).

Figures mirror the paper's Figures 1-3 (radial, p=5/50/100) and Figures 4-6
(sparsity, p=5/50/100). Uses fresh full-range radial results and frozen/fresh
sparsity results.
"""
import json
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

RES = Path(__file__).resolve().parent.parent / "results"
FIG = RES / "figures"
FIG.mkdir(parents=True, exist_ok=True)

STYLE = {
    "MLE": dict(color="gray", ls="--", lw=1.5),
    "Fixed-scale BNN": dict(color="red", ls="-", lw=2),
    "BetaPrime (minimax)": dict(color="blue", ls="-", lw=2),
    "Dropout BNN": dict(color="green", ls="-", lw=2),
}


def plot_radial(p):
    d = json.load(open(RES / f"radial_risk_p{p}_full.json"))
    r = np.array(d["r_values"])
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.axhline(p, color="gray", ls="--", lw=1.5, label="MLE")
    for key, name in [("fixed_risk", "Fixed-scale BNN"),
                      ("betaprime_risk", "BetaPrime (minimax)"),
                      ("dropout_risk", "Dropout BNN")]:
        ax.plot(r, d[key], **STYLE[name], label=name)
    ax.set_xlabel(r"$||\theta||$")
    ax.set_ylabel("Risk")
    ax.set_title(f"Radial Risk Curves (p={p})")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.savefig(FIG / f"radial_risk_p{p}.png", dpi=140, bbox_inches="tight")
    plt.close(fig)
    print(f"saved radial_risk_p{p}.png")


def plot_sparsity(p):
    # try fresh first, then reduced-MC dense1c, then frozen
    fresh = RES / f"sparsity_p{p}_fresh.json"
    dense = RES / f"sparsity_p{p}_dense1c.json"
    if fresh.exists():
        d = json.load(open(fresh))
    elif dense.exists():
        d = json.load(open(dense))
    else:
        cand = list((Path(r"F:\dataset\2604.04673v1\output\data")).glob(f"*sparsity_p{p}*.json"))
        if not cand:
            print(f"no sparsity data for p={p}")
            return
        d = json.load(open(cand[-1]))
    r = np.array(d["r_values"])
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.axhline(p, color="gray", ls="--", lw=1.5, label="MLE")
    ax.plot(r, d["betaprime_risk"], **STYLE["BetaPrime (minimax)"], label="BetaPrime (minimax)")
    cmap = plt.cm.viridis
    hs = d.get("horseshoe_risk", {})
    for i, (k, arr) in enumerate(sorted(hs.items(), key=lambda x: int(x[0]))):
        ax.plot(r, arr, color=cmap(0.1 + 0.8 * i / max(len(hs) - 1, 1)),
                lw=1.5, label=f"Horseshoe (k={k})")
    ax.set_xlabel(r"$||\theta||$")
    ax.set_ylabel("Risk")
    ax.set_title(f"Sparsity-Dependent Risk (p={p})")
    ax.legend(fontsize=9, loc="upper left")
    ax.grid(alpha=0.3)
    fig.savefig(FIG / f"sparsity_risk_p{p}.png", dpi=140, bbox_inches="tight")
    plt.close(fig)
    print(f"saved sparsity_risk_p{p}.png")


if __name__ == "__main__":
    for p in [5, 50, 100]:
        plot_radial(p)
    for p in [5, 50, 100]:
        plot_sparsity(p)
