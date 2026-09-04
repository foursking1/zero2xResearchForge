#!/usr/bin/env bash
# Reproducible full pipeline for task 2406.12747_tsibench (offline, CPU).
set -euo pipefail
cd "$(dirname "$0")"
python3 impute_bench.py --seeds 42 43 44
python3 verify_anchor.py
echo "OK: results written to ../results (evidence_table.csv, metrics.json)"