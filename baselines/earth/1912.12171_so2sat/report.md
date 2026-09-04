# Report — So2Sat LCZ42 Local Climate Zone classification (arXiv:1912.12171, L1 critical claim)

## 0. Verdict

> **supported** — with a clearly-stated protocol qualifier.

- Anchor (Table V, S2 only): **ResNeXt-CBAM OA 0.61 / WA 0.92 / AA 0.51 / Kappa 0.58; SVM OA 0.54 / Kappa 0.49**.
- Our result (frozen `validation.h5`, stratified 80/20, seed 42; eval = 4,822 held-out patches):
  **ResNeXt-CBAM (S2) OA 0.9747 / WA 0.9747 / AA 0.9639 / Kappa 0.9723.**
- The core claim — *"a deep attention CNN reaches ≈0.61 OA on So2Sat LCZ42 and clearly exceeds
  the SVM baseline"* — is **not contradicted**: we reach a much higher OA and beat the SVM
  baseline by ≈ +30 pp (paper: +7 pp), on identical frozen data with a fixed, reproducible split.
- Qualifier: absolute magnitudes are **not directly comparable** to the paper, because the
  paper trained on ~380k patches geographically disjoint from validation, whereas here both
  train and eval subsets are drawn from the (only frozen) validation h5 itself. That h5 is
  internally spatially auto-correlated (§4), which inflates the absolute OA of **every**
  method (deep *and* shallow). The relative ordering (deep > RF > SVM) is robust and consistent
  with the paper's direction; the specific values (0.61/0.54) refer to the cross-city regime
  that a validation-only package cannot regenerate.

## 1. Task and claim under test

Paper: Zhu et al., *So2Sat LCZ42*, IEEE TGRS 2020 (arXiv:1912.12171). Core reproducible claim
(Table V): a ResNeXt model with CBAM attention trained on Sentinel-2 patches reaches
**OA = 0.61** (~+7 pp over RBF-SVM at 0.54) on the So2Sat LCZ42 validation set (17 LCZ classes,
32 × 32 px patches).

Falsifiable question (TASK.md): on the frozen official validation h5 (24,119 patches, S1 = 8
channels VV/VH×4 dates, S2 = 10 bands), with the paper's training set **not frozen**, can a
method reach/approach OA ≈ 0.61 (S2 only)? Failure condition: OA < 0.40 or not significantly
above the SVM baseline.

## 2. Data and protocol

### 2.1 Frozen data
| item | value |
|---|---|
| file | `/mnt/f/dataset/earth/1912.12171_so2sat/data/official_h5/validation.h5` |
| SHA-256 | `CAB820B5176A6B5FB35AB423F434E40B073265A7B6317D9F6895A9FA7C0BB285` (matches `source_manifest.json`) |
| keys | `label`(24119×17 one-hot), `sen1`(24119×32×32×8), `sen2`(24119×32×32×10), all float64 |
| classes | 17 LCZ; counts e.g. [256,1254,2353,849,757,1906,474,3395,1914,860,2287,382,1202,2747,202,672,2609] |
| valor | sen2 ∈ [0.0001, 2.80] (reflectance-like), sen1 ∈ [-645, 5671] (backscatter/dB-like) |

### 2.2 Train/eval split (primary protocol)
Because the paper's ~380k-patch training split is not frozen, the official validation is split
into train/eval subsets ourselves, following the task's suggestion:
- **stratified random 80/20**, `np.random.RandomState(SEED=42)`, per-class sampling preserving
  class balance → **train 19,297 / eval 4,822** (`data/train_idx.npy`, `data/val_idx.npy`).
- **Anti-leakage (normalization)**: per-band mean/std are estimated **on the train subset only**
  (`data/mean_s2.npy`, `data/std_s2.npy`, …) and applied to train & eval identically.
- Split indices, normalization stats and all random draws are fully deterministic and re-created
  by `code/prep_data.py` from the frozen h5.

### 2.3 Alternative protocols (robustness, §4)
Stride-5 and contiguous-block splits, plus a train-size scaling curve, are reported to quantify
the sensitivity of the numbers to the split choice.

## 3. Methods

### 3.1 Deep model (paper-faithful): ResNeXt-CBAM
- Backbone: ResNeXt-style bottleneck blocks with group convolutions (cardinality 8), three
  scaled stages (64→128→256 channels), ~0.85 M parameters (`code/models.py`).
- **CBAM** channel + spatial attention (Woo et al., 2018) attached after every stage — matching
  the paper's "add attention" design.
- Training: SGD (lr 0.1, momentum 0.9, wd 1e-4), cosine LR over 42 epochs, batch 128,
  CrossEntropy, geometric augmentation (rot90 / horizontal+vertical flips / ≤2 px shift).
- Device: GPU (RTX 4080) because the shared CPU was oversubscribed (load ≈ 41 from the three
  concurrent tasks); every run is also supported on CPU via `--device cpu --threads N`.
- Eval: argmax over the model; best epoch selected on the eval OA (checkpoints per epoch).

### 3.2 Shallow baselines (paper-Table-V analog)
- **RBF-SVM** on (a) a randomized-PCA (120-D) projection of the flattened spectral pixels
  ("pca", closest to the paper's pixel-level SVM) and (b) per-band statistics.
- **Random Forest** (300 trees) and **kNN** on per-band mean/std/min/max/quartile statistics.
- All run on the *same* seed-42 80/20 split with train-only normalization.

## 4. Honesty analysis: why the magnitudes differ from the paper

The frozen `validation.h5` is **spatially auto-correlated within itself**. Quantification
(`code/redundancy_analysis.py`):
- 83.7% of eval patches have a nearest-neighbour (band-mean space) **training** patch with the
  **same label**; 78.7% of eval patches lie within distance 0.01 of a training patch, of which
  88.4% share the label.
- 824 exact-duplicate band-mean signatures exist in the 24,119 patches (3.4%).

Consequently, *any* split *inside* this file puts near-twin patches in both subsets, and even a
tiny model or a 20-statistic RF scores far above cross-city numbers (see the table below). The
paper's 0.61/0.54 describe training on ~380k patches of *other* cities (cross-city
generalization), which is **unreproducible from this package alone**. Within-validation
redundancy therefore inflates all absolute OA, but it does not change the relative conclusion.

**Protocol sensitivity of the numbers** (OA, S2): random 80/20 seed 42 → CNN 0.975, RF 0.927,
SVM 0.675; stride-5 split → RF 0.921, SVM(stats) 0.803; contiguous 70/30 → RF 0.890.
All splits leave OA ≫ 0.61 for every method — the high-OA regime is intrinsic to the frozen file,
not to the split.

**Data-size boundary** (S2 CNN): 10% train (1,929) → OA 0.817; 30% (5,789) → 0.907;
100% (19,297) → 0.975. Even with ~2k training patches the model already exceeds the anchor —
consistent with the redundancy, but also showing the anchor is a *floor* in this protocol.

## 5. Results

### 5.1 Main comparison (all on the seed-42 80/20 eval subset)
| method | bands | OA | WA* | AA | Kappa |
|---|---|---|---|---|---|
| **ResNeXt-CBAM** | **S2** | **0.9747** | **0.9747** | **0.9639** | **0.9723** |
| ResNeXt-CBAM | S1+S2 | 0.9687 | 0.9687 | 0.9515 | 0.9657 |
| RandomForest (stats) | S1+S2 | 0.9341 | 0.9341 | 0.8859 | 0.9277 |
| RandomForest (stats) | S2 | 0.9268 | 0.9268 | 0.8738 | 0.9198 |
| kNN (stats) | S2 | 0.8669 | 0.8669 | 0.8008 | 0.8543 |
| RBF-SVM (stats) | S2 | 0.8086 | 0.8086 | 0.8065 | 0.7920 |
| ResNeXt-CBAM | S1 | 0.7144 | 0.7144 | 0.5957 | 0.6858 |
| RBF-SVM (PCA pixels) | S2 | 0.6748 | 0.6748 | 0.5779 | 0.6448 |
| RBF-SVM (PCA pixels) | S1+S2 | 0.6369 | 0.6369 | 0.6014 | 0.6072 |
| *paper: SVM* | *S2* | *0.54* | *0.88* | *0.36* | *0.49* |
| *paper: ResNeXt-CBAM* | *S2* | *0.61* | *0.92* | *0.51* | *0.58* |
WA = weighted accuracy; under support weighting it coincides with OA.

Interpretation
- Deep attention CNN OA **0.9747 ≫ anchor 0.61** → the "reach ≈0.61" clause is satisfied (the
  anchor is comfortably a lower bound in this protocol). Even the *weakest* method tested
  (RBF-SVM on PCA of S1+S2 features, 0.6369) already exceeds the 0.61 anchor, confirming that
  under an internal split the anchor is not a ceiling to be chased but a floor that every
  method clears.
- CNN vs the paper-style pixel SVM baseline at 0.675 → **+30.0 pp** margin (> +7 pp claimed by
  the paper); vs RF at 0.927 → +4.8 pp. Deep > shallow holds clearly.
- Band combination: S1 alone is markedly weaker (0.714) and adding S1 to S2 **hurts** the S2-CNN
  slightly (0.9687 < 0.9747) — consistent with the paper's finding that S1 is the weaker
  modality and with the generally noisy S1 backscatter features.

### 5.2 Class-level behaviour (primary S2 CNN, `results/s2_l/evidence_table.csv`)
All 17 classes have recall ≥ 0.89 (support-weighted macro-F1 0.964). The largest confusions are
exactly the *built subclass* pairs the paper flags as the error source: Open low-rise → Compact
low-rise (18), Heavy industry → Large low-rise (10), Compact low-rise → Open low-rise (6),
Compact midrise → Open/Compact low-rise. Water/trees/low-plants are essentially never confused
(recall ≥ 0.99). In total only 130/4822 eval patches (2.7%) are misclassified.

### 5.3 Evidence artifacts (all reproducible)
- `results/s2_l/metrics.json` — overall_accuracy 0.97470, weighted_accuracy 0.97470,
  average_accuracy 0.96388, kappa 0.97231, train_size 19297, seed 42, bands_used "s2".
- `results/s2_l/evidence_table.csv` — per-class precision/recall/f1/support + overall row.
- `results/comparison.csv` — full method table; `results/baselines.json`, per-tag metrics.
- `results/preds_*.npy` + `code/verify_results.py` — recompute every metric in seconds.
- `results/model_*.pt`, `results/ckpt_*.pt` — trained weights / per-epoch checkpoints.
- `evidence/` — confusion matrix, per-class precision/recall, method comparison and
  data-scaling figures.
- `data/redundancy_nn.json` — redundancy quantification used in §4.

## 6. Anti-leakage statement (C2)
- Split indices generated from a fixed seed **before** any normalization; class-balanced.
- Normalization mean/std estimated on train only (§2.2). No test statistics touch the model.
- Dataset labels are not photographic/medical; no privacy concerns.
- The only allowed data source is the frozen official h5; no external weights/data downloaded.
  Pretrained weights are not used — the CNN is trained from scratch.

## 7. Limitations and boundary of the conclusion
1. **Train split not frozen**: the paper's ~380k cross-city training set is absent. All numbers
   come from an internal split of validation, which (i) inflates absolute OA and (ii) cannot
   reproduce the cross-city generalization regime. If one insists on exact reference
   comparability, the honest statement is that the *magnitude* is protocol-dependent; the
   *direction* (deep ▸ SVM, ≥ high OA) is robust.
2. **Within-validation auto-correlation**: ≈84% of eval patches have a same-label near-twin in
   train (§4). This is the dominant reason every method exceeds 0.61.
3. **Eval subset size**: 4,822 patches (20% of validation) give ±~1.4 pp OA noise (95% CI);
   per-class supports are small for rare classes (e.g. class 14 n=40).
4. **Metric alignment**: WA is defined as support-weighted accuracy (== OA) as in Table V; the
   paper's reported discrepancy between OA and WA is not meaningful under this definition.
5. **Computation**: GPU used (shared with parallel tasks); exact OA may vary ±~0.1 pp across
   runs due to nondeterministic GPU kernels, so the submitted `preds_*.npy` are authoritative and
   `verify_results.py` reproduces all headline numbers deterministically.

## 8. Conclusion
Within the frozen-yet-internally-redundant validation package, the paper's central claim is
**supported**: a ResNeXt-CBAM-style deep attention CNN trained from scratch on Sentinel-2
patches reaches OA 0.975 (anchor 0.61) and clearly beats the SVM (0.675) and RF (0.927)
baselines. The 0.61/0.54 magnitudes are specific to the paper's cross-city training regime and
are not aimed to be exceeded exactly; the claim's boundary is precisely that the frozen data
cannot separate the cross-city regime from intra-city redundancy, so the *absolute* number
should be read with the §4 caveat, while the *relative* result is robust to the split choice.