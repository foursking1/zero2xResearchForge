#!/usr/bin/env bash
# End-to-end reproducible pipeline for the TAPE protein-tasks claim validation.
# Run from agent_solution/ :  bash code/run_all.sh
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE"

echo "==> [1/5] dataset stats (A1)"
python3 code/dataset_stats.py

echo "==> [2/5] ESM-2 embeddings (pretrained representation, sequences only)"
python3 code/embed_esm.py --model facebook/esm2_t6_8M_UR50D
python3 code/embed_esm.py --model facebook/esm2_t33_650M_UR50D

echo "==> [3/5] regression heads + baselines + evaluation (A2/A3)"
python3 code/regression_head.py

echo "==> [4/5] figures"
python3 code/make_figures.py

echo "==> [5/5] done"
echo "Outputs:"; echo "  results/evidence_table.csv"; echo "  results/metrics.json"; echo "  evidence/figures/*.png"