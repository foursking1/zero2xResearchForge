#!/usr/bin/env bash
# Reproduce all results of the LP-PDBBind leakage-verification task from the
# frozen data/ package. Fixed seed 0 everywhere. Expected wall time ~20-30 min
# (dominated by the two DeepDTA-like CNN trainings on CPU).
set -euo pipefail
cd "$(dirname "$0")/.."

code=agent_solution/code
[ -d agent_solution ] || { echo "run from task root"; exit 1; }

echo "==> 0. dependency check";
python3 - "$code" <<'EOF' || exit 1
import sys
sys.path.insert(0, sys.argv[1])
import common
for mod in ["numpy", "pandas", "sklearn", "torch", "rdkit", "matplotlib", "joblib"]:
    try:
        __import__(mod)
        print(f"  ok: {mod}")
    except Exception as e:
        print(f"  MISSING: {mod} ({e})"); sys.exit(1)
ok = True
for fn, good in common.verify_checksums().items():
    print(f"  checksum {fn}: {'OK' if good[0] else 'MISMATCH '+good[1]}")
    ok = ok and good[0]
sys.exit(0 if ok else 1)
EOF

echo "==> 1. leakage statistics (time vs random split)";
python3 "$code/01_leakage_stats.py"

echo "==> 2. Random-Forest baseline (time vs random split)";
python3 "$code/02_rf_model.py"

echo "==> 3. DeepDTA-like 1D CNN (time vs random split)";
python3 "$code/03_ddta_cnn.py"

echo "==> 4. BDB2020+ external evaluation (RF)";
python3 "$code/04_bdb2020_eval.py"

echo "==> 5. aggregate evidence_table.csv / metrics.json / claims.json";
python3 "$code/05_finalize.py"

echo "==> 6. result figures -> agent_solution/evidence/";
python3 "$code/06_figures.py"

echo "Done."