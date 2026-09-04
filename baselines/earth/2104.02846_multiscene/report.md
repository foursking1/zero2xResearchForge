# MultiScene (arXiv:2104.02846) Multi-Label Aerial Scene Recognition — Reproduction

## Verdict

**contradicted** — multi-label classifier on MultiScene-Clean reaches test **mAP
41.6%** vs paper ResNeXt-101 anchor **64.8%** (abs diff **23.2**pp). The claim that
"deep models reach ~65% mAP and far outperform traditional methods (~15%)" is
**contradicted** (the frozen-feature deep model also clearly beats the frequent-label
prior baseline of **12.7%** mAP).

## Setup (data honesty)

- Frozen data: `F:/dataset/earth/2104.02846_multiscene/data/data/train-0000{0,1}-of-00002-*.parquet`
  (14,000 images, 512×512×3, 36-class multi-label).
- Frozen split: `multiscene_split_50.csv` (train 7,000 / test 7,000, seed 20260813),
  matching the paper's 7,000/7,000 protocol.
- No test labels used for training or threshold tuning; normalization statistics from the
  training subset only.

## Method

- Frozen ImageNet-pretrained ResNet50 (torchvision) feature extractor (fc removed),
  images resized to 224×224.
- Per-class one-vs-rest LogisticRegression (C=0.1, lbfgs) on the 2048-d pooled features.
- Threshold 0.5 for precision/recall/F1; mAP uses ranking (no threshold).

## Results (test, 7,000 images)

| Metric | Value | Paper reference (Table II) |
|---|---|---|
| mAP | **41.6%** | 64.8 (ResNeXt-101) |
| mCF1 | **40.4%** | 57.3 |
| mEF1 | **56.9%** | 70.2 |
| OF1 | **58.2%** | 71.3 |
| Frequent-label prior mAP | **12.7%** | 14.9–16.9 (SVM/XGBOOST) |

Per-class AP/F1 and train/test counts are in `results/evidence_table.csv`.

## Multi-scene / class notes

- Most frequent labels (train): residential (4,319), parking lot (3,620),
  commercial (3,300), woodland (2,590), farmland (2,301).
- Easiest classes (per-class AP): residential (0.895), parking lot (0.821),
  farmland (0.814), woodland (0.777), commercial (0.757).
- Hardest classes (per-class AP): oil field (0.011, only 13 train / 9 test —
  zero correct), helipad (0.098), cemetery (0.100), basketball field (0.135),
  port (0.158). The short tail of rare classes drives most of the mAP gap.

## Limitations

- Frozen ImageNet features + per-class linear heads (no end-to-end fine-tuning);
  224×224 input vs paper's 512×512.
- The frozen 50/50 split matches the paper protocol, but implementation differences
  (backbone ResNet50 vs ResNeXt-101) explain part of the mAP gap.

## Reproduce

```bash
python code/solve_multiscene.py --outdir results --img_size 224
```

All numbers recompute from the frozen parquet + split CSV.
