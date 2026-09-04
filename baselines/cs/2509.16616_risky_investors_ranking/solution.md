# Solution — Reproducing Appendix D (Tables 8/9) of PA-RiskRanker (arXiv:2509.16616)

> Full details in `report.md`. Evidence: `results/evidence_table.csv`,
> `results/metrics.json`, `results/summary.md`, `evidence/data_facts.json`.

## Protocol (self-built from the frozen CSVs)
- **creditcard** (284,807×31): label = top-1% by `Amount` (leak-free features:
  Time+V1–V28; `Amount` kept only as the impact probe / loss weight).
- **jobprofit** (14,479×31, Kaggle's current version — the manifest's "9,998
  rows" note is stale): drop 7 future-information columns; label = top-1% by
  `Jobs_Gross_Margin` (dollar-profit "profitability" proxy).
- **Splits**: 3 stratified 70/10/20 with ≈1%/99% (`random_state=2026`, val seed
  1/7/42). **Groups**: 1 positive + 99 normals per ranking group (train only).
- **with-prior** = declare top `round(1%·n_test)` by score; F1=2PS/(P+S);
  financial loss = Σ over all misclassified of Amount / max(margin,0); AUC
  threshold-free. 3-fold averaged.
- Models: PA-RiskRanker (PA-BCE + self-cross-trader attention + impact-proxy
  aux, 3-seed ensemble), Rankformer-bsl (ListNet, no cross-attn), λMART
  (XGB rank:ndcg), LightGBM, XGBoost, RandomForest. PyTorch on CPU, seeded.

## Results (with-prior, 3-fold mean) — `results/summary.md`

| dataset | model | F1  | FinLoss | AUC |
|---|---|---|---|---|
| creditcard | PARiskRanker (3-seed ens) | 0.9088 | 100,620 | 0.99971 |
| creditcard | rankformer   | 0.9357 | 74,355 | 0.99987 |
| creditcard | lambdamart   | 0.9415 | 67,605 | 0.99987 |
| creditcard | lgbm | 0.9550 | 51,895 | 0.99993 |
| creditcard | xgb  | 0.9556 | 51,520 | 0.99992 |
| creditcard | rf   | 0.9468 | 61,366 | 0.99988 |
| jobprofit   | PARiskRanker (3-seed ens) | 0.8046 | 35,283 | 0.99858 |
| jobprofit   | rankformer | 0.8506 | 26,630 | 0.99903 |
| jobprofit   | lambdamart | 0.8621 | 24,630 | 0.99945 |
| jobprofit   | lgbm | 0.9310 | 11,770 | 0.99968 |
| jobprofit   | xgb  | 0.9425 | 10,537 | 0.99980 |
| jobprofit   | rf   | 0.8161 | 30,728 | 0.99880 |

## Claim verdicts (with-prior, 3-fold mean, our implementation)

- (a) creditcard highest F1 — **contradicted**: PA-RiskRanker (0.9088) <
  LGBM/XGB (0.9550/0.9556).
- (b) jobprofit highest F1 — **contradicted**: PA-RiskRanker (0.8046) < XGB
  (0.9425), LGBM (0.9310), and below every other baseline (λMART 0.8621,
  rankformer 0.8506, RF 0.8161).
- (c) lowest financial loss — **contradicted**: PA loss (creditcard 100.6k /
  jobprofit 35.3k) > GBM losses (≈51.7k / ≈11.2k).
- (d) beats Rankformer in F1 — **contradicted** on both datasets in our runs
  (creditcard 0.9088 vs 0.9357; jobprofit 0.8046 vs 0.8506).

All four claims are **contradicted** on the frozen folds with our clean-room
implementation; insight into *why* is in report.md §6. This is reported as a
replicability gap (the Appendix-D winners use proprietary trader time-series
pretraining not available offline), not as disproof of the paper's
proprietary-data claims.

### Why the paper's finding does not transfer here (analysis)
1. **Replicability gap**: authors' pipeline uses the proprietary trader time-
   series (13.6M records) pre-training weights we do not have; the appendix
   tabular adaptation is under-specified. We re-implemented from-scratch on
   CPU with the frozen raw CSVs and self-built folds.
2. **Task shape**: on these tabular proxies, with-prior F1 is a hard 1%-
   boundary classification; GBDTs fit it sharply. The PA-BCE ranking benefit
   (catching *high-value* positives first) shows up more in loss weighting
   than in raw top-1% count on these benchmarks.
3. **Small folds**: jobprofit has only ~29 positives/test → F1 moves in coarse
   steps and is dominated by a couple of samples.

These are honest boundaries, not full reproductions; per the rubric's A3/C
guidance we report them as such rather than claiming a clean win.

## Deliverables
- `code/` — full pipeline (preprocessing → models → 3-fold evaluation).
- `results/evidence_table.csv` (dataset, setting, model, fold, f1,
  financial_loss, auc, precision, sensitivity, specificity) incl. per-fold and
  mean; `results/metrics.json`.
- `evidence/data_facts.json` — frozen-data facts for judge B-checks.
- `report.md` — methods, hyperparameters, leakage control, limitations.