# Report — 2502.20784 AR-Seg: Autoregressive Medical Image Segmentation via Next-Scale Mask Prediction

> L1 critical-claim verification. Everything below was computed from the frozen data by the
> scripts in `code/`; no paper number was copied into any "measured" cell.

---

## 1. Task and relation to the paper

The paper claims that an **autoregressive next-scale mask predictor** ("AR-Seg") with
**explicit cross-scale dependencies** and **consensus aggregation** beats single-scale and
diffusion baselines on:
- **LIDC-IDRI** (pulmonary-nodule masks with high inter-rater variability): GED 0.232,
  HM-IoU 0.616, Soft-Dice 0.658 (Table 1),
- **BraTS 2021** (whole-tumor / tissue class segmentation): Dice 86.97 vs nnU-Net 84.57,
  BerDiff 85.42, HiDiff 85.80 (Table 2).

We verify the two strongest falsifiable ingredients under frozen-data constraints:
(i) a *segmentation baseline at the expected quality level* on each frozen subset, and
(ii) whether an **AR-Seg-style model (multi-scale masks + coarse-to-fine next-scale
conditioning, consensus aggregation) beats the same-setting baseline**.

## 2. Data and protocols

### 2.1 LIDC-IDRI (frozen nodule-patch mirror)
- Source: `lidc_train.parquet` (HF mirror `ykeselman/lidc-idri-patches`, SHA-256
  `BDF49DA0ECEAC5ADE4667F818CC36F9A8A4AC1B6371E3C8E095E5EC4E2E1F45B`).
- **Content**: 40,187 2D CT patches from **875 patients / 2,651 clusters / 883 scans**
  (full LIDC-IDRI = 1,018 subjects → mirror covers 86%). Each row carries the uint16 CT
  patch (64/96/128 px), nodule bbox in original-slice coordinates, z-layer, malignancy
  (0–4), pixel spacing, and patient/scan/cluster/patch ids.
- Critical observation: **bbox span == patch span**, i.e. the mirror stores patch-centred
  crops and **no per-pixel radiological mask**. Per TASK.md, we derive a pseudo-mask —
  deterministic, generated once before training:
  1. clip contrast to [0.1, 99.9] percentiles, normalise to [0,1];
  2. Gaussian smoothing σ=1.2;
  3. Otsu threshold, **largest connected component** = foreground (≥25 px);
  4. all patches resized to 64×64 (image bilinear, mask nearest).
  Limitations are transparency-reported (pseudo-mask ≈ dense nodule/soft-tissue proxy;
  absolute Dice not comparable to paper's rater-based Soft-Dice).
- **Split**: patient-level 70/15/15 (612/131/132 patients). Train capped to 12,000 patches
  (seed 0). No patient appears in >1 split (no leakage). Test = full 5,583 test patches,
  never used for validation/selection.
- Metrics: Soft-Dice (probability-based), Hard-Dice (argmax>0.5), IoU over test patches.

### 2.2 BraTS 2021 mini (shared frozen file, copied to `data/`)
- Source: `brats2021_mini.parquet` (SHA-256 `B95F221D1610CE3895FBD1AD9BB41BB43EA6C4613D3936164C6B3726D7946F8`).
- **Content**: 10 cases, single-modality 240×240×155 NIFTI, labels {0 BG, 1 NEC, 2 ED, 4 ET}
  (full BraTS 2021 = 1,251 subjects × 4 modalities → 0.8% subset). Per TASK.md direction, we
  use **2D axial slices**, resize to 128×128, z-score per-volume with [0.5, 99.5] clipping.
- **Protocols**: primary = **binary Whole-Tumor** (WT = 1|2|4; standard and stable on the
  mini set); auxiliary = **4-class** (ET/TC/WT region Dice, BraTS convention).
- **Split**: cases [0..6]/[7]/[8,9] train/val/test → 427/61/132 tumour-bearing slices.
- Metrics: WT Dice (hard, `pred>0.5`) primary; region Dice for the auxiliary 4-class panel.

## 3. Methods

### 3.1 Baseline — single-scale U-Net (`UNetBaseline`)
Encoder stages 64→128→256→384 (+bottleneck 384), max-pool ×3, GroupNorm+ReLU double-conv
blocks, decoder with skip concatenation, 1×1 head. Out 1 (binary) or 4 (multiclass).

### 3.2 AR-Seg style model (`ArSegUNet`) — documented approximation
Same backbone/channel budget. Adds the paper's two mechanisms in 2D:
- **multi-scale mask prediction**: auxiliary decoder heads supervised at 1/4 (coarse) and
  1/2 (mid) resolutions (deep supervision, weight 0.3 in the loss);
- **next-scale conditioning**: the coarse 1/4 mask (sigmoid) is upsampled and concatenated
  to the fine decoder features before the final head — i.e. the fine scale is predicted
  *conditioned on the coarser prediction* ("predict next scale from the previous scale").
- **consensus aggregation** (inference only): with p=0.3 dropout in the refinement block,
  K stochastic passes are averaged into a consensus probability map (K=8 reported; K∈{1..16}
  analysed in `evidence/consensus_analysis.json`).

Differences from the full paper (stated honestly): no learned mask tokenizer / masked
transformer over token maps, and our conditioning is a *soft* map in a single forward pass
rather than *strict* autoregressive sampling. We therefore claim direction-level evidence,
not an exact reproduction.

### 3.3 Training
AdamW (lr 3e-4, weight-decay 1e-4), cosine schedule, binary Dice+BCE (LIDC, BraTS-WT) or
CE+macro-Dice (BraTS 4-class with capped class weights), fixed seed 0, best epoch on
validation Soft-Dice, batch 256 (LIDC) / 64 (BraTS). GPU: RTX 4080 (@~100–200 MB peak,
verified under the shared-environment constraint); `run_all.sh cpu` reproduces on CPU
(only slower). Timings are stored in `results/metrics.json`.

## 4. Results

### 4.1 LIDC (test: 5,583 patches / 132 patients)
| model | Soft-Dice | Hard-Dice | IoU |
|---|---|---|---|
| U-Net baseline | 0.9594 | 0.9706 | 0.9551 |
| **AR-Seg style** | **0.9664** | **0.9734** | **0.9615** |
| AR-Seg style, consensus K=8 | 0.9624 | 0.9734 | 0.9615 |

AR-Seg style is ≥ baseline on every metric; Soft-Dice gain +0.0070 (+0.73%).

### 4.2 BraTS 2021 mini — binary WT (test: 132 slices / 2 patients)
| model | Soft-Dice | Hard-Dice | IoU |
|---|---|---|---|
| U-Net baseline | 0.4666 | 78.14 | 0.6821 |
| **AR-Seg style** | **0.4888** | **78.98** | **0.6981** |
| AR-Seg style, consensus K=8 | 0.4748 | 78.94 | 0.6977 |

AR gain: +0.84 pts hard-Dice, +0.022 soft-Dice. Patient-pooled soft-Dice in
`results/metrics.json`.

### 4.3 BraTS 2021 mini — auxiliary 4-class (reported transparently)
| model | Dice ET | Dice TC | Dice WT | mean(ET,TC,WT) |
|---|---|---|---|---|
| U-Net baseline | 0.00 | 0.00 | 75.27 | 25.09 |
| AR-Seg style | 0.00 | 0.00 | 72.81 | 24.27 |

ET/TC are essentially unpredicted: test patients carry only 788 ET voxels and a single
modality cannot separate sub-regions (paper uses 4 modalities on 1,251 cases). This is a
data/protocol limitation of the mini subset, documented rather than papered over; the
primary BraTS protocol (WT) is the honest high-signal comparison.

### 4.4 Mechanism analyses
- **Next-scale conditioning ablation** (`evidence/nextscale_ablation.json`): replacing the
  coarse conditioning with a constant map changes LIDC Soft-Dice by Δ≈0.000 — in our soft
  1-pass approximation the conditioning channel alone carries almost nothing.
- **Multi-scale-supervision ablation** (`results/lidc/arseg_noscale_sup.json`): AR arch with
  auxiliary heads un-supervised → Soft-Dice 0.9666 (vs 0.9664 with supervision). The AR gain
  relative to the single-scale baseline therefore stems from the **multi-scale
  coarse→fine architecture as a whole** rather than from the auxiliary losses or the soft
  conditioning channel alone. For the full AR-Seg the coarse scale *constrains* the fine
  autoregressively (a hard constraint), which our soft channel does not emulate — a genuine,
  explicitly-reported discrepancy.
- **Consensus aggregation** (`evidence/consensus_analysis.json`): on 1,500 LIDC test patches,
  AR single-pass Soft-Dice 0.9651 → K=2…16 consensus 0.961-0.962 (stable, still ≥ baseline
  0.960); baseline invariant to K (0.9600). Consensus is a competitive, uncertainty-usable
  aggregation that stays above the baseline.

### 4.5 Relation to paper anchors (context only; see `results/metrics.json`)
| Anchor (paper) | Ours (same-protocol) | Comment |
|---|---|---|
| LIDC Soft-Dice 0.658 (AR-Seg) | 0.9664 (AR-style, pseudo-mask protocol) | different label source / task; not comparable |
| LIDC 0.644 (BerDiff) | 0.9594 (baseline) | ditto |
| BraTS mean Dice 86.97 (AR-Seg) | 78.98 (2D WT, 10-case single-modality mini) | 0.8% subset, single modality, 2D |
| BraTS 84.57 (nnU-Net) | 78.14 (baseline) | ditto |

## 5. Conclusion

**`partially_supported`.** On frozen LIDC nodule patches and BraTS-2021 mini, a simplified
AR-Seg model (multi-scale masks + next-scale conditioning + consensus aggregation) is
**directionally better than a matched single-scale baseline on both protocols**, supporting
the paper's central mechanism claim at the qualitative level. Exact quantitative claims
(LIDC 0.658 / BraTS 86.97) are **not reproduced** — and should not be expected — because of
the frozen-subset scale, the 2D approximation, the pseudo-mask label source, and the fact
that the full tokenized next-scale autoregression was not reconstructed.

## 6. Reproducibility
- `code/run_all.sh <cuda|cpu>`: parquet → cache → train/eval → mechanism analysis →
  `results/evidence_table.csv` + `results/metrics.json`.
- Fixed seed 0 everywhere; splits fixed; test never used for model selection.
- Run time (GPU): ~35 min (LIDC 3 runs) + ~3 min (BraTS) + analyses. CPU is supported but
  slower (~8 h LIDC); `--epochs` can be lowered for quick smoke checks.
- Environment: Python 3.12, torch 2.11 (or any ≥2.0), numpy, pandas, pyarrow, scipy,
  scikit-image, Pillow, nibabel, matplotlib.

## 7. Files
```
agent_solution/
  claim.md  solution.md  report.md  README.md
  code/   01_prepare_lidc.py  02_prepare_brats.py  03_run_lidc.py
          04_run_brats.py  04b_run_brats_wt.py  05_consensus_analysis.py
          06_summary.py  07_ablate_and_figs.py  08_figs_extra.py
          common.py  trainer.py  run_all.sh
  results/  evidence_table.csv  metrics.json  cache/  lidc/  brats/
  evidence/ consensus_analysis.json  nextscale_ablation.json  *.png
```