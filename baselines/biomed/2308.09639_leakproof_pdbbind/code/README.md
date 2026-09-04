# Run & dependencies

Reproduce everything from the frozen `data/` package:

```bash
bash agent_solution/code/run_all.sh
```

Steps (all fixed seed=0, CPU, single process, no network):

1. `01_leakage_stats.py`  → `results/leakage_stats.csv` (ligand/target cross-set duplication, time vs random split)
2. `02_rf_model.py`        → RF (ECFP4 + dipeptide) time & random splits, RMSE/Pearson on LP test CL2 non-covalent (2171); saves models to `results/models/`
3. `03_ddta_cnn.py`        → DeepDTA-like 1D-CNN time & random splits (CPU, ~10 min for both)
4. `04_bdb2020_eval.py`    → RF on external BDB2020+ (115)
5. `05_finalize.py`        → `results/evidence_table.csv`, `results/metrics.json`, `results/claims.json`
6. `06_figures.py`         → `evidence/fig*.png`

Quick judge verification (cheap, ~2–4 min): `python3 agent_solution/code/07_verify.py`

Dependencies (python3.12): numpy, pandas, scikit-learn, torch (CPU ok), rdkit, matplotlib, joblib.

```bash
pip install numpy pandas scikit-learn torch rdkit matplotlib joblib
```