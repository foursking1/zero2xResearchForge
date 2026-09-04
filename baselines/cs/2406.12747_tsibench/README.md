# agent_solution — task 2406.12747_tsibench (TSI-Bench, ETT_h1 simple baselines)

Reproduction/verification of the TSI-Bench (arXiv:2406.12747v2) claims on the
frozen `data/ETT-h1.csv`:

- **C1** simple-imputer ordering `Linear < LOCF < Median ≈ Mean`
- **C2** linear imputation is competitive with deep methods

**Verdict: `supported`** (see `claim.md`).

## Layout

| path | content |
|---|---|
| `claim.md` | claim statements, falsification conditions, four-level verdict, seed robustness |
| `solution.md` | condensed method + results + how-to-reproduce |
| `report.md` | full method / results / limitations report |
| `code/impute_bench.py` | complete pipeline (split → train-only z-score → windows → 10% masks → 4 baselines → test-masked MAE/MSE) |
| `code/verify_anchor.py` | independent spot-check of the two scorer numbers (2385 pts, Linear 0.2033…) |
| `code/make_figure.py` | `evidence/seed_sensitivity.png` + `evidence/mae_by_baseline.csv` |
| `code/run_all.sh` | one-shot reproducible run |
| `results/evidence_table.csv` | `imputer,seed,mae,mse` every baseline × seed (42,43,44) + mean/std rows |
| `results/metrics.json` | full machine-readable output incl. per-seed metrics, train stats, config, verdict |
| `results/seed_*.json`, `results/run.log` | raw per-seed outputs and console log |
| `evidence/` | figure + verify output + extracted comparison table |

## Reproduce (offline, no network, no GPU)

```bash
cd agent_solution/code
bash run_all.sh        # or: python impute_bench.py --seeds 42 43 44
# expects to find ETT-h1.csv via --data / TSIBENCH_DATA / default candidates;
# SHA-256 is verified against data/source_manifest.json at startup.
```

Dependencies: Python ≥ 3.10, `numpy`, `pandas` (`matplotlib` for the figure only).
Total runtime < 60 s on CPU.

## Key numbers (seed 42, matching the frozen reference protocol)

- test windows: 72; test masked points: **2385**
- Linear test MAE = **0.2033249300539183**; LOCF 0.3024; Mean 0.8713; Median 0.8588
- ordering holds on every seed {42,43,44}; deep-method values quoted, not measured