# Solution — RSVQA LR visual question answering (arXiv:2003.07333)

**Task anchor**: reproduce/approach the paper's LR test-set **overall accuracy
79.08% (±0.20)** on the frozen 2,000-QA subset with a visual (image-conditioned)
VQA model, with per-type accuracy, random-image language-bias ablation, and
reproducible evidence.

## Verdict

- **Verdict: `partially_supported`** — an image-conditioned CNN-LSTM VQA model
  trained only on the frozen subset reaches **overall accuracy ≈ 68.1%**
  (held-out 20-image eval split), i.e. relative gap `d = |68.10−79.08|/79.08 ≈ 13.9%`
  vs the paper anchor. On this much smaller training budget (1580 rows / 80 images
  vs the paper's full LR training set) the model clearly *does* answer visual
  questions from the imagery, but exact count prediction remains far below the
  paper's figure, which is the main cause of the gap.

## Highlights

| metric | value |
|---|---|
| overall accuracy (eval, 420 QAs / 20 unseen images) | **68.10%** |
| Presence | 87.9% |
| Comparison | 86.7% |
| Rural/Urban | 100% (n=5) |
| Count | 26.9% |
| random-image ablation OA (same model, shuffled images) | 32.1% |
| language-prior (per-template majority) baseline | 48.1% |
| global-majority baseline | 31.9% |

## Method (summary)

- **Data**: frozen RSVQA LR validation subset (2,000 QA pairs, 100 unique images).
  Image-level 80/20 split (seed 42) so no image ever appears in both train and eval;
  64 images for training, 16 for config selection, **20 held-out for final eval**.
- **Visual**: frozen ImageNet-pretrained **ResNet-18** conv-5 (7×7×512) and conv-4
  (14×14×256) maps **plus** a frozen **ViT-B/16** global token concatenated per
  spatial location (offline cached features; no network use).
- **Language**: embedding + 1-layer **LSTM** question encoder (vocab 108).
- **Fusion**: question-conditioned **self/cross attention** over the spatial CNN
  map; element-wise product fusion + MLP (RSVQA-style fusion).
- **Outputs**: 2-way classifier for Presence/Comparison/Rural-Urban; count branch
  regresses `log1p(count)` (smooth-L1), decoded by rounding `expm1`.
- **Training**: Adam, 20 epochs on all 80 train images (epoch budget from a
  64/16 train/dev trial), per-type losses, fixed seeds; CPU execution.

## Why the claim is only partially supported

The model genuinely uses imagery (random-image ablation drops OA to ~32%, and the
language-prior baseline is only ~48%), so "multi-modal CNN-LSTM answers RSVQA
visual questions" is **supported**. But the exact accuracy level (~79.08%) is out
of reach with 1580 train questions; the count sub-task (67% in the paper) is the
bottleneck (~27%), because exact counting needs far more paired
(image, category) examples than the frozen subset provides. Boundaries:
training scale, heavy-tailed count answers, and image-level held-out splitting.

Files: `code/` (full pipeline), `results/` (evidence_table.csv, metrics.json,
figures), `report.md` (detailed report), `run_all.sh` (reproduce).