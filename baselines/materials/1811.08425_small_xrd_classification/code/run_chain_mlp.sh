#!/bin/bash
# Sequential runner for the final evidence-table experiments.
cd "$(dirname "$0")"
for args in \
  "--aug  --model mlp --seeds 3 --tag mlp_aug_s3" \
  "--noaug --model mlp --seeds 3 --tag mlp_noaug_s3" \
  "--aug  --model mlp --seeds 5 --tag mlp_aug_s5" \
  "--noaug --model mlp --seeds 5 --tag mlp_noaug_s5" \
  ; do
  echo "############ $args"
  python3 -u run_final.py $args 2>&1 | grep -v -E "UserWarning|warnings.warn"
done