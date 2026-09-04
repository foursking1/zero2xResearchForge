# agent_solution — 2307.11958 transferability estimation (frozen MSD subset)

Reproducier of arXiv:2307.11958 "Pick the Best Pre-trained Model: Towards
Transferability Estimation for Medical Image Segmentation" on the frozen
Spleen + Liver subsets.

## Verdict
`claim.md` → **partially_supported** | details in `report.md`, overview in `solution.md`.

## Contents
- `code/` — deterministic, CPU-only pipeline (fixed seeds):
  - `01_prepare.py`  2-D slice build (organ-aware crops, fixed splits)
  - `02_pretrain.py` source-model pool on Liver
  - `03_finetune.py` target fine-tune (full-network AND decoder/probe readouts) + Dice
  - `04_te.py`       TE scores: CC-FV, LogME, LEEP, GBC
  - `05_analyze.py`  Pearson / weighted Kendall τ-b / top-1 hit, tables & figures
  - `run_all.sh`     end-to-end driver
- `results/` — `metrics.json` (primary = probe readout), `metrics_full.json`
  (full fine-tune sensitivity), `evidence_table.csv`, per-stage jsons,
  `splits.json`, `data_check.json` (freeze-integrity audit).
- `evidence/` — TE-vs-Dice scatter + data-integrity crops.

## Reproduce
```bash
bash code/run_all.sh                # from this directory
export DATA_ROOT=/path/to/frozen/*.nii.gz   # auto-detected normally
```
The frozen Liver **image** streams are gzip-truncated (SHA-256 matches
`data/README.md`); `common.read_raw_nifti` recovers the real compressed prefix,
so all scripts run on the shipped bytes as-is. No downloads needed.