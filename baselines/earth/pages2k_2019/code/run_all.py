"""Run the full pages2k_2019 re-discovery analysis.

Usage:  python run_all.py
Outputs: ../results/c0X_results.json for each claim, then compiles
         ../results/evidence_table.csv and ../results/metrics.json
"""
from __future__ import annotations

import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    scripts = ["analysis_c01.py", "analysis_c02.py", "analysis_c03.py", "analysis_c04.py"]
    for s in scripts:
        print(f"\n########## {s} ##########")
        r = subprocess.run([sys.executable, os.path.join(HERE, s)], cwd=HERE)
        if r.returncode != 0:
            raise SystemExit(f"script {s} failed with code {r.returncode}")

    print("\n########## compile results ##########")
    r = subprocess.run([sys.executable, os.path.join(HERE, "compile_results.py")], cwd=HERE)
    if r.returncode != 0:
        raise SystemExit(f"compile_results.py failed with code {r.returncode}")


if __name__ == "__main__":
    main()
