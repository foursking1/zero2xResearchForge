#!/usr/bin/env bash
# VIPERS photometric-redshift reproduction entry point (arXiv:2211.01901).
set -euo pipefail
cd "$(dirname "$0")/../code"
PY="C:/Users/Administrator/.workbuddy/binaries/python/versions/3.13.12/python.exe"
"$PY" analyze_vipers.py
echo "VIPERS reproduction done."
