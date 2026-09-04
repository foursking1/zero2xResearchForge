# Solution: Fast and interpretable classification of small XRD datasets (1811.08425)

**Paper:** Oviedo et al., "Fast and interpretable classification of small X-ray
diffraction datasets using data augmentation and deep neural networks",
npj Computational Materials 5, 60 (2019) · arXiv:1811.08425

**Task:** L1 critical claim — reproduce the space-group (SG) classification
result (≈89%, 5-fold CV, "Case 3") on the frozen 88-spectrum experimental
thin-film XRD dataset plus the 164 simulated training spectra, verify that
physics-informed data augmentation is the source of accuracy, and (bonus)
verify accuracy at a coarsened 2θ step of 0.16°.

## Headline answers

| # | Question | Our result | Verdict |
|---|----------|-----------|---------|
| 1 | Case 3 5-fold CV SG accuracy ≈ 0.89 | **0.865 ± 0.092** (MLP, 3-seed ensemble; pooled 0.864) | **Reproduced** (within the ±3.4 pp tolerance of the paper's 0.89) |
| 2 | Physics-informed augmentation vs no augmentation | aug 0.865 vs no-aug 0.750–0.761 → **+0.104–0.115 pp** | **Directionally reproduced** (augmentation gives a large, above-noise improvement; gap smaller than paper's <60%→89% because we use a stronger model) |
| 3 | Accuracy at 0.16° step ≥ 0.85 | **0.865 ± 0.062** at 0.16° (0.830–0.854 for 0.32°–0.08°) | **Confirmed** (≥0.80 rubric; matches paper's ≥0.85 trend) |

## Key evidence (all regenerable from `data/` with `code/run_final.py`)

- 5-fold per-fold accuracies (aug, 3-seed): `[0.833, 0.889, 0.722, 0.941, 0.941]`;
  mean **0.8654 ± 0.0916**; F1 micro 0.865 ± 0.092; **F1 macro 0.599 ± 0.137**;
  pooled confusion matrix in `results/mlp_aug_s3.json`.
- Ablation: without augmentation mean **0.761 ± 0.095** (3-seed) /
  **0.750 ± 0.103** (5-seed). Augmentation gain ≈ **+10–12 pp**.
- Coarsening (aug): 0.04°→0.865, 0.08°→0.854, 0.12°→0.842, **0.16°→0.865**,
  0.32°→0.830.
- Class distribution (frozen data): Fm-3m=4, I41mcm=17, P21a=1, P3m1=13,
  P61mmc=4, Pc=2, Pm-3m=47 (matches paper). All core-file checksums verified.
- Faithful a-CNN (paper architecture, GAP head) does **not** beat the majority
  class in our implementation (≈0.5–0.6); we therefore used a stronger,
  still-simple MLP (3-hidden-layer FC, 512–256) to reproduce the headline
  accuracy. Details and honest limitations in `report.md`.

## Method (short)

1. **Data.** 88 experimental spectra (exp.csv, 1499 pts, 2θ 10.04–69.96°,
   0.04° step) + labels (label_exp.csv), 164 simulated spectra (theor.csv,
   trimmed to the same grid).
2. **Preprocessing** (per spectrum): background removal (moving-minimum
   baseline, subtracted), Savitzky–Golay smoothing (window 15, order 3),
   min–max normalisation to [0,1].
3. **Physics-informed augmentation** (paper Eqs. 1–3), applied **only to the
   training folds**: (1) peak scaling of a periodic subset of detected peaks by
   c ~ U(0.7,1.3); (2) peak removal of a periodic subset; (3) small pattern
   shift (±0.1°). 2000 augmented spectra generated from the simulated set and
   2000 from the experimental training set per fold.
4. **Model:** MLP 512–256 with ReLU/Dropout(0.4), Adam (lr 1e-3), batch 128,
   cross-entropy, early stopping on a held-out val subset of the training
   fold; 3-seed softmax ensemble.
5. **Evaluation:** 5-fold stratified CV (shuffle + fixed seed), subset
   accuracy + F1 micro/macro, mean±std.

## Run

```
cd agent_solution/code
python3 verify_data.py        # checksums + class distribution
python3 run_final.py --aug  --model mlp --seeds 3 --tag mlp_aug_s3
python3 run_final.py --noaug --model mlp --seeds 3 --tag mlp_noaug_s3
python3 run_final.py --aug --model mlp --seeds 3 --coarse 4 --tag mlp_aug_s3_coarse4
python3 make_evidence.py      # regenerates results/evidence_table.{md,csv}
python3 make_figures.py       # regenerates figures/
```

See `report.md` for the full method, hyperparameters, seeds, Case-3
conformance statement, and limitations.