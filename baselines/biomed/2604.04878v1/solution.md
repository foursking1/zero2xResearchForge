# Solution: Evaluating the LPR Claims of arXiv:2604.04878v1

**Paper**: *Learning, Potential, and Retention: An Approach for Evaluating Adaptive AI-Enabled Medical Devices*
(Burgon et al., FDA/CDRH/OSEL; arXiv:2604.04878v1)

**Task ID**: 2604.04878v1 (L2, RCBench lightweight protocol v2.0)

**Analysis date**: 2026-08-13

---

## 1. Summary of Verdicts

| Claim | Verdict | Rationale (one line) |
|---|---|---|
| **C01** Single population shift: stable performance/retention; learning follows potential; potential max at step 1 | **Contradicted** | In the frozen data performance falls ~29%, retention falls ~45%, learning does **not** track potential (Pearson r = −0.46, sign agreement 0.25), and potential peaks at step 3, not step 1. |
| **C02** Limited plasticity: gradual performance decrease; learning never reaches potential; stable retention | **Partially supported** | Performance decreases monotonically and learning < potential at all 4 steps (**supported**), but retention is **not** stable (1.00 → 0.75, monotonic decline). |
| **C03** Double population shift: non-monotonic performance; learning/potential spike at steps 1 & 3; retention increases at step 3 | **Partially supported** | Non-monotonic performance, potential spikes at steps 1 & 3, and retention increase at step 3 are all confirmed; **but learning does not spike at step 3** (it is strongly negative, −0.134). |
| **C04** Metrics computed using Equations 1–3 with λ = 0.5 | **Supported** | Recomputing learning/potential/retention from the stored 5×5 AUROC matrices reproduces the recorded values to machine precision; λ = 0.5 is the *only* decay value that reproduces the recorded retention series. |

---

## 2. Data

All analysis uses the **frozen reproduction workspace**, read in place (nothing copied):

```
F:/dataset/2604.04878v1/results/
├── single_shift/            rep_1_result.json, aggregated.csv
├── single_shift_limited/    rep_1_result.json, aggregated.csv
├── double_shift/            rep_1_result.json, aggregated.csv
F:/dataset/2604.04878v1/VIGILANT/src/   reference VIGILANT package (Equations 1–3)
F:/dataset/2604.04878v1/arxiv_2604.04878v1.pdf   paper
```

Each `rep_1_result.json` contains a **5×5 AUROC performance matrix** `M[i, j] = S(Model_{i+1} | Dataset_{j+1})`
(model version i+1 evaluated on dataset version j+1), computed from a ResNet-18 trained on
synthetic chest-X-ray populations (A/B/C). The reproduction ran **1 repetition** (seed 1042)
per experiment, not the paper's 25 repetitions.

The paper's `reproduction_report.md` explicitly documents this synthetic 1-repetition
demonstration and its deviations from the paper (real MIDRC data, 25 repetitions, 95% CIs).
The present analysis evaluates the *claims against this frozen reproduction data*.

### Indexing convention

The paper numbers modification steps from 0; VIGILANT versions are 1-indexed. Throughout:

```
paper modification step  0  1  2  3  4
VIGILANT version         1  2  3  4  5
```

LPR metrics are defined for modification steps 1–4 (= versions 2–5); step 0 / version 1 is the
unmodified baseline. The paper's "modification step 1" therefore corresponds to **version 2**
and "modification step 3" to **version 4**.

---

## 3. Methods

### 3.1 Metrics (paper Equations 1–3, as implemented in VIGILANT)

With `S(M_v | D_v)` = AUROC of model version `v` on dataset version `v`:

- **Learning** (Eq. 1): `L(M_V) = S(M_V|D_V) − S(M_{V−1}|D_V)` — improvement of the new model on the current dataset.
- **Potential** (Eq. 2): `P(M_V) = S(M_{V−1}|D_{V−1}) − S(M_{V−1}|D_V)` — performance change attributable to the dataset shift alone.
- **Retention** (Eq. 3): `R(M_V) = Σ_{v=0}^{V−1} S(M_V|D_v) · W((V−1)−v)`, with exponential decay `W(t) = e^{−λt}`, normalized, **λ = 0.5**.

`run_experiment.py` calls `vigilant.learning(df)`, `vigilant.potential(df)`, and
`vigilant.retention(df, decay=0.5)`, matching the paper's λ = 0.5 (also the VIGILANT default).

### 3.2 Verification of C04 (metric computation)

`code/verify_lpr_metrics.py`:
1. Rebuilds the VIGILANT input DataFrame from each stored 5×5 matrix and recomputes the three metrics with the reference package.
2. Compares each recomputed value to the value recorded in `rep_1_result.json`.
3. Recomputes retention for λ ∈ {0.0, 0.25, 0.5, 0.75, 1.0} and checks which λ reproduces the recorded values.
4. Runs the VIGILANT toy-example test cases.

### 3.3 Trend analysis for C01–C03

`code/analyze_claims.py` computes, per experiment, the performance diagonal
`S(M_v|D_v)`, learning/potential/retention series, and the following quantitative checks
(criteria stated *a priori* in the script):

| Rule | Criterion for "support" |
|---|---|
| R01 performance stable | max−min AUROC ≤ 0.10 **or** \|relative decline\| ≤ 0.10 |
| R02 learning tracks potential | \|Pearson r\| ≥ 0.8 and small mean \|L−P\| |
| R03 potential max at step 1 | `potential[step1] == max(potential)` |
| R04 retention stable | max−min ≤ 0.10 **or** \|relative decline\| ≤ 0.10 |
| R05 gradual performance decrease | all first differences ≤ 0 and negative slope |
| R06 learning never reaches potential | `learning < potential` at every step 1–4 |
| R07 retention stable (limited) | max−min ≤ 0.10 **or** \|relative decline\| ≤ 0.10 |
| R08 performance non-monotonic | not monotone (≥1 sign change in first differences) |
| R09 potential/learning spike at steps 1 & 3 | local maximum at step 1 (> next) and at step 3 (> prev and > next) |
| R10 step-3 performance↓ + retention↑ | `perf[step3] < perf[step2]` and `ret[step3] > ret[step2]` |

All numbers are computed directly from the frozen data; no paper values were copied.

---

## 4. Results

### 4.1 C04 — metric computation with λ = 0.5 (verified numerically)

| Experiment | max \|recomputed − recorded\| (learning / potential / retention) |
|---|---|
| single_shift | 0.0 / 0.0 / 0.0 |
| single_shift_limited | 0.0 / 0.0 / 0.0 |
| double_shift | 0.0 / 0.0 / 0.0 |

Retention λ-sensitivity (max absolute error vs. recorded values):

| λ | 0.00 | 0.25 | **0.50** | 0.75 | 1.00 |
|---|---|---|---|---|---|
| single_shift | 0.0337 | 0.0161 | **0.0** | 0.0136 | 0.0249 |
| single_shift_limited | 0.0167 | 0.0079 | **0.0** | 0.0064 | 0.0112 |
| double_shift | 0.0064 | 0.0026 | **0.0** | 0.0020 | 0.0042 |

→ **λ = 0.5 is the only decay value reproducing the recorded retention.** The VIGILANT
toy-example checks also pass (all 12 value checks; Learning 0.30/0.20, Potential 0.10/0.30,
Retention 0.40/0.3245).

**C04: supported.**

### 4.2 C01 — single population shift (`single_shift`)

| Step | 0 | 1 | 2 | 3 | 4 |
|---|---|---|---|---|---|
| Performance (AUROC, diagonal) | 0.9875 | 0.9595 | 0.8557 | 0.6880 | 0.6977 |
| Version (VIGILANT) | 1 | 2 | 3 | 4 | 5 |

Metrics (steps 1–4):

| Step (version) | Learning | Potential | Retention |
|---|---|---|---|
| 1 (v2) | −0.0056 | 0.0224 | 0.9929 |
| 2 (v3) | −0.0072 | 0.0966 | 0.9706 |
| 3 (v4) | −0.0497 | 0.1180 | 0.8591 |
| 4 (v5) | 0.0716 | 0.0620 | 0.5477 |

| Rule | Statistic | Value | Verdict |
|---|---|---|---|
| R01 perf. stable | range / rel. decline / slope | 0.2995 / −0.2935 / −0.0851 | **contradict** |
| R02 learning↔potential | Pearson r / mean\|L−P\| / sign agree | −0.4619 / 0.0773 / 0.25 | **contradict** |
| R03 potential max at step 1 | potential[step1] vs max (at step) | 0.0224 vs 0.1180 (step 3) | **contradict** |
| R04 retention stable | range / rel. decline / slope | 0.4452 / −0.4483 / −0.1447 | **contradict** |

**C01: contradicted.** The frozen reproduction does **not** exhibit the paper's Fig-5 pattern
(stable performance/retention, learning tracking potential, potential peaking at step 1).
Performance declines by ~29% and retention by ~45% across the shift; learning is negative at
steps 1–3 while potential is positive (sign agreement only 25%); potential peaks at step 3.

### 4.3 C02 — limited plasticity (`single_shift_limited`)

| Step | 0 | 1 | 2 | 3 | 4 |
|---|---|---|---|---|---|
| Performance (AUROC, diagonal) | 1.0000 | 0.9789 | 0.9073 | 0.8835 | 0.8316 |
| Version | 1 | 2 | 3 | 4 | 5 |

Metrics (steps 1–4):

| Step (version) | Learning | Potential | Retention |
|---|---|---|---|
| 1 (v2) | 0.0029 | 0.0240 | 1.0000 |
| 2 (v3) | 0.0115 | 0.0831 | 0.9898 |
| 3 (v4) | 0.0292 | 0.0530 | 0.9330 |
| 4 (v5) | 0.0026 | 0.0544 | 0.7501 |

| Rule | Statistic | Value | Verdict |
|---|---|---|---|
| R05 gradual perf. decrease | monotone / slope / total decline | True / −0.0432 / 0.1684 | **support** |
| R06 learning < potential always | all steps / min(P−L) | True / 0.0211 | **support** |
| R07 retention relatively stable | range / rel. decline / slope | 0.2499 / −0.2499 / −0.0807 | **contradict** |

**C02: partially supported.** The two core plasticity mechanisms reproduce well: performance
decreases monotonically across the 4 modification steps and learning never reaches potential
at any step. However, retention is **not stable** — it declines monotonically from 1.00 to 0.75
(−25%), contradicting the paper's "retention remains relatively stable."

### 4.4 C03 — double population shift (`double_shift`)

| Step | 0 | 1 | 2 | 3 | 4 |
|---|---|---|---|---|---|
| Performance (AUROC, diagonal) | 0.9981 | 0.9624 | 0.7396 | 0.4835 | 0.4929 |
| Version | 1 | 2 | 3 | 4 | 5 |

Metrics (steps 1–4):

| Step (version) | Learning | Potential | Retention |
|---|---|---|---|
| 1 (v2) | 0.0686 | 0.1043 | 0.9979 |
| 2 (v3) | −0.1692 | 0.0537 | 0.4963 |
| 3 (v4) | −0.1336 | 0.1224 | 0.5181 |
| 4 (v5) | 0.0342 | 0.0248 | 0.5006 |

| Rule | Statistic | Value | Verdict |
|---|---|---|---|
| R08 perf. non-monotonic | monotone / n sign-changes | False / 1 | **support** |
| R09 potential spike @ steps 1 & 3 | step1 / step3 | True / True | **support** |
| R09 learning spike @ steps 1 & 3 | step1 / step3 | True / **False** | **contradict** |
| R10 step 3: perf↓ & retention↑ | perf 0.7396→0.4835; ret 0.4963→0.5181 | True / True | **support** |

**C03: partially supported.** The overall signature is reproduced: performance is non-monotonic
(decrease through step 3, tiny rebound at step 4); potential shows local maxima at steps 1 and 3
and dips at steps 2 and 4 exactly as in the paper's Fig. 7; and at step 3 performance drops
while retention rises (+0.0217). The single deviation is **learning at step 3**, which is strongly
negative (−0.1336) rather than a positive spike — the model catastrophically underperforms the
previous model on the newly introduced Population-C dataset, so the "learning spikes with each new
population" component is only partially confirmed.

---

## 5. Conclusions

1. **C04 (supported)** — The frozen data are internally consistent with Equations 1–3 and λ = 0.5:
   the VIGILANT package recomputes every recorded learning/potential/retention value exactly, and
   λ = 0.5 uniquely matches the recorded retention series.
2. **C01 (contradicted)** — The single-shift reproduction does **not** reproduce the paper's
   stability / learning-tracking / step-1-potential-peak pattern. Likely because the synthetic
   Population-B transition produced a larger effective domain shift (and a single seed) than the
   paper's gradual real-data transition.
3. **C02 (partially supported)** — Limited-plasticity reproduces the "gradual performance
   decrease" and "learning never reaches potential" findings, but not "stable retention"
   (retention falls monotonically 1.00 → 0.75).
4. **C03 (partially supported)** — Double-shift reproduces non-monotonic performance, the
   potential double-spike, and the step-3 performance↓/retention↑ trade-off, but learning does
   not spike at step 3.

**Overall**: the *metric computation* claim is fully supported; the three *phenomenological*
claims are reproduced only partially (C02, C03) or not at all (C01) in the frozen 1-repetition
synthetic data. These verdicts apply to the frozen reproduction dataset, not to the paper's own
25-repetition real-data figures.

---

## 6. Limitations (honesty bounds)

- **n = 1 repetition**: the paper reports mean ± 95% CI over 25 repetitions; the frozen data
  contain a single run (seed 1042), so no confidence intervals exist and all trend inferences
  are based on one realization. `aggregated.csv` confirms `*_ci = 0.0` with `n_repetitions = 1`.
- **Synthetic data**: the reproduction used synthetic chest-X-ray populations defined by imaging
  characteristics, not the paper's MIDRC Open-A1/R1 real images; domain-shift magnitudes differ.
- **Verdict scope**: conclusions evaluate the claims against the frozen reproduction data only;
  deviations may reflect reproduction scope rather than invalidity of the paper's framework.
- **Monotonicity/trend tests** on 4–5 points have low statistical power; reported slopes and
  correlations are descriptive statistics, not significance-tested claims.

---

## 7. Reproducing this analysis

```bash
# from D:/project/paper-bench/tasks_legacy/2604.04878v1/agent_solution
python code/verify_lpr_metrics.py    # C04 verification -> results/*.csv
python code/analyze_claims.py        # C01-C03 trend analysis -> evidence_table.csv, metrics.json
python code/plot_lpr_results.py      # figure -> results/lpr_summary_figure.png
```

Requires: python ≥3.10, numpy, pandas, scipy; `vigilant` package loaded from
`F:/dataset/2604.04878v1/VIGILANT/src` (added to `sys.path` by the scripts).

### Files produced

| File | Description |
|---|---|
| `solution.md` | This report |
| `code/verify_lpr_metrics.py` | C04 verification (recompute + λ sensitivity + toy examples) |
| `code/analyze_claims.py` | C01–C03 trend analysis; emits evidence table & metrics |
| `code/plot_lpr_results.py` | 3-panel summary figure |
| `results/evidence_table.csv` | Metric / value / criterion / verdict per rule (27 rows) |
| `results/metrics.json` | Machine-readable key metrics (keys match evidence table) |
| `results/lpr_verification.csv` | Recomputed-vs-recorded LPR values per experiment/version |
| `results/retention_lambda_sensitivity.csv` | Retention error per λ for all experiments |
| `results/toy_example_validation.csv` | VIGILANT toy-example value checks |
| `results/claims_analysis.csv` | Full per-step metric series (all experiments) |
| `results/lpr_summary_figure.png` | Performance / learning / potential / retention vs step |
