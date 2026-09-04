"""Generate comparison figures from results/evidence_table.csv."""
import os
import csv
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
RESULTS = os.path.join(ROOT, "results")
EVIDENCE = os.path.join(ROOT, "evidence")

ORDER = ["p_onset", "p_peak", "p_offset",
         "qrs_onset", "qrs_peak", "qrs_offset",
         "t_onset", "t_peak", "t_offset"]
LABELS = {pt: pt.replace("onset", "onset").upper() for pt in ORDER}


def load():
    with open(os.path.join(RESULTS, "evidence_table.csv")) as fo:
        rows = list(csv.DictReader(fo))
    out = {}
    for r in rows:
        out.setdefault(r["method"], {})[r["point_type"]] = r
    return out


def main():
    data = load()
    methods = ["multilead", "singlelead_ii", "singlelead_perlead_all12"]
    colors = {"multilead": "#1f77b4", "singlelead_ii": "#ff7f0e",
              "singlelead_perlead_all12": "#2ca02c"}
    names = {"multilead": "Multi-lead (12-lead consensus)",
             "singlelead_ii": "Single-lead (II)",
             "singlelead_perlead_all12": "Single-lead per-lead (12 pooled)"}

    pts = ORDER
    x = np.arange(len(pts))
    width = 0.26

    fig, axes = plt.subplots(1, 2, figsize=(16, 5.5))
    for ax, metric in zip(axes, ["se", "ppv"]):
        for mi, m in enumerate(methods):
            vals = [float(data[m][pt][metric]) if pt in data[m] else 0.0
                    for pt in pts]
            ax.bar(x + (mi - 1) * width, vals, width, label=names[m],
                   color=colors[m], alpha=0.9)
        ax.set_xticks(x)
        ax.set_xticklabels([LABELS[p] for p in pts], rotation=30, fontsize=8)
        ax.set_ylabel(f"{'Sensitivity' if metric=='se' else 'Positive predictive value'} (%)")
        ax.set_ylim(0, 105)
        ax.set_title(f"{'Sensitivity (Se)' if metric=='se' else 'PPV'} by point type")
        ax.legend(fontsize=9, loc="lower right")
        ax.grid(alpha=0.3)
    fig.suptitle("LUDB delineation: multi-lead vs single-lead methods (200 records, "
                 "ANSI/AAMI EC57 +/-150 ms)", fontsize=12)
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    fig.savefig(os.path.join(EVIDENCE, "se_ppv_comparison.png"), dpi=150)
    print("saved", os.path.join(EVIDENCE, "se_ppv_comparison.png"))

    # Time errors
    fig2, ax = plt.subplots(figsize=(9, 5))
    for mi, m in enumerate(methods):
        means = [float(data[m][pt]["mean_err_ms"]) for pt in pts]
        stds = [float(data[m][pt]["std_err_ms"]) for pt in pts]
        ax.errorbar(np.arange(len(pts)) + (mi-1)*0.12, means, yerr=stds,
                    fmt="o", capsize=4, label=names[m], color=colors[m])
    ax.axhline(0, color="k", lw=0.8)
    ax.set_xticks(np.arange(len(pts)))
    ax.set_xticklabels([LABELS[p] for p in pts], rotation=30, fontsize=8)
    ax.set_ylabel("time error m +/- sd (ms)")
    ax.set_title("Delineation time errors by point type")
    ax.legend(fontsize=9)
    ax.grid(alpha=0.3)
    fig2.tight_layout()
    fig2.savefig(os.path.join(EVIDENCE, "time_errors.png"), dpi=150)
    print("saved", os.path.join(EVIDENCE, "time_errors.png"))


if __name__ == "__main__":
    main()