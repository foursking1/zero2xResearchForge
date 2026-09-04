"""Figure generation (SVG + PNG) for the reproduction.

Reads the tables produced by run_experiments.py from results/ and writes:

  figure_scatter_complete.png/svg  -- observed vs imputed log10(mass), the
                                      six-property complete subset, 150 test
                                      planets (paper Fig. 3 style).
  figure_scatter_full.png/svg      -- observed vs imputed log10(mass), full
                                      archive six-property regime (paper
                                      Fig. 7 style, colours show the 150-test
                                      subset).
  figure_errorbars.png/svg         -- epsilon comparison per algorithm across
                                      datasets.
  figure_distributions.png/svg     -- kNN x KDE mass distributions for a set
                                      of example planets (paper Fig. 4 / 8
                                      style).
"""
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import config

FULL_ALGOS = ["kNN-Imputer", "MissForest", "GAIN", "MICE", "kNN×KDE"]
TAGS = {"kNN-Imputer": "knn", "MissForest": "missforest", "GAIN": "gain",
        "MICE": "mice", "kNN×KDE": "knnkde"}

PLOT_COLORS = {"kNN-Imputer": "#1f77b4", "MissForest": "#2ca02c",
               "GAIN": "#d62728", "MICE": "#9467bd", "kNN×KDE": "#ff7f0e"}


def _scatter(ax, log_obs, log_imp, name, eps, eps150=None, color="#1f77b4",
             s=10, alpha=0.5):
    ax.scatter(log_obs, log_imp, s=s, alpha=alpha, color=color)
    lo = np.nanmin([log_obs.min(), log_imp.min()]) - 0.2
    hi = np.nanmax([log_obs.max(), log_imp.max()]) + 0.2
    ax.plot([lo, hi], [lo, hi], "k--", lw=0.8, alpha=0.7)
    tag = f"epsilon = {eps:.3f}"
    if eps150 is not None:
        tag += f"\n150-subset = {eps150:.3f}"
    ax.text(0.04, 0.96, name, transform=ax.transAxes, fontsize=9, va="top",
            fontweight="bold")
    ax.text(0.04, 0.06, tag, transform=ax.transAxes, fontsize=8, va="top")
    ax.set_xlim(lo, hi)
    ax.set_ylim(lo, hi)
    ax.tick_params(labelsize=7)
    ax.set_aspect("equal")


def scatter_complete():
    df = pd.read_csv(config.RESULTS_DIR / "imputed_complete.csv")
    fig, axes = plt.subplots(2, 3, figsize=(11, 7))
    axes = axes.ravel()
    order = ["kNN-Imputer", "MissForest", "MICE", "GAIN", "kNN×KDE", "mBM-class"]
    colmap = {**TAGS,
              "mBM-class": "mBM-class", "PS-CP (CK17)": "PS-CP(CK17)"}
    for ax, name in zip(axes, order):
        key = "log_mass_imp_" + colmap[name]
        eps = _eps(df["log_mass_obs"], df[key])
        _scatter(ax, df["log_mass_obs"], df[key], name, eps,
                 color=PLOT_COLORS.get(name, "#555555"))
        ax.set_xlabel("observed $\\log_{10}(M/M_\\oplus)$", fontsize=8)
        if ax is axes[0]:
            ax.set_ylabel("imputed $\\log_{10}(M/M_\\oplus)$", fontsize=8)
    fig.suptitle("Complete six-property subset - 150 test planets (transit regime)",
                 fontsize=11)
    fig.tight_layout()
    for ext in ("png", "svg"):
        fig.savefig(config.RESULTS_DIR / f"figure_scatter_complete.{ext}", dpi=150)
    plt.close(fig)


def _eps(o, i):
    m = np.isfinite(o) & np.isfinite(i)
    d = (o[m] - i[m]) * np.log(10.0)
    return float(np.sqrt(np.mean(d ** 2)))


def scatter_full():
    df = pd.read_csv(config.RESULTS_DIR / "imputed_full.csv")
    meta_full = pd.read_csv(config.DATA_CSV, low_memory=False)
    testdf = pd.read_csv(config.RESULTS_DIR / "imputed_complete.csv")
    test_names = set(testdf["planet"])
    mask150 = df["planet"].isin(test_names)

    fig, axes = plt.subplots(2, 3, figsize=(11, 7))
    axes = axes.ravel()
    for ax, name in zip(axes, FULL_ALGOS):
        key = "log_mass_imp_" + TAGS[name]
        m = df["log_mass_obs"].notna() & df[key].notna()
        e_full = _eps(df["log_mass_obs"][m], df[key][m])
        m150 = m & mask150
        e150 = _eps(df["log_mass_obs"][m150], df[key][m150])
        ax.scatter(df["log_mass_obs"][m], df[key][m], s=6, alpha=0.4,
                   color="#999999")
        ax.scatter(df["log_mass_obs"][m150], df[key][m150], s=16, alpha=0.9,
                   color=PLOT_COLORS[name])
        lo = -1.2
        hi = np.nanmax([df["log_mass_obs"].max(), df[key].max()]) + 0.3
        ax.plot([lo, hi], [lo, hi], "k--", lw=0.8, alpha=0.7)
        ax.text(0.04, 0.95, name, transform=ax.transAxes, fontsize=9, va="top",
                fontweight="bold")
        ax.text(0.04, 0.04, f"epsilon = {e_full:.3f}   (150-subset {e150:.3f})",
                transform=ax.transAxes, fontsize=8, va="top")
        ax.set_xlim(lo, hi)
        ax.set_ylim(lo, hi)
        ax.tick_params(labelsize=7)
        ax.set_xlabel("observed $\\log_{10}(M/M_\\oplus)$", fontsize=8)
        if ax is axes[0]:
            ax.set_ylabel("imputed $\\log_{10}(M/M_\\oplus)$", fontsize=8)
    # PS-CP panel
    ax = axes[-1]
    key = "log_mass_imp_pscp"
    m = df["log_mass_obs"].notna() & df[key].notna()
    e_full = _eps(df["log_mass_obs"][m], df[key][m])
    m150 = m & mask150
    e150 = _eps(df["log_mass_obs"][m150], df[key][m150])
    ax.scatter(df["log_mass_obs"][m], df[key][m], s=6, alpha=0.4, color="#999999")
    ax.scatter(df["log_mass_obs"][m150], df[key][m150], s=16, alpha=0.9,
               color="#555555")
    lo = -1.2
    hi = np.nanmax([df["log_mass_obs"].max(), df[key].max()]) + 0.3
    ax.plot([lo, hi], [lo, hi], "k--", lw=0.8, alpha=0.7)
    ax.text(0.04, 0.95, "PS-CP (CK17)", transform=ax.transAxes, fontsize=9,
            va="top", fontweight="bold")
    ax.text(0.04, 0.04, f"epsilon = {e_full:.3f}   (150-subset {e150:.3f})",
            transform=ax.transAxes, fontsize=8, va="top")
    ax.set_xlim(lo, hi)
    ax.set_ylim(lo, hi)
    ax.tick_params(labelsize=7)
    ax.set_xlabel("observed $\\log_{10}(M/M_\\oplus)$", fontsize=8)
    fig.suptitle("Full archive - six properties (transit regime)", fontsize=11)
    fig.tight_layout()
    for ext in ("png", "svg"):
        fig.savefig(config.RESULTS_DIR / f"figure_scatter_full.{ext}", dpi=150)
    plt.close(fig)


def errorbars():
    ev = pd.read_csv(config.RESULTS_DIR / "evidence_table.csv")
    # use eps_full for full/extended rows, eps for complete rows
    key = np.where(ev["dataset"] == "complete", ev["eps"], ev["eps"]).astype(float)
    datasets = ["complete", "full"]
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.2))
    for ax, dset in zip(axes, ["complete", "full"]):
        sub = ev[ev["dataset"] == dset]
        order = sub.sort_values("eps")["algorithm"].tolist()
        sub = sub.set_index("algorithm").loc[order]
        ax.bar(range(len(sub)), sub["eps"], color=[
            PLOT_COLORS.get(a, "#555555") for a in sub.index])
        ax.set_xticks(range(len(sub)))
        ax.set_xticklabels(sub.index, rotation=30, ha="right", fontsize=7)
        ax.set_ylabel("epsilon = RMS(ln(m_obs/m_imp))")
        ax.set_title(f"Dataset: {dset}")
        for i, v in enumerate(sub["eps"]):
            ax.text(i, v, f"{v:.3f}", ha="center", va="bottom", fontsize=7)
    # extended bar
    fig2, ax2 = plt.subplots(figsize=(4, 4))
    ext = ev[ev["dataset"] == "extended"]
    for i, v in enumerate(ext["eps"]):
        ax2.bar(i, v, color="#ff7f0e")
    vals = ext["eps"].tolist()
    ax2.set_xticks(range(len(ext)))
    ax2.set_xticklabels(ext["algorithm"], rotation=30, ha="right", fontsize=8)
    ax2.set_ylabel("epsilon")
    ax2.set_title("Dataset: extended (8 properties)")
    fig2.tight_layout()
    fig.tight_layout()
    for ext_ in ("png", "svg"):
        fig.savefig(config.RESULTS_DIR / f"figure_errorbars.{ext_}", dpi=150)
        fig2.savefig(config.RESULTS_DIR / f"figure_errorbars_extended.{ext_}",
                     dpi=150)
    plt.close(fig)
    plt.close(fig2)


def distributions_examples():
    stats = pd.read_csv(config.RESULTS_DIR / "distributions_stats.csv")
    rows = list(stats.iterrows())
    cols = 2
    n = len(rows)
    rows_n = int(np.ceil(n / cols))
    fig, axes = plt.subplots(rows_n, cols, figsize=(11, 3.6 * rows_n))
    axes = np.asarray(axes).ravel()

    for k, (ax, (i, row)) in enumerate(zip(axes, rows)):
        name = row["planet"]
        fname = f"distribution_{name.replace(' ', '_')}.csv"
        grid = pd.read_csv(config.RESULTS_DIR / fname)
        ax.fill_between(10 ** grid["log10_mass"], grid["density"],
                        alpha=0.35, color="#ff7f0e")
        ax.plot(10 ** grid["log10_mass"], grid["density"], lw=1.4,
                color="#e06c00")
        ax.axvline(10 ** row["obs_logmass"], color="k", ls="-", lw=1.4,
                   alpha=0.9)
        ax.axvline(10 ** row["imp_logmass"], color="#d62728", ls="--", lw=1.2,
                   alpha=0.8)
        modes = row.get("n_modes")
        if pd.isna(modes):
            mlabel = "8-property"
        else:
            mlabel = f"{int(modes)} mode(s)"
        ax.set_xscale("log")
        ax.tick_params(labelsize=8)
        ax.set_title(f"{name}  |  {mlabel}  |  w68={float(row['width_68']):.2f} dex"
                     if not pd.isna(row.get("width_68")) else
                     f"{name}  |  8-property", fontsize=9)
        ax.set_xlabel("mass [M$_\\oplus$]", fontsize=8)
        ax.set_ylabel("density", fontsize=8)
    for ax in axes[len(rows):]:
        ax.axis("off")
    fig.suptitle("kNN x KDE mass distributions (full archive, transit regime; "
                 "solid black = observed mass, dashed red = imputed mean)",
                 fontsize=11)
    fig.tight_layout()
    for ext in ("png", "svg"):
        fig.savefig(config.RESULTS_DIR / f"figure_distributions.{ext}", dpi=150)
    plt.close(fig)


def make_all():
    scatter_complete()
    scatter_full()
    errorbars()
    distributions_examples()


if __name__ == "__main__":
    make_all()