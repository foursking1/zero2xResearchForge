#!/usr/bin/env bash
# PTA normalizing-flow reproduction entry point (arXiv:2504.04211).
set -euo pipefail
cd "$(dirname "$0")/../code"
PY="C:/Users/Administrator/.workbuddy/binaries/python/versions/3.13.12/python.exe"
# Main run (reuses cached MCMC chains; trains NFs; runs DW MCMC fresh).
"$PY" run_pta.py --n_train 15000 --n_epochs 40 --n_eval 8000 \
  --cache "D:/project/paper-bench/tasks/astro/2504.04211_pta_normalizing_flows/agent_solution/code/cache_smoke" \
  --skip_mcmc --models PowerLaw,SMBHB,DW
# Post-process: robust figures + IS-based Bayes-factor consistency table.
"$PY" pta_postprocess.py
echo "PTA reproduction done."
