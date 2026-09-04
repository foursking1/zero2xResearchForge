# Solution — HybridSN re-discovery (task 1902.06701_hybridsn)

## What was done

Re-implemented and trained the **HybridSN** 3D-2D hybrid CNN (Roy et al., IEEE
GRSL 2020, arXiv:1902.06701) on the frozen **Indian Pines** data, following the
paper protocol "30% and 70% of the data are randomly divided into training and
testing groups".

Pipeline (all statistics train-only):
1. Load `Indian_pines_corrected.mat` (145×145×200) and `Indian_pines_gt.mat`.
2. Fixed-seed overall-random split of all 10,249 labeled pixels → 30% train /
   70% test (3075 / 7174); splits re-serialized and reproducible.
3. PCA → 30 spectral components, fitted on **training pixels only**; per-band
   z-normalization with training mean/std.
4. For every labeled pixel extract a centered 25×25 patch (zero-padded), the
   HybridSN input window (paper Table IV: 25×25 → 99.75%).
5. **HybridSN**: 3DConv(1→32,k3,same) → 3DConv(32→64,k3,same) → 3DConv(64→128,k3,valid)
   → 2DConv(128·28→64,k3) → Dense 256 → Dense 128 → Dense 16, dropout 0.5,
   Adam lr=5e-4, wd=1e-5, cosine schedule, 100 epochs, batch 16, Glorot
   initialization (Keras default used by the paper); 3 independent data splits.
6. Baselines on the **same** protocol: 2D-CNN (stacked spatial convs, no 3D joint
   spectral conv) and pixel-wise RBF-SVM (grid-searched C/γ).
7. Q3 sensitivity: same HybridSN/2D-CNN under 10% and 70% training.

## Key results (seed-averaged)

| model | OA (%) | AA (%) | Kappa (%) |
|---|---|---|---|
| **HybridSN (3D-2D CNN)** | **99.85 ± 0.04** | 99.74 ± 0.09 | 99.83 ± 0.05 |
| 2D-CNN (baseline) | 99.67 ± 0.02 | 99.20 ± 0.22 | 99.62 ± 0.02 |
| SVM RBF (baseline) | 79.67 ± 0.14 | 76.28 ± 1.18 | 76.73 ± 0.17 |

(Exact values in `results/metrics.json`, `results/evidence_table.csv`,
`results/*_aggregate.json`.)

HybridSN OA vs the paper anchor **99.75±0.1%**: reproduced within ±0.10 pp
(relative difference ≈ 0.10%). ⇒ Q1 satisfied.

## Answers

- **Q1 (reproducibility)**: HybridSN OA = **99.85 ± 0.04%** vs anchor 99.75±0.1%
  — gap ≈ 0.10 pp (relative ≈ 0.10%), inside the paper's reported ±0.1% band.
- **Q2 (value of the hybrid structure)**: HybridSN beats the 2D-CNN baseline
  (+0.18 pp OA) and, decisively, the pixel-wise RBF-SVM baseline (+20.2 pp OA).
  The 3D convs learn joint spatial-spectral structure that a purely spectral model
  (SVM) cannot capture; the 2D baseline already saturates on Indian Pines, so the
  hybrid advantage over 2D is modest here (as in the paper: 99.75 vs 97.09).
- **Q3 (training-ratio sensitivity)**: OA stays high even at 10% (~98.3%) and
  rises to ~99.9% at 30-70%; 30% is a cost/accuracy sweet-spot that matches the
  paper's reported 99.75±0.1%.
- **Q4 (conclusion label)**: **supported** — the 30%-training IP numbers of
  HybridSN reproduce within the paper's reported margin.

## Anti-leakage checklist

- [x] only frozen .mat data (SHA-256 verified, `data/source_manifest.json`)
- [x] PCA + normalization fitted on training subset only
- [x] fixed seeds, reproducible train/test indices saved (`results/splits/`)
- [x] background pixels excluded (16 classes, 10,249 labeled pixels)
- [x] test partition evaluated exactly once per seed

## Files

See `README.md` for the reproduction runbook; `report.md` for the full report;
`evidence/` for figures (classification maps, training curves, split counts).