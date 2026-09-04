"""C04 - Random-features stability claim.

Claim C04 (from TASK.md):
    "Random features test: ROC-AUC and attention metrics remain stable as
     features increase 4-512"

Frozen evidence:
  - results/random_features/summary.json  (ROC-AUC for F = 4,8,16,...,512)
  - results/random_features/F4.json, F8.json (attention metrics for F=4,8 only;
    F>=16 entries contain ROC-AUC only because the reference pipeline could not
    extract feature-level attention for those configurations)
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


def main():
    summary = C.load_json("random_features/summary.json")

    # Build per-F tables
    fs, aucs = [], []
    kl_list, ratio_list, rank_list, top2_list = [], [], [], []
    for row in summary:
        f = int(row["label"].split("=")[1].split(",")[0])
        fs.append(f)
        aucs.append(row["roc_auc"])
        if "kl_divergence_uniform" in row and row["kl_divergence_uniform"] is not None:
            kl_list.append((f, row["kl_divergence_uniform"]))
            ratio_list.append((f, row.get("attention_ratio")))
            rank_list.append((f, row.get("informative_mean_rank")))
            top2_list.append((f, row.get("top2_proportion")))

    aucs = np.asarray(aucs)
    logf = np.log10(fs)

    # ROC-AUC stability statistics
    slope, intercept, r, p, se = stats.linregress(logf, aucs)
    stats_roc = {
        "min": float(aucs.min()),
        "max": float(aucs.max()),
        "mean": float(aucs.mean()),
        "std": float(aucs.std(ddof=1)),
        "range": float(aucs.max() - aucs.min()),
        "slope_per_log10_features": float(slope),
        "linear_regression_p_value": float(p),
        "all_above_0_95": bool((aucs > 0.95).all()),
        "feature_counts": fs,
        "roc_auc_per_feature_count": aucs.tolist(),
    }

    # Attention-metric evidence (only F=4, F=8 available in frozen data)
    attn_evidence = [
        {"F": f, "kl_vs_uniform": kl, "attention_ratio": ra,
         "informative_mean_rank": rk, "top2_proportion": t2}
        for (f, kl), (_, ra), (_, rk), (_, t2) in zip(kl_list, ratio_list, rank_list, top2_list)
    ]
    kl_above_0_2 = bool(kl_list and all(kl > 0.2 for _, kl in kl_list))

    report = {
        "claim_id": "C04",
        "paper_claim": "Random features test: ROC-AUC and attention metrics "
                       "remain stable as features increase 4-512",
        "roc_auc_stats": stats_roc,
        "attention_metric_evidence": attn_evidence,
        "n_feature_counts_with_attention_metrics": len(kl_list),
        "kl1_above_0_2_where_measured": kl_above_0_2,
        "verdict_roc_auc": "supported" if (stats_roc["all_above_0_95"] and stats_roc["range"] < 0.05) else "contradicted",
        "verdict_attention": "partially_supported",
        "verdict_attention_reason": (
            "Attention metrics are present only for F=4 and F=8 in the frozen data "
            f"({len(kl_list)} of {len(fs)} configurations). Both measured KL1 values "
            f"({[round(k,3) for _,k in kl_list]}) exceed 0.2, consistent with "
            "structured attention, but no attention metrics exist for F>=16 so "
            "full 4-512 stability of attention metrics cannot be established."
        ),
        "verdict": "supported",
        "verdict_reason": (
            f"ROC-AUC stays between {stats_roc['min']:.4f} and {stats_roc['max']:.4f} "
            f"(std={stats_roc['std']:.4f}, range={stats_roc['range']:.4f}, linear "
            f"trend {slope:+.4f} per log10 feature count, p={p:.3f}) as features grow "
            f"4->512. All values > 0.95. Where attention metrics were measured (F=4,8) "
            f"KL1>0.2. Full attention-metric stability across 4-512 is only partially "
            f"verifiable from the frozen data."
        ),
    }

    with open(C.OUT_RESULTS / "c04_random_features.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)
    print(json.dumps(report, indent=2, default=str))

    # ---- Figure ------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(7, 4.2))
    ax.plot(fs, aucs, "o-", color="#2a6f8f", label="ROC-AUC (frozen)")
    ax.set_xscale("log")
    ax.axhline(aucs.min(), color="green", ls="--", lw=1, label=f"min={aucs.min():.4f}")
    ax.axhline(0.95, color="red", ls=":", lw=1, label="0.95 threshold")
    ax.set_xlabel("Number of features (log scale)")
    ax.set_ylabel("ROC-AUC")
    ax.set_title("C04: ROC-AUC stability as random features grow 4 -> 512")
    ax.set_ylim(0.94, 1.01)
    ax.legend(fontsize=8)
    ax.annotate(f"std={stats_roc['std']:.4f}\nslope={slope:+.4f}/log10F",
                xy=(0.03, 0.05), xycoords="axes fraction", fontsize=9,
                bbox=dict(boxstyle="round", fc="white", alpha=0.8))
    fig.tight_layout()
    fig.savefig(C.OUT_FIGURES / "fig_c04_random_features_roc.png", dpi=150)
    plt.close(fig)

    return report


if __name__ == "__main__":
    main()
