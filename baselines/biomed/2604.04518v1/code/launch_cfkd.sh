#!/usr/bin/env bash
# Usage: bash launch_cfkd.sh <dataset> <poison>
# Detached cfkd.py run.
set -euo pipefail
DS=$1; POISON=$2
PY="C:\Users\Administrator\.workbuddy\binaries\python\versions\3.13.12\python.exe"
CODE="D:\project\paper-bench\tasks_legacy\2604.04518v1\agent_solution\code"
LOG="D:\project\paper-bench\tasks_legacy\2604.04518v1\agent_solution\workspace\logs"
powershell -NoProfile -Command "\$env:OMP_THREADS='3'; \$p = Start-Process -FilePath '$PY' -ArgumentList 'cfkd.py','$DS','$POISON' -WorkingDirectory '$CODE' -RedirectStandardOutput '$LOG/cfkd_${DS}_${POISON}.log' -RedirectStandardError '$LOG/cfkd_${DS}_${POISON}.err' -WindowStyle Hidden -PassThru; Write-Output \$p.Id"
