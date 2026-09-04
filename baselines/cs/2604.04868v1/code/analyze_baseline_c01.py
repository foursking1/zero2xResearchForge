"""C01 - Baseline claim verification.

Claim C01 (from TASK.md):
    "Baseline: TabPFN achieves ROC-AUC=0.974; attention heatmaps show progressive
     concentration across layers {3,6,9,12}"

Frozen evidence used:
  - results/baseline/baseline_metrics.json
  - results/go_no_go/gate_result.json
  - results/memory_smoke_test.json
  - results/baseline/attention_heatmaps.png  (analysed separately in
    analyze_heatmaps.py; here we only summarise the quantitative attention
    metric from the frozen JSON)

Paper reference numbers (must be labelled as paper citations):
  - ROC-AUC = 0.974  (paper Sec. 3.1)
  - attention concentration across layers {3,6,9,12}  (paper Fig. 1)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402


def main():
    baseline = C.load_json("baseline/baseline_metrics.json")
    gate = C.load_json("go_no_go/gate_result.json")
    smoke = C.load_json("memory_smoke_test.json")

    roc_auc = baseline["roc_auc"]
    attn = baseline["attention_metrics"]

    # True informative positions for the baseline data (shuffle=True, seed 42,
    # n_samples=1500 -- must match the reference experiment's sample count)
    true_info = C.informative_positions(n_features=8, n_informative=2,
                                        n_samples=1500, random_state=42)
    # What the reference pipeline assumed (first n tokens are informative)
    assumed_info = [0, 1]

    report = {
        "claim_id": "C01",
        "paper_claim": "TabPFN achieves ROC-AUC=0.974; attention heatmaps show "
                       "progressive concentration across layers {3,6,9,12}",
        "paper_roc_auc_cited": 0.974,   # paper citation, not measured
        "reproduced_roc_auc": roc_auc,
        "roc_auc_gap_vs_paper": float(roc_auc - 0.974),
        "attention_kl_vs_uniform": attn.get("kl_divergence_uniform"),
        "attention_metric_seq_len": attn.get("seq_len"),
        "attention_metric_n_heads": attn.get("n_heads"),
        "n_attention_calls": baseline.get("n_attention_calls"),
        "informative_positions_true": true_info,
        "informative_positions_assumed_by_reference": assumed_info,
        "gate_passed": gate.get("passed"),
        "gate_roc_auc": gate.get("roc_auc"),
        "memory_smoke_passed": smoke.get("passed"),
        "memory_smoke_vram_mb": smoke.get("vram_used_mb"),
    }

    # ---- Verdict logic -----------------------------------------------------
    # 1) ROC-AUC claim: reproduced value high and >= paper's 0.974.
    roc_supported = bool(roc_auc >= 0.974 and roc_auc > 0.95)
    report["roc_auc_claim_supported"] = roc_supported

    # 2) Attention concentration (quantitative, last feature-attention layer):
    #    KL vs uniform > 0.2 was the reproduction-plan pass criterion.
    kl = attn.get("kl_divergence_uniform")
    kl_structured = bool(kl is not None and kl > 0.2)
    report["attention_structured_kl_gt_0_2"] = kl_structured

    # 3) Progressive concentration across layers {3,6,9,12} is assessed from the
    #    frozen heatmap figure in analyze_heatmaps.py (pixel based). Here we note
    #    whether a per-layer quantitative artifact exists in frozen JSON data.
    per_layer_artifacts = list((C.RESULTS_DIR / "baseline").glob("*layer*"))
    report["frozen_per_layer_artifacts"] = [p.name for p in per_layer_artifacts]

    # ---- Output ------------------------------------------------------------
    out = C.OUT_RESULTS / "c01_baseline.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)
    print(json.dumps(report, indent=2, default=str))

    # ---- Figure: paper vs reproduced ROC-AUC ------------------------------
    fig, ax = plt.subplots(figsize=(5.5, 4))
    labels = ["Paper (cited)", "Reproduced (frozen)"]
    vals = [0.974, roc_auc]
    bars = ax.bar(labels, vals, color=["#b0b0b0", "#2a6f8f"])
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.003, f"{v:.4f}",
                ha="center", fontsize=10)
    ax.set_ylim(0.90, 1.02)
    ax.axhline(0.95, color="gray", ls="--", lw=1)
    ax.text(1.36, 0.951, "0.95", color="gray", fontsize=8)
    ax.set_ylabel("ROC-AUC")
    ax.set_title("C01 baseline ROC-AUC")
    fig.tight_layout()
    fig.savefig(C.OUT_FIGURES / "fig_c01_baseline_roc.png", dpi=150)
    plt.close(fig)

    return report


if __name__ == "__main__":
    main()
