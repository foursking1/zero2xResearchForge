#!/usr/bin/env bash
set -euo pipefail
# Reproducibility driver: run all analysis steps end-to-end.
# Requires: python3 with pandas/numpy/scikit-learn/matplotlib.
# Data: the frozen package (see config.py candidate paths or $CTO_DATA_DIR).
cd "$(dirname "$0")"
python3 01_reproduce_ctorf.py
python3 02_consistency_coverage.py
python3 03_finalize_metrics.py
echo "ALL DONE -> ../results/ , ../report_fig/"