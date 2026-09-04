#!/usr/bin/env bash
# 05_run_kd_all.sh — run all few-shot KD compression jobs (all configs x repeats)
# Usage: bash scripts/05_run_kd_all.sh [device]
set -u
DEVICE="${1:-auto}"
export PYTHONPATH="$(cd "$(dirname "$0")/.." && pwd)/scripts"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
mkdir -p results/students

# episodes and repeats (fixed, deterministic; primary seed 42 is repeat 0)

run_job () {
  local N=$1 cfg=$2 seed=$3 epochs=$4
  local logfile="logs_kd_${cfg}_N${N}_seed${seed}.txt"
  echo "[run] ${cfg} N=${N} seed=${seed} epochs=${epochs}"
  python3 scripts/04_compress_kd.py --N "$N" --config "$cfg" --seed "$seed" \
      --epochs "$epochs" --device "$DEVICE" > "$logfile" 2>&1
}

for N in 10 50 100; do
  if   [ "$N" = "10" ]; then EP=400
  elif [ "$N" = "50" ]; then EP=300
  else EP=260; fi
  for seed in 42 7 2024; do
    run_job $N balanced   $seed $EP
    run_job $N imbalanced $seed $EP
  done
done
echo "[run_all] all KD jobs done"