#!/usr/bin/env bash
# SEP Random Hivemind reproduction entry point (arXiv:2303.08092).
set -euo pipefail
cd "$(dirname "$0")/../code"
PY="C:/Users/Administrator/.workbuddy/binaries/python/versions/3.13.12/python.exe"
# 10 random stratified 70/30 splits, base 150 epochs (RH scaled by 12/n_sel).
"$PY" run_sep.py --n_splits 10 --epochs 150 --seed 20260817
echo "SEP reproduction done."
