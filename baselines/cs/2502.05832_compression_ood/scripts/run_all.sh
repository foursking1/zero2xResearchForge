#!/usr/bin/env bash
# run_all.sh — end-to-end reproducible pipeline for the 
# few-sample class-imbalance compression reproduction (arXiv:2502.05832).
#
#   step 0: verify frozen data (B-check #1)
#   step 1: construct balanced/imbalanced subsets (fixed seeds)
#   step 2: train VGG-16 teacher from scratch on frozen CIFAR-10
#   step 3: train all KD-compressed students (3 repeats x 3 episodes x 2 configs)
#   step 4: aggregate evidence (evidence_table.csv, metrics.json)
#   step 5: independent final evaluation on frozen test set
#   step 6: figures
#
# Usage: bash scripts/run_all.sh [device_for_students]
set -u
DEVICE="${1:-auto}"
cd "$(dirname "$0")/.."
export PYTHONPATH="$(pwd)/scripts"

set -e
echo "== [step 0] verify frozen data =="
python3 scripts/01_verify_data.py

echo "== [step 1] build subsets =="
python3 scripts/02_prepare_subsets.py

echo "== [step 2] train VGG-16 teacher (GPU preferred) =="
python3 scripts/03_train_teacher.py --epochs 120

echo "== [step 3] few-shot KD compression =="
bash scripts/05_run_kd_all.sh "$DEVICE"

echo "== [step 4] build evidence =="
python3 scripts/06_build_evidence.py

echo "== [step 5] final evaluation on test set =="
python3 scripts/07_evaluate.py

echo "== [step 6] figures =="
python3 scripts/08_figures.py

echo "== [step 7] per-class mechanism analysis =="
python3 scripts/09_perclass_analysis.py

echo "ALL DONE"