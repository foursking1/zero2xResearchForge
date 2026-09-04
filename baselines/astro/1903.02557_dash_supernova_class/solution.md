# Solution — 1903.02557 DASH supernova classification

**Verdict: supported** (on the frozen 69-spectrum subset).

## Key numbers
- **Match rate (paper convention):** 56/64 = **0.875** overall
  (Ia 49/54 = 0.907, II 6/8 = 0.75, Ibc 1/2 = 0.50); 5 top-1 `Ic-broad`
  predictions excluded per paper Sec.5.2.  Paper: 197/212 = 0.929.
- **Speed:** full 69-spectrum autonomous batch **3.59 s** wall
  (model setup 1.55 s + forward pass 2.03 s).  Paper: <20 s / 212.
- **Data:** 69 frozen OzDES spectra (runs 24–28), 67 unique objects, matched to
  `all_atels.txt`; ATel labels Ia 47 / Ia? 9 / II 9 / II? 2 / Ibc 1 / Ibc? 1.
- **Model:** official DASH v06 (`zeroZ`), `knownZ=True`, `smooth=6`,
  tensorflow-cpu 2.21 in TF1-compat graph mode, astrodash 1.0.22.

## How to reproduce
```
cd code
"C:/Users/Administrator/.workbuddy/binaries/python/envs/default/Scripts/python.exe" dash_data.py   # frozen data facts
"C:/Users/Administrator/.workbuddy/binaries/python/envs/default/Scripts/python.exe" dash_run.py    # DASH classification
```
Outputs: `results/{metrics,evidence_table,critical_checks,uncertainty}.json`,
`results/dash_predictions.csv`, `figures/dash_match.svg`.

## Deviations from paper
- Frozen subset 69 vs paper 212 spectra (subset difference, must be stated).
- Official v06 model vs 2019 paper model (some subtype/broad-class drift).
- numpy 2.x runtime shims needed for astrodash 1.0.22 (compatibility only).
