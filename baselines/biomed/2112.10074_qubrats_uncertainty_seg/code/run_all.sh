#!/usr/bin/env bash
# Full reproducible pipeline for task 2112.10074 (QU-BraTS critical claim).
# All outputs go to ../results/ (relative to this file's code/ dir).
set -euo pipefail
cd "$(dirname "$0")/.."

PY="python3"
DATA="${2:-../data/brats2021_mini.parquet}"   # relative to agent_solution/
DEVICE="${1:-cuda:0}"                        # override: bash run_all.sh cpu

# 1. parse frozen data -> data_cache/
$PY code/01_prepare_data.py --data "$DATA" --cache data_cache

# 2. train 5 models (2 MC-Dropout + 3 deterministic)
for spec in "mcd_s0:0:0.3:yes" "mcd_s1:1:0.3:yes" "det_s2:2:0.0:no" \
            "det_s3:3:0.0:no" "det_s4:4:0.0:no"; do
  IFS=: read -r name seed pdrop mc <<< "$spec"
  args=""
  [ "$mc" = "yes" ] && args="--mc-dropout"
  $PY -u code/train.py --name "$name" --seed "$seed" --p-drop "$pdrop" \
       $args --epochs 35 --device "$DEVICE" --cache data_cache --outdir models
done

# 3. evaluate test cases with QU-BraTS metrics (entropy uncertainty; MC for dropout models)
$PY -u code/evaluate.py --models mcd_s0 mcd_s1 det_s2 det_s3 det_s4 \
     --ensemble-members ensemble_det det_s2 det_s3 det_s4 \
     --random-unc --mc-samples 15 --device "$DEVICE" \
     --cache data_cache --models-dir models --outdir results

# 4. aggregate -> evidence_table.csv, threshold tables, metrics.json
$PY code/aggregate.py

# 5. figures
$PY code/plots.py

# 6. verify
$PY code/verify.py

echo "PIPELINE COMPLETE"