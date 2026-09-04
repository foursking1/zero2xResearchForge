#!/usr/bin/env bash
# Usage:
#   bash launch_train.sh <dataset> <poison> <epochs> [threads] [protocol] [squares_dir] [lr]
# protocol: ramp (default) | plateau | ramp_strong
# squares_dir: optional override for where the squares splits live.
# lr: optional learning rate override (default 0.01).
# Launches a detached python process training an ERM student. Survives the
# launching shell. Output goes to workspace/logs/<ds>_<poison>.log|.err
set -euo pipefail
DS=$1; POISON=$2; EPOCHS=$3; THREADS=${4:-4}; PROTOCOL=${5:-ramp}; SQDIR=${6:-}; LR=${7:-0.01}
PY="C:\Users\Administrator\.workbuddy\binaries\python\versions\3.13.12\python.exe"
CODE="D:\project\paper-bench\tasks_legacy\2604.04518v1\agent_solution\code"
LOG="D:\project\paper-bench\tasks_legacy\2604.04518v1\agent_solution\workspace\logs"
mkdir -p "$(dirname "$LOG")"
SQENV=""
if [ -n "$SQDIR" ]; then SQENV="\$env:SQUARES_DIR='$SQDIR';"; fi
powershell -NoProfile -Command "\$env:STUDENT_EPOCHS='$EPOCHS'; \$env:OMP_THREADS='$THREADS'; \$env:STUDENT_PROTOCOL='$PROTOCOL'; \$env:STUDENT_LR='$LR'; $SQENV \$p = Start-Process -FilePath '$PY' -ArgumentList 'train_student.py','$DS','$POISON' -WorkingDirectory '$CODE' -RedirectStandardOutput '$LOG/${DS}_${POISON}.log' -RedirectStandardError '$LOG/${DS}_${POISON}.err' -WindowStyle Hidden -PassThru; Write-Output \$p.Id"
