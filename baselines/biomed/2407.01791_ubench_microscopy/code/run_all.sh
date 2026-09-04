#!/usr/bin/env bash
# End-to-end reproduction of the mu-Bench perception shard evaluation.
# Requires: data/ubench-test-00000-of-00007.arrow (frozen), Python 3.13 env with
#   torch, torchvision, timm, pyarrow, pandas, scikit-learn, scipy, matplotlib.
# All steps run fully offline on CPU (default). ~40-60 min total on CPU.
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"
PY="${PYTHON:-/home/dministrator/miniconda3/bin/python}"
cd "$HERE/code"

echo "[1/4] parse shard + dataset statistics"
$PY 01_stats.py

echo "[2/4] extract frozen image features (CPU)"
$PY 02_extract_features.py --model vit_base_patch16_224 --device cpu --batch 32
$PY 02_extract_features.py --model resnet18 --device cpu --batch 64

echo "[3/4] closed-VQA evaluation (grouped 5-fold CV linear probes)"
$PY 03_evaluate.py

echo "[4/4] figures"
$PY 04_figures.py

echo "done -> $HERE/results, $HERE/evidence"