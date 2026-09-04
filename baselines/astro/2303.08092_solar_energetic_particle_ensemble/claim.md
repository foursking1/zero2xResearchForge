# Claim verification: Random Hivemind SEP prediction (arXiv:2303.08092)

## Falsifiable scientific claim (one sentence)

The Random Hivemind (RH) ensemble deep-learner predicts solar energetic particle
(SEP) events with TSS comparable-or-better than a conventional neural network
(CoNN) and a same-feature committee (Committee) while having **significantly lower
score dispersion** across random 70/30 splits (paper Table 2 med±MAD: CoNN TSS
0.906±0.042 → Committee 0.926±0.023, RH v1 0.915±0.010, RH v2 0.944±0.005), with
RH v2 on average the best.

## Failure conditions

1. RH v2 median TSS < CoNN median TSS (relative anchor).
2. Ensemble (Committee/RH) TSS dispersion is not lower than CoNN.
3. RH v2 is not ≥ Committee and RH v1 in TSS/HSS.

## Result

Frozen SEPTEBBS data, cleaned per the paper's exclusion criteria: **24,570 rows /
74 SEP** (paper: 18,311 / 64 — expanded data version, reported). 10 random
stratified 70/30 splits, base epochs 150 (paper: 500; RH epochs scaled by 12/n_sel).

| method | TSS med±MAD (ours) | HSS med±MAD (ours) | TSS med (paper) | ΔTSS vs paper |
|---|---|---|---|---|
| CoNN | 0.807±0.055 | 0.051±0.008 | 0.906±0.042 | -0.099 |
| Committee | 0.833±0.067 | 0.064±0.011 | 0.926±0.023 | -0.093 |
| RH v1 | 0.882±0.026 | 0.105±0.010 | 0.915±0.010 | -0.033 |
| RH v2 | 0.868±0.032 | 0.109±0.015 | 0.944±0.005 | -0.076 |

Judgments:
1. **RH v2 median TSS ≥ CoNN**: 0.868 ≥ 0.807 — **HOLDS** (also HSS 0.109 ≥ 0.051).
2. **Ensemble dispersion < CoNN**: RH v1 (MAD 0.026) and RH v2 (0.032) ≪ CoNN
   (0.055) — **HOLDS** for the RH methods; Committee (0.067) does **not** (partially fails).
3. **RH v2 ≥ Committee & RH v1**: RH v2 ≥ Committee in TSS (0.868 vs 0.833) and HSS
   (0.109 vs 0.064) — **HOLDS**; but RH v2 < RH v1 in TSS median (0.868 vs 0.882),
   ≥ RH v1 in HSS (0.109 vs 0.105) — **partially fails**.

## Conclusion label

**partially_supported** — the key relative anchors hold: RH v2 beats CoNN on TSS and
HSS, and the RH feature-subsampling ensembles are markedly more stable across random
splits than the single CoNN (TSS MAD 0.026–0.032 vs 0.055).  Not fully reproduced:
Committee dispersion is *not* lower than CoNN, and RH v2 does not beat RH v1 in TSS.
Absolute values are 0.03–0.10 below the paper, consistent with the reduced training
budget (150 vs 500 base epochs) and the expanded frozen data version (24,570/74 vs
18,311/64).
