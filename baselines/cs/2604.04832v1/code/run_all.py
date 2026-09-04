"""Run the complete analysis end-to-end and assemble evidence.

Usage:  python run_all.py
Stages: data check -> stage1 (FDR) -> stage2 (MLP) -> stage3 (ablation)
        -> evidence table + verify.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import common

sys.path.insert(0, str(Path(__file__).parent))


def main() -> None:
    t0 = time.time()
    ok = common.verify_features_match_frozen()
    if not ok:
        print("WARNING: feature recomputation does not match frozen features; "
              "results may differ from the frozen reproduction.")
        print("Continuing with frozen feature matrix for FDR/MLP anyway.")

    import stage1_fdr, stage2_mlp, stage3_ablation, make_evidence, verify
    import robustness_mlp, generate_figures

    print("\n=== Stage 1: FDR separability ===")
    stage1_fdr.main()
    print("\n=== Stage 2: MLP oracle ===")
    stage2_mlp.main()
    print("\n=== Stage 3: sensor ablation ===")
    stage3_ablation.main()
    print("\n=== Robustness: MLP seed sweep ===")
    robustness_mlp.main()
    print("\n=== Figures ===")
    generate_figures.main()
    print("\n=== Evidence assembly ===")
    make_evidence.main()
    print("\n=== Verification ===")
    rc = verify.main()
    print(f"\ntotal time {time.time() - t0:.1f}s")
    sys.exit(rc)


if __name__ == "__main__":
    main()
