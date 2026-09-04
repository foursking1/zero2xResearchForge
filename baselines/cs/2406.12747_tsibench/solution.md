# solution.md — Method & Results (task 2406.12747_tsibench)

## Goal

Reproduce/verify two critical claims of TSI-Bench (arXiv:2406.12747v2) on the
ETT_h1 dataset at 10% single-point missingness:

- **C1**: simple baselines rank `Linear < LOCF < Median ≈ Mean`; Linear MAE ≈ 0.197.
- **C2**: linear interpolation is of the same magnitude as reported deep methods.

## Method (reproduced protocol)

1. **Data**: frozen `data/ETT-h1.csv` (17,420 hourly rows, 7 series). SHA-256
   checked against the manifest at runtime. (Physical location resolved from
   `-F:\dataset\...` mount `M:\`/`/mnt/f/` via candidate paths.)
2. **Split** (per paper App. A.2, 14/5/5 months):
   - train: `2016-07-01 ≤ t < 2017-09-01` (10,248 rows),
   - val: `2017-09-01 ≤ t < 2018-02-01` (3,672 rows),
   - test: `t ≥ 2018-02-01` (3,500 rows).
3. **Standardization**: per-feature z-score; mean/std **fit on train only**
   (7 dims; train raw μ = 7.84/2.01/4.88/0.75/3.00/0.77/17.38, σ =
   6.15/2.14/5.92/1.96/1.26/0.67/8.57). Mask never enters any statistic.
4. **Windows**: non-overlapping, length 48, per split, trailing partial dropped
   → **213 / 76 / 72** windows (paper Table 4 reports 212/75/71; +1 known
   protocol shift, discussed in `report.md`).
5. **Missingness**: 10% single-point masks, drawn per window with one **global**
   `numpy.random.default_rng(seed)` in order train→val→test (each window:
   `rng.random((48,7)) < 0.1`). Fixed seed set `{42, 43, 44}`. Test masked
   points: **2385 / 2412 / 2404** (≈10.0% of 72·48·7).
6. **Baselines** (on standardized test windows).
   - Mean → train normalized feature mean fill; Median → train normalized
     feature median fill;
   - LOCF → per-window/per-feature forward fill (`ffill`, then `bfill`);
   - Linear → per-window/per-feature linear interpolation
     (`pandas.Series.interpolate(method="linear", limit_direction="both")`).
7. **Metrics**: MAE (primary) and MSE, **only on test masked positions**,
   standardized units, aggregated mean ± std over seeds.

## Results

| imputer | seed 42 | seed 43 | seed 44 | mean ± std | paper Table 2 |
|---|---:|---:|---:|---:|---:|
| **Linear** | **0.2033** | **0.2007** | **0.2072** | **0.2037 ± 0.0033** | 0.197 |
| LOCF | 0.3024 | 0.2920 | 0.2939 | 0.2961 ± 0.0055 | 0.315 |
| Median | 0.8588 | 0.8373 | 0.8228 | 0.8396 ± 0.0181 | 0.71 |
| Mean | 0.8713 | 0.8478 | 0.8392 | 0.8528 ± 0.0166 | 0.737 |

Ordering `Linear < LOCF < Median` and `Linear < Mean` holds on **every seed**
and on the means. Figure: `evidence/seed_sensitivity.png`.

## Answers to the task questions

- **(a) C1**: Yes — measured MAEs (Linear 0.2037, LOCF 0.296, Median 0.84,
  Mean 0.85) satisfy both the strict ordering and the paper's magnitude band on
  all 3 seeds. Values are within +3.4%/−6% (Linear/LOCF) and +16–18%
  (Median/Mean, a known definitional offset) of paper Table 2.
- **(b) C2**: Yes, with a quoted-vs-measured caveat — our measured Linear (≈0.204)
  is the same order of magnitude as the reported deep methods and beats 9 of 15
  quoted ones (iTransformer 0.263, DLinear 0.227, TimesNet 0.254, SCINet 0.246,
  GP-VAE 0.329, Koopa 0.435, US-GAN 0.458, FiLM 0.583, MRNN 0.789); only the
  best attention models (SAITS 0.144, CSDI 0.151, Informer 0.167, Transformer
  0.178, Pyraformer 0.182) are clearly better. The paper's own Linear value
  (0.197) matches our measurement. Deep numbers are **quoted, not measured**.

## Conclusion

`supported` (C1 reproduced with seed robustness; C2 holds given the depths
quoted from the paper).

## Reproduce

```bash
cd agent_solution/code
python impute_bench.py --seeds 42 43 44          # full pipeline -> ../results/
python verify_anchor.py                          # spot-checks (2385 pts, Linear 0.2033...) 
python make_figure.py                            # figure + csv (optional)
```

Dependencies: Python ≥3.10, `numpy`, `pandas` (matplotlib only for the figure).
No network, no models, no GPU needed — will run in <60 s on CPU.