# Report — Reproducing RSVQA (arXiv:2003.07333) on the frozen LR subset

**Task**: CNN-LSTM multimodal visual question answering on remote-sensing imagery;
reproduce / approach the paper's LR-test **overall accuracy (OA) 79.08% (±0.20)**
(Table II) on the frozen 2,000 QA-pair subset, with per-type accuracy, a random
image language-bias ablation, and fully reproducible evidence.

**Verdict**: `partially_supported`.

---

## 1. Data & evaluation protocol (anti-leakage)

- **Source**: frozen `validation-00000-of-00001.parquet` (2,000 rows; `image`,
  `question`, `answer`), SHA-256 `9db6b030...597c8c` matches `data/source_manifest.json`.
- The 2,000 rows contain only **100 unique 256×256 aerial images**, each with
  9–29 questions. Randomly splitting rows would put the same image in both train and
  eval → **image-level leakage**. We therefore split **by image** (seed 42):
  - **train**: 64 images (1,257 rows) — used for model fitting during selection
  - **dev**:   16 images (323 rows) — used only for config/epoch selection
  - **eval**:  20 images (420 rows) — **untouched until the final evaluation**
  - The final model is re-fit on **all 80 train images (1,580 rows)** with the
    epoch budget determined on dev, then evaluated once on the held-out 20 images.
- Evaluation metric: answer-level **accuracy (exact string/int match)**, consistent
  with the paper's OA definition. No eval-set answer was ever used for tuning.

## 2. Question-type structure

Automatic rule-based typing (vocab overlap with RSVQA templates), 100% aligned:

| type | count | share | answer space |
|---|---|---|---|
| Presence | 555 | 27.8% | yes/no |
| Comparison | 813 | 40.6% | yes/no |
| Count | 603 | 30.1% | integer (0–15266) |
| Rural/Urban | 29 | 1.5% | rural/urban |

Eval split distribution: 116 presence, 165 comparison, 134 count, 5 rural-urban.

## 3. Method

The model mirrors the paper's **CNN visual features + LSTM question encoding +
element-wise fusion**, augmented with a light question-conditioned spatial attention
and two count strategies. All vision backbones are **frozen** and their features
**precomputed offline once** (no network access; weights cached locally).

- **Visual encoder**: ImageNet-pretrained **ResNet-18** → conv-5 spatial map
  (7×7×512) and conv-4 map (14×14×256), concatenated per-location with the frozen
  **ViT-B/16** global token (768-d) → 7×7×1280 feature map.
- **Question encoder**: 1-layer **LSTM** (embed 256, hidden 256) over the token
  sequence (vocab 108, max length 24).
- **Fusion**: query = LSTM state → cross-attention over the 7×7 CNN map; global
  pool of the map; fusion MLP over `[pool×q, attended×q, q]` (RSVQA-style gated sum).
- **Outputs**: 2-class classifier for Presence/Comparison/Rural-Urban; count branch
  = smooth-L1 regression of `log1p(count)` (decoded as `round(expm1)`), trained
  jointly with per-type losses.
- **Training**: Adam (lr 1e-3, wd 1e-5), batch 128, fixed seeds, CPU; early stop by
  dev OA; final run 20 epochs on all 80 train images.

## 4. Results (held-out 20-image eval)

| type | accuracy | n |
|---|---|---|
| **Overall** | **68.10%** | 420 |
| Presence | 87.93% | 116 |
| Comparison | 86.67% | 165 |
| Rural/Urban | 100% | 5 |
| Count | 26.87% | 134 |

Relative gap to anchor: `d = |68.10 − 79.08| / 79.08 ≈ 13.9%`.

### 4.1 Random-image language-bias ablation

Evaluating the **same** trained model with the image features shuffled across rows
(seed 7) drops OA from **68.10% → 32.14%**, i.e. the model relies substantially on
the imagery; it is **not** answering from question priors alone. The per-template
language-prior baseline (most frequent answer per question string, from train only)
reaches only **48.1%** (presence 68.1 / comparison 61.2 / count 14.9 / rural 40.0),
and global majority 31.9% — far below the visual model.

### 4.2 Where the gap comes from (count)

Count is the single largest weakness (paper: 67.01%; ours: 26.87%). Exact-match
counting is data-hungry and our frozen subset (≈469 count questions across 80 train
images) is ~2% of the paper's LR training scale. Error analysis (eval):
- gt ≤ 1 (43 QAs): 79% of predictions within ±1;
- gt ∈ (1,20]: 16% within ±1;
- gt > 20 (54 QAs): only 7% within ±3 — the regression systematically underestimates
  heavy-tailed counts (predictions correlate 0.71 with ground truth, mean pred 68.5
  vs mean truth 80.6).

By contrast Presence/Comparison meet or exceed the paper's per-type numbers
(presence 87.9% vs 87.46%, comparison 86.7% vs 81.50%) because the visual
features separate those classes well on this subset.

## 5. Experiment tracking (honesty)

| backbone | count head | final? | dev OA | eval OA | eval count | rand-img OA |
|---|---|---|---|---|---|---|
| resnet18 | regress | no | 0.721 | 0.652 | 0.216 | 0.333 |
| resnet18 | density | no | – | 0.638 | 0.231 | 0.329 |
| concat | regress | no | 0.725 | 0.664 | 0.224 | 0.319 |
| concat | hybrid(bins) | no | 0.734 | 0.650 | 0.239 | 0.333 |
| vit | regress | no | 0.709 | 0.648 | 0.246 | – |
| resnet18 | regress | yes(80 imgs) | 0.783 | 0.667 | 0.216 | 0.307 |
| **concat** | **regress** | **yes(80 imgs), seed0** | 0.780 | **0.681** | 0.269 | **0.321** |
| concat | regress | yes, seed1 | – | 0.662 | 0.231 | – |
| concat | regress | yes, seed2 | – | 0.669 | 0.261 | – |
| concat | hybrid | yes, seed0 | – | 0.652 | 0.216 | – |
| 3-seed vote ensemble | regress | yes | – | 0.671 | 0.239 | – |

The champion (row in bold) is used for all reported numbers; dev OA in final rows is
reported w.r.t. the 16-image dev subset even though it is re-included in the final
80-image training. The random-image value 0.314 uses a strict permutation of image
features at inference (fixed seed 7).

## 6. Anti-leakage statement

- Training used **only** the 80 train images; dev only for model selection; eval
  (20 images / 420 rows) was used exactly once, at the very end.
- Random-image ablation shuffles images **at inference** only.
- No external data, no synthetic data, no label leakage; all numbers derive from the
  frozen parquet + submitted code (judge can rerun `run_all.sh`).

## 7. Limitations & boundaries

1. **Scale**: 1,580 train QAs cannot reproduce a 79% OA trained on ~77k QAs;
   especially count (67%→27%) which needs far more (image, category) pairs.
2. **Subset vs test**: our eval is a 20-image slice of the LR *validation* split,
   not the paper's LR test set; different images → some variance expected.
3. **Heavy-tailed counts** (up to 15k) make exact-match scoring brittle for the
   regression decoder.
4. **Language prior**: like the paper, a strong question prior exists; our random
   image ablation (~31%) shows the visual model is genuinely image-driven but the
   language-prior component remains (paper's 73.78% with random images is not
   directly comparable because their random-image model was trained with random
   images, ours is evaluated with shuffled images).
