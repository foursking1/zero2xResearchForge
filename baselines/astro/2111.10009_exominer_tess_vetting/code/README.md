# ExoMiner TESS vetting — reproducible analysis scripts (task 2111.10009)

Analysis of the frozen TESS SPOC 2-min vetting catalog officially released by
the NASA/ExoMiner repository (`exominer_vetting_tess.csv`, SHA-256
`6B4F2491E3C54BE770A4ADE9EFEFD25CDB4258BAADE7D985033EDC46013DE862`).
The data is the Sectors 1–67, `ExoMiner Score > 0.1` display subset of the
web-catalog dashtable. No synthetic data is used anywhere.

## What each script does

| script | purpose |
|---|---|
| `data_loader.py` | Locates the frozen CSV (env var `EXOMINER_DATA_PATH`, local `data/`, or the frozen `/mnt/f/...` path), checks expected shape, prints SHA-256. |
| `run_analysis.py` | Full analysis: score distribution, low-MES conservatism + MES bins, high-confidence population, Spearman correlations, four-tier verdict. Writes `results/metrics.json`, `results/evidence_table.csv`, `results/check3.txt`, figures, and evidence exports. |
| `verify_check3.py` | Judge-facing spot-check: just reproduces total rows=11,289, score>0.99 count=1,070, MES<10.5&score>0.99=30. |

## How to run

Requires Python 3.11+ with `pandas`, `numpy`, `scipy` (matplotlib optional for
figures). All statistics are deterministic (no randomness involved).

```bash
cd code
python3 run_analysis.py      # full pipeline
python3 verify_check3.py     # spot-check 3 numbers
```

If the frozen CSV is not found by auto-detection, point to it explicitly:

```bash
EXOMINER_DATA_PATH=/path/to/exominer_vetting_tess.csv python3 run_analysis.py
```

## Outputs

```
../results/metrics.json       machine-readable metrics (verdict included)
../results/evidence_table.csv MES-bin table + score-distribution rows
../results/check3.txt         the 3 judge spot-check numbers
../results/figures/*.png      5 supporting figures
../evidence/*.csv             evidence exports (high-confidence population,
                              low-MES score>0.99 subset)
```