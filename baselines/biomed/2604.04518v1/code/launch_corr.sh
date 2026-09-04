#!/usr/bin/env bash
# Usage: bash launch_corr.sh <dataset> <poison> [method]
# Detached run_corrections.py. Env overrides: CORR_EPOCHS, GDRO_EPOCHS,
# GDRO_WDS, RRCLARC_LAMS, OMP.
set -euo pipefail
DS=$1; POISON=$2; METHOD=${3:-}
PY="C:\Users\Administrator\.workbuddy\binaries\python\versions\3.13.12\python.exe"
CODE="D:\project\paper-bench\tasks_legacy\2604.04518v1\agent_solution\code"
LOG="D:\project\paper-bench\tasks_legacy\2604.04518v1\agent_solution\workspace\logs"
CORR_EPOCHS="${CORR_EPOCHS:-30}"; GDRO_EPOCHS="${GDRO_EPOCHS:-100}"
GDRO_WDS="${GDRO_WDS:-0.1}"; RRCLARC_LAMS="${RRCLARC_LAMS:-1.0}"
OMP="${OMP:-3}"
if [ -n "$METHOD" ]; then
  METHOD_ARG=",'$METHOD'"
else
  METHOD_ARG=""
fi
powershell -NoProfile -Command "\$env:CORR_EPOCHS='$CORR_EPOCHS'; \$env:GDRO_EPOCHS='$GDRO_EPOCHS'; \$env:GDRO_WDS='$GDRO_WDS'; \$env:RRCLARC_LAMS='$RRCLARC_LAMS'; \$env:OMP_THREADS='$OMP'; \$p = Start-Process -FilePath '$PY' -ArgumentList '-u','run_corrections.py','$DS','$POISON'$METHOD_ARG -WorkingDirectory '$CODE' -RedirectStandardOutput '$LOG/corr_${DS}_${POISON}.log' -RedirectStandardError '$LOG/corr_${DS}_${POISON}.err' -WindowStyle Hidden -PassThru; Write-Output \$p.Id"
