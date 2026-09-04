"""Produce diagnostic figures for the solution report."""
from __future__ import annotations

import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from common import (load_reconstructions, load_models_fullforced, load_danda,
                    METHODS, METHOD_SLICES, bandpass_fft)

HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(HERE, "..", "results", "figures")
os.makedirs(FIG, exist_ok=True)
CMAP = {"PCR": "#1f77b4", "CPS": "#ff7f0e", "PAI": "#2ca02c"}


def main():
    a = load_reconstructions()
    years = np.arange(1, 2001)

    # ---- Fig 1: ensemble-mean reconstructions (re-referenced) and bandpass ----
    ref = a[1960:1990, :].mean(axis=0)
    a_ref = a - ref[None, :]
    ensmean = {m: a_ref[:, sl].mean(axis=1) for m, sl in METHOD_SLICES.items()}
    fig, ax = plt.subplots(2, 1, figsize=(11, 7), sharex=True)
    for m in METHODS:
        ax[0].plot(years, ensmean[m], lw=1.2, color=CMAP[m], label=m)
    ax[0].set_ylabel("GMST anomaly (degC, ref 1961-1990)")
    ax[0].legend(loc="upper left", ncol=3, fontsize=9)
    ax[0].set_title("Ensemble-mean reconstructions (frozen subset: 3 of 7 methods)")
    ax[0].axhline(0, color="k", lw=0.5)
    for m in METHODS:
        bp = bandpass_fft(ensmean[m])
        ax[1].plot(years, bp, lw=1.2, color=CMAP[m], label=m)
    ax[1].set_ylabel("30-200 yr filtered anomaly (degC)")
    ax[1].axhline(0, color="k", lw=0.5)
    ax[1].set_xlabel("Year CE")
    ax[1].legend(loc="upper left", ncol=3, fontsize=9)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig1_reconstructions.png"), dpi=150)
    plt.close(fig)

    # ---- Fig 2: C03 variance ratios & correlations (member pairs) ----
    models, names = load_models_fullforced()
    model_sl = slice(149, 1150)
    model_bp = np.zeros((1001, models.shape[1]))
    for j in range(models.shape[1]):
        col = models[:, j]
        if np.isnan(col).any():
            col = np.nan_to_num(col, nan=np.nanmean(col))
        model_bp[:, j] = bandpass_fft(col)[model_sl]
    model_var = model_bp.var(axis=0)
    bp = np.empty_like(a)
    for j in range(a.shape[1]):
        bp[:, j] = bandpass_fft(a[:, j])
    recon_bp = bp[999:2000, :]

    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    ratios_box, corrs_box = [], []
    for m, sl in METHOD_SLICES.items():
        mv = recon_bp[:, sl].var(axis=0)
        r = model_var[:, None] / mv[None, :]
        ratios_box.append(np.log10(r.ravel()))
        cs = np.array([np.corrcoef(model_bp[:, i], recon_bp[:, sl][:, j])[0, 1]
                       for i in range(model_bp.shape[1]) for j in range(1000)])
        corrs_box.append(cs.ravel())
    axes[0].boxplot(ratios_box, tick_labels=METHODS, showfliers=False)
    axes[0].set_ylabel("log10(var_model/var_member)")
    axes[0].axhline(0, color="k", lw=0.8, ls="--")
    axes[0].set_title("Variance ratio (30-200yr, 1000-2000 CE)")
    axes[1].boxplot(corrs_box, tick_labels=METHODS, showfliers=False)
    axes[1].set_ylabel("corr(model, member)")
    axes[1].axhline(0, color="k", lw=0.8, ls="--")
    axes[1].set_title("Model-member correlation")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig2_c03.png"), dpi=150)
    plt.close(fig)

    # ---- Fig 3: C04 residual vs control distributions ----
    d = load_danda()
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.hist(d["resid"], bins=60, density=True, alpha=0.6, label="D&A residuals (7000)")
    ax.hist(d["ctl_var"], bins=40, density=True, alpha=0.7, color="orange", label="Control runs (42)")
    ax.axvline(d["resid"].min(), color="C0", ls=":", lw=1)
    ax.axvline(d["resid"].max(), color="C0", ls=":", lw=1)
    ax.set_xlabel("Unforced variability estimate (authors' units)")
    ax.set_ylabel("density")
    ax.legend()
    ax.set_title("C04: D&A residual variability vs control-run variability")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig3_c04.png"), dpi=150)
    plt.close(fig)

    print("figures written to", FIG)


if __name__ == "__main__":
    main()
