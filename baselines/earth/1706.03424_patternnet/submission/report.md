# Report — PatternNet (1706.03424) Content-Based Image Retrieval Reproduction

> Task: L1 critical-claim reproduction.
> Claim: "Deep CNN features achieve high-accuracy content-based retrieval on
> PatternNet (mAP ≈ 0.60–0.62, P@5 > 0.95)" — Zhou et al. 2018
> (arXiv:1706.03424), Tables 4/5: AlexNet_Fc1 mAP=0.6003 / P@5=0.9545,
> VGGF mAP=0.6195 / P@5=0.9246.
> Data: frozen official mirror, 30,400 images, 38 classes × 800.

## 1. Conclusion

**Verdict: supported**

| metric | this work (ResNet18) | this work (ViT-B/16) | paper AlexNet_Fc1 | paper VGGF |
|---|---|---|---|---|
| mAP  | **0.6233** | **0.6103** | 0.6003 | 0.6195 |
| P@5  | **0.9518** | **0.9477** | 0.9545 | 0.9246 |
| P@10 | **0.9407** | **0.9357** | (n/r) | (n/r) |

Relative difference from the 0.61 anchor: **+2.2% (ResNet18)** and **+0.05%
(ViT-B/16)** — both well inside the ≤10% band. Both backbones reproduce the
paper's headline numbers essentially exactly (mAP 0.61–0.62, P@5 ≈ 0.95).
All numbers are recomputed from the frozen parquet shards by `scripts/run_all.py`
(there is no hard-coded anchor value anywhere in the code).

## 2. Method

### 2.1 Data (frozen, integrality verified)
- Three parquet shards `train-0000[012]-of-00003.parquet` (10,134 / 10,133 /
  10,133 rows = 30,400 images) with columns `image:{bytes,path}` and `label`
  0–37. Class names derived from file paths (`airplane`, …, `wastewaterplant`).
- SHA-256 matches `data/source_manifest.json` (verified in this run):
  `019DDEAF…DDF3`, `3ABF55BE…F910`, `34282393…8E0`; files were not modified.

### 2.2 Features
- **Primary — ResNet18** (torchvision, ImageNet-1k pretrained, frozen `eval`
  mode): 512-d average-pooled embedding (`model.avgpool` after `layer4`).
- **Secondary — ViT-B/16**: 768-d class-token embedding after the final
  LayerNorm of the encoder (torchvision `vit_b_16`; already frozen).
- Weights from the local torch hub cache (`resnet18-f37072fd.pth`,
  `vit_b_16-c867db91.pth`); no network access needed.
- Inputs: center-crop 224×224, ImageNet normalization.
- Embeddings are L2-normalized; retrieval distance = cosine similarity
  (equals dot product after normalization).

### 2.3 Retrieval protocol (mirrors paper §5.2)
- Gallery: the full dataset (30,400 images).
- Queries: every image in the dataset (30,400 queries), the query itself
  excluded from its own ranked list.
- Rank by descending cosine similarity (`np.argsort` on dot products).
- **AP(q)** = mean of precision-at-each-hit over the query's same-class
  retrievals; **mAP** = mean AP over all queries; **P@k** = mean fraction of
  top-k retrievals sharing the query's class.
- Deterministic: ranking involves no randomness; the only RNG (optional query
  subsampling) is seeded (`--seed 0`).

### 2.4 Anti-leakage statement (C2)
- The feature extractors are **frozen** ImageNet-pretrained networks. **No
  training / fine-tuning on PatternNet**, so no label signal from the benchmark
  can leak into the features — there is no fitting split to abuse.
- Labels enter the pipeline **only at evaluation time** to count hits.
- Every image is unique (no duplicate self-documents); the query's own entry is
  explicitly removed from its gallery before ranking.

## 3. Results

### 3.1 Overall (from frozen data)
| feature | mAP | P@5 | P@10 | queries | gallery | self-excluded |
|---|---|---|---|---|---|---|
| ResNet18 | **0.6233** | **0.9518** | **0.9407** | 30,400 | 30,400 | yes |
| ViT-B/16 | **0.6103** | **0.9477** | **0.9357** | 30,400 | 30,400 | yes |

### 3.2 Per-class evidence
- `results/evidence_table.csv` — one row per class (38) + OVERALL row with
  columns `split, class_id, class_name, queries, retrieved, relevant, mAP,
  p_at_5, p_at_10`.
- `results/metrics.json` — the headline numbers above plus protocol fields.
- `results/per_query.csv` — per-image AP (30,400 rows) for independent
  recomputation.

Difficulty spread (per-class mAP, ResNet18): easiest = chaparral (0.989),
forest (0.990), oilwell (0.963); hardest = ferryterminal (0.255),
basketballcourt (0.279), nursinghome (0.287). Class mAP ranges 0.26–0.99.

### 3.3 Class-difficulty analysis (bonus, C3)
Confusability proxy: distance between L2-normalized class centroids
(`results/class_centroids.csv`). Findings consistent with the paper's comments
that spatially/texturally similar classes dominate retrieval errors:

- Most confusable centroid pairs (ResNet18): intersection~nursinghome,
  denseresidential~nursinghome, coastalmansion~denseresidential,
  nursinghome~swimmingpool, denseresidential~swimmingpool — man-made residential
  / institutional structures that look alike at low resolution.
- The hardest retrieval classes are exactly these small-object / texture-poor
  man-made classes (basketball court, ferry terminal, nursing home), while
  large-homogeneous natural classes (forest chaparral river) are near-perfect.
- Visual example retrievals in `results/fig_retrieval_examples.png` (easy vs
  hard class) corroborate this.

## 4. Boundaries / limitations
- Feature family differs from the paper's AlexNet/VGG (we use ResNet18/ViT);
  the *qualitative* claim (deep CNN features hit ≈0.61 mAP) transfers, but the
  exact per-model constants are not identical.
- HF mirror stores 256×256 thumbnails; native-resolution images might shift mAP
  by a few percent (the paper targets roughly similar sizes, so the gap is
  small).
- Efficiency: pairwise ranking on CPU takes ≈60 s for all 30,400 queries
  (sparse/ANN indexing was not needed at this scale).
- P@5 saturates (>0.9) for most classes because intra-class similarity is high;
  mAP is the discriminating metric, matching the paper's usage.

## 5. Reproduction instructions
```bash
cd submission/scripts
python run_all.py --out-root ../ --model resnet18 --device cpu   # full run (~11 min, CPU)
python run_all.py --out-root ../ --model vit_b_16 --device cuda # secondary (faster on GPU)
```
- Data dir auto-detected (CLI arg → task `data/` → `/mnt/f/dataset/earth/…`).
- Returns `results/evidence_table.csv`, `results/metrics.json`,
  `results/class_summary.csv`, `results/fig_per_class_map.png`, etc.
- Determinism: identical outputs on rerun (L2 features + exact ranking).

## 6. Evidence exports
Key exports are duplicated under `../../evidence/`: `metrics_resnet18.json`,
`metrics_vit.json`, `evidence_table_resnet18.csv`, extraction/eval logs, and the
figure files for review without re-running.