#!/usr/bin/env bash
# Full reproducible pipeline for the EuroSAT RGB classification task.
# Frozen data is read from DATA_ROOT and NEVER modified.
set -euo pipefail

CODE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$CODE_DIR")"

DATA_ROOT="${EUROSAT_DATA:-/mnt/f/dataset/earth/1709.00029_eurosat/data/data}"
CACHE_DIR="${EUROSAT_CACHE:-$ROOT_DIR/cache}"
ARTIFACTS="$ROOT_DIR/artifacts"
RESULTS="$ROOT_DIR/results"
THREADS="${EUROSAT_THREADS:-10}"

mkdir -p "$ARTIFACTS" "$RESULTS"

echo "=== [1/4] decode frozen parquet -> cache ==="
python3 "$CODE_DIR/01_prepare_data.py" --data-root "$DATA_ROOT" --cache-dir "$CACHE_DIR"

echo "=== [2/4] train compact CNN on CPU ==="
python3 "$CODE_DIR/02_train.py" --epochs 45 --batch 256 --threads "$THREADS" \
    --cache-dir "$CACHE_DIR" --outdir "$ARTIFACTS"

echo "=== [3/4] evaluate on frozen test split ==="
python3 "$CODE_DIR/03_evaluate.py" --data-root "$DATA_ROOT" --threads "$THREADS" \
    --checkpoint "$ARTIFACTS/eurosat_cnn_seed00.pt" --outdir "$RESULTS"

echo "=== [4/4] confusion-pair + channel diagnostic analysis ==="
python3 "$CODE_DIR/04_analyze.py" --data-root "$DATA_ROOT" --threads "$THREADS" \
    --checkpoint "$ARTIFACTS/eurosat_cnn_seed00.pt" --outdir "$RESULTS"

echo "=== done: results in $RESULTS ==="