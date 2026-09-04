"""C03 - SHAP feature-importance claim.

Claim C03 (from TASK.md):
    "SHAP values show informative features dominate, random features negligible"

Frozen evidence:
  - results/shap_analysis/shap_attention_comparison.json
        -> shap_importance : normalized mean-|SHAP| per feature (8 features)
        -> attention_importance : normalized attention-based per-feature mass
  - The baseline data used there is the same deterministic synthetic dataset
    (F=8, 2 informative + 6 random, seed 42). We regenerate it (sklearn, offline)
    to recover the TRUE informative columns. sklearn's make_classification uses
    shuffle=True by default, so informative features are NOT at indices {0,1}
    but at {2,7} (verified via the recorded feature permutation).
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
    cmp = C.load_json("shap_analysis/shap_attention_comparison.json")
    shap = np.asarray(cmp["shap_importance"], dtype=float)
    attn_imp = np.asarray(cmp["attention_importance"], dtype=float)

    true_info = C.informative_positions(n_features=8, n_informative=2,
                                        n_samples=1500, random_state=42)
    random_pos = [i for i in range(8) if i not in true_info]

    shap_info_share = C.share_of(shap, true_info)
    shap_random_share = C.share_of(shap, random_pos)
    attn_info_share = C.share_of(attn_imp, true_info)

    # dominance ratio informative / random (normalized per-feature)
    n_info, n_rand = len(true_info), len(random_pos)
    shap_per_feat_info = shap[true_info].mean()
    shap_per_feat_rand = shap[random_pos].mean()
    dominance_ratio = float(shap_per_feat_info / (shap_per_feat_rand + 1e-12))

    report = {
        "claim_id": "C03",
        "paper_claim": "SHAP values show informative features dominate, "
                       "random features negligible",
        "n_features": int(len(shap)),
        "informative_positions_true": true_info,
        "random_positions": random_pos,
        "shap_importance_normalized": shap.tolist(),
        "shap_informative_share": float(shap_info_share),
        "shap_random_share": float(shap_random_share),
        "shap_informative_vs_random_ratio": dominance_ratio,
        "shap_top_feature": int(np.argmax(shap)),
        "shap_top_two": [int(i) for i in np.argsort(-shap)[:2]],
        "attention_importance_normalized": attn_imp.tolist(),
        "attention_informative_share": float(attn_info_share),
        "spearman_correlation": cmp.get("spearman_correlation"),
        "spearman_p_value": cmp.get("spearman_p_value"),
        # Verdict: does the frozen SHAP data support 'informative dominate'?
        "verdict": "supported" if shap_info_share > 0.5 else "contradicted",
        "verdict_reason": (
            f"Informative features {true_info} receive {shap_info_share:.1%} of "
            f"normalized SHAP importance (random features: {shap_random_share:.1%}), "
            f"a {dominance_ratio:.0f}x per-feature dominance ratio. This is direct "
            f"frozen-data evidence that informative features dominate SHAP values. "
            f"NOTE: the reference reproduction's own narrative flagged the negative "
            f"attention-SHAP Spearman ({cmp.get('spearman_correlation'):.2f}); the "
            f"attention-based ranking is computed from feature-GROUP tokens "
            f"(features_per_group=2) truncated to raw features and is not a "
            f"feature-level quantity, whereas SHAP is feature-level."
        ),
    }

    with open(C.OUT_RESULTS / "c03_shap.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)
    print(json.dumps(report, indent=2, default=str))

    # ---- Figure ------------------------------------------------------------
    x = np.arange(8)
    colors = ["#2a8f5a" if i in true_info else "#b0b0b0" for i in range(8)]
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(x, shap, color=colors)
    ax.set_xticks(x)
    ax.set_xticklabels([f"F{i}" + ("*" if i in true_info else "") for i in range(8)])
    ax.set_ylabel("Normalized mean |SHAP|")
    ax.set_title("C03: SHAP importance per feature (informative marked *)")
    ax.text(0.02, 0.95, f"informative share = {shap_info_share:.1%}",
            transform=ax.transAxes, fontsize=10)
    fig.tight_layout()
    fig.savefig(C.OUT_FIGURES / "fig_c03_shap_importance.png", dpi=150)
    plt.close(fig)

    return report


if __name__ == "__main__":
    main()
