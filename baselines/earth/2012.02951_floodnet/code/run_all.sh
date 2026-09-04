#!/usr/bin/env bash
# Reproduce the full FloodNet VQA experiment from the frozen data.
#
#   bash run_all.sh            # full pipeline (features re-extracted)
#   bash run_all.sh --features # skip precomputed feature extraction (default if files exist)
#
# Steps:
#   1. data_prep.py      image-level 85/15 (+dev) split, seed 42        -> results/split.json
#   2. extract_features  ResNet-18 (448px) + ViT-B/16 (224px) features   -> workspace/features_*.npz
#   3. train.py          train 5 configurations, select best on dev      -> workspace/model_*.pt + results/train_summary.json
#   4. evaluate.py       eval OA / per-type / ablations / evidence       -> results/metrics.json + evidence_table.csv
#   5. analysis.py       per-template CSV + figures                       -> results/analysis.json + figures/
set -e
cd "$(dirname "$0")"

echo "[1/5] split"
python3 data_prep.py

R18F=../workspace/features_r18.npz
VITF=../workspace/features_vit.npz
if [ ! -f "$R18F" ] || [ ! -f "$VITF" ] || [ "$1" == "--features" ]; then
  echo "[2/5] feature extraction"
  python3 extract_features.py
else
  echo "[2/5] features already present, skipping extraction"
fi

echo "[3/5] train"
python3 train.py > ../workspace/train_log.txt 2>&1

echo "[4/5] evaluate"
python3 evaluate.py > ../workspace/eval_log.txt 2>&1

echo "[5/5] analysis + figures"
python3 analysis.py > ../workspace/analysis_log.txt 2>&1

echo "done. see ../results/metrics.json and ../results/evidence_table.csv"