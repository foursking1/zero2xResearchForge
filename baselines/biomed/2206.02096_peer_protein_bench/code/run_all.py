"""End-to-end run: data stats -> feature models -> encoders -> deliverables.

Usage:
    python3 run_all.py              # full pipeline (CPU-friendly DDE/Moran; GPU-or-CPU encoders)
"""
import os
import subprocess
import sys

HERE = os.path.dirname(__file__)
STEPS = [
    "01_data_stats.py",
    "02_feature_models.py",
    "03_encoder_models.py",
    "04_assemble_results.py",
]


def main():
    for step in STEPS:
        print("=" * 78)
        print(f"Running {step}")
        print("=" * 78)
        rc = subprocess.call([sys.executable, os.path.join(HERE, step)])
        if rc != 0:
            sys.exit(f"{step} failed with code {rc}")
    print("=" * 78)
    print("Pipeline complete. Deliverables in ../results/")


if __name__ == "__main__":
    main()