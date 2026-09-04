#!/usr/bin/env bash
# Reproducible end-to-end pipeline (primary protocol: source pool = Liver,
# target = Spleen).  Runs CPU-only with fixed seeds.
#
# NOTE on the frozen data: 9/10 Liver *image* streams are gzip-truncated
# (SHA matches data/README.md); the loader in common.py recovers the real
# compressed prefix of every volume, so Sapien* runs identically on the frozen
# files.  Two fine-tune ground truths are produced:
#   (a) full-network fine-tune  -> results/finetune_liver2spleen_full.json
#   (b) decoder/probe fine-tune -> results/finetune_liver2spleen.json (PRIMARY)
set -euo pipefail
cd "$(dirname "$0")/.."

export PYTHONUNBUFFERED=1
export OMP_NUM_THREADS=16

echo "[1/7] preparing 2-D slices + inventory"
python3 code/01_prepare.py

echo "[2/7] pre-training the source-model pool on Liver"
python3 code/02_pretrain.py --source liver

echo "[3/7] full-network fine-tune on Spleen (paper-style ground truth)"
python3 code/03_finetune.py --target spleen --source liver --epochs 20 --ft-out finetune_liver2spleen_full.json

echo "[4/7] decoder/probe fine-tune on Spleen (primary ground truth)"
python3 code/03_finetune.py --target spleen --source liver --epochs 30 --freeze-encoder

echo "[5/7] transferability estimation (CC-FV, LogME, LEEP, GBC) - decoder features"
python3 code/04_te.py --source liver --target spleen --scale dec

echo "[6/7] analysis against probe ground truth (PRIMARY)"
python3 code/05_analyze.py --directions "liver2spleen" --runs probe_ft

echo "[7/7] analysis against full fine-tune ground truth (sensitivity)"
python3 code/05_analyze.py --directions "liver2spleen" --runs full_ft --ft-suffix _full

echo "DONE. results/ = metrics.json (primary), metrics_full.json, evidence_table.csv; evidence/ = figures"