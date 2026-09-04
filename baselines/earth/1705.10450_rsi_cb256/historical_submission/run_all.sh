#!/usr/bin/env bash
# Full reproducible pipeline for task 1705.10450_rsi_cb256.
# All scripts read from the FROZEN data (parquet shards + split csv); nothing frozen is modified.
# Run from agent_solution/ root. GPU is NOT required (CPU-only by design).

set -euo pipefail
cd "$(dirname "$0")"

export TORCH_THREADS="${TORCH_THREADS:-8}"
LOG=results

echo "== 01 preprocess (decode frozen parquet -> images_224.memmap) =="
python3 -u src/01_preprocess.py 2>&1 | tee "$LOG/01_preprocess.log"

echo "== 02 frozen ResNet18 feature extraction (reference baseline) =="
python3 -u src/02_extract_features.py 2>&1 | tee "$LOG/02_extract.log"

echo "== 03 linear probe on frozen features (fast baseline) =="
python3 -u src/03_linear_probe.py 2>&1 | tee "$LOG/03_probe.log"

echo "== 03b MLP head on frozen features (fast strong baseline) =="
python3 -u src/03b_mlp_probe.py 2>&1 | tee "$LOG/03b_mlp_probe.log"

echo "== 04 MAIN: fine-tune ResNet18 (layer4+heads) + two-level heads (CPU) =="
python3 -u src/04_finetune.py --epochs 2 --lr 2e-2 --backbone-lr 5e-4 \
    --freeze layer0_3 --batch 64 --out checkpoints/resnet18_mtl.pt 2>&1 |
    tee "$LOG/04_finetune.log"

echo "== 05 final evaluation -> evidence_table.csv / metrics.json / confusion =="
python3 -u src/05_evaluate.py --model resnet --ckpt checkpoints/resnet18_mtl.pt 2>&1 |
    tee "$LOG/05_evaluate.log"

echo "== 08 analysis (data stats + confusion pairs) =="
python3 -u src/08_analysis.py 2>&1 | tee "$LOG/08_analysis.log"

echo "== 09 figures =="
python3 -u src/09_figures.py 2>&1 | tee "$LOG/09_figures.log"

echo "== 06 verify metrics from saved evidence (no retrain) =="
python3 -u src/06_verify.py 2>&1 | tee "$LOG/06_verify.log"

echo "=== pipeline complete ==="