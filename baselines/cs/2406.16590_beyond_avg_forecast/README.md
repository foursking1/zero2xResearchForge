# Beyond Average Forecast: Multi-View Evaluation of Forecasting Methods

Agent solution for task `2406.16590_beyond_avg_forecast` (L2 end-to-end
scientific **re-discovery** of the multi-view evaluation study:

> Cerqueira, V., Roque, L., Soares, C. (2024). *Forecasting with Deep Learning:
> Beyond Average of Average of Average Performance*. arXiv:2406.16590.

We implement the full protocol on the **frozen M3 + Tourism** package
(4,140 series), compute SMAPE through **seven evaluation views**, and answer
Q1–Q4 (see `report.md`).

## Layout

```
agent_solution/
├── README.md               # this file
├── solution.md             # concise method & results summary
├── report.md               # full scientific report (Q1–Q4, limitations)
├── main.py                 # assembles all views -> evidence_table.csv + metrics.json
├── run_all.sh              # end-to-end reproducibility script
├── data_loader.py          # .tsf parser + frozen-data validation (A1 facts)
├── config.py               # protocol & model configuration
├── baselines/              # classical local methods (SNaive, Theta, SES, ETS, RWD, ARIMA)
├── method/                 # deep global model (PyTorch N-HiTS) + training
├── protocols/              # multi-view SMAPE protocol
├── scripts/make_figures.py # publication-style figures
├── results/                # evidence_table.csv, metrics.json, forecasts/, ckpt/, figures/
└── evidence/               # key figures & tables exported for the judge
```

## Reproduce

```bash
cd agent_solution
./run_all.sh                       # CPU-only (classical + NHITS + eval + figures)
# or, if verified free GPU VRAM (>= 4 GiB):
#   NHITS_DEVICE=cuda NHITS_TARGET_CLIP=5 ./run_all.sh
```

Each stage is resume-safe (output files are cached). Deterministic:
`SEED=42`; the N-HiTS DataLoader uses a seeded generator; classical methods are
deterministic; the evaluation is a pure function of the forecast files.

## Protocol (identical test conditions for every method)

- **Data**: 6 frozen `.tsf` files (M3 2,829 = 1,428/756/645 monthly/quarterly/
  yearly; Tourism 1,311 = 366/427/518). Test = the last `@horizon` observations
  of each series (M3 18/8/6; Tourism 24/8/4), used **only** for scoring.
- **SMAPE** = `100%/n · Σ |ŷ−y| / ((|ŷ|+|y|)/2)`; `0/0 → 0` (declared).
- **Views**: overall · horizon (first/last step) · frequency · difficult series
  (SNaive per-series SMAPE > 95% quantile) · anomalies (outside the SNaive 99%
  prediction interval) · expected shortfall · per-series win/loss.
- **Deep model**: global N-HiTS — one model per sampling frequency trained on
  all series of that frequency (M3 + Tourism jointly); input windows from the
  pre-test segment only; validation/early-stopping windows also pre-test.
- **Classical**: local methods fitted per series on the pre-test segment.