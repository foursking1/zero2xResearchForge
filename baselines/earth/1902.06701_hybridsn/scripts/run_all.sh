#!/usr/bin/env bash
# One-command reproduction of the full pipeline (task 1902.06701_hybridsn).
# Recommended: run the steps one by one for interactive progress.
set -euo pipefail
cd "$(dirname "$0")/.."
ROOT=$(pwd)
DEVICE=${DEVICE:-cpu}
EPOCHS=${EPOCHS:-100}

echo "[1/5] protocol splits (30/10/70%) ..."
python protocols/split_data.py --seeds 0,1,2 --ratio 0.3
python protocols/split_data.py --seeds 0,1,2 --ratio 0.1
python protocols/split_data.py --seeds 0,1,2 --ratio 0.7

echo "[2/5] HybridSN training (3 seeds) ..."
DEVICE=$DEVICE python method/train_hybridsn.py --seeds 0,1,2 --epochs $EPOCHS --device $DEVICE

echo "[3/5] 2D-CNN baseline + SVM baseline ..."
DEVICE=$DEVICE python method/train_2dcnn.py --seeds 0,1,2 --epochs $EPOCHS --device $DEVICE
python method/baseline_svm.py --seeds 0,1,2

echo "[4/5] ratio sensitivity (Q3) ..."
DEVICE=$DEVICE python method/train_ratio_sweep.py --ratios 10,30,70 --epochs 60 --device $DEVICE

echo "[5/5] finalize deliverables ..."
DEVICE=$DEVICE python method/finalize.py --device $DEVICE

echo "DONE -> results under $ROOT/results, figures under $ROOT/evidence"