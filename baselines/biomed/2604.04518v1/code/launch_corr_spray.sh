#!/usr/bin/env bash
# Usage: bash launch_corr_spray.sh <dataset> <poison> <layer> [method]
# Detached run_corrections_spray.py run.
set -euo pipefail
DS=$1; POISON=$2; LAYER=$3; METHOD=${4:-}
PY="C:\Users\Administrator\.workbuddy\binaries\python\versions\3.13.12\python.exe"
CODE="D:\project\paper-bench\tasks_legacy\2604.04518v1\agent_solution\code"
LOG="D:\project\paper-bench\tasks_legacy\2604.04518v1\agent_solution\workspace\logs"
CORR_EPOCHS="${CORR_EPOCHS:-30}"
OMP="${OMP:-3}"
if [ -n "$METHOD" ]; then
  ARGSTR="'run_corrections_spray.py','$DS','$POISON','$LAYER','$METHOD'"
else
  ARGSTR="'run_corrections_spray.py','$DS','$POISON','$LAYER'"
fi
powershell -NoProfile -Command "\$env:CORR_EPOCHS='$CORR_EPOCHS'; \$env:OMP_THREADS='$OMP'; \$p = Start-Process -FilePath '$PY' -ArgumentList $ARGSTR -WorkingDirectory '$CODE' -RedirectStandardOutput '$LOG/corrspray_${DS}_${POISON}_l${LAYER}.log' -RedirectStandardError '$LOG/corrspray_${DS}_${POISON}_l${LAYER}.err' -WindowStyle Hidden -PassThru; Write-Output \$p.Id"
