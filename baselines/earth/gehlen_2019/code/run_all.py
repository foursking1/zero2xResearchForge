#!/usr/bin/env python3
"""
run_all.py
==========
Run the complete gehlen_2019 claim-evaluation pipeline in order:

  01_c01_lvi_recompute.py       -> recompute LVI per LFA (CM2.6) from frozen data
  02_c02_temperature_compare.py -> characterise CM2.6/BNAM temperature data
  03_evidence_summary.py        -> assemble evidence_table.csv + metrics.json
  04_sensitivity_lvi.py         -> LVI binning sensitivity analysis

Usage:
    python run_all.py            (from anywhere; paths are absolute in the scripts)

Requirements (tested on Python 3.13 / Windows):
    numpy, pandas, scipy, netCDF4, pyreadr, matplotlib, openpyxl, pyyaml
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = [
    "01_c01_lvi_recompute.py",
    "02_c02_temperature_compare.py",
    "03_evidence_summary.py",
    "04_sensitivity_lvi.py",
]


def main() -> int:
    for s in SCRIPTS:
        print(f"\n########## Running {s} ##########")
        r = subprocess.run([sys.executable, str(HERE / s)])
        if r.returncode != 0:
            print(f"FAILED: {s} (exit {r.returncode})")
            return r.returncode
    print("\nAll scripts completed successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
