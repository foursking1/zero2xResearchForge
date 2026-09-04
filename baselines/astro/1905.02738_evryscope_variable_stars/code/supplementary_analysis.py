#!/usr/bin/env python3
"""
supplementary_analysis.py - Joint Size x SpType tables, edge cases, and figures.

Reads results/evidence_table.csv and prints/addecore the joint Class x Size
distributions (per table), the 2 unclassified rows, the missing (`---`)
marker handling, and renders a 2-panel figure saved to results/.

Usage: python3 supplementary_analysis.py [EVIDENCE_CSV] [OUT_PREFIX]
"""
import os
import sys
from collections import Counter

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def spectral_class(sptype: str) -> str:
    """Leading alpha chars => spectral class (handles 'K6 2', '' etc.)."""
    return "".join(ch for ch in (sptype or "").strip() if ch.isalpha()) or "NONE"


def main():
    ev_csv = sys.argv[1] if len(sys.argv) > 1 else "results/evidence_table.csv"
    out_prefix = sys.argv[2] if len(sys.argv) > 2 else "results/fig_catalog"

    import csv
    rows = []
    with open(ev_csv, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if r["table"] in ("table10", "table11"):
                rows.append(r)

    eb = [r for r in rows if r["table"] == "table11"]
    var = [r for r in rows if r["table"] == "table10"]

    print("=== Joint Size x Spectral Class ===")
    def joint(tbl):
        j = Counter()
        for r in tbl:
            j[(r["size"] or "empty", spectral_class(r["sptype"]))] += 1
        return j
    j_eb, j_var = joint(eb), joint(var)
    all_keys = sorted(set(j_eb) | set(j_var))

    print(f"{'class':<8}{'EB ms':>7}{'EB gnt':>7}{'VAR ms':>7}{'VAR gnt':>7}{'VAR emp':>7}  TOT")
    cmap = {"EB": {"ms": j_eb.get(("ms", ""), 0), "giant": 0},
            "VAR": {"ms": j_var.get(("ms", ""), 0), "giant": j_var.get(("giant", ""), 0)}}
    # simpler: aggregate by class+size on fixed class order
    classes = sorted({spectral_class(r["sptype"]) for r in rows if spectral_class(r["sptype"]) != "NONE"})
    for c in classes:
        row = [c]
        for tbl, cols in ((eb, ["ms", "giant"]), (var, ["ms", "giant", "empty"])):
            for sz in cols:
                row.append(sum(1 for r in tbl if (r["size"] or "empty") == sz and spectral_class(r["sptype"]) == c))
        print(f"{row[0]:<8}{row[1]:>7}{row[2]:>7}{row[3]:>7}{row[4]:>7}{row[5]:>7}  {sum(row[1:]):>4}")

    # unclassified rows
    print("\n=== 2 not-classified rows (empty Size) ===")
    for r in rows:
        if not (r["size"] or "").strip():
            print(f"  {r['table']:>7}  esid={r['esid']}  Per={r['per_h']} h  Amp={r['amp']}")

    # period/amp extremes
    def stats(tbl, key):
        xs = [float(r[key]) for r in tbl if r[key]]
        xs.sort()
        import statistics as st
        return {"min": min(xs), "max": max(xs), "p25": st.quantiles(xs, n=4)[0],
                "median": st.median(xs), "p75": st.quantiles(xs, n=4)[2]}
    print("\n=== Period / amplitude percentiles ===")
    for name, tbl in (("EB", eb), ("VAR", var)):
        p = stats(tbl, "per_h")
        a = stats(tbl, "amp")
        print(f"  {name:>3}  Per[h]  min={p['min']:8.2f} med={p['median']:8.2f} max={p['max']:8.2f}"
              f" | Amp[mag] min={a['min']:.3f} med={a['median']:.3f} max={a['max']:.3f}")

    # ---- figure ----
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.4))

    # panel 1: Size x Class stacked bars per table
    import numpy as np
    classes_order = ["O", "B", "A", "F", "G", "K", "M"]
    cnt = Counter()
    for r in rows:
        cls = spectral_class(r["sptype"])
        cnt[cls] += 1
    xlabs = [c for c in classes_order if cnt.get(c, 0) > 0]
    width = 0.38
    for i in (0, 1):
        tbl = eb if i == 0 else var
        label = "EB" if i == 0 else "VAR"
        color = "#4C78A8" if i == 0 else "#F58518"
        y = [sum(1 for r in tbl if spectral_class(r["sptype"]) == c) for c in xlabs]
        ax1.bar(np.arange(len(xlabs)) + i * width, y, width, label="EB" if i == 0 else "VAR",
                color=color)
        s = [sum(1 for r in tbl if (r["size"] or "empty") == z) for z in ("ms", "giant", "empty")]
        print(f"    {label:>3} size={dict(zip(('ms','giant','empty'), s))}")
    ax1.set_xticks(np.arange(len(xlabs)) + width / 2)
    ax1.set_xticklabels(xlabs)
    ax1.set_ylabel("N discoveries")
    ax1.set_xlabel("Spectral class")
    ax1.set_title("Discovered population by spectral class")
    ax1.legend()
    ax1.grid(alpha=0.3)

    # panel 2: period vs amplitude scatter
    for r in eb:
        ax2.scatter(float(r["per_h"]), float(r["amp"]), s=9, color="#4C78A8",
                    alpha=0.65, label="EB" if False else "")
    for r in var:
        ax2.scatter(float(r["per_h"]), float(r["amp"]), s=12, color="#F58518",
                    alpha=0.65, marker="^")
    from matplotlib.patches import Patch
    from matplotlib.lines import Line2D
    ax2.axvline(75, color="gray", ls="--", lw=1)
    ax2.text(0.985, 0.06, "Per=75h", transform=ax2.transAxes)
    ax2.axhspan(0.05, 0.25, color="gray", alpha=0.10)
    ax2.set_xscale("log"); ax2.set_yscale("log")
    ax2.set_xlabel("Period [h]"); ax2.set_ylabel("Amplitude [mag]")
    ax2.set_title("Period–amplitude plane (shaded: amp 5–25%)")
    ax2.legend(handles=[Line2D([0],[0],marker="o",ls="",color="#4C78A8",label="EB (table11)"),
                        Line2D([0],[0],marker="^",ls="",color="#F58518",label="Var (table10)")],
               loc="upper left")
    ax2.grid(alpha=0.3, which="both")

    fig.tight_layout()
    fig.savefig(f"{out_prefix}.png", dpi=160)
    print(f"\nwrote figure: {out_prefix}.png")


if __name__ == "__main__":
    main()