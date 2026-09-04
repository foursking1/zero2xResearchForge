#!/bin/bash
cd "$(dirname "$0")"
for c in 2 3 4 8; do
  echo "############ coarse factor $c"
  python3 -u run_final.py --aug --model mlp --seeds 3 --coarse $c \
    --tag mlp_aug_s3_coarse$c 2>&1 | grep -v -E "UserWarning|warnings.warn"
done