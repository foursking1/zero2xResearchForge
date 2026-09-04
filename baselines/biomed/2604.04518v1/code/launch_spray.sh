#!/usr/bin/env bash
# Usage: bash launch_spray.sh <dataset> <poison> <layer> [method]
# Detached: computes+saves SpRAy features via spray_feats.py (exits immediately).
# Run spray_labels_from_feats.py separately once the .npy exists.
set -euo pipefail
DS=$1; POISON=$2; LAYER=$3; METHOD=${4:-km2}
PY="C:\Users\Administrator\.workbuddy\binaries\python\versions\3.13.12\python.exe"
CODE="D:\project\paper-bench\tasks_legacy\2604.04518v1\agent_solution\code"
LOG="D:\project\paper-bench\tasks_legacy\2604.04518v1\agent_solution\workspace\logs"
powershell -NoProfile -Command "\$env:OMP_THREADS='3'; \$p = Start-Process -FilePath '$PY' -ArgumentList '-u','spray_feats.py','$DS','$POISON','$LAYER' -WorkingDirectory '$CODE' -RedirectStandardOutput '$LOG/spray_${DS}_${POISON}_l${LAYER}.log' -RedirectStandardError '$LOG/spray_${DS}_${POISON}_l${LAYER}.err' -WindowStyle Hidden -PassThru; Write-Output \$p.Id"