# Report — Reproducing arXiv:2509.16616 Appendix D (Tables 8/9) on the frozen public data

## 1. Task and claims under test

The paper "Learn to Rank Risky Investors: A Case Study of Predicting Retail
Traders' Behaviour and Profitability" (Li & Ma, ACM TOIS 44(1) Article 15,
2025) proposes **PA-RiskRanker**: risk identification recast as learning-to-
rank with a profit-aware BCE loss (PA-BCE), a transformer encoder, and
self-cross-trader attention among traders. The headline accuracy/profit claims
(§abstract: 8.4% F1 / 10–17% profit gains) are made on a proprietary retail-
broker transaction dataset (13.6M records, not publicly available). For the
publicly-reproducible part, Appendix D reports, on two Kaggle datasets
(creditcard fraud; job profitability), the **with-prior** setting — assume 1%
of the population are risky — and 3-fold averages of F1 and financial loss,
with PA-RiskRanker **best in both F1 and financial loss** on both datasets.

This package tests the falsifiable claims (a)–(d) from TASK.md on the frozen
data:

- (a) PA-RiskRanker has the highest F1 among all implemented baselines on
  `creditcard`;
- (b) same on `jobprofit`;
- (c) PA-RiskRanker has the lowest financial loss on both datasets;
- (d) PA-RiskRanker improves over Rankformer (the strongest LETOR baseline) in
  F1 on both datasets.

Paper anchors (Appendix D, with-prior, 3-fold mean): creditcard PA-RiskRanker
F1=0.9870 / loss=31,368.39 vs Rankformer 0.9820 / 43,821.78; jobprofit
PA-RiskRanker 0.9491 / 19,363.32 vs Rankformer 0.8539 / 59,177.19.

## 2. Protocol (rebuilt from the frozen CSVs) — `code/common.py`

| | creditcard | jobprofit |
|---|---|---|
| frozen CSV | `data/creditcard/creditcard.csv` | `data/jobprofit/job_profitability.csv` |
| rows × cols | 284,807 × 31 | **14,479** × 31 (Kaggle's current edition; `SOURCE.md`/manifest note "9,998" is stale — the file size/checksum below is authoritative) |
| SHA-256 | `76274b691b16…851a89` | `5a2a7dfae5f7…6ed8b` |
| label | `Amount` top-1% (≥ 1017.97) | `Jobs_Gross_Margin` (dollar profit proxy) top-1% |
| prediction features | Time + V1–V28 (29) | 24 remaining columns after dropping the 7 future-info columns |
| dropped columns | `Class`, `Amount` (leak/label) | `Job_Number`, `Jobs_Subtotal`, `Labor`, `Jobs_Total`, `Lead_Generated_From_Source`, `Pricebook_Price`, `Jobs_Gross_Margin` |
| positives | 2,849 (1.0006%) | 145 (1.0016%) |

`Amount`/`Jobs_Gross_Margin` are excluded from *features* because the binary
label is defined on them (direct label leakage) — but they remain the
financial-impact probe for the loss penalty and the profit-aware weighting.
This matches the paper's own XGB value (0.9755), which would collapse to ≈1.0
if `Amount` were a regressor feature.

**Splits.** 3 independent stratified 70/10/20 splits preserving ≈1%/99% in
every part: `StratifiedShuffleSplit(n_splits=3, test_size=0.2, seed=2026)`;
val (10% of data) carved from train with fold seeds {1, 7, 42}
(`common.make_splits`). Per fold: creditcard — train 205,060 (2,051 pos), val
22,785 (228 pos), test 56,962 (570 pos); jobprofit — train 10,424 (104 pos),
val 1,159 (12 pos), test 2,896 (29 pos). Verified in `evidence/data_facts.json`.

**Ranking groups (paper §3.2, tabular adaptation).** Every train positive
anchors a group of 100 (`group_size=100`): itself + 99 normals sampled without
replacement (seeded). Used by λMART and the two transformer rankers.

**Evaluation.**
- with-prior (primary): sort by score, declare top `round(0.01·n_test)`;
  F1 = 2·P·S/(P+S) with P=TP/k, S=TP/n_pos, Sp=TN/n_neg.
- financial loss = Σ over all misclassified (FN ∪ FP) of the impact probe:
  `Amount` (creditcard) and `max(Jobs_Gross_Margin, 0)` (jobprofit; floored
  at 0 → it is a penalty).
- AUC = RankROC on raw scores (threshold-free; identical in both settings).
- without-prior (secondary): per-seed val-optimal score cutoff applied to
  test.

## 3. Models (`code/model.py`, `code/train_pa.py`, `code/run_one_fold_baseline.py`)

**PA-RiskRanker (ours).** For each ranking group, embed every trader's features
(2-layer MLP, d=128), run a 2-layer transformer encoder (4 heads, pre-norm,
GELU, dropout 0.1) so each trader attends to every other trader in its group —
the *self-cross-trader attention*. Training objectives:
  ① **PA-BCE** (the paper's profit-aware BCE): BCE weighted so that risky
  traders have `w = 40 · clip(impact/mean_positive_impact, 0, 3)` and normals
  have `w = 1` — misranking a high-impact trader is penalised much more than a
  low-impact one;
  ② auxiliary profit-proxy head: Huber regression of z-scored `asinh(impact)`
  (our tabular stand-in for the profitability supervision the paper reads from
  the broker data).
  AdamW(lr=1e-3, wd=0.02), cosine schedule, gradient clipping 5.0, batch
  32/16, early stopping on val top-1% F1, ≤60 epochs, CPU, seeds {10,20,30}.
  **Reported metric = 3-seed score ensemble** (mean scores → top-1% selection).

**Rankformer-baseline.** Identical backbone *without* cross-trader attention
(per-token MLP transformer), trained with ListNet listwise loss on the same
groups, no profit signal. Contrast isolates the PA-BCE + attention contribution.

**Other baselines.** λMART = XGBoost `rank:ndcg` on the same groups (350
rounds, η=0.04); LightGBM (600 trees), XGBoost (400 trees), RandomForest (150
trees × depth 18). All single training on train only.

## 4. Results (all from frozen data; `results/evidence_table.csv`, `results/metrics.json`, `results/summary.md`)

### 4.1 with-prior — 3-fold means

| dataset | model | F1 | FinLoss | AUC | P | S | Sp |
|---|---|---|---|---|---|---|---|
| creditcard | PARiskRanker | **0.9088** | 100,619.5 | 0.99971 | 0.9088 | 0.9088 | 0.99910 |
| creditcard | rankformer | 0.9357 | 74,355.0 | 0.99987 | 0.9357 | 0.9357 | 0.99932 |
| creditcard | lambdamart | 0.9415 | 67,604.9 | 0.99987 | 0.9415 | 0.9415 | 0.99941 |
| creditcard | rf | 0.9468 | 61,365.6 | 0.99988 | 0.9468 | 0.9468 | 0.99946 |
| creditcard | lgbm | 0.9550 | 51,894.6 | 0.99993 | 0.9550 | 0.9550 | 0.99954 |
| creditcard | xgb | 0.9556 | 51,520.5 | 0.99992 | 0.9556 | 0.9556 | 0.99954 |
| jobprofit | PARiskRanker | 0.8046 | 35,283.0 | 0.99858 | 0.8046 | 0.8046 | 0.99796 |
| jobprofit | rankformer | 0.8506 | 26,629.8 | 0.99903 | 0.8506 | 0.8506 | 0.99848 |
| jobprofit | lambdamart | 0.8621 | 24,630.3 | 0.99945 | 0.8621 | 0.8621 | 0.99860 |
| jobprofit | rf | 0.8161 | 30,727.8 | 0.99880 | 0.8161 | 0.8161 | 0.99809 |
| jobprofit | lgbm | 0.9310 | 11,770.5 | 0.99968 | 0.9310 | 0.9310 | 0.99928 |
| jobprofit | xgb | 0.9425 | 10,537.2 | 0.99980 | 0.9425 | 0.9425 | 0.99944 |

PA-RiskRanker rows = 3-seed (10/20/30) score ensemble per fold (9 runs /
dataset), 63 runs total incl. baseline reproduction. Bold = PA-RiskRanker
(paper's claim); gray-highlighted = gradient-boosted pointwise baselines beat
it on both datasets.

### 4.2 without-prior (boundary check, val-optimal cut)
`results/evidence_table.csv` (setting column) and `metrics.json`.

### 4.3 Comparison with paper Tables 8/9
- **Direction**: the paper's claim "PA-RiskRanker is best" is **not**
  reproduced on these folds. In our experiments the gradient-boosted pointwise
  classifiers (LGBM, XGB) are the strongest under with-prior top-1% F1 on both
  datasets; PA-RiskRanker (0.9088 creditcard / 0.8046 jobprofit) stays below
  Rankformer (0.9357 / 0.8506) in both.
- **Magnitude**: our creditcard numbers are close to the paper's absolute
  levels for the GBMs (paper XGB 0.9755 here 0.9556; split re-sampling
  variance is expected), but the ranking-position of PA-RiskRanker differs.
- **Sources of divergence** (see §6).

## 5. Verdicts (evidence-strength graded)

- (a) highest F1 on creditcard — **contradicted** on the frozen folds
  (PA-RiskRanker 0.9088 < LGBM 0.9550 / XGB 0.9556). F1 vs Rankformer is also
  negative (0.9088 < 0.9357, outside the ±0.01 direction band).
- (b) highest F1 on jobprofit — **contradicted** (PA-RiskRanker 0.8046 <
  XGB 0.9425 / LGBM 0.9310 / λMART 0.8621 / Rankformer 0.8506).
- (c) lowest financial loss — **contradicted** on both datasets (PA loss
  creditcard 100.6k vs GBM ≈51.7k; jobprofit 35.3k vs ≈11.2k).
- (d) PA-RiskRanker > Rankformer F1 — **contradicted** in our runs
  (creditcard 0.9088 < 0.9357; jobprofit 0.8046 < 0.8506).

Strength: medium-high for the *negative* claims (3-fold × 3-seed ensembles,
seeded, CPU, offline); low for asserting anything about the *paper's* global
accuracy since the proprietary dataset and the authors' pretrained weights are
unavailable. The results therefore show a **replicability gap**, not evidence
either way about the paper's proprietary-data claims.

## 6. Why we did not reproduce the claimed ordering (analysis)

1. **Data gap**: the proprietary time-series trader dataset (§3) and the
   authors' pretrained model parameters are not available; the appendix
   tabular adaptation is under-specified. We re-implemented from scratch.
2. **Task geometry**: with prior F1 is decided purely by catching the most
   risky 1% — a hard *boundary* classification on tabular features. GBDTs fit
   such boundaries sharply; the profit-aware ranking signal mainly re-weights
   *which* positives matter (loss), not raw top-1% recall.
3. **Fold granularity**: jobprofit test folds hold only ≈29 positives; a
   1–2 sample swing moves F1 by several points, making fine comparisons noisy.
4. We reproduce the *without-prior* behaviour the paper itself reports for
   jobprofit (pointwise classifiers overtake ranking methods), consistent with
   the paper's own boundary discussion.

## 7. Verifiability / anti-leakage

- Everything reads the frozen CSVs (`data/`) only; no downloads, no other
  datasets, no synthetic resampling.
- Train/val/test are disjoint per fold; val used only for early stopping and
  threshold selection; test touched only for the final score computation.
- `code/data_facts.py` recomputes counts / labels / split ratios from the CSVs
  (`evidence/data_facts.json`); `code/common.py` + `code/aggregate.py`
  reproduce the numbers in `evidence_table.csv`.
- Rerun guide: `agent_solution/README.md`. All runs are deterministic (seeded),
  CPU-only, and take ≈1–2 h wall.

## 8. Limitations

- Absolute F1/loss cannot be matched to the paper (different splits built from
  raw CSVs; authors' folds/pretraining unavailable) — judged on direction and
  ranking.
- `Amount`-exclusion and aux-head are documented design choices; alternative
  treatments exist.
- A stronger transformer (authors' architecture + pretraining, GPU, more
  epochs) might reduce but not obviously reverse the observed gap on these
  tabular benchmarks.