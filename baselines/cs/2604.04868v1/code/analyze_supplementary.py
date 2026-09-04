"""Supplementary: other parametric tests from the frozen data.

The TASK focuses on claims C01-C04, but the paper's central narrative is that
TabPFN is robust to correlated features, sample size, and label noise.  We
summarize the frozen results for those tests as supplementary context (not used
for the C01-C04 verdicts, but useful for the overall picture and mentioned in
solution.md).

Frozen evidence:
  - results/correlated_features/summary.json
  - results/sample_size/summary.json
  - results/label_noise/summary.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402


def build_summary(name, rows, x_parser):
    """Build a summary dict from frozen summary.json rows.

    x_parser: callable(row) -> x value.
    """
    xs = [float(x_parser(r)) for r in rows]
    aucs = np.asarray([r["roc_auc"] for r in rows], dtype=float)
    return {
        "test": name,
        "x_values": xs,
        "roc_auc_values": aucs.tolist(),
        "min_roc_auc": float(aucs.min()),
        "max_roc_auc": float(aucs.max()),
        "mean_roc_auc": float(aucs.mean()),
        "std_roc_auc": float(aucs.std(ddof=1)),
        "range_roc_auc": float(aucs.max() - aucs.min()),
    }


def main():
    # Correlated: labels like 'Corr=8, Rand=502, Total=512'
    corr = build_summary(
        "correlated_features",
        C.load_json("correlated_features/summary.json"),
        lambda r: int(r["label"].split(",")[0].split("=")[1]),
    )

    # Sample size: labels like 'N=2000 (train=1600)'
    sample = build_summary(
        "sample_size",
        C.load_json("sample_size/summary.json"),
        lambda r: int(r["label"].split("=")[1].split(" ")[0]),
    )

    # Label noise: labels like 'noise=0.20'
    noise = build_summary(
        "label_noise",
        C.load_json("label_noise/summary.json"),
        lambda r: float(r["label"].split("=")[1]),
    )

    report = {"correlated_features": corr, "sample_size": sample,
              "label_noise": noise}

    with open(C.OUT_RESULTS / "supplementary_parametric.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)
    print(json.dumps(report, indent=2, default=str))

    # ---- Combined figure ----------------------------------------------------
    fig, axes = plt.subplots(1, 3, figsize=(12, 3.6))
    for ax, data, xlabel in zip(
        axes,
        [corr, sample, noise],
        ["correlated features", "training rows N", "label noise fraction"],
    ):
        xs = data["x_values"]
        aucs = data["roc_auc_values"]
        ax.plot(xs, aucs, "o-", color="#2a6f8f")
        ax.axhline(data["min_roc_auc"], color="green", ls="--", lw=1,
                   label=f"min={data['min_roc_auc']:.4f}")
        ax.set_xlabel(xlabel)
        ax.set_ylabel("ROC-AUC")
        ax.set_title(f"{data['test']}\nrange={data['range_roc_auc']:.4f}")
        ax.legend(fontsize=7)
        ax.grid(alpha=0.3)
    fig.suptitle("Supplementary frozen parametric results (context only)")
    fig.tight_layout()
    fig.savefig(C.OUT_FIGURES / "fig_supplementary_parametric.png", dpi=150)
    plt.close(fig)

    return report


if __name__ == "__main__":
    main()
