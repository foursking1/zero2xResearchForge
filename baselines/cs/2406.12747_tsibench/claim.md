# Claim Verdict — TSI-Bench ETT_h1 simple-baseline claims (task 2406.12747_tsibench)

## Verified claims

- **C1 (simple-imputer ordering)** — On ETT_h1 test windows with 10% single-point
  missingness, simple baselines rank `Linear < LOCF < Median ≈ Mean`, with Linear
  MAE ≈ 0.2 (standardized units), LOCF ≈ 0.3, Median/Mean ≈ 0.8.
- **C2 (linear-imputation competitiveness)** — Linear interpolation is not
  dominated by deep learning methods: its MAE is of the same order of magnitude
  as reported deep models, better than several (iTransformer, DLinear, TimesNet,
  SCINet, GP-VAE, Koopa, US-GAN, FiLM, MRNN) and worse than only the best
  attention/self-attention models (SAITS, CSDI, Informer, Transformer,
  Pyraformer).

## Falsification conditions

- C1 fails if, on **any** test mask seed, measured MAE violates the strict order
  `Linear < LOCF < Median` or `Linear < Mean`.
- C2 fails if measured Linear MAE is outside the range of reported deep-method
  MAE on the same setting (i.e., clearly worse than essentially all deep
  baselines), or if Linear were competitive only by a margin dwarfed against all
  deep methods.
- C1 numeric support additionally fails if measured Linear MAE is not ≈ paper's
  0.197 (e.g. outside [0.10, 0.40] — magnitude anomaly).

## Protocol summary (reproduced, seed-level values from code)

| | mean MAE ± std (3 seeds) | paper Table 2 | rel. diff |
|---|---|---|---|
| **Linear** | **0.2037 ± 0.0033** | 0.197 | +3.4% |
| LOCF | 0.2961 ± 0.0055 | 0.315 | −6.0% |
| Median | 0.8396 ± 0.0181 | 0.71 | +18.3% |
| Mean | 0.8528 ± 0.0166 | 0.737 | +15.7% |

Per-seed test MAE (standardized units): seed 42 → Linear 0.2033, LOCF 0.3024,
Median 0.8588, Mean 0.8713; seed 43 → 0.2007, 0.2920, 0.8373, 0.8478; seed 44 →
0.2072, 0.2939, 0.8228, 0.8392.

## Cross-seed robustness

- Strict ordering `Linear < LOCF < Median` **and** `Linear < Mean` holds on
  **every seed** (42, 43, 44) and for the multi-seed means. Forcing the reverse
  ordering would require a change of >0.09 MAE (Linear→LOCF gap) / >0.52
  (LOCF→Median), ~15–90× the per-seed spread of Linear (std 0.0033), so the
  ordering is overwhelmingly stable.
- Absolute magnitudes: Linear/LOCF reproduce the paper within 3.4%/−6.0%;
  Median/Mean are 16–18% above the paper but stay in the same "≈0.8–0.9" band on
  all seeds (relative spread ≤2.2%), consistent with the known definitional
  difference (train-statistic fill vs. observed-value fill).

## Four-level conclusion

**`supported`**

- C1: the ordering claim is reproduced and is seed-robust; magnitudes agree
  within expected protocol/definition noise.
- C2: measured Linear (0.2037) is at the same order of magnitude as the reported
  deep methods (best SAITS 0.144, worst MRNN 0.789) and strictly better than 9
  of the 15 quoted deep baselines; the paper's own Linear value (0.197) is
  consistent with our measurement.

## Data-support strength

- Strong: all numbers (except the quoted deep-method values used only for C2
  discussion) are recomputed by code from the frozen `ETT-h1.csv` (SHA-256
  `f18de3ad…66` verified at run time); standardization uses train-only Z-scores;
  mask seeds are fixed {42,43,44}; seed=42 bit-for-bit matches the frozen
  reference protocol (test masked points = 2385, Linear = 0.2033249300539183).
- Qualified: deep-method MAEs (SAITS 0.144 …) are citations from paper Table 2,
  **not** measured here — see the C2 caveat in `report.md`.