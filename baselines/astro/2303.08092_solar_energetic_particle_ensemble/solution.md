# Solution — 2303.08092 SEP Random Hivemind

**Verdict: partially_supported** (on the frozen SEPTEBBS data, 10 splits).

## Key numbers
- **Data:** 24,570 clean rows / 74 SEP (frozen 24,797/76; paper 18,311/64 — expanded
  version). 12 features per paper §2.
- **TSS med±MAD (10 splits):** CoNN 0.807±0.055, Committee 0.833±0.067, RH v1
  0.882±0.026, RH v2 0.868±0.032.  HSS med: CoNN 0.051, Committee 0.064, RH v1 0.105,
  RH v2 0.109.
- **Judgments:** RH v2 ≥ CoNN (TSS 0.868 vs 0.807, HSS 0.109 vs 0.051) — HOLDS;
  RH v1/v2 dispersion ≪ CoNN (MAD 0.026/0.032 vs 0.055) — HOLDS; Committee dispersion
  not < CoNN (0.067) — fails; RH v2 ≥ RH v1 in HSS but not TSS (0.868 vs 0.882) — partial.
- **Paper Table 2 TSS med:** CoNN 0.906, Committee 0.926, RH v1 0.915, RH v2 0.944
  (our deltas -0.03 to -0.10, mainly from reduced epochs 150 vs 500 + data version).

## How to reproduce
```
cd code
"C:/Users/Administrator/.workbuddy/binaries/python/versions/3.13.12/python.exe" run_sep.py --n_splits 10 --epochs 150 --seed 20260817
```
Outputs: `results/{metrics,evidence_table,critical_checks,uncertainty}.json`,
`figures/sep_metrics.svg`.

## Deviations from paper
- Base epochs 500 → 150 (compute limit; RH epochs still scaled by 12/n_sel).
- Frozen data are an expanded portal version (24,570/74 vs 18,311/64).
- 10 splits (paper §2 protocol; §4/表注 uses 50).
- Operating threshold: Youden-J on training (paper operating point ~FPR 4%).
