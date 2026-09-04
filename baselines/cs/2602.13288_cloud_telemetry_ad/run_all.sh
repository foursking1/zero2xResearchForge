#!/usr/bin/env bash
# Full reproduction pipeline for the frozen NAB + Microsoft telemetry AD task.
#
# Steps:
#   1. data self-check (B-dimension facts, frozen checksums)
#   2. run all models on all series (CPU, multiprocessing, fixed seed)
#   3. aggregate -> results/evidence_table.csv + results/metrics.json
#   4. build figures + final report tables (results/*.png / *_table.csv)
#
# Usage:
#   ./run_all.sh [n_workers] [seed]
set -euo pipefail
cd "$(dirname "$0")"

NW=${1:-8}
SEED=${2:-0}
echo "==> data self-check"
python3 code/verify_data_facts.py

echo "==> running pipeline (workers=$NW, seed=$SEED)"
python3 code/run_series.py --jobs "$NW" --seed "$SEED" \
    --outdir results

echo "==> analysis tables + figures"
python3 code/analyze.py

echo "==> done. see results/, report.md, solution.md"