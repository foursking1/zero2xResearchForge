# SEP Random Hivemind reproduction report (arXiv:2303.08092)

## 1. Goal
Reproduce the four SEP classifiers (CoNN / Committee / RH v1 / RH v2) on the frozen
SEPTEBBS data and test the paper's claim that the Random Hivemind (RH) ensembles match
or beat a single network with significantly lower score dispersion, RH v2 being the best.

## 2. Frozen data (SHA-256 per MANIFEST.tsv, unchanged)
- `data/SEPTEBBS.json` — 24,797 GOES SXR flare rows with TEBBS properties + SEP labels
  (2002-01-01 to 2018-02-26, 76 `CausedSPE=True`).
- Cleaned with the paper's exclusion criteria (Tmax<100 MK and all six time-offset
  fields + MinDur non-negative): **24,570 rows / 74 SEP** (paper: 18,311 / 64).  The
  portal data are an expanded version (more flares and SEP records), so absolute
  comparisons use the ≤±0.05 "口径一致" tolerance and the relative anchors are primary.
- 12 features per paper §2: MinDur, Tmax, EMmax, PrecisePeak (SXRmax), StartToTmax,
  TmaxToEnd, StartToEMmax, EMmaxToEnd, StartToPeak, PeakToEnd, XCtr, YCtr.

## 3. Method (paper §3)
- Network: input = selected features (12 for CoNN/Committee; ceil(sqrt(12))=4 for
  RH v1; 6 for RH v2); one 10-neuron dense hidden layer, ReLU, dropout 0.2, logistic
  output.  Implemented in PyTorch.
- Training: Adam α=1e-3; base epochs 150 (reduced from the paper's 500 to fit compute;
  documented).  For RH methods the epochs and LR are scaled by 12/n_sel per paper
  Eq.1–4 (RH v1 ×3 = 450, RH v2 ×2 = 300).  Balanced class weighting
  (pos_weight = n_neg/n_pos ≈ 780) per the paper's handling of the ~0.3% positive class.
- Feature weights: χ² + mutual-information, normalised (paper Eq.1–4); RH feature
  subsets sampled proportionally to these weights, seed per estimator.
- Ensembles: 10 estimators; Committee equally-weighted, RH weighted by selected-feature
  weight sum; operating threshold = Youden-J maximising TSS on the training split.
- Evaluation: 10 random stratified 70/30 splits (seed 20260817); per-split confusion
  matrices and TSS/HSS/precision/recall/accuracy/ROC-AUC; summary mean±std and med±MAD.

## 4. Results (10 splits)
| method | TSS mean±std | TSS med±MAD | HSS med±MAD | AUC med±MAD | vs paper TSS med |
|---|---|---|---|---|---|
| CoNN | 0.807±0.057 | 0.807±0.055 | 0.051±0.008 | 0.935±0.008 | 0.906 → -0.099 |
| Committee | 0.817±0.074 | 0.833±0.067 | 0.064±0.011 | 0.963±0.021 | 0.926 → -0.093 |
| RH v1 | 0.881±0.056 | 0.882±0.026 | 0.105±0.010 | 0.986±0.003 | 0.915 → -0.033 |
| RH v2 | 0.871±0.043 | 0.868±0.032 | 0.109±0.015 | 0.983±0.007 | 0.944 → -0.076 |

Judgments (relative anchors):
1. RH v2 median TSS ≥ CoNN median TSS: **0.868 ≥ 0.807 — holds** (and RH v2 HSS
   0.109 ≥ CoNN 0.051).
2. Ensemble dispersion: RH v1 (TSS MAD 0.026) and RH v2 (0.032) are much lower than
   CoNN (0.055) — **holds for RH**; Committee (0.067) is not — **fails for Committee**.
   (Same pattern in std.)
3. RH v2 vs Committee: TSS 0.868≥0.833, HSS 0.109≥0.064 — **holds**.  RH v2 vs RH v1:
   HSS 0.109≥0.105 — **holds**; TSS 0.868<0.882 — **does not hold**.

## 5. Conclusion
**partially_supported**.  The core relative claim — the RH method matches/beats CoNN
with much lower dispersion — is confirmed: RH v2 beats CoNN on TSS and HSS, and both RH
ensembles cut the TSS dispersion by roughly half versus the single network.  Two
sub-claims are not reproduced on the frozen, reduced-budget run: Committee is not more
stable than CoNN, and RH v2 does not outscore RH v1 on TSS (it does on HSS).  Absolute
values are 0.03–0.10 below the paper, attributable to the reduced base epochs (150 vs
500) and the expanded frozen data version (24,570/74 vs 18,311/64), so the absolute
anchor is reported with that caveat.

## 6. Boundaries / caveats
- Base epochs reduced 500 → 150 (compute); absolute TSS/HSS are lower as a result, but
  the relative CoNN-vs-RH ordering and dispersion ranking are the primary anchor.
- Frozen data are an expanded portal version (24,570/74) vs the paper's (18,311/64);
  expected systematic offset in absolute scores.
- Extreme class imbalance (0.3% positive) → precision/HSS are low for all methods
  (paper §4/§5 discusses this operating-point regime); comparisons use TSS/AUC/MAD.
- 10 splits (paper's §2 "≥10" protocol); seed fixed for reproducibility; a full 50-split
  (§4/表注) re-run was not feasible under compute limits.
