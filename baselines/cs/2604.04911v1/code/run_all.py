"""Reproducible pipeline entry point for the SpatialEdit (2604.04911v1) analysis.

Run from the agent_solution directory:

    python code/run_all.py

This executes, in order:
  1. analyze_frozen_data.py    -- benchmark inventory + camera geometry + FE/VE aggregation
  2. verify_paper_tables.py    -- claim numbers vs paper tables + consistency checks
  3. fe_by_command.py          -- FE decomposition by command type + zoom-handling sensitivity
  4. build_evidence.py         -- write results/evidence_table.csv and results/metrics.json

All inputs are read from the frozen data location (F:\\dataset\\2604.04911v1);
nothing is downloaded.  The only model-inference outputs used are the frozen
per-sample FE/VE CSVs under <data_root>/results/ that were produced by the
prior reproduction pipeline on the real benchmark triplets.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main() -> int:
    scripts = [
        "analyze_frozen_data.py",
        "verify_paper_tables.py",
        "fe_by_command.py",
        "build_evidence.py",
    ]
    for name in scripts:
        print(f"\n=== {name} ===", flush=True)
        rc = subprocess.run([sys.executable, str(HERE / name)], cwd=HERE.parent).returncode
        if rc != 0:
            print(f"FAILED: {name} (exit {rc})", file=sys.stderr)
            return rc
    print("\nAll scripts completed successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
