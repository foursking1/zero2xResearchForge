"""
Generate the evidence figure: per-atom band energy and drift vs system size.

Reads ../results/size_transfer_results.json (or given path) and writes
../results/size_transfer_figure.png with two panels:
  (a) band energy per atom (eV/atom) vs system size, with the 256-atom
      baseline and the paper's +/-43 meV/atom (chemical accuracy) window
      highlighted;
  (b) drift vs 256-atom baseline (meV/atom) on a log scale in size.

Usage: python make_figure.py [path_to_size_transfer_results.json]
"""
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
IN_PATH = (sys.argv[1] if len(sys.argv) > 1
           else os.path.join(HERE, "size_transfer_results.json"))
OUT_PATH = os.path.join(HERE, "..", "results", "size_transfer_figure.png")


def main():
    with open(IN_PATH, encoding="utf-8") as f:
        data = json.load(f)
    results = data["results"]
    drift = data.get("drift", {})
    sizes = sorted(int(k) for k in results)
    band = np.array([results[str(n)]["band_energy_per_atom_eV"] for n in sizes])
    drift_mev = np.array([drift[str(n)]["band_energy_per_atom_drift_meV"]
                          for n in sizes])
    electrons = np.array([results[str(n)]["electrons_per_atom"] for n in sizes])

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.2))
    ax = axes[0]
    ax.plot(sizes, band, "o-", color="C0", label="MALA band energy/atom")
    ax.axhline(band[0], color="gray", ls="--", lw=1,
               label="256-atom baseline")
    ax.fill_between(sizes, band[0] - 0.043, band[0] + 0.043,
                    color="C1", alpha=0.15,
                    label="+/-43 meV/atom (chem. accuracy)")
    ax.set_xscale("log")
    ax.set_xticks(sizes)
    ax.get_xaxis().set_major_formatter(plt.ScalarFormatter())
    ax.set_xlabel("system size (atoms)")
    ax.set_ylabel("band energy per atom (eV)")
    ax.set_title("(a) band energy per atom vs size")
    ax.legend(fontsize=7)

    ax = axes[1]
    colors = ["C0" if abs(d) <= 10 else ("C2" if abs(d) <= 43 else "C3")
              for d in drift_mev]
    ax.axhspan(0, 10, color="C2", alpha=0.15,
               label=r"0-10 meV/atom (gold)" )
    ax.axhspan(10, 43, color="C0", alpha=0.12, label="10-43 meV/atom")
    ax.axhspan(-43, -10, color="C0", alpha=0.12)
    ax.axhspan(-10, 0, color="C2", alpha=0.15)
    ax.axhline(0, color="black", lw=0.8)
    ax.scatter(sizes, drift_mev, c=colors, s=60, zorder=5)
    ax.plot(sizes, drift_mev, "--", color="gray", lw=0.8)
    for x, y in zip(sizes, drift_mev):
        ax.annotate(f"{y:+.1f}", (x, y), textcoords="offset points",
                    xytext=(0, 8), ha="center", fontsize=8)
    ax.set_xscale("log")
    ax.set_xticks(sizes)
    ax.get_xaxis().set_major_formatter(plt.ScalarFormatter())
    ax.set_xlabel("system size (atoms)")
    ax.set_ylabel("drift relative to 256 (meV/atom)")
    ax.set_title("(b) band-energy drift vs 256-atom baseline")
    ax.legend(fontsize=7, loc="lower right")

    ax = axes[2]
    ax.plot(sizes, electrons, "s-", color="C4")
    ax.axhline(2.0, color="gray", ls="--", lw=1, label="2 e-/atom (Be)")
    ax.set_xscale("log")
    ax.set_xticks(sizes)
    ax.get_xaxis().set_major_formatter(plt.ScalarFormatter())
    ax.set_xlabel("system size (atoms)")
    ax.set_ylabel("electrons / atom")
    ax.set_ylim(1.990, 2.006)
    ax.set_title("(c) electron-count self-consistency")
    ax.legend(fontsize=7)

    fig.tight_layout()
    fig.savefig(OUT_PATH, dpi=150)
    print("wrote", OUT_PATH)


if __name__ == "__main__":
    main()