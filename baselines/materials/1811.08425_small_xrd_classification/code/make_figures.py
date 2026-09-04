"""Generate publication-style figures from results and data."""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import config
from data_loader import load_data, _read_exp, _bg_remove, _smooth, _normalize
from augmentation import _find_peaks_norm, _scale_peaks, _remove_peaks, \
    _shift_pattern

R = config.RESULTS_DIR
F = config.FIGURES_DIR
SG = config.SG_ENCODING


def load(tag):
    with open(os.path.join(R, f"{tag}.json")) as f:
        return json.load(f)


def fig_class_examples():
    d = load_data()
    fig, axes = plt.subplots(4, 2, figsize=(11, 13))
    for c in range(7):
        ax = axes.flat[c]
        idx = np.where(d["y_exp"] == c)[0][:2]
        for i in idx:
            ax.plot(d["tw"], d["X_exp"][i], lw=0.9, alpha=0.85,
                    label=f"sample {i}")
        ax.set_title(f"SG {c}: {SG[c]}", fontsize=10)
        ax.set_xlabel("2$\\theta$ (°)")
        ax.grid(alpha=0.25)
    axes.flat[7].axis("off")
    fig.suptitle("Processed experimental XRD spectra by space group "
                 "(background removal + SG smoothing + normalisation)")
    fig.tight_layout()
    fig.savefig(os.path.join(F, "fig_spectra_by_class.png"), dpi=130)


def fig_augmentation_demo():
    d = load_data()
    tw, X = d["tw"], d["X_exp"]
    rng = np.random.default_rng(3)
    spec = X[0]
    peaks, widths = _find_peaks_norm(spec, tw)
    fig, axes = plt.subplots(1, 3, figsize=(13, 3.6))
    for ax, (title, fn) in zip(axes.ravel(), [
        ("Peak scaling (Eq.1)", lambda s: _scale_peaks(s, peaks, widths, rng)),
        ("Peak removal (Eq.2)", lambda s: _remove_peaks(s, peaks, widths, rng)),
        ("Pattern shift (Eq.3)", lambda s: _shift_pattern(s, tw, rng)),
    ]):
        out = fn(spec.copy())
        ax.plot(tw, spec, lw=0.8, color="0.4", label="original")
        ax.plot(tw, out, lw=0.9, color="C3", label="augmented")
        ax.set_title(title, fontsize=11)
        ax.grid(alpha=0.25)
    axes[0].legend(loc="upper right")
    fig.tight_layout()
    fig.savefig(os.path.join(F, "fig_augmentation_demo.png"), dpi=130)


def fig_cv_bars():
    aug = load("mlp_aug_s3")["agg"]
    no = load("mlp_noaug_s3")["agg"]
    fig, ax = plt.subplots(figsize=(6, 4))
    x = np.arange(2)
    means = [no["accuracy_mean"], aug["accuracy_mean"]]
    stds = [no["accuracy_std"], aug["accuracy_std"]]
    ax.bar(x, means, yerr=stds, width=0.5, capsize=6,
           color=["0.55", "C0"])
    ax.set_xticks(x, ["no augmentation", "with augmentation"])
    ax.set_ylabel("5-fold CV subset accuracy")
    ax.axhline(0.89, color="C1", ls="--", lw=1, label="paper ≈0.89")
    ax.axhline(0.86, color="k", ls=":", lw=1, label="full-mark 0.86")
    ax.legend()
    ax.set_ylim(0.5, 1.0)
    ax.grid(alpha=0.3, axis="y")
    fig.tight_layout()
    fig.savefig(os.path.join(F, "fig_cv_aug_vs_noaug.png"), dpi=130)


def fig_coarsening():
    steps, accs, stds = [], [], []
    for c4, s in [(1, 0.04), (2, 0.08), (3, 0.12), (4, 0.16), (8, 0.32)]:
        d = load(f"mlp_aug_s3_coarse{c4}") if c4 > 1 else load("mlp_aug_s3")
        if d is None:
            continue
        steps.append(s)
        accs.append(d["agg"]["accuracy_mean"])
        stds.append(d["agg"]["accuracy_std"])
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.errorbar(steps, accs, yerr=stds, marker="o", capsize=4, lw=1.5)
    ax.axhline(0.85, color="C2", ls="--", lw=1, label="paper ≥0.85")
    ax.axhline(0.80, color="k", ls=":", lw=1, label="rubric ≥0.80")
    ax.set_xlabel("2$\\theta$ step (°)")
    ax.set_ylabel("5-fold CV subset accuracy (aug)")
    ax.legend()
    ax.grid(alpha=0.3)
    ax.set_ylim(0.7, 1.0)
    ax.set_xscale("log")
    fig.tight_layout()
    fig.savefig(os.path.join(F, "fig_coarsening.png"), dpi=130)


def fig_confusion():
    aug = load("mlp_aug_s3")
    cm = np.asarray(aug["agg"]["overall_cm"])
    fig, ax = plt.subplots(figsize=(6.5, 5.5))
    im = ax.imshow(cm, cmap="Blues")
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(j, i, int(cm[i, j]), ha="center", va="center",
                    color="white" if cm[i, j] > 0.5 * cm.max() else "black")
    ax.set_xticks(range(7), SG, rotation=45, ha="right")
    ax.set_yticks(range(7), SG)
    ax.set_xlabel("predicted"); ax.set_ylabel("true")
    ax.set_title("Confusion matrix (5-fold pooled, aug)")
    fig.colorbar(im, shrink=0.85)
    fig.tight_layout()
    fig.savefig(os.path.join(F, "fig_confusion.png"), dpi=130)


def main():
    fig_class_examples()
    fig_augmentation_demo()
    fig_cv_bars()
    fig_coarsening()
    fig_confusion()
    print("figures written to", F)


if __name__ == "__main__":
    main()