# solution.md — Method & Results Summary

Task `2406.16590_beyond_avg_forecast`: re-implementation of the **multi-view
evaluation** of forecasting methods on the frozen M3 + Tourism package
(4,140 univariate series), following the protocol of Cerqueira et al. (2024,
arXiv:2406.16590) — *Forecasting with Deep Learning: Beyond Average of Average
of Average Performance*.

This document summarises the method and the headline results. The full
scientific report with Q1–Q4, detailed tables, figures and limitations is in
`report.md`.

---

## 1. Protocol (identical for all 6 datasets × 7 methods)

| Item | Setting |
|---|---|
| Data | M3 (1,428/756/645 monthly/quarterly/yearly) + Tourism (366/427/518), 4,140 series total |
| Test | **last `@horizon` observations** of every series (M3 `18/8/6`; Tourism `24/8/4`), used only for scoring |
| Train/Val | everything strictly before the test segment (NHITS validation windows too) — no leakage |
| Error metric | SMAPE = `100%/n · Σ |ŷ−y| / ((|ŷ|+|y|)/2)`; `0/0 → 0` (declared); pooled over the relevant points |
| Deep model | **N-HiTS (global)**: one model per sampling frequency trained jointly on all series of that frequency (M3 + Tourism); PyTorch, 2 stacks × 2 blocks, width 64, max-pool multi-rate [2,4], identity-basis interpolation, per-window standardisation; Adam lr=1e-3 wd=1e-4, early-stopped on a pre-test validation split, seed 42 |
| Classical (local) | **SNaive**, **Theta** (SES-with-drift, Hyndman–Billah form), **SES**, **ETS** (AIC-selected exponential smoothing), **RWD**, **ARIMA** (order grid + drift via linear exog, AIC) — each fitted per series on the pre-test segment |
| Views | overall · horizon (first/last step) · frequency · difficult series · anomalies · expected shortfall · per-series win/loss |

Difficult / anomaly definitions (SNaive-derived, leak-free):
- **difficult series** = per-series SNaive SMAPE > its 95% quantile (53.9, 207
  of 4,140 series);
- **anomalous points** = test points outside the SNaive 99% prediction interval
  (interval from the std of in-sample one-step seasonal-naive residuals);
- **expected shortfall** = mean of the worst 5% of the per-method errors among
  the anomalous points.

## 2. Headline results (SMAPE, %)

### Overall (pooled over all 4,140 series, 49,894 test points)

| Method | ETS | **NHITS** | SNaive | SES | ARIMA | Theta | RWD |
|---|---|---|---|---|---|---|---|
| SMAPE | **16.99** | 17.34 | 18.31 | 20.79 | 21.20 | 22.93 | 23.48 |

### Horizon (All)

| Step | ARIMA | ETS | NHITS | RWD | SES | SNaive | Theta |
|---|---|---|---|---|---|---|---|
| first | 16.58 | **12.48** | 13.26 | 19.33 | 15.85 | 16.46 | 17.67 |
| last | 25.59 | 23.97 | **21.54** | 24.36 | 23.94 | 23.69 | 24.43 |

### Frequency (All)

| Frequency | ARIMA | ETS | NHITS | RWD | SES | SNaive | Theta |
|---|---|---|---|---|---|---|---|
| monthly | 21.59 | **17.03** | 17.39 | 24.34 | 21.36 | 18.37 | 24.28 |
| quarterly | 16.23 | **12.12** | 15.31 | 18.58 | 16.76 | 13.07 | 18.19 |
| yearly | 26.87 | 24.47 | **20.33** | 26.27 | 23.95 | 26.35 | 22.68 |

### Conditional (All)

| View | ARIMA | ETS | NHITS | RWD | SES | SNaive | Theta |
|---|---|---|---|---|---|---|---|
| difficult series | 82.37 | 69.73 | **59.46** | 92.93 | 69.39 | 84.40 | 71.79 |
| anomaly points | 26.59 | 23.18 | **20.32** | 28.07 | 29.05 | 33.93 | 26.99 |
| expected shortfall | 175.26 | 135.15 | **99.11** | 174.48 | 138.15 | 157.17 | 134.26 |

### Per-series win rate of NHITS

| vs SNaive | vs Theta | vs ETS | vs SES | vs RWD | vs ARIMA |
|---|---|---|---|---|---|
| 0.580 | 0.626 | 0.432 | 0.625 | 0.599 | 0.551 |

All NHITS win rates fall inside 0.30–0.70 — the deep model is **not** a stable
all-round winner at the per-series level.

## 3. Q1–Q4 verdicts

| Q | Answer | Label |
|---|---|---|
| Q1 overall | NHITS is **not** best overall on this subset: **ETS** is (16.99), NHITS second (17.34). NHITS **does** beat SNaive, SES, ARIMA, Theta, RWD overall. Best classical = **ETS** (classical best; Theta is not best here) | partly reproduced |
| Q2 horizon/frequency | NHITS is the **best multi-step forecaster** (last-step 21.54 vs 23.97 ETS) and near-best at the first step (13.26 vs 12.48 ETS, comfortably better than Theta/SES). By frequency: best on yearly (20.33), close on monthly (17.39 vs 17.03), behind ETS/SNaive on quarterly | reproduced (horizon); partial (frequency) |
| Q3 conditions | NHITS stays the best on difficult series and on anomalies (opposite of the paper's reversal) — but win rates are far from 100% (0.43 vs ETS, 0.63 vs Theta), i.e., **not a stable all-win model** | mixed |
| Q4 thesis | A single Overall SMAPE visibly masks the horizon reversal (winner flips ETS→NHITS), the frequency heterogeneity, and the per-series near-ties — the multi-view framework materially changes the model ranking/interpretation | **partially_supported** |

## 4. Reproducibility

```bash
cd agent_solution
NHITS_DEVICE=cuda ./run_all.sh     # or plain ./run_all.sh (CPU)
```

- Seeded everywhere (seed 42); N-HiTS DataLoader uses a seeded generator;
  classical methods deterministic; cached/resume-safe per stage.
- Outputs land in `results/`: `evidence_table.csv` (dataset × view × method
  SMAPE), `winloss_table.csv`, `metrics.json`, forecasts, checkpoints, figures.
- Key evidence images also copied to `evidence/`.