#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Supplementary figures for the 4FGL population analysis (CPU only, matplotlib).
Re-parses the frozen catalog (same byte offsets as analyze_4fgl.py) and draws:

  fig1_glat_distribution.png : |GLAT| histogram (all sky + |b|>10 cut line)
  fig2_population_composition.png : stacked bar of class groups across the three
      populations (all sky, |b|>10, |b|>10 + extragalactic sample)

Usage: python3 make_figures.py [--data-dir PATH] [--outdir PATH]
"""

from __future__ import annotations

import argparse
import gzip
import os
import sys
from collections import Counter

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

EXPECTED_RECORDS = 5065
GZIP_SIZE = 6883415
FIELDS = {
    "Source_Name": (0, 28),
    "GLON": (37, 47),
    "GLAT": (48, 58),
    "CLASS1": (3977, 3982),
}
EXCL = {"PSR", "psr", "spp", "SNR", "snr", "PWN", "pwn", "glc", "gal",
        "sbg", "SFR", "sfr", "hmb", "HMB", "lmb", "LMB"}


def find_data_dir(provided):
    cands = [provided] if provided else []
    if os.environ.get("FROZEN_DATA_DIR"):
        cands.append(os.environ["FROZEN_DATA_DIR"])
    cands += [
        "data",
        r"F:\dataset\astro\2211.03400_fermi_4fgl_jetted_agn",
        "/mnt/f/dataset/astro/2211.03400_fermi_4fgl_jetted_agn",
        "/mnt/d/dataset/astro/2211.03400_fermi_4fgl_jetted_agn",
    ]
    for c in cands:
        dat = os.path.join(c, "4fgl.dat.gz")
        if os.path.isfile(dat) and os.path.getsize(dat) == GZIP_SIZE:
            return c
    raise FileNotFoundError("4FGL data not found; pass --data-dir")


def load(data_dir):
    rows = []
    with gzip.open(os.path.join(data_dir, "4fgl.dat.gz"), "rt",
                   encoding="latin-1") as f:
        for ln in f:
            l = ln.rstrip("\n").rstrip("\r")
            if l.strip() == "":
                continue
            rows.append({
                "name": l[0:18].strip(),
                "glon": float(l[FIELDS["GLON"][0]:FIELDS["GLON"][1]].strip()),
                "glat": float(l[FIELDS["GLAT"][0]:FIELDS["GLAT"][1]].strip()),
                "class1": l[FIELDS["CLASS1"][0]:FIELDS["CLASS1"][1]].strip(),
            })
    assert len(rows) == EXPECTED_RECORDS
    return rows


GROUP_MAP = {
    "BLL": {"bll", "BLL"},
    "FSRQ": {"fsrq", "FSRQ"},
    "bcu": {"bcu", "BCU"},
    "other-AGN": {"rdg", "RDG", "nlsy1", "NLSY1", "agn", "AGN",
                  "sey", "css", "ssrq"},
    "no-class / no counterpart": {"", "unk"},
    "galactic-excluded": {"PSR", "psr", "spp", "SNR", "snr", "PWN", "pwn",
                          "glc", "gal", "sbg", "SFR", "sfr", "hmb", "HMB",
                          "lmb", "LMB"},
}
GROUP_ORDER = ["BLL", "FSRQ", "bcu", "other-AGN", "no-class / no counterpart",
               "galactic-excluded"]
COLORS = ["#1f77b4", "#ff7f0e", "#2ca02c", "#9467bd", "#d62728", "#7f7f7f"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default=None)
    ap.add_argument("--outdir", default=os.path.dirname(os.path.abspath(__file__)))
    args = ap.parse_args()

    dd = find_data_dir(args.data_dir)
    print(f"[data] {dd}")
    rows = load(dd)
    glat = np.array([r["glat"] for r in rows])
    glon = np.array([r["glon"] for r in rows])
    cls1 = [r["class1"] for r in rows]
    m_absb = np.abs(glat) > 10.0
    nonempty = np.array([c != "" for c in cls1])
    nongal = np.array([c not in EXCL for c in cls1])
    in_samp = m_absb & nonempty & nongal

    os.makedirs(args.outdir, exist_ok=True)

    # ---- fig 1: GLAT distribution ----
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.5))
    bins = np.linspace(-90, 90, 91)
    ax1.hist(glat, bins=bins, color="#4c72b0", edgecolor="white", lw=0.3)
    ax1.axvline(10, color="red", ls="--", lw=1.2, label="|b| = 10°")
    ax1.axvline(-10, color="red", ls="--", lw=1.2)
    ax1.set_xlabel("GLAT (deg)"); ax1.set_ylabel("Number of sources")
    ax1.set_title("4FGL-DR1 all sky (5065): GLAT distribution")
    ax1.legend()

    ax2.hist(glon[np.abs(glat) > 10], bins=36, color="#55a868", edgecolor="white", lw=0.3)
    ax2.set_xlabel("GLON (deg)"); ax2.set_ylabel("Number of sources")
    ax2.set_title(f"|b|>10° ({m_absb.sum()} sources): GLON distribution")
    plt.tight_layout()
    fig.savefig(os.path.join(args.outdir, "fig1_glat_glon_distributions.png"), dpi=160)
    plt.close(fig)

    # ---- fig 2: population composition ----
    def group_counts(mask):
        c = Counter(cls1[i] for i in np.where(mask)[0])
        return {g: sum(v for k, v in c.items() if k in codes_)
                for g, codes_ in GROUP_MAP.items()}

    masks = {
        "all sky (5,065)": np.ones(len(rows), bool),
        "|b|>10° (3,646)": m_absb,
        "extragal. sample (2,866)": in_samp,
    }
    counts = {k: group_counts(m) for k, m in masks.items()}
    fig, ax = plt.subplots(figsize=(9, 5))
    width = 0.62
    x = np.arange(len(masks))
    bottom = np.zeros(len(masks))
    for i, g in enumerate(GROUP_ORDER):
        vals = np.array([counts[m][g] for m in masks])
        ax.bar(x, vals, width, bottom=bottom, label=g, color=COLORS[i],
               edgecolor="white", lw=0.4)
        bottom += vals
    for xi, m in enumerate(masks):
        ax.text(xi, bottom[xi] + 30, str(sum(counts[m].values())),
                ha="center", fontweight="bold")
    ax.set_xticks(x); ax.set_xticklabels(list(masks))
    ax.set_ylabel("Number of sources")
    ax.set_title("4FGL-DR1 population by CLASS1 group across selection layers")
    ax.legend(ncol=2, fontsize=9)
    plt.tight_layout()
    fig.savefig(os.path.join(args.outdir, "fig2_population_composition.png"), dpi=160)
    plt.close(fig)

    print("figures written to", args.outdir)
    return 0


if __name__ == "__main__":
    sys.exit(main())