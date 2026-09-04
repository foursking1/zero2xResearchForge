# HybridSN re-discovery (task 1902.06701_hybridsn) — reproduction package

Re-implementation and evaluation of the **HybridSN** 3D-2D hybrid CNN
(Roy et al., "HybridSN: Exploring 3-D-2-D CNN Feature Hierarchy for
Hyperspectral Image Classification", IEEE GRSL 2020, arXiv:1902.06701)
on the frozen Indian Pines dataset, following the paper protocol
(30% random training / 70% testing).

## Directory layout

```
agent_solution/
├── protocols/            data splits (fixed-seed, paper 30/70 protocol)
│   └── split_data.py
├── method/
│   ├── config.py
│   ├── data_utils.py     .mat loading, PCA(30), train-only normalization, 25x25 patches
│   ├── models.py         HybridSN (3D-2D CNN) and CNN2D baseline
│   ├── train_utils.py    Adam training loop (cosine schedule, history logging)
│   ├── train_hybridsn.py HybridSN 3x seed training + eval
│   ├── train_2dcnn.py    2D-CNN baseline 3x seed training + eval
│   ├── baseline_svm.py   SVM/RBF pixel-wise baseline (grid-searched)
│   ├── train_ratio_sweep.py  Q3: 10% / 30% / 70% ratio sensitivity
│   ├── finalize.py       evidence_table.csv, metrics.json, figures
│   └── metrics.py        OA / AA / Kappa / per-class accuracy
├── results/              all numeric outputs (splits, checkpoints, metrics, evidence)
├── evidence/             figures (classification maps, training curves, split counts)
├── report.md             full scientific report
└── solution.md           concise solution summary
```

## Requirements

```
python>=3.10, numpy, scipy, scikit-learn, torch>=2.0, matplotlib
```

## Reproduction (end-to-end)

From the task working directory root (`data/` holds the frozen .mat files):

```bash
cd agent_solution

# 1) Paper protocol: fixed-seed random 30%/70% split of labeled pixels
python protocols/split_data.py --seeds 0,1,2 --ratio 0.3
python protocols/split_data.py --seeds 0,1,2 --ratio 0.1   # for Q3
python protocols/split_data.py --seeds 0,1,2 --ratio 0.7   # for Q3

# 2) Train and evaluate HybridSN (3 seeds x 100 epochs; default device cpu)
DEVICE=cuda python method/train_hybridsn.py --seeds 0,1,2 --epochs 100 --device cuda

# 3) Baselines
DEVICE=cpu  python method/baseline_svm.py   --seeds 0,1,2        # SVM/ RBF pixel-wise
DEVICE=cuda python method/train_2dcnn.py    --seeds 0,1,2 --epochs 100 --device cuda

# 4) Q3: ratio sensitivity (10/30/70%, seed 0)
DEVICE=cuda python method/train_ratio_sweep.py --ratios 10,30,70 --epochs 60 --device cuda

# 5) Finalize deliverables (evidence_table.csv, metrics.json, figures)
DEVICE=cuda python method/finalize.py --device cuda
```

## Data integrity

- Only the frozen files under `data/` are used:
  `Indian_pines_corrected.mat` (145x145x200), `Indian_pines_gt.mat` (145x145, 0=bg).
  SHA-256 recorded in `data/source_manifest.json`.
- **Anti-leakage**: the PCA transformation and per-band normalization statistics are
  fitted **only on the training pixels** of the active protocol; the test partition is
  held out until final evaluation.
- Background pixels (label 0) never enter training or evaluation; 16 classes.

## Key results (main run)

| model | OA (3-seed mean ± std) | AA | Kappa |
|---|---|---|---|
| **HybridSN (3D-2D CNN)** | 99.85 ± 0.04 | 99.74 ± 0.09 | 99.83 ± 0.05 |
| 2D-CNN (baseline) | 99.67 ± 0.02 | 99.20 ± 0.22 | 99.62 ± 0.02 |
| SVM RBF (baseline) | 79.67 ± 0.14 | 76.28 ± 1.18 | 76.73 ± 0.17 |

Exact numbers: see `results/metrics.json`, `results/evidence_table.csv`,
`results/hybridsn_aggregate.json`, `results/cnn2d_aggregate.json`,
`results/svm_aggregate.json`.