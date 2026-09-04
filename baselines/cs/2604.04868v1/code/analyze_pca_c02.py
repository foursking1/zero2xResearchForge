"""C02 - PCA feature-token embedding separation claim.

Claim C02 (from TASK.md):
    "PCA of feature-token embeddings shows progressive separation across layers"

The paper (Sec. 3.1.2, Fig. 2) claims that projecting feature-token embeddings
of the TabPFN transformer onto 2D via PCA shows increasing separation between
informative and random feature tokens across layers {3,6,9,12}.

Frozen-data audit: does ANY frozen artifact contain the raw feature-token
embeddings or a PCA/embedding figure?

  * The reference reproduction's own evidence collector (artifacts/collect_
    report.json, rule R03) recorded "No PCA embedding separation figure found
    in results directory" for this claim.
  * We re-audit the entire frozen results/ tree for any embedding / PCA file.

If no frozen embedding data exists, the claim is UNVERIFIABLE from the frozen
data (inconclusive) - it is neither supported nor contradicted by the provided
artifacts, and we cannot re-run the TabPFN forward pass because no model weights
are available offline.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402

# Keywords that would indicate a PCA / embedding artifact
KEYWORDS = ("pca", "embed", "projection", "latent", "tsne")


def audit_frozen_results() -> list[str]:
    hits = []
    for root, _dirs, files in os_walk(C.RESULTS_DIR):
        for fn in files:
            low = fn.lower()
            if any(k in low for k in KEYWORDS):
                hits.append(str(Path(root) / fn))
    return sorted(hits)


def os_walk(root):
    import os

    for r, d, f in os.walk(root):
        yield r, d, f


def main():
    hits = audit_frozen_results()

    # Also check the paper text: does it describe the PCA method? (context only)
    report = {
        "claim_id": "C02",
        "paper_claim": "PCA of feature-token embeddings shows progressive "
                       "separation across layers",
        "frozen_pca_embedding_artifacts": hits,
        "n_frozen_pca_embedding_artifacts": len(hits),
        "verdict": "inconclusive",
        "verdict_reason": (
            "No frozen figure or JSON containing feature-token embeddings or a "
            "PCA projection was produced by the reference reproduction pipeline. "
            "The paper's Fig. 2 (PCA of feature-token embeddings) therefore cannot "
            "be verified from the provided frozen data. Re-running the TabPFN "
            "forward pass to regenerate embeddings is not possible offline "
            "(no cached model weights; internet downloads prohibited)."
        ),
    }

    with open(C.OUT_RESULTS / "c02_pca.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)
    print(json.dumps(report, indent=2, default=str))

    # ---- Figure: audit summary --------------------------------------------
    fig, ax = plt.subplots(figsize=(5.5, 3.4))
    ax.bar(["Frozen PCA/embedding artifacts"], [len(hits)], color="#c05555")
    ax.set_ylabel("count")
    ax.set_title("C02: PCA/embedding evidence in frozen data")
    ax.set_ylim(0, max(1, len(hits)))
    ax.text(0, len(hits) + 0.02, f"{len(hits)}", ha="center", fontsize=12)
    fig.tight_layout()
    fig.savefig(C.OUT_FIGURES / "fig_c02_pca_audit.png", dpi=150)
    plt.close(fig)

    return report


if __name__ == "__main__":
    main()
