#!/usr/bin/env bash
# Reproducible end-to-end run of the MedMNIST v2 L1 task.
#
#   ./run_all.sh [--device cpu|cuda] [--epochs N]
#
# Steps:
#   1. statistics pass over the frozen npz (class counts, split sizes)
#   2. train + evaluate ResNet-18@28 on the 5 datasets (early stop on VAL AUC,
#      one final evaluation on the TEST split)
#   3. write results/evidence_table.csv, results/metrics.json, checkpoints
#
# Frozen data is located via config.find_data_dir() (env MEDMNIST_DATA_DIR or
# well-known paths under F:\\dataset\\...). By default only the CPU is used.
set -euo pipefail
cd "$(dirname "$0")"

DEVICE="${1:-cpu}"
EPOCHS="${2:-45}"

python3 code/data_stats.py
python3 code/train.py --device "$DEVICE" --epochs "$EPOCHS"

echo
echo "Done. see results/evidence_table.csv and results/metrics.json"