#!/usr/bin/env bash
# Run the DNABERT-2-117M + LoRA fine-tuning for the 4 frozen GUE tasks.
# Uses the GPU by default (small LoRA footprint); falls back to CPU per task arg.
# Logs to logs/finetune_<tag>.log ; per-task metrics to results/finetune/.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p logs results/finetune

DEVICE="${1:-cuda}"
TAG="${2:-full}"
MAXL_EMP=128
MAXL_MOUSE=64
MAXL_PROM300=96
MAXL_PROMCORE=32
EXTRA="${3:-}"

for spec in "EMP_H3:$MAXL_EMP" "mouse_0:$MAXL_MOUSE" "prom_300_all:$MAXL_PROM300" "prom_core_all:$MAXL_PROMCORE"; do
  ds="${spec%%:*}"; ml="${spec##*:}"
  echo "===== $(date) $ds (max_length=$ml, device=$DEVICE, tag=$TAG) ====="
  python3 -u code/run_finetune_dnabert2.py --dataset "$ds" --device "$DEVICE" \
    --max_length "$ml" --run_tag "$TAG" --out results/finetune --epochs 6 --patience 2 \
    --batch_size 16 --lr 2e-4 $EXTRA
done
echo "===== all done $(date) ====="