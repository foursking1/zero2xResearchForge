# Everglades Water-Level Forecasting — Reproduction Package

Reproduces and evaluates the core claims of
**"How Effective are Large Time Series Models in Hydrology? A Study on Water
Level Forecasting in Everglades"** (arXiv:2505.01415, Table 1 Overall MAE),
using only the frozen official CSV.

Task id: `2505.01415_everglades_water_level`

## Layout

```
agent_solution/
├── README.md                 this file
├── solution.md               method + results summary (claims labelled)
├── report.md                 full report (protocol, leak-guards, limitations)
├── code/
│   ├── common.py             data loading / split / scaling utilities
│   ├── models.py             NLinear, DLinear, NBEATS (PyTorch)
│   ├── models_extra.py       MLPResidual, TSMixer, PatchTST
│   ├── train_eval.py         main training + daily-rolling evaluation
│   ├── run_chronos.py        zero-shot Chronos (-t5-small, local weights)
│   ├── run_baselines.py      persistence / moving-average baselines
│   ├── make_evidence.py      builds evidence_table.csv + figures + claim labels
│   └── verify_data.py        independent data-fact checks (1411 rows, dates, …)
├── results/
│   ├── evidence_table.csv         (model, lead_time, overall MAE/RMSE, per-station MAE)
│   ├── evidence_station_lead.csv  raw per (station, lead) MAE
│   ├── metrics_*.csv              per-lead metrics per model
│   ├── predictions_*.npz          raw test forecasts (seeded, reproducible)
│   ├── model_states/*.pt          best trained weights
│   ├── claim_analysis.md          auto-derived claim labels
│   └── figures/                   MAE-vs-horizon & per-station plots
└── evidence/
    ├── data_facts.json            frozen-CSV facts (+ sha256)
    └── (key tables / logs)
```

## Requirements

* Python >= 3.11; `torch`, `numpy`, `pandas`, `matplotlib`
* Optional (for claim c / Chronos): `chronos-forecasting` + `transformers`
* The frozen CSV at `data/final_concatenated_data.csv` (path configurable via
  env var `EVERGLADES_CSV`)

## Quick start

```bash
# 0. (optional) point at your frozen CSV
export EVERGLADES_CSV=/path/to/final_concatenated_data.csv

# 1. data-fact verification (row count, date range, missing, checksum)
python code/verify_data.py

# 2. baselines (persistence etc., for context)
python code/run_baselines.py

# 3. task-specific models (fixed seeds, deterministic)
python code/train_eval.py --model DLinear    --seed 42 --device cpu
python code/train_eval.py --model NLinear    --seed 42 --device cpu
python code/train_eval.py --model NBEATS     --seed 42 --device cpu
python code/train_eval.py --model MLPResidual --seed 42 --device cpu
python code/train_eval.py --model MLPResidual --seed 42 --device cpu --mc 0.05  # MC-dropout
python code/train_eval.py --model TSMixer    --seed 42 --device cpu
python code/train_eval.py --model PatchTST   --seed 42 --device cpu

# 4. zero-shot Chronos (only if chronos-forecasting installed + local weights;
#     GPU strongly recommended -- CPU is ~1-2 h. Set CHRONOS_DIR to a local
#     chronos-t5-{small,base,large}/ directory if available)
python code/run_chronos.py --context 512 --device gpu
python code/run_chronos.py --context 100 --device gpu

# 5. assemble evidence tables + figures + claim labels
python code/make_evidence.py
```

GPU (`--device gpu`) is faster but not required; all headline numbers reported
in `evidence_table.csv` are CPU runs with seed 42.

## Protocol (paper §3.1)

* 1411 daily rows, 2020-10-16 → 2024-08-26, 37 variables (5 target stations +
  32 covariates), no missing values.
* train = first 1200 days; validation = last 211 days *inside* train
  (indices 989–1199, used only for early stopping, disjoint from test);
  test = last 211 days (2024-01-29 → 2024-08-26).
* input = previous 100 days of all 37 variables; single model trained with
  h = 28; every test day is an origin whose context ends strictly before it;
  MAE/RMSE computed per station and lead {7, 14, 21, 28}, Overall = mean over
  the five stations (Table-1 convention).
* No leakage: standardization statistics fitted on train only; rolling windows
  never touch future values; the test segment never enters training,
  validation, early stopping or any calibration.