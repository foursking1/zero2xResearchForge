#!/usr/bin/env bash
# Full reproducible pipeline for task 2502.20784_arseg_next_scale_seg.
# Usage:  bash run_all.sh [device]
#   device: cuda (default if a GPU is detected) or cpu
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"

DEVICE="${1:-}"
if [ -z "$DEVICE" ]; then
  if nvidia-smi -L >/dev/null 2>&1; then DEVICE=cuda; else DEVICE=cpu; fi
fi
export ARSEG_DEVICE="$DEVICE"
export OMP_NUM_THREADS=6

echo "== device: $DEVICE =="

python3 01_prepare_lidc.py
python3 02_prepare_brats.py

# LIDC: baseline + AR-style (+ multi-scale-supervision ablation)
python3 03_run_lidc.py --device "$DEVICE" --epochs 30 --batch 256 --run baseline
python3 03_run_lidc.py --device "$DEVICE" --epochs 30 --batch 256 --run arseg
python3 03_run_lidc.py --device "$DEVICE" --epochs 30 --batch 256 --run arseg_nosup

# BraTS: primary binary WT protocol + auxiliary 4-class analysis
python3 04b_run_brats_wt.py --device "$DEVICE" --epochs 25 --batch 64
python3 04_run_brats.py        --device "$DEVICE" --epochs 25 --batch 64

# Mechanism analysis: consensus aggregation curves, next-scale conditioning ablation,
# extra figures
python3 05_consensus_analysis.py
python3 07_ablate_and_figs.py
python3 08_figs_extra.py

# Assemble results/evidence_table.csv + results/metrics.json
python3 06_summary.py

echo "== ALL DONE =="