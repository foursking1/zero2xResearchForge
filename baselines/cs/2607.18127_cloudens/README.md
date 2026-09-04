# agent_solution — ClouDens reproduction (task `2607.18127_cloudens`)

End-to-end, from-scratch reproduction of the ClouDens critical claim on the frozen IBM
Cloud Telemetry data.

## Layout
```
scripts/run_repro.py    # pipeline: data -> train (GRU / ClouDens) -> MD+LF scoring -> NAB -> evidence
scripts/recompute_lf.py # rebuild LF rows with the global-pooled median/IQR normalisation
scripts/analyze.py      # data-facts verification + figures
src/                    # loader, models, scoring, NAB, anomaly-likelihood, TGCN/A3TGCN2 cells
results/                # evidence_table.csv, grid files, figures, validation artifacts
report.md               # full report (method, results, claims, limitations)
solution.md             # concise verdict + evidence summary
```

## Data
The pipeline reads the frozen parquet directly:
`/mnt/f/dataset/cs/2607.18127_cloudens/pivoted_data_all.parquet` and
`…/data/labels/anomaly_windows.csv` (paths at the top of `scripts/run_repro.py`).
The 5xx-count subset is cached under `data/` after the first load.

## Reproduce (primary run, batch 32 — the batch the paper text specifies for both models)
```bash
python scripts/run_repro.py --model both --device cuda --epochs 15 --batch 32 --seed 42 --outdir results
python scripts/recompute_lf.py results     # LF rows with global-pooled normalisation
python scripts/analyze.py all              # data facts + figures
```
`--device auto|cpu|cuda`; class CPUs for training is possible but the A3T-GCN is
hours on CPU — use the GPU (models use ≲100 MB VRAM).

## Validation run (reproduction-package default batch 16)
```bash
python scripts/run_repro.py --model both --device cuda --epochs 15 --batch 16 --seed 42 --outdir results/validation_batch16
```
This reproduces the official GRU numbers to the last digit (Table IV MD 5.89/10.95 and the
package’s best-row 10.76/14.19); see `results/validation_batch16/`.

## Python deps
`numpy pandas pyarrow scipy scikit-learn torch torch-geometric matplotlib tqdm`

## Key results (batch 32, seed 42)
| strategy | model | NAB Standard | NAB LowFN | IM detected |
|---|---|---|---|---|
| MD 99.8 | GRU | 6.45 | 11.32 | [6,8,14,17] (4/9) |
| MD 99.8 | ClouDens | 16.84 | 21.76 | [6,7,9,14,17] (5/9) + issue [3] |

Full table: `results/evidence_table.csv`. Claims A/C supported, B partially supported
(see `report.md` §3).