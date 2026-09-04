# Solution — gehlen_2019 Claim Verification

**Task**: Climate Change Vulnerability of American Lobster Fishing Communities in
Atlantic Canada (Greenan et al. 2019, *Front. Mar. Sci.* 6:579,
doi:10.3389/fmars.2019.00579).  L2 end-to-end reproduction using the frozen data
bundle `bnam_cm26_input_subset_v1`.

**Working data (read in place, never copied)**:
- `E:\scisolvebench-data\asset-data\datasets-v1\v1\gehlen_2019\real_data_candidates\bnam_cm26_input_subset_v1\files\`
  - `CM2.6_bottom_temperature_change.nc` — CM2.6 bottom-temperature change
    (one-percent-minus-control), control and projection means, 30-level potential
    temperature change, on the CM2.6 grid (`coords.npz` matches).
  - `BNAM_TSUV_AllDepths.zip` — BNAM monthly bottom-temperature climatology
    (present day, 1990–2015), 8 depth levels.
  - `BNAM_Temperature_DataDictionary.xlsx`, `coords.npz`.
- `F:\dataset\gehlen_2019\reproduce\` — the frozen reproduction workspace
  (BNAM extracted netCDFs, CM2.6 processing, 100-iteration GAM bootstrap
  prediction matrices, P08/P09/P11 intermediate tables).

All numbers below were **computed by running the scripts in `code/`** against
the frozen data.  Values attributed to the paper are explicitly labelled
“paper-cited”.

---

## 1. The two claims under test

- **C01** (paper p. 11, Fig 6): “LVI scores per LFA range from 2 to 2.5;
  LFA 41 scores 2.5 (BNAM) / 2 (CM2.6); none experience net loss.”
- **C02** (paper p. 9): “BNAM and CM2.6 bottom temperature projections show
  similar spatial patterns but different magnitudes.”

LVI = Lobster Vulnerability Index, per LFA (Lobster Fishing Area).

---

## 2. Methods

### 2.1 C01 — LVI per LFA (recomputation)

The paper (p. 8, “Lobster Vulnerability Index Formulation” / “Scoring Matrix”)
defines LVI as a Table 2 5×5 matrix lookup of (exposure score, stock-status
score).  We recompute each term from frozen data:

1. **Exposure — percent change in suitable habitat (CM2.6)**.
   - 10,401 RV-survey rows, each with a predicted habitat suitability for the
     current (observed) and the CM2.6-projected bottom temperature, from the
     frozen 100-iteration bootstrap GAM matrices
     (`P06_bootstrap/predictions_matrix_current.rds`,
     `predictions_matrix_cm26.rds`, read via `pyreadr`).
   - A station is “suitable” when suitability > 0.3 (paper p. 8 / Cook et al.
     2017).  For each (LFA, iteration): `pct = (n_cm26 − n_current)/n_current × 100`.
   - Per-LFA exposure summary = **median** of the 100 iterations
     (matches the median line of paper Fig 5 boxplots).
   - Exposure bin (1–5): `>25 → 1; [5,25] → 2; [−5,5) → 3; [−25,−5) → 4; <−25 → 5`
     (Table 1 row definitions).
   - Station→LFA assignment is the frozen `P09_stock_status/stations_with_lfa.csv`
     (point-in-polygon, LFA 41 polygon constructed; 8 paper LFAs reported).

2. **Stock status** — geometric mean of four 1–5 component scores
   (potential suitable habitat, occupancy, abundance status, food-availability
   trend), taken directly from the frozen `P09_stock_status.csv` /
   `P09_stock_status_detailed.csv`.  Composite → integer bin by
   round-half-away-from-zero (sensitivity to floor/ceil in `04_sensitivity_lvi.py`).

3. **LVI lookup** — `TABLE2[exposure_bin, stock_status_bin]` using the paper's
   Table 2 verbatim.  LFAs 27, 31A, 31B, 32 are excluded (no offshore fishery,
   paper rule).

### 2.2 C02 — Bottom temperature projections

1. **CM2.6 change field**: `bottom_temp_change` from
   `CM2.6_bottom_temperature_change.nc` (projection minus control, 20-yr mean,
   annual).  Statistics over all valid ocean cells (29,252 of 47,040),
   area-weighted (cos-lat) mean, percentiles, warming fractions, subregion means.
2. **BNAM**: present-day monthly bottom-temperature climatology from
   `Bottom_TSUV.nc` (annual, winter JFM, summer JAS means in the CM2.6 domain).
   The extracted file was verified byte-identical (SHA-256) to the
   `BNAM_TSUV_AllDepths.zip` entry in the frozen bundle.
3. **Present-day model agreement** (context, not the claim): CM2.6 control
   sampled to the BNAM grid by nearest neighbour; Pearson correlation, mean
   bias, RMSE over 43,528 overlapping ocean cells.
4. **BNAM projection availability**: a search of the frozen workspace confirms
   no BNAM 2055 RCP8.5 (2046–2065) field exists (the frozen P03/P17 reports
   document this gap).  Therefore the BNAM *change* field cannot be computed.

---

## 3. Results

### 3.1 C01 — Recomputed LVI per LFA (CM2.6)

**Per-LFA percent change in suitable habitat (>0.3), median over 100 iterations:**

| LFA | n stations | median % | q025 % | q975 % | min % | max % | frac. iters < 0 |
|----:|-----------:|---------:|-------:|-------:|------:|------:|----------------:|
| 33  | 80  | +10.96 | +1.03 | +22.22 | −2.27 | +28.13 | 0.01 |
| 34  | 66  | +6.78  | +3.33 | +12.73 | +1.69 | +15.38 | 0.00 |
| 35  | 15  | 0.00   | 0.00  | 0.00   | −6.67 | 0.00   | 0.01 |
| 36  | 32  | 0.00   | 0.00  | 0.00   | 0.00  | 0.00   | 0.00 |
| 37  | 4   | 0.00   | 0.00  | 0.00   | 0.00  | 0.00   | 0.00 |
| 38  | 28  | 0.00   | 0.00  | +8.70  | 0.00  | +13.64 | 0.00 |
| 40  | 69  | +4.62  | +2.28 | +6.35  | +1.54 | +10.17 | 0.00 |
| 41  | 582 | +4.63  | −4.63 | +12.14 | −7.48 | +12.75 | 0.17 |

**LVI per LFA (Table 2 lookup):**

| LFA | Exposure bin | Stock-status composite | SS bin | LVI (recomputed) | Paper (CM2.6, Fig 6) | Match |
|----:|------:|------:|------:|------:|------:|------:|
| 33 | 2 (some gain)  | 3.130 (strict) | 3 | **2.5** | 2.0 | ✗ |
| 34 | 2 (some gain)  | 2.378 (strict) | 2 | **2.0** | 2.0 | ✓ |
| 35 | 3 (no change)  | 2.378 (strict) | 2 | **2.5** | 2.5 | ✓ |
| 36 | 3 (no change)  | 2.378 (strict) | 2 | **2.5** | 2.5 | ✓ |
| 38 | 3 (no change)  | 2.213 (strict) | 2 | **2.5** | 2.0 | ✗ |
| 41 | 3 (no change)  | 4.000 (loose¹)  | 4 | **3.5** | 2.0 | ✗ |

¹ LFA 41's abundance-status component (C3, RV-survey landings) is missing from
the frozen data (Brennan et al. model output / RV landings not archived); the
loose geometric mean of the available components (C1=4, C2=4, C4=4) is used.

**Sensitivity** (all binning combinations in `04_sensitivity_lvi.py`): with
round/floor stock-status binning and median or mean exposure, the recomputed
CM2.6 LVI is invariant — LFAs 34, 35, 36 match the paper; LFAs 33, 38, 41 do
not.  Ceil binning inflates all values and matches nothing.

### 3.2 C02 — Bottom temperature projections

**CM2.6 annual-mean bottom-temperature change (projection − control):**

| Statistic | Value (°C) |
|----------:|-----------:|
| Mean | 1.52 |
| Area-weighted mean | 1.49 |
| Median | 0.87 |
| Std | 1.34 |
| Min / Max | 0.28 / 6.81 |
| Cells warming (>0) | 100 % |
| Cells > 1 / 2 / 3 / 4 °C | 47.9 % / 33.9 % / 18.1 % / 4.5 % |
| Max location | lon −65.55, lat 42.14 |

Subregion means: Georges Bank **3.71** °C, Gulf of Maine **3.58** °C, Bay of
Fundy **2.69** °C, Scotian Shelf **2.60** °C, NE US Shelf **2.28** °C.

**BNAM (present-day only)** — annual mean bottom temperature in the CM2.6
domain: 3.45 °C (summer JAS 3.95 °C; winter JFM 2.89 °C).  No BNAM future
(2055 RCP8.5) field exists in the frozen data, so **no BNAM change field and no
direct BNAM-vs-CM2.6 projection comparison could be computed**.

**Present-day model agreement (context only)**: Pearson spatial correlation of
CM2.6-control vs BNAM bottom temperature = 0.70; mean bias BNAM − CM2.6 =
−0.35 °C; RMSE = 1.81 °C (43,528 overlap cells).

---

## 4. Conclusions

### C01 — **partially_supported**

- ✅ **“None of the LFAs were predicted to experience a net loss of suitable
  habitat” is supported.**  Every paper LFA has median percent change ≥ 0 under
  CM2.6 (LFA 33 +11.0 %, 34 +6.8 %, 40 +4.6 %, 41 +4.6 %, others ≈ 0).
- ⚠️ **The reported LVI values are not reproduced.**  Recomputed CM2.6 LVI
  ranges **2.0–3.5** (paper: 2–2.5); LFAs 33 and 38 recompute to **2.5**
  (paper: 2), LFA 41 to **3.5** (paper: 2).  The mismatch is robust to
  stock-status binning and to median-vs-mean exposure.  Root causes
  (documented in the frozen workspace reports) are: (i) the frozen GAM-bootstrap
  exposure magnitudes are systematically smaller than the paper's Figure 5B
  values; (ii) LFA 41's stock status is incomplete (C3 missing), forcing a
  loose composite of 4.0 → bin 4.
- ❓ **The BNAM-specific value (LFA 41 = 2.5) is unverifiable** — the BNAM
  2055 RCP8.5 temperature field is not part of the frozen data, so the BNAM
  exposure (and hence the BNAM LVI) cannot be computed.

### C02 — **inconclusive**

- The direct comparison “BNAM vs CM2.6 projections: similar spatial patterns,
  different magnitudes” **cannot be tested** with the frozen data, because the
  BNAM projected change field is absent.  Only the BNAM present-day climatology
  is available.
- What *is* verifiable and consistent with the paper: the CM2.6 change field is
  positive everywhere, large in magnitude (mean 1.52 °C, max 6.81 °C) and
  spatially structured (largest on Georges Bank / Gulf of Maine / Scotian
  Shelf) — qualitatively matching the paper's statement that “the projected
  change is larger for CM2.6 than BNAM” (paper-cited, not independently
  verifiable here).  The present-day spatial correlation (0.70) provides only
  weak, indirect context about model similarity, not evidence about the
  *projection* patterns.
- Verdict: **inconclusive** (data-limited).  The claim can be neither confirmed
  nor refuted with the frozen bundle.

---

## 5. Reproducibility

```bash
python agent_solution/code/run_all.py
```

Sequential scripts (all read frozen data in place, all outputs under
`agent_solution/results/`):

| Script | Purpose | Key outputs |
|--------|---------|-------------|
| `01_c01_lvi_recompute.py` | LVI per LFA (CM2.6) from frozen prediction matrices + Table 2 | `pct_change_per_lfa_cm26_recomputed.csv`, `lvi_per_lfa_recomputed.csv`, `lvi_per_lfa_detailed_recomputed.csv` |
| `02_c02_temperature_compare.py` | CM2.6 change-field stats; BNAM present-day climatology; present-day model agreement | `cm26_temp_change_stats.csv`, `cm26_temp_change_subregions.csv`, `bnam_present_temp_stats.csv`, `cm26_vs_bnam_present_comparison.csv`, `figures/` |
| `03_evidence_summary.py` | Assemble evidence table + metrics | `evidence_table.csv`, `metrics.json` |
| `04_sensitivity_lvi.py` | Binning sensitivity for the LVI recomputation | `lvi_sensitivity.csv` |

**Environment**: Python 3.13 (Windows), `numpy`, `pandas`, `scipy`, `netCDF4`,
`pyreadr`, `matplotlib`.  No network access used; no data copied; only frozen
files read.

**Data-gap statement (also in `02_c02_temperature_compare.py` §4)**:
the frozen bundle contains the BNAM present-day climatology but **not** the BNAM
2055 RCP8.5 projection (P03/P17 reports), and the CM2.6 change field is an
annual mean (no monthly/seasonal resolution, P04 report).  These gaps make the
BNAM-vs-CM2.6 projection comparison and the BNAM-side LVI non-reproducible.
