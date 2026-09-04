#!/usr/bin/env bash
# DASH (arXiv:1903.02557) reproduction entry point.
# Uses the venv that has astrodash + tensorflow-cpu 2.21 installed.
set -euo pipefail
cd "$(dirname "$0")/../code"
PY="C:/Users/Administrator/.workbuddy/binaries/python/envs/default/Scripts/python.exe"
"$PY" dash_data.py
"$PY" dash_run.py
echo "DASH reproduction done."
