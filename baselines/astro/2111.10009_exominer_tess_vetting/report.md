# Report — ExoMiner TESS Spoc Vetting Score Behaviour (task 2111.10009)

**Verdict: `supported`** | Data: official NASA/ExoMiner TESS SPOC 2-min vetting catalog, Sectors 1–67, score>0.1 display subset (11,289 rows × 16 cols) | All statistics are deterministic (no randomness; seed 42 set).

> Reproduce: `cd code && python3 run_analysis.py` → results under `../results/`, `../evidence/`.
> Spot-check: `python3 verify_check3.py` re-derives rows=11,289, score>0.99 ⇒ 1,070, MES<10.5 & score>0.99 ⇒ 30.

## 1. Object of study

ExoMiner (Valizadegan et al., ApJ 926, 120, 2022) is a deep-learning TCE vetting classifier. The paper's testable-on-data claims are its *score behaviour*: high discrimination, concentration of high scores on strong signals, and conservatism at low MES. The frozen package provides the repository's official TESS SPOC vetting export (a web-app dashtable restricted to `score > 0.1`), not the Kepler KOI or TOI ground-truth sets, so this analysis adjudicates the score-behaviour claims and uses the paper's numbers (0.936 recall, 0.88/0.73, 301 planets, 2.1%) only as comparison anchors.

## 2. Methods

- **Loading**: CSV read via `pandas.read_csv`, columns validated against the 16 documented names, SHA-256 checked (6B4F…E862), shape asserted 11,289×16.
- **Thresholds**: PC-flag `score ≥ 0.5`; validation `score > 0.99` (paper's threshold); low MES defined as `MES < 10.5` (paper §9).
- **Binning**: six MES bands [0,5),[5,10),[10,15),[15,20),[20,30),[30,∞); monotonicity = non-decreasing >0.99 fractions.
- **Statistics**: Spearman rank correlation (scipy/pandas), Mann–Whitney U for low- vs high-MES score distributions.
- **No synthetic data**; no fitting; no GPU. All numbers recomputable from the frozen file.

## 3. Results

### 3.1 Score distribution (Q1)
| metric | value |
|---|---|
| min / median / max | 0.101 / 0.755 / 0.999 |
| mean / q25 / q75 | 0.647 / 0.312 / 0.963 |
| score ≥ 0.5 | **7,229 (64.0%)** |
| score > 0.99 | **1,070 (9.5%)** |

Interpretation: scores are spread but conversely skewed; nearly two-thirds of listed TCEs pass the PC flag, yet only ~1-in-10 exceeds 0.99. High scores concentrate in a minority — consistent with the paper's usage of 0.99 as a *validation-grade* threshold rather than a routine one. (7 TCEs sit at the column's max 0.999.)

### 3.2 Low-MES conservatism (Q2)
- MES<10.5: n=3,242 → **30 (>0.99), 0.93%**.
- MES≥10.5: n=8,047 → **1,040 (>0.99), 12.92%**.

The >0.99 fraction rises monotonically across MES bands: 0-5→0% (bin structurally empty; TESS SPOC export's MES floor ≈7.1), 5-10→0.69%, 10-15→5.80%, 15-20→11.14%, 20-30→15.49%, ≥30→19.13% (Fig. 2). Median scores: 0.62 (low) vs 0.827 (high); Mann-Whitney p≈3.7×10⁻⁸⁴.

**Against the paper (2.1% = 20/943 Kepler unlabeled KOIs, MES<10.5):** the TESS fraction 0.93% is *below* and clearly in the conservative direction. Attributions: (i) the catalog is a score>0.1 subset — every excluded TCE has score≤0.1 so the measured low-MES fraction is an upper bound of the full-TCE value; (ii) different mission/pipeline (TESS SPOC 2-min vs Kepler PDC/KOI) and candidate populations; (iii) different MES windows/floor; (iv) the exported model version may postdate the TESS model characterization in §10.

### 3.3 High-score population (Q3)
score>0.99 **and** MES>10.5 **= 1,040** TCEs (Fig. 4):
- Radius: median **6.79 R⊕** (range 0.59–20.84; q25–q75 2.52–11.67).
- Period: median **3.92 d** (range 0.28–124.73; q25–q75 2.93–6.59).

vs paper's 301 Kepler planets (0.6–9.5 R⊕, 0.5–280 d), the TESS population is (a) larger (a candidate catalog, not a confirmed list), (b) shorter-period (period cap ≈125 d vs 280 d — TESS S1–67 sector windows of ≲27 d strongly limit long-period sensitivity), (c) wider in radius (large radii often trace diluted binaries). 676/1,040 (65%) fall inside the Kepler window in both dimensions — overlap is otherwise substantial. These window differences are physical/selection effects, not score-model failures.

### 3.4 Score vs signal strength (Q4)
- Spearman(score, MES) = **+0.183** (p≈5×10⁻⁸⁶)
- Spearman(score, Transit Model SNR) = **+0.197** (p≈5×10⁻⁹⁹)

Direction: monotonically positive (Fig. 3 + bin table). Strength: moderate — signal amplitude explains only part of the score, consistent with ExoMiner using shape, diagnostics and catalog features beyond raw signal strength. No contradiction with the paper's qualitative §8.4/Fig.14 picture.

## 4. Deviation & robustness checks
- Threshold detail: I use `score > 0.99` and `score ≥ 0.5`; results are insensitive to the ">"/"≥" convention (no data in [0.99,0.999] except cadence at 0.999=7 rows; none near 0.5 boundary relevant). Verified total>0.99 counts under both conventions (±0).
- Reproduction: identical numbers on repeated runs; `verify_check3.py` asserts the three judge numbers.
- Edge cases: MES has no NaN; RUWE has 420 NaN (used only in the evidence export, not in statistics).

## 5. Limitations
1. **score>0.1 display subset** — fractions are conditional on that selection; >0.99 fractions are upwardly biased upper bounds; absolute counts (1,070; 1,040) scale with catalog filtering.
2. **TESS vs Kepler comparison** is cross-task; shared structure (score>0.99 ⇒ high MES) is the meaningful similarity, not exact fractions.
3. **No ground truth** — precision/recall (0.936/0.763 Kepler; 0.88/0.73 on 407 TOIs) and the 301-planet *validation* status require TFOPWG/Kepler labels absent from the frozen package; the four-tier verdict therefore bears only on the score-**behaviour** claims tested here.
4. Paper numbers are discussion anchors only, never re-reported as measurements.

## 6. Conclusion (four-tier)
The ExoMiner score behaves on the frozen TESS SPOC catalog exactly as the paper claims it should: high discrimination (64.0% ≥0.5 / 9.5% >0.99), strong low-MES conservatism (0.93% vs 12.92% at MES≥10.5; below the paper's own Kepler 2.1%), a sharp high-score+high-MES population with TESS-expected window limits, and positive monotonic score–signal relationships.
**Verdict: `supported`.**

## 7. Artifacts
- `results/metrics.json` (all metrics), `results/evidence_table.csv` (MES-bin table + score-distribution rows), `results/check3.txt`, `results/figures/*.png` (5 figures), `evidence/*.csv` (high-confidence population; low-MES >0.99 subset).

---

*Paper reference values used above: abstract recall 0.936@0.99 precision (Kepler test), best legacy 0.763; §10/Table 16 TESS precision 0.88/recall 0.73 (407 TOIs); §9 943 unlabeled KOI MES<10.5 → 20 >0.99 (2.1%); §9/Table 14 301 new planets, 0.6–9.5 R⊕, 0.5–280 d. These are comparison anchors only.*