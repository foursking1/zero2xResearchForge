#!/usr/bin/env bash
# Full reproducible pipeline for the physics-aware GNN OOD claim verification.
#
#   bash run_all.sh               # full primary protocol (4 variants x 5 seeds, GPU if available)
#   bash run_all.sh --quick       # fast smoke: 2 variants x 1 seed x 8 epochs
#   bash run_all.sh --sensitivity # also rerun the plain-BCE / strong-aux sensitivity regime
set -euo pipefail
cd "$(dirname "$0")"
PY=${PY:-python}
DEVICE=${DEVICE:-auto}
if [[ "$DEVICE" == "auto" ]]; then
    DEVICE="cuda" # falls back to cpu inside the script if unavailable
fi
# hard-coded device override used by train scripts below
export TRAIN_DEVICE="$DEVICE"

echo "[1/4] labels + featurization (sascore / complexity / strain / graphs)"
$PY data_pipeline.py

mkdir -p ../results
echo "[2/4] training (baseline + phys-aware variants) and OOD evaluation on COCONUT"
if [[ "${1:-}" == "--quick" ]]; then
    $PY train_eval.py --variants baseline complexity --seeds 0 --max_epochs 8 --out raw_evals_quick.json
else
    $PY train_eval.py --variants baseline complexity strain both --seeds 0 1 2 3 4\
        --device "$TRAIN_DEVICE" --out raw_evals.json
    if [[ "${1:-}" == "--sensitivity" ]]; then
        $PY train_eval.py --variants baseline complexity strain both --seeds 0 1 2 3 4\
            --device "$TRAIN_DEVICE" --pos_weight 0 --aux_w 0.5 --out raw_evals_regime2.json
        cp ../results/raw_evals.csv ../results/regime2_plaince_raw_evals.csv
        $PY analyze.py --evals ../results/regime2_plaince_raw_evals.csv
        mkdir -p ../results/regime2_plaince
        mv ../results/regime2_plaince_raw_evals.csv ../results/regime2_plaince/raw_evals.csv
        mv ../results/metrics.json ../results/regime2_plaince/metrics.json
        mv ../results/evidence_table.csv ../results/regime2_plaince/evidence_table.csv
    fi
fi

echo "[3/4] statistics (paired bootstrap CI, evidence tables, metrics)"
$PY analyze.py

echo "[4/4] done - see agent_solution/results/* and agent_solution/evidence/*"