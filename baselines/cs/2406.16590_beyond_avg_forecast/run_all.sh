#!/usr/bin/env bash
# End-to-end reproducibility script.
#  1) classical local baselines (SNaive, Theta, SES, ETS, RWD, ARIMA)
#  2) deep global N-HiTS (one model per sampling frequency)
#  3) multi-view SMAPE protocol -> results/evidence_table.csv + metrics.json
#  4) figures
#
# A CPU-only environment: ensure none of NHITS_DEVICE/NHITS_TARGET_CLIP set.
# If free GPU VRAM is verified (e.g. nvidia-smi > 4GiB free), you may run with:
#   NHITS_DEVICE=cuda NHITS_TARGET_CLIP=10 ./run_all.sh
set -e
cd "$(dirname "$0")"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1

echo "== [1/4] classical local baselines =="
python3 baselines/run_classical.py
echo "== [2/4] deep global N-HiTS =="
python3 method/run_nhits.py
echo "== [3/4] multi-view evaluation =="
python3 main.py
echo "== [4/4] figures =="
python3 scripts/make_figures.py
echo "ALL DONE"