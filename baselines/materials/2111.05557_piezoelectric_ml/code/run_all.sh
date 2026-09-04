#!/usr/bin/env bash
# Reproducible end-to-end run for task 2111.05557_piezoelectric_ml.
# Usage:
#   export PIEZO_DATA_DIR=/path/to/2111.05557_piezoelectric_ml   # frozen data
#   bash code/run_all.sh
#
# Requires: python3 + numpy/pandas/scikit-learn/scipy/matplotlib/torch (CPU ok).
set -e
cd "$(dirname "$0")/.."

echo "[run_all] cleaning previous derived results"
rm -f results/evidence_table.csv results/ml_metrics.json results/gnn_metrics.json \
      results/metrics.json results/expansion_summary.json \
      results/data_stats.csv results/features.npz results/columns_*.csv \
      results/oof_predictions.csv results/*_oof.npy \
      results/mp_expansion_predictions.csv results/mp_top20.csv
rm -f evidence/figures/*.png

run() { echo; echo "===== $1 ====="; python3 -W ignore "$1"; }

run code/01_explore_data.py
run code/02_build_features.py
run code/03_train_ml.py
run code/04_train_gnn.py
run code/05_predict_mp.py
run code/06_summarize.py
run code/07_make_figures.py

echo
echo "[run_all] done. See results/metrics.json and report.md."