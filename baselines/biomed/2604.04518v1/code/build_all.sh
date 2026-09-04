#!/usr/bin/env bash
# Detached rebuild of all real-dataset tensors at IMG_SIZE=128.
set -euo pipefail
PY="C:\Users\Administrator\.workbuddy\binaries\python\versions\3.13.12\python.exe"
CODE="D:\project\paper-bench\tasks_legacy\2604.04518v1\agent_solution\code"
cd "$CODE"
for spec in "smiling symmetric" "smiling asymmetric" "blond symmetric" "blond asymmetric" "camelyon symmetric" "camelyon asymmetric"; do
  set -- $spec
  IMG_SIZE=128 BUILD_WORKERS=6 OMP_THREADS=1 "$PY" build_tensors.py "$1" "$2"
done
echo "ALL_DONE"
