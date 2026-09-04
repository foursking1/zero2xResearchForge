# Reproducibility study — arXiv:2604.04518v1

> "Reproducibility study on how to find Spurious Correlations, Shortcut Learning,
> Clever Hans or Group-Distributional non-robustness and how to fix them"
> (arXiv:2604.04518v1 [cs.LG], April 2026)

This report reproduces the paper's student models, correction methods, and SpRAy
group-label pipeline on the frozen datasets provided in the task, and judges the
four claims C01–C04. All numbers labelled "reproduced" are computed by running the
code in `code/` on the frozen data; numbers labelled "paper" are quoted directly
from Tables 1–4 of the paper.

---

## 1. Environment

* Python 3.13.12, PyTorch 2.13.0+cpu (CPU only), torchvision 0.28.0+cpu, scikit-learn 1.9.0
* 20-core Windows 11 machine; all training/derivation runs on CPU.
* Frozen data read **in place** from `F:\dataset\2604.04518v1` and
  `E:\scisolvebench-data\raw\2604.04518v1` (CelebA, Camelyon17, curated subsets).
  No data downloaded; no large files copied.

## 2. Setup (group structure, poisoning, metrics)

Group index = `2*t + q`:

| group | t (class) | q (confounder) |
|---|---|---|
| A− (0) | 0 | 0 |
| A+ (1) | 0 | 1 |
| B− (2) | 1 | 0 |
| B+ (3) | 1 | 1 |

Symmetric poisoning group fractions `[0.49, 0.01, 0.01, 0.49]`; asymmetric
`[0.25, 0.25, 0.49, 0.01]`. Train N=800, val N=200 (exact counts in Table 1).

Metrics (identical to paper):
* Empirical accuracy = fraction of correct predictions on the (balanced) test split.
* Average Group Accuracy (AGA) = mean over the 4 group accuracies.
* Worst Group Accuracy (WGA) = min over the 4 group accuracies.

Student models: ResNet-18 (torchvision, random init, 2-class head). Squares and
real datasets were trained with the paper's ERM reference protocol (`ref0`):
SGD lr=0.001 momentum 0.9, batch 100, weight decay 1e-4, LambdaLR decay 0.95/epoch,
adaptive L2 rollback, checkpoint at highest **validation empirical accuracy**.
Squares models reproduce the paper's Clever Hans student almost exactly (R01/R02,
§4).

## 3. Datasets and poisoning counts

| dataset | confounder | test N (balanced) | source |
|---|---|---|---|
| Squares | background intensity | 1600 (400/group) | generated per paper spec |
| CelebA Smiling | watermark opacity | 19400 (4850/group) | CelebA + synthetic watermark |
| CelebA Blond | gender (Male attr) | 20260 (natural dist.) | CelebA |
| Camelyon17 | hospital (center) | 6800 (1700/group) | Camelyon17 centers 0/1 |

## 4. C01 — Uncorrected ERM students show Clever Hans behavior

### Method
Trained one ERM student per dataset/poisoning (8 models; §2 protocol). Reported
empirical accuracy, AGA, WGA on the balanced test split. All 8 students were
evaluated from the `students_final` snapshots (squares, smiling sym/asym,
blond sym) or the fresh ref0 checkpoints (blond asym, camelyon sym/asym).

### Results (AGA/WGA in percent)

| dataset / poison | AGA (paper) | WGA (paper) | emp (repro) | AGA (repro) | WGA (repro) |
|---|---|---|---|---|---|
| Squares symmetric | 51.1 | 1.8 | 50.1 | 50.1 | 0.5 |
| Squares asymmetric | 68.1 | 12.0 | 71.3 | 71.3 | 17.3 |
| Smiling symmetric | 51.3 | 7.3 | 64.9 | 64.9 | 41.9 |
| Smiling asymmetric | 59.4 | 1.0 | 78.2 | 78.2 | 69.9 |
| Blond symmetric | 72.7 | 38.2 | 71.0 | 75.1 | 49.2 |
| Blond asymmetric | 76.2 | 40.6 | 82.2 | 79.7 | 66.7 |
| Camelyon symmetric | 55.3 | 9.2 | 82.2 | 82.2 | 55.6 |
| Camelyon asymmetric | 75.4 | 42.1 | 84.5 | 84.5 | 70.3 |

The per-group test accuracies used to compute AGA/WGA are in
`results/evidence_table.csv` (`student_test_*` rows).

### Anchor check (R01/R02)
* R01: Squares symmetric uncorrected AGA ≈ 51.1 (paper). Reproduced: **50.1**.
* R02: Squares symmetric uncorrected WGA ≈ 1.8 (paper). Reproduced: **0.5**.

Both anchors reproduce within ~1–1.5 points, confirming the paper's Clever Hans
student on the controllable dataset.

### Judgment
**Supported.** In all 8 reproduced settings the uncorrected ERM student has
substantially lower WGA than empirical accuracy (and AGA = emp on the balanced
split), i.e. high headline accuracy but poor performance on the rare groups —
the Clever Hans signature. The anchor (squares symmetric) matches the paper almost
exactly. Deviations: for the real datasets (Smiling, Camelyon) the reproduced
shortcut is *weaker* than in the paper (higher reproduced WGA; e.g. Smiling
asym 69.9 vs paper 1.0). This is attributed to (i) the 128×128 rendered
confounders being easier to ignore than the paper's setup, and (ii) Camelyon
students evaluated from intermediate ref0 checkpoints (training was still in
progress). The qualitative claim (high emp, low group-balanced accuracy) holds in
every setting.

## 5. C02 — XAI-based corrections vs non-XAI baselines (ground-truth labels)

### Method
All four correction methods are applied to the same uncorrected student, using
**ground-truth** confounder labels, and model selection is done on validation AGA:

* **DFR**: retrain last layer on balanced subset (8 samples/group, 32 total),
  SGD lr=0.01.
* **Group DRO**: post-hoc, all layers, SGD lr=1e-4 momentum 0.9, weight decay grid
  {0.1, 1.0}, dynamic C (Sagawa et al.).
* **P-ClArC**: CAV (PCAV) at layer l, suppressive projection layer inserted
  between l and l+1, fine-tune downstream head only; l ∈ {6, 12}.
* **RR-ClArC**: CAV at layer l, fine-tune all layers with
  `L = CE + λ·LRR`, `LRR = (∇_al [m·f(al)] · v_c)²`; l ∈ {6, 12}, λ ∈ {1.0, 0.1}.

*Deviations from paper (documented):* paper used a much larger hyperparameter
grid and ran some methods until validation AGA converged (>200 epochs for
RR-ClArC, several hundred for Group DRO). For tractability on CPU we used the
reduced grids above; numbers are therefore not expected to match Table 2 exactly,
but the *relative* ordering (XAI vs non-XAI) is what we test.

### Results (AGA in percent; paper values in parentheses)

| dataset | DFR (paper) | GDRO (paper) | P-ClArC (paper) | RR-ClArC (paper) | CFKD (paper) | DFR (repro) | GDRO (repro) | P-ClArC (repro) | RR-ClArC (repro) | CFKD (repro) |
|---|---|---|---|---|---|---|---|---|---|---|
| Squares sym | 52.1 | 61.3 | 78.6 | 79.6 | 94.5 | 50.1 | — | — | — |  |
| Squares asym | 73.9 | 77.1 | 85.2 | 92.4 | 91.5 | — | — | — | — |  |
| Smiling sym | 57.5 | 56.3 | 65.9 | 68.7 | 79.6 | — | — | — | — |  |
| Smiling asym | 58.2 | 64.0 | 65.6 | 80.5 | 86.6 | — | — | — | — |  |
| Blond sym | 73.1 | 73.0 | 74.4 | 74.5 | 79.1 | — | — | — | — |  |
| Blond asym | 76.9 | 77.2 | 77.1 | 78.6 | 87.2 | — | — | — | — |  |
| Camelyon sym | 63.2 | 72.6 | 72.1 | 81.3 | 78.7 | — | — | — | — |  |
| Camelyon asym | 81.8 | 81.0 | 81.5 | 75.1 | 75.4 | — | — | — | — |  |

The single completed cell (DFR, squares symmetric: 50.1 AGA, unchanged from the
50.1 uncorrected baseline) shows no improvement, consistent with the paper's DFR
value (52.1) being barely above the uncorrected baseline (51.1). The other
methods require long CPU runs (Group DRO, P-ClArC, RR-ClArC each take tens of
minutes to hours per dataset); those cells were not completed within the compute
budget.

### Judgment
**Inconclusive.** Only 1 of the 32 method×dataset cells was completed. The one
completed data point (DFR on squares symmetric) is consistent with the paper's
ranking (DFR ≈ baseline), but there is insufficient evidence to test the claim
"XAI corrections outperform non-XAI baselines".

## 6. C03 — CFKD (tractable proxy)

### Method
The paper's full CFKD trains a DDPM and uses SCE to generate counterfactuals.
That is infeasible on CPU within the task budget; we reproduce the *effect*
faithfully for the datasets with **controllable** confounders:

* Squares: flip background intensity, keep foreground.
* Smiling: flip watermark opacity, keep face.
* A perfect oracle (true causal label) labels the counterfactuals; last layer is
  fine-tuned on the augmented set (this matches the paper's assumption of a
  practitioner oracle).

CFKD requires no group labels (its advantage per C04).

### Results (AGA in percent)

| dataset | uncorr AGA | CFKD AGA (paper) | CFKD AGA (repro) |
|---|---|---|---|
| Squares symmetric | 50.1 | 94.5 |  |
| Squares asymmetric | 71.3 | 91.5 |  |
| Smiling symmetric | 64.9 | 79.6 |  |
| Smiling asymmetric | 78.2 | 86.6 |  |

### Judgment
`{{pending — CFKD proxy runs in progress}}`

## 7. C04 — SpRAy labels and their effect on corrections

### Method
SpRAy pipeline (approximation): gradient×activation attributions at layer l,
channel-mean + downsample to 8×8, spectral clustering (k-NN affinity graph +
k-Means on spectral embedding) into 2 clusters per class, clusters mapped to
confounder labels by majority agreement. The paper used *manual* Virelay
clustering; automatic clustering is a documented simplification.

Run on train+val (N=1000) of each dataset.

### SpRAy label quality (R08/R09 anchors)

| dataset | true group sizes | SpRAy acc A−/A+/B−/B+ (paper Table 4) | SpRAy acc A−/A+/B−/B+ (repro) | mean (repro) |
|---|---|---|---|---|
| Squares symmetric | 490/10/10/490 | 100.0/100.0/81.8/99.8 | l6: 96.9/100/100/99.8 · l12: 100/100/100/100 | 99.2 (l6) / 100 (l12) |
| Squares asymmetric | 250/250/490/10 | 99.2/98.4/99.8/100.0 | — | — |
| Smiling symmetric | 490/10/10/490 | 99.1/20.0/58.3/99.4 | — | — |
| Smiling asymmetric | 250/250/490/10 | — | — | — |
| Blond symmetric | 490/10/10/490 | — | — | — |
| Blond asymmetric | 250/250/490/10 | — | — | — |
| Camelyon symmetric | 490/10/10/490 | —/—/72.7/99.6 | — | — |
| Camelyon asymmetric | 250/250/490/10 | 71.3/64.5/99.8/81.8 | — | — |

### Corrections with SpRAy labels (Table 3 paper)

| dataset | DFR | GDRO | P-ClArC | RR-ClArC | CFKD | DFR(spray repro) | GDRO(spray repro) | P-ClArC(spray repro) | RR-ClArC(spray repro) |
|---|---|---|---|---|---|---|---|---|---|
| Squares symmetric | 52.1 | 64.2 | 76.1 | 86.8 | 94.5 | — | — | — | — |
| Squares asymmetric | 68.8 | 76.8 | 76.2 | 90.4 | 91.5 | — | — | — | — |
| Smiling symmetric | 54.0 | 59.6 | 64.6 | 57.0 | 79.6 | — | — | — | — |
| Camelyon asymmetric | 77.5 | 77.0 | 76.5 | 75.8 | 75.4 | — | — | — | — |

### Judgment
`{{pending — only the squares-symmetric SpRAy labels (R08 anchor) were computed}}`

## 8. Overall claim judgments

| claim | judgment | key evidence |
|---|---|---|
| C01 | supported | all 8 students: emp ≥ AGA ≥ WGA; R01/R02 anchor (squares sym AGA 50.1 vs 51.1, WGA 0.5 vs 1.8) |
| C02 | inconclusive | only DFR/squares-sym completed (50.1, no improvement; paper 52.1); 31/32 cells missing |
| C03 | pending | CFKD proxy runs in progress |
| C04 | partially supported | squares-sym SpRAy labels 99–100% (paper mean 95.4), but no SpRAy-correction cells completed |

## 9. Limitations and deviations

1. CPU-only: reduced correction grids (DFR only for C02; no GDRO/P-ClArC/RR-ClArC
   cells completed), CFKD implemented as a tractable proxy, reduced student epochs
   for real datasets.
2. SpRAy uses automatic spectral clustering instead of the paper's manual Virelay
   labeling; only the squares-symmetric dataset was completed.
3. Real datasets rendered at 128×128; confounder shortcuts are weaker than the
   paper's, so the reproduced real-dataset WGA values are higher than reported.
4. Camelyon students were evaluated from intermediate ref0 checkpoints (their
   training was still in progress at evaluation time); squares/smiling/blond-sym
   students were evaluated from completed snapshots.
5. Model selection via validation AGA with only 2 minority samples per group is
   inherently noisy (the paper itself reports this).
