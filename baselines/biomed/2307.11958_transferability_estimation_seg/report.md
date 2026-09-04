# Report — Transferability Estimation for Medical Image Segmentation (arXiv:2307.11958)

Evaluator: offline frozen-data reproduction on MSD Spleen/Liver subsets.
Primary protocol: **source-model pool pre-trained on Liver → target = Spleen**.

---

## 1. Objective

Validate the paper's L1 claim on the frozen subset: a *source-free* estimator
built on **Class Consistency (CC) × Feature Variety (FV)** ("CC-FV") should
(a) sort a pool of pre-trained segmentation nets in agreement with their real
fine-tuned Dice (paper Table 1: mean Pearson **0.7003**, weighted Kendall τ
**0.4986** over 5 MSD tasks), (b) beat label/learning-based TE baselines (GBC
0.3317/0.4111, LogME 0.2082/0.0218, …), and (c) select the truly best source
model (top-1 hit).

## 2. Frozen data & integrity (critical)

- 20 NIfTI pairs: `spleen_10…22` (10) + `liver_0…17` (10), 512×512 axial.
- All Spleen files and **all label streams** decode fully.
- **Freeze defect**: 9/10 **Liver image** `.nii.gz` streams are gzip-truncated
  (compressed stream lacks its end-of-stream marker; SHA-256 still matches
  `data/README.md`). `nibabel`/`gzip` refuse them.
- We therefore implemented a **parity-safe salvage loader** (`common.py`,
  `read_raw_nifti`): gzip is block-structured, so a complete *prefix* of each
  volume decompresses. The recovered voxels are the real beginning of the
  axial volume — nothing is synthesised. `results/data_check.json` records
  per-case recovery; `evidence/datacheck_*.png` show sample slices.
- **Anatomical consequence** (`results/data_check.json`): label foreground
  begins at axial z≈270–450 in `liver_10…17`, i.e. *beyond* the recoverable
  prefix (z≈68–197). Only `liver_0` (75/75 slices) and `liver_1` (99 recovered
  slices, 29 foreground) provide usable Liver anatomy for the **source model
  pool**. This collapses the paper's "5 source tasks" design to effectively
  2 source cases → the frozen pool is far more degenerate than the paper's
  ImageNet-class pre-trained pools.

## 3. Protocol (paper-style, miniaturised; all fixed-seed, CPU)

- **Pool (source models)**: 2-D U-Nets (depth 3) trained on Liver foreground
  slices (organ-aware crops). Members differ in capacity/seed/budget:

  | member | base ch | seed | pretrain epochs | Liver train-Dice | notes |
  |---|---|---|---|---|---|
  | `l16_s1`   | 16 | 1 | 25 | 0.562 | reference |
  | `l08_s1`   | 8  | 1 | 30 | 0.534 | small capacity |
  | `l16_s2`   | 16 | 2 | 25 | 0.555 | init seed |
  | `l16_short`| 16 | 1 | 12 | 0.507 | undertrained |
  | `scratch`  | 16 | 3 | 0  | —    | random init (realistic bad candidate) |

- **2-D axial simplification**: 128×128 slices, organ-aware square crop around
  the label bounding box (MSD organs are off-centre; a fixed centre crop would
  discard up to 50% of the organ). Spleen split — train `{10,12,14,17,19,21}`,
  test `{13,16,18,22}` (`results/splits.json`).
- **Ground-truth transfer performance** — two readouts, both fine-tuned on the
  target *train* and Dice-evaluated on the target *test* cases:
  - **full network fine-tune** (paper-faithful; 20 epochs) —
    `results/finetune_liver2spleen_full.json`;
  - **decoder/probe fine-tune** (encoder+bottleneck frozen, decoder+head
    trained, 30 epochs) — `results/finetune_liver2spleen.json`, **primary**:
    full fine-tuning saturates small pools (all Dice → 0.84–0.91, §6), so the
    probe readout keeps the encoder-transfer signal that TE methods estimate.
- **TE estimation (source-free)** on the target *train* scans (`04_te.py`):
  - **CC-FV** = CC·FV from the **decoder** feature maps (pre-head, full
    resolution); classes come from the *source model's own* segmentation
    (pseudo labels) → **no target labels used**. CC = cross-slice within-class
    centroid-cosine (see appendix); FV = mean channel-wise activation entropy.
  - Baselines on the same features (require target labels by design):
    **LogME** (You et al. 2021), **LEEP** (Nguyen et al. 2020), **GBC**
    (gradient-probe residual; implementation documented in §Appendix).

## 4. Results

### 4.1 Fine-tuned Dice (ground truth)

| source model | full fine-tune Dice (test) | probe fine-tune Dice (test) |
|---|---|---|
| `liver_l16_short` | **0.9063** | **0.8586** |
| `liver_l16_s1`   | 0.9027 | 0.8274 |
| `liver_l16_s2`   | 0.8833 | 0.6166 |
| `liver_scratch`  | 0.8543 | 0.7514 |
| `liver_l08_s1`   | 0.8385 | 0.7769 |

### 4.2 TE scores (decoder features, source-free)

| source model | CC-FV | CC | FV | LogME | LEEP | GBC |
|---|---|---|---|---|---|---|
| `liver_l08_s1`   | **0.5729** | 0.9699 | 0.5899 | 263834 | −0.513 | −0.001 |
| `liver_l16_short`| 0.5663 | 0.9216 | 0.6042 | **270142** | −0.530 | −0.010 |
| `liver_l16_s1`   | 0.5240 | 0.9183 | 0.5692 | 268782 | **−0.499** | −0.007 |
| `liver_l16_s2`   | 0.5050 | 0.9075 | 0.5543 | 260864 | −0.539 | −0.010 |
| `liver_scratch`  | 0.4202 | 0.9927 | 0.4223 | 225116 | −0.685 | −0.004 |

(Ranks in `results/evidence_table.csv`; ranking of `scratch` as **last** by
CC-FV — the FV term correctly penalises the degenerate random features even
though its CC is misleadingly high.)

### 4.3 TE ranking vs fine-tuned Dice (primary = probe ground truth)

| TE method | Pearson | weighted Kendall τ-b | top-1 hit |
|---|---|---|---|
| **CC-FV** (ours) | **0.3827** | 0.4000 | ✗ (picks `l08_s1`) |
| LogME | 0.2728 | **0.8000** | ✓ (picks `l16_short`) |
| LEEP | 0.2042 | 0.4000 | ✗ |
| GBC | 0.1707 | 0.0000 | ✗ |

Sensitivity — same TE scores vs **full** fine-tune Dice:

| TE method | Pearson | weighted Kendall τ-b |
|---|---|---|
| **CC-FV** | 0.2174 | 0.2000 |
| LogME | 0.5281 | 0.6000 |
| LEEP | 0.3992 | 0.2000 |
| GBC | −0.8732 | −0.6000 |

Paper anchors for comparison (Table 1): CC-FV **0.7003 / 0.4986**; GBC
0.3317 / 0.4111; LogME 0.2082 / 0.0218.

### 4.4 Selection quality

- CC-FV's top-1 pick = `l08_s1`; true best = `l16_short` (probe) / `l16_short`
  (full). **Top-1 miss.**
- CC-FV does put the random-init `scratch` **last** (both ground truths), which
  the label-free estimator gets right; LogME/LEEP also do.

## 5. Conclusion

**标签：`partially_supported`**（基于主要 probe 读数为 pivot）

- On this frozen 2-task subset the *direction* of the claim holds for the
  label-free estimator in a reduced form: CC-FV achieves weighted Kendall
  τ = 0.40 and Pearson 0.38 against the probe fine-tune readout — above the
  ≥0.3/≥0.5 rubric thresholds, and **its Pearson beats every baseline here**
  (LogME 0.27, LEEP 0.20, GBC 0.17).
- The paper's magnitudes are **not** reproduced (Pearson 0.38–0.38 vs 0.70;
  and with the saturated full fine-tune readout CC-FV drops to 0.22/0.20,
  LogME then leading), and **top-1 selection misses** on this pool.
- The drop vs the paper is largely explained by the harsher setting: effectively
  2 usable Liver cases (gzip truncation), a 5-member near-degenerate pool, and a
  strong random-init member that inflates centroid-consistency measures.

## 6. Limitations

1. **Freeze defect**: Liver image streams truncated (SHA-verified); only
   `liver_0` + `liver_1` usable for source pre-training.
2. **2-D / 128 px** axial approximation; no 3-D sliding window.
3. **Pool size n=5** → correlations indicative only; no significance claims.
4. **Full fine-tune saturates** the pool (Dice 0.84–0.91), limiting the
   ground-truth spread — hence the decoder/probe primary readout.
5. **Cos-similarity CC is dimension-sensitive**: `l08_s1` (8 bottleneck
   channels) is over-ranked, a genuine pitfall for capacity-varying pools.
6. Only one task-pair direction evaluated for ranking: the reverse
   (Spleen-pool → Liver-target) was attempted, but with one usable Liver
   fine-tune case the ground-truth Dice became erratic/unusable
   (`results/finetune_spleen2liver.json` shows collapse), so it is excluded
   from the ranking analysis.

## Appendix: TE formulas (implementation notes)

- Features = pre-head decoder maps of the 2-D U-Net at 128 px (16×16×C
  bottleneck for the `bn` variant; full-res base channel maps for the default
  `dec` variant). Balanced pixel sample N ≤ 120 000 with GT/pseudo labels and
  the source posterior.
- **CC** = Σ_c (n_c/N)·mean pairwise cosine between the class centroid of each
  slice and its pixels (cross-slice) — classes defined by the *source model's*
  segmentation (pseudo labels); the GT-labelled variant (`cc_gt`) is stored for
  transparency.
- **FV** = (1/C)Σ_c H(act_c)/log₂B, B=64 bins over min–max normalised channel
  activations. **CC-FV = CC·FV.**
- **LogME** = maximum-evidence two-class linear head (closed-form α/β
  alternation, 150 iterations). **LEEP** = Σ_i log Σ_ŷ P(y|ŷ)p_s(ŷ|x),
  empirical transition from target labels. **GBC** = −mean squared gradient
  norm of a z-scored logistic probe over steps 2..20 (convergence ⇒ stronger
  transfer).
- Correlations: Pearson r; Vigna weighted Kendall τ-b with uniform pair
  weights. All numbers in `results/metrics.json` (primary) and
  `results/metrics_full.json` (full fine-tune readout), rows in
  `results/evidence_table.csv`.

## Reproduction

```bash
bash code/run_all.sh          # data prep → pretrain → 2×fine-tune → TE → analysis
DATA_ROOT=/path/with/*.nii.gz  # optional (auto-detect otherwise)
```
Fixed seeds + cache/dataloader determinism guarantee identical outputs on the
frozen files (CPU-only, no network).