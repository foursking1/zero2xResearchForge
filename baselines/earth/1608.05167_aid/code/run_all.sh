#!/usr/bin/env bash
# Reproducible pipeline for AID reproduction (task 1608.05167_aid).
# Run from agent_solution/code/. GPU is used if available.
set -e

PY=${PY:-/home/dministrator/miniconda3/envs/verovlm/bin/python}
cd "$(dirname "$0")"

# 1) Multi-label 17-class (frozen AID_MultiLabel parquet, 60/20/20 split)
#    Trains and writes results/evidence_table.csv + results/metrics_multilabel.json
$PY train_multilabel.py --epochs 30 --batch-size 32 --size 224 \
    --outdir ../results

# 2) Fast recompute of the evidence table directly from the frozen parquet
#    (no retraining; verifies mAP/macro-F1/subset-acc from saved predictions)
$PY recompute_metrics.py --results ../results

# 3) Single-label 30-class OA on the original AID folders (frozen 50/50 split)
$PY train_singlelabel.py --epochs 40 --batch-size 64 --size 224 \
    --outdir ../results

# 4) Exports: exact split indices + top-1-in-GT rate
$PY export_split.py --results ../results

# 5) Fill report/solution numbers from the generated metrics
$PY finalize_docs.py

# 6) Figures
$PY make_figures.py --results ../results --evidence ../evidence
$PY analyze.py --results ../results --evidence ../evidence

echo "done."