#!/usr/bin/env bash
# Regenerate every evidence table from the frozen dataset.
#
# Prerequisites: python3 with pandas/numpy/sklearn (the repo's own scripts
# need sentence_transformers which is NOT offline-available; our re-implemented
# evaluators in code/ use only the standard library + difflib).
#
# From the task root directory:
#     bash agent_solution/run_all.sh
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_DIR="$HERE/../data/dataset"

if [ ! -d "$DATA_DIR/superMat" ]; then
    echo "data/dataset not found; looking for the original location used by the benchmark"
    if [ -d "/mnt/f/dataset/materials/2401.11052_llm_materials_mining/dataset" ]; then
        echo "using /mnt/f/dataset/materials/2401.11052_llm_materials_mining/dataset (DATA_LOCATION.md)"
    else
        echo "ERROR: frozen dataset not available. Expected data/dataset or F:\\dataset. Aborting." >&2
        exit 1
    fi
fi

cd "$HERE/code"

echo ">> [1/3] SuperMat materials NER (strict / soft / formula)             "
python3 run_ner.py
echo ">> [2/3] MeasEval properties NER (strict / soft)                       "
python3 run_measeval.py 2>/dev/null > "$HERE/work/measeval_runs.json"
echo ">> [3/3] SuperMat relation extraction (strict / soft)                  "
python3 run_re.py 2>/dev/null > "$HERE/work/re_runs.json"

echo ">> aggregating evidence tables                                         "
python3 aggregate.py

echo ">> copying per-run records into results/                               "
cp "$HERE/work/ner_runs.json"        "$HERE/results/ner_runs.json"
cp "$HERE/work/measeval_runs.json"   "$HERE/results/measeval_runs.json"
cp "$HERE/work/re_runs.json"         "$HERE/results/re_runs.json"

echo ">> integrity check of inputs (checksum manifest)                       "
python3 verify_inputs.py

echo "done. See agent_solution/results/evidence_table.md"