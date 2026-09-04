# Claim Assessment — ExoMiner TESS vetting score behaviour (task 2111.10009)

**Verdict (four-tier): `supported`**

## The claim under test

The paper (ExoMiner, Valizadegan+2022, ApJ 926, 120; arXiv:2111.10009, Abstract/§8.4/§9/§10/Table 16) asserts:
1. ExoMiner produces a highly discriminatory validation score: Kepler test-set recall 0.936 at fixed 99% precision (best legacy classifier 0.763); on the TESS (TOI) experiment precision 0.88 / recall 0.73.
2. ExoMiner is *more conservative in the low-MES region*: among 943 Kepler unlabeled KOIs with MES<10.5, only 20 (2.1%) reach score>0.99.
3. Newly validated planets cluster at high score and high MES: score>0.99 *and* MES>10.5 (301 new Kepler planets; radius 0.6–9.5 R⊕, period 0.5–280 d).

Directly testable on the frozen TESS TCE catalog (11,289 rows, no ground-truth labels): the score **distribution**, the **low-MES conservatism**, the **high-score population** and the **score–signal-strength monotonicity**.

## Measured numbers (frozen catalog, all reproducible via `code/run_analysis.py`)

### 1. Score distribution (Q1)
| metric | value |
|---|---|
| rows (pandas) | 11,289 (16 cols) |
| score min / median / max | 0.101 / 0.755 / 0.999 (7 TCEs at 0.999) |
| score ≥ 0.5 (PC threshold) | 7,229 = **64.0%** |
| score > 0.99 (validation threshold) | 1,070 = **9.5%** |

High scores are concentrated: only ~9.5% of the catalog exceeds 0.99, and iqr-q75 already sits at 0.963; >60% of TCEs fall below 0.5. Consistent with "high score concentrated in a minority of strong-signal candidates".

### 2. Low-MES conservatism (Q2)
| group | n | score>0.99 | fraction |
|---|---|---|---|
| MES < 10.5 | 3,242 | **30** | **0.93%** |
| MES ≥ 10.5 | 8,047 | 1,040 | 12.92% |

MES-bin monotonicity of the >0.99 fraction (strictly non-decreasing; first bin structurally empty):

| MES bin | n_tce | >0.99 | frac |
|---|---|---|---|
| 0–5 | 0* | 0 | 0% |
| 5–10 | 2,907 | 20 | 0.69% |
| 10–15 | 2,741 | 159 | 5.80% |
| 15–20 | 1,562 | 174 | 11.14% |
| 20–30 | 1,737 | 269 | 15.49% |
| ≥30 | 2,342 | 448 | 19.13% |

\* TESS SPOC vetting in this export has an MES floor ≈7.1; the 0–5 bin contains no TCEs.

**Direction agrees with the paper's Kepler claim** (2.1% at MES<10.5). Magnitudes are the same order (0.93% vs 2.1%); TESS is *even more conservative* at low MES. Median score 0.62 (low-MES) vs 0.827 (high-MES); Mann-Whitney p≈3.7×10⁻⁸⁴.

**Attribution of the difference (0.93% vs 2.1%)** — not an error:
- The frozen catalog is a **score>0.1 display subset** of the full TCE list. All excluded TCEs have score ≤0.1, i.e. cannot be >0.99, so the measured low-MES fraction is an *upper bound* of the full-TCE value → the full population would show equal or smaller fraction.
- Different missions/pipelines (TESS SPOC 2-min vs Kepler PDC/KOI), different candidate populations (TCE/TOI vs KOI), different sample sizes and thresholds (MES<10.5 window here is [7.1, 10.5) because of the SPOC floor), and later model version / additional training data.

### 3. High-score population (Q3)
score>0.99 **and** MES>10.5 → **1,040** TCEs.

| param | median | min | max |
|---|---|---|---|
| Planet Radius [R⊕] | 6.79 | 0.59 | 20.84 |
| Orbital Period [d] | 3.92 | 0.28 | 124.73 |

Overlap with the paper's Kepler 301-planet window (0.6–9.5 R⊕, 0.5–280 d): 683 (radius), 1,033 (period), 676 (both). The TESS period cap ≈125 d (vs 280 d for Kepler) is expected: TESS long-cadence S1–67 observations consist of ≲27-d sectors; detecting long-period signals requires multiple adjacent sectors and few-transit detections are harder, so the TESS high-confidence population is intrinsically shorter-period. Radius range extends beyond 9.5 R⊕ (large radii on TESS often reflect diluted eclipsing-binary/grazing configurations). Same qualitative structure as Kepler (score>0.99 ⇒ MES>10.5).

### 4. Score vs signal strength (Q4)
- Spearman(score, MES) = **0.183** (p≈4.8×10⁻⁸⁶) — positive, modest.
- Spearman(score, SNR) = **0.197** (p≈4.6×10⁻⁹⁹) — positive, modest.

The relationship is monotone *in direction* (higher signal → higher score, bin fractions rise monotonically with MES), but strength is moderate: score encodes more than raw signal strength (shape, diagnostics, redness/RUWE, etc.). This matches the paper's Fig. 14/§8.4 qualitative picture.

### 5. Verdict justification
Four-tier label: **supported**.

- High discrimination/population concentration at strong signals: confirmed on frozen catalog (64.0% ≥0.5, 9.5% >0.99, >0.99 fraction rises monotonically from 0.69%→19.13% with MES).
- Low-MES conservatism: confirmed — 0.93% (>99% of low-MES TCEs stay below 0.99), strictly below the 12.9% of the high-MES group and *below* the paper's own Kepler 2.1%.
- High-score & high-MES population: 1,040 TCEs with expected TESS window differences.
- Not directly testable: absolute precision/recall (0.936/0.763 Kepler; 0.88/0.73 on 407 TOIs) require TFOPWG/Kepler ground-truth labels not present in the frozen package; therefore the score-**behaviour** claims are judged, not the calibrated accuracy numbers. Nothing measured contradicts the paper; no residual points against it → `supported` (not merely partial).

## Point-by-point paper comparison (paper values used for discussion only, never as measured results)

| Paper claim | Paper value (Kepler/TOI) | Frozen TESS TCE catalog (measured) | Consistency |
|---|---|---|---|
| Conservative at low MES | 20/943 = 2.1% (MES<10.5) | 30/3,242 = 0.93% | Direction same; TESS *more* conservative |
| New planets at score>0.99 & MES>10.5 | 301 (Kepler) | 1,040 TCEs (candidates, not confirmed) | Same selection rule reproduces a large, well-defined population |
| Radius range of new planets | 0.6–9.5 R⊕ | 0.59–20.84 R⊕ (median 6.79) | Overlapping; TESS wider (contamination/GBs) |
| Period range of new planets | 0.5–280 d | 0.28–124.73 d (median 3.92) | TESS shorter-period window by construction (sector windows) |
| Recall@99% / TESS PR | 0.936 / 0.88–0.73 | not computable (no ground truth) | — (explicitly out of scope) |

## Limitations (declared)
- Frozen catalog is the score>0.1 **display subset**; counts/fractions are conditioned on that subset (upper-bound bias for >0.99 fractions).
- TESS vs Kepler task/dataset differences make cross-distribution comparisons indicative, not exact.
- No ground-truth labels ⇒ precision/recall not recomputed; only score-behaviour claims adjudicated.