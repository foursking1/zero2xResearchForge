#!/usr/bin/env bash
# One-shot reproduction helper. Usage: ./run_all.sh [frozen.parquet] [device]
set -euo pipefail
cd "$(dirname "$0")"
DATA="${1:-}"
DEVICE="${2:-auto}"
SRC=src

if [ -z "$DATA" ]; then
  echo "No --data given; relying on DSAT_DATA or common.py defaults."
fi

if [ ! -f data_cache/sat6_split.npz ]; then
  python3 "$SRC/prepare_data.py" ${DATA:+--data "$DATA"}
else
  echo "Using existing data_cache/ (delete to re-prepare)."
fi

if [ -f model_sat6.pt ] && [ ! -f FORCE_RETRAIN ]; then
  echo "Checkpoint present -> fast evidence rebuild (delete model_sat6.pt to retrain)."
  python3 "$SRC/reproduce_metrics.py" ${DATA:+--data "$DATA"} --device "$DEVICE"
else
  echo "Full re-train from scratch..."
  python3 "$SRC/train.py" --device "$DEVICE" --epochs 30 --patience 7
fi

python3 "$SRC/analyze_baselines.py" ${DATA:+--data "$DATA"} || true
echo "Done. Artifacts under results/, figure/, model_sat6.pt."