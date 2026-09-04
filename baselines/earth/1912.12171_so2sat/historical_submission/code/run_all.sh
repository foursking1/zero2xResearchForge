#!/usr/bin/env bash
# End-to-end pipeline for the So2Sat LCZ42 (1912.12171) L1 task.
# All results derive from the frozen official validation.h5.
#
# Steps:
#   1) prep_data        : split (stratified 80/20, seed 42) + train-stats normalization.
#   2) run_baselines    : RBF-SVM / RF / kNN shallow baselines (S2 & S1+S2).
#   3) train_cnn        : ResNeXt-CBAM, S2-only (primary) and S1+S2 fusion.
#   4) verify_results   : recompute all metrics from saved predictions (fast).
#
# The deep runs can use --device cpu (threads=10) or --device cuda; run them
# sequentially if using the shared GPU.

set -e
cd "$(dirname "$0")/.."

echo "=== 1/4 data prep ==="
python3 code/prep_data.py

echo "=== 2/4 baselines (S2 / S1+S2) ==="
python3 code/run_baselines.py

echo "=== 3/4 ResNeXt-CBAM S2-only ==="
python3 code/train_cnn.py --bands s2  --variant l --epochs 42 --batch-size 128 --lr 0.1 --device cuda

echo "=== 3b/4 ResNeXt-CBAM S1+S2 fusion ==="
python3 code/train_cnn.py --bands s1s2 --variant l --epochs 38 --batch-size 128 --lr 0.1 --device cuda

echo "=== 4/4 verification ==="
python3 code/verify_results.py

echo "=== optional robustness ==="
python3 code/robustness_split.py