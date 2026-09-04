#!/usr/bin/env bash
# End-to-end reproducible pipeline for task 2505.06646 (CheXNet reproduction).
#
# Protocol (all train/val splits fixed at seed 42; model seeds vary):
#   repro    <- seed 42 + seed 43, BCE, threshold fixed at 0.5
#   enhanced <- seed 42 + seed 43 + seed 44, Focal Loss (a=0.75) + ColorJitter
#               + RandomAffine + RandomErasing + AdamW/EMA, per-class thresholds
#               tuned on the validation split
# Final reported numbers = per-seed snapshot ensembles averaged over seeds.
#
# Frozen data location is auto-detected (see code/common.py) or set PB_DATA_DIR.
set -e
cd "$(dirname "$0")/.."
DEVICE="${DEVICE:-auto}"     # cuda / cpu / auto
EPOCHS="${EPOCHS:-22}"       # repro epochs; enhanced uses EPOCHS+2

echo "[1/6] repro seed 42"
python3 code/train.py --model repro --epochs "$EPOCHS" --lr 3e-5 \
    --weight-decay 1e-3 --label-smoothing 0.05 --aug strong --ema 0.999 \
    --seed 42 --tag s42 --device "$DEVICE"

echo "[2/6] repro seed 43"
python3 code/train.py --model repro --epochs "$EPOCHS" --lr 3e-5 \
    --weight-decay 1e-3 --label-smoothing 0.05 --aug strong --ema 0.999 \
    --seed 43 --tag r43 --device "$DEVICE"

echo "[3/6] enhanced seed 42"
python3 code/train.py --model enhanced --epochs $((EPOCHS+2)) --lr 3e-5 \
    --weight-decay 1e-3 --label-smoothing 0.05 --aug strong --ema 0.999 \
    --focal-alpha 0.75 --seed 42 --tag en_s42b --device "$DEVICE"

echo "[4/6] enhanced seed 43"
python3 code/train.py --model enhanced --epochs $((EPOCHS+2)) --lr 3e-5 \
    --weight-decay 1e-3 --label-smoothing 0.05 --aug strong --ema 0.999 \
    --focal-alpha 0.75 --seed 43 --tag en_s43 --device "$DEVICE"

echo "[5/6] enhanced seed 44"
python3 code/train.py --model enhanced --epochs $((EPOCHS+2)) --lr 3e-5 \
    --weight-decay 1e-3 --label-smoothing 0.05 --aug strong --ema 0.999 \
    --focal-alpha 0.75 --seed 44 --tag en_s44 --device "$DEVICE"

echo "[6/6] merge seeds, evaluate, plot"
python3 code/merge_seeds.py
python3 code/evaluate.py
python3 code/analysis_plots.py

echo "done. results in results/, plots in evidence/."