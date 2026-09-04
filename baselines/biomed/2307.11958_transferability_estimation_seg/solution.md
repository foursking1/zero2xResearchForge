# Solution — 2307.11958 Transferability Estimation for Medical Segmentation

## Summary

This package reproduces the paper's **source-free transferability-estimation**
framework (CC-FV = Class Consistency × Feature Variety) on the frozen MSD
Spleen/Liver subset, and tests the claim that CC-FV ranks a pool of pre-trained
segmentation models in agreement with their real fine-tuned Dice.

**Protocol (fixed seeds, CPU):** source pool = Liver-pretrained 2-D U-Nets
(5 members: `l16_s1`, `l08_s1`, `l16_s2`, `l16_short`, `scratch`) → target =
Spleen. Two fine-tune ground truths: full-network (paper-faithful) and
decoder/probe (primary — full fine-tune saturates the tiny pool). TE computed
source-free on the target train scans (decoder features; CC-FV uses the source
model's own pseudo-labels, no target labels).

## Key results (primary = probe ground truth)

| TE method | Pearson | weighted Kendall τ | top-1 hit |
|---|---|---|---|
| **CC-FV** | **0.3827** | **0.4000** | ✗ |
| LogME | 0.2728 | 0.8000 | ✓ |
| LEEP | 0.2042 | 0.4000 | ✗ |
| GBC | 0.1707 | 0.0000 | ✗ |

Paper anchor: CC-FV Pearson 0.7003 / τ 0.4986 (Table 1, 5-task mean).
Sensitivity on saturated full fine-tune: CC-FV 0.2174/0.2000.

**Conclusion: `partially_supported`** — the label-free estimator reproduces the
*direction* of the claim on this subset (τ=0.40, best-in-pool Pearson, and it
ranks the random-init model last), but not the paper's magnitude, and its
top-1 source selection misses.

## Data integrity note (important)

9/10 Liver **image** streams in the freeze are gzip-truncated (SHA matches
`data/README.md`); labels decode fully. The included loader (`common.py`)
recovers each volume's real compressed prefix. Anatomically this leaves only
`liver_0` + `liver_1`(foreground) usable for the source pool, so the pool is
far more degenerate than the paper's 5-task setting — the main driver of the
gap with the paper numbers.

## Layout

- `code/` — full reproducible pipeline (`run_all.sh`), fixed seeds, CPU.
- `results/` — `metrics.json` (primary), `metrics_full.json` (sensitivity),
  `evidence_table.csv`, `te_*.json`, `finetune_*.json`, `splits.json`,
  `data_check.json`, pretrain summaries.
- `evidence/` — scatter figures (TE vs Dice), data-integrity crops.
- `claim.md`, `report.md` — claim verdict and the full write-up.

Reproduce: `bash code/run_all.sh` (uses frozen `data/`; `DATA_ROOT` auto-detects).