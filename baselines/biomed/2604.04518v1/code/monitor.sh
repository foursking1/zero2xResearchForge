#!/usr/bin/env bash
# Quick status of all training jobs + their log tails.
cd "$(dirname "$0")/../workspace/logs" || exit 1
echo "=== python procs ==="
powershell -NoProfile -Command "Get-Process python -ErrorAction SilentlyContinue | Select-Object Id,CPU,@{N='MemMB';E={[math]::Round(\$_.WorkingSet64/1MB)}} | Format-Table -HideTableHeaders"
echo
for f in *.log; do
  last=$(tail -1 "$f")
  ck=$(ls "../models/students/${f%.log}" 2>/dev/null | grep -E 'last|ckpt' | tr '\n' ' ')
  echo "[$f] $last | $ck"
done
