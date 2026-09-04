# Solution — Noise Immunity in In-Context Tabular Learning (arXiv 2604.04868v1)

**Task**: Verify the four claims C01–C04 against the **frozen reproduction data** located in
`F:\dataset\2604.04868v1` (read in place; nothing copied). All numbers below are either (a) read
from frozen JSON artifacts produced by the reference reproduction pipeline, or (b) recomputed from
frozen figures / the deterministic seeded data generator. **No** TabPFN model weights were required
and **no** internet access was used.

---

## 1. Verdict summary

| Claim | Verdict | One-line evidence |
|---|---|---|
| **C01** Baseline ROC-AUC ≈ 0.974 | **Supported** (ROC-AUC part) | Frozen baseline ROC-AUC = **0.9958** (even higher than the paper's 0.974); attention KL vs uniform = **1.058** (structured). |
| **C01** Attention concentration across layers {3,6,9,12} | **Partially supported** | Frozen heatmap figure shows the last panel far more concentrated (pixel KL **0.22**) than the first three (0.03–0.04), but exact layer indices {3,6,9,12} cannot be confirmed from the frozen artifact. |
| **C02** PCA feature-token embedding separation | **Inconclusive** | No frozen PCA/embedding figure or data exists in the provided results (reference collector also recorded "no evidence"). Cannot re-run offline (no cached weights). |
| **C03** SHAP: informative dominate, random negligible | **Supported** | Informative features {2,7} hold **98.8%** of normalized SHAP importance; random features hold **1.2%** (per-feature dominance ratio **≈253×**). |
| **C04** ROC-AUC stable as random features 4→512 | **Supported** | ROC-AUC ∈ [0.9872, 0.9998] across F=4…512 (std **0.0045**, range **0.0126**, trend p = 0.28). |
| **C04** Attention metrics stable as random features 4→512 | **Partially supported** | Attention metrics only exist for F=4,8 in frozen data (KL 0.772, 1.058, both > 0.2); F≥16 have ROC-AUC only. |

---

## 2. Frozen data used

All artifacts live under `F:\dataset\2604.04868v1\results\`.

| Claim | Frozen artifact(s) |
|---|---|
| C01 | `baseline/baseline_metrics.json`, `baseline/attention_heatmaps.png`, `go_no_go/gate_result.json`, `memory_smoke_test.json` |
| C02 | (audit of the whole `results/` tree) |
| C03 | `shap_analysis/shap_attention_comparison.json` |
| C04 | `random_features/summary.json`, `random_features/F4.json`, `F8.json` |
| Supplementary | `correlated_features/summary.json`, `sample_size/summary.json`, `label_noise/summary.json` |

The reference pipeline generated its synthetic data with `sklearn.datasets.make_classification`
(`n_samples=1500`, `n_informative=2`, `n_redundant=0`, `n_repeated=0`, `n_clusters_per_class=1`,
`class_sep=1.0`, `flip_y=0.01`, `random_state=42`, default `shuffle=True`). The raw data matrices
were not frozen (`data/generated/` is empty), so this deterministic generator is re-run locally
**only** to recover the ground-truth informative-feature columns (see §3.1). No model inference is
performed.

---

## 3. Method

### 3.1 Key methodological point — where the informative features really are

The reference pipeline's attention/SHAP metrics assume the first 2 columns are informative. This is
**incorrect** for this data: `make_classification` uses `shuffle=True` by default, which permutes
feature columns. By recording the final column permutation inside a `RandomState` subclass (same
seed, same `n_samples=1500`), the **true informative columns are {2, 7}** for the baseline F=8 data.

| Feature column | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
|---|---|---|---|---|---|---|---|---|
| Univariate AUC (recomputed) | 0.519 | 0.491 | **0.948** | 0.510 | 0.493 | 0.517 | 0.516 | **0.516** |
| Informative? (true) | ✗ | ✗ | ✓ | ✗ | ✗ | ✗ | ✗ | ✓ |

Feature 2 carries most of the signal univariately; feature 7 completes the 2-dim informative signal
(2-feature logistic AUC of {2,7} = 0.962 > 0.948 for feature 2 alone). **Consequence**: the frozen
attention-metric rows `informative_mean_rank=8.0`, `top2_proportion=0.0` for the baseline were
computed against the wrong columns and are **not** a valid refutation of attention-on-informative;
the SHAP row, however, was computed per raw feature and is valid.

### 3.2 Metric definitions

- **ROC-AUC**: area under the ROC curve of TabPFN's predicted class probability on the test split
  (frozen value from the reference run).
- **KL vs uniform (KL1)**:
  `KL(P ‖ uniform)` of the attention column-mass distribution (attention received per token),
  taken from the last feature-level attention block. Larger = sharper attention.
- **SHAP informative share**: fraction of normalized mean-|SHAP| (PermutationExplainer, 50
  background samples, 200 explained test samples) assigned to the informative feature set.
- **Attention importance**: normalized attention mass per token, truncated from feature-group
  tokens (TabPFN v2.2 default `features_per_group=2`) to the 8 raw features — **this is a group-level
  proxy, not a true per-feature quantity**; treated as context only.
- **Heatmap pixel concentration**: the frozen baseline heatmap PNG is a 4-panel `imshow` of
  feature-level attention (Blues colormap, `aspect='auto'`). For each panel we (1) locate the grid
  bounding box, (2) split it into the 12×12 attention cells reported by the frozen JSON
  (`seq_len=12`), (3) convert cell colour to relative attention using the panel's colourbar as a
  calibration curve, (4) row-normalize each query row, and (5) compute KL vs uniform of the column
  mass. Values are relative/monotone, not exact.

### 3.3 Analysis pipeline

`code/run_all.py` orchestrates:

1. `common.py` — paths, frozen-JSON loader, seeded data generator, ground-truth informative-column
   recovery, metric helpers.
2. `analyze_baseline_c01.py` — C01 quantitative baseline.
3. `analyze_heatmaps.py` — C01 attention-heatmap figure (pixel) analysis.
4. `analyze_pca_c02.py` — C02 frozen-evidence audit.
5. `analyze_shap_c03.py` — C03 SHAP dominance.
6. `analyze_random_features_c04.py` — C04 random-features stability.
7. `analyze_supplementary.py` — correlated / sample-size / label-noise context.

Outputs: `results/*.json`, `results/evidence_table.csv`, `results/metrics.json`,
`results/figures/*.png`.

---

## 4. Results

### 4.1 C01 — Baseline

| Quantity | Value | Source |
|---|---|---|
| ROC-AUC (reproduced, frozen) | **0.9958** | `baseline/baseline_metrics.json` |
| ROC-AUC (paper, cited) | 0.974 | paper Sec. 3.1 (citation only) |
| ROC-AUC gap (reproduced − paper) | +0.0218 | computed |
| Attention KL vs uniform (last feature layer) | **1.058** | `baseline/baseline_metrics.json` |
| Attention matrix size / heads | 12×12 / 6 heads | `baseline/baseline_metrics.json` |
| Go/No-Go gate | passed (gate ROC-AUC = 1.0) | `go_no_go/gate_result.json` |
| Memory smoke test | passed (1.0 GB VRAM) | `memory_smoke_test.json` |

**Interpretation.** The reproduced baseline ROC-AUC (0.9958) is consistent with, and even above, the
paper's 0.974 on the same synthetic setup (differences plausibly due to TabPFN version/seed).
Attention is strongly non-uniform (KL1 = 1.06 ≫ 0), i.e. structured.

**Attention concentration across the 4 heatmap panels** (pixel-derived, from
`baseline/attention_heatmaps.png`):

| Panel | KL vs uniform | Gini | Max column share | Column of max |
|---|---|---|---|---|
| 1 | 0.032 | 0.128 | 0.131 | 0 |
| 2 | 0.038 | 0.096 | 0.101 | 8 |
| 3 | 0.028 | 0.089 | 0.102 | 0 |
| 4 | **0.221** | **0.380** | **0.293** | 11 (label token) |

The last panel is markedly more concentrated than the first three, consistent with the paper's
"attention sharpens in deeper layers" narrative. **Caveats**: the panels are the first 4 captured
feature-level attention calls (earliest transformer layers, not verifiably {3,6,9,12}), the values
are pixel-relative, and the concentration increase is not strictly monotone panel-by-panel (panel 3
dips). Hence **partially supported**.

### 4.2 C02 — PCA feature-token embedding separation

An audit of the entire frozen `results/` tree found **0** artifacts matching `pca|embed|projection|
latent|tsne`. The reference reproduction's own evidence collector recorded the same gap
(`artifacts/collect_report.json`, rule R03: "No PCA embedding separation figure found"). Because the
feature-token embeddings were never frozen, and regenerating them requires TabPFN weights (not
available offline; downloads prohibited), the claim is **inconclusive** from the provided data.

### 4.3 C03 — SHAP dominance

Frozen `shap_analysis/shap_attention_comparison.json`:

| Metric | Value |
|---|---|
| SHAP importance on informative {2,7} (share of normalized mean-|SHAP|) | **0.9883 (98.8%)** |
| SHAP importance on random {0,1,3,4,5,6} | 0.0117 (1.2%) |
| Per-feature dominance ratio (informative / random) | **≈253×** |
| Top-2 SHAP features | {2, 7} (exactly the informative set) |

The two informative features dominate SHAP values almost entirely, and the random features are
negligible — **supported**. The paper's qualitative point "one informative feature dominates the
other" also holds: feature 2 (0.597) > feature 7 (0.391). (The negative attention–SHAP Spearman
ρ = −0.74 in the frozen file is a consequence of the attention-importance proxy being computed on
feature-**group** tokens, and is treated as context, not evidence against the SHAP claim.)

### 4.4 C04 — Random features 4 → 512

Frozen `random_features/summary.json` (2 informative features fixed; 2→510 random features added):

| Quantity | Value |
|---|---|
| ROC-AUC min / max | 0.9872 / 0.9998 |
| ROC-AUC mean / std | 0.9935 / 0.0045 |
| ROC-AUC range | 0.0126 |
| Linear slope vs log10(F) | −0.0026 (p = 0.280) |
| All 8 configurations > 0.95 | **yes** |

ROC-AUC is essentially flat as the number of random features grows from 4 to 512 — **supported**.

**Attention metrics** are present only for F=4 and F=8 in the frozen data (2 of 8 configurations):

| F | KL1 vs uniform | attention ratio | informative mean rank | top-2 proportion |
|---|---|---|---|---|
| 4 | 0.772 | 1.187 | 2.0 | 0.5 |
| 8 | 1.058 | 0.252 | 8.0* | 0.0* |

Both measured KL1 > 0.2, consistent with the paper's "attention stays sharp" claim where measured.
F≥16 configurations contain ROC-AUC only (the reference pipeline could not extract feature-level
attention there), so full 4–512 stability of *attention* metrics cannot be established from the
frozen data → **partially supported**. (*Rank/top-2 for F=8 are computed against assumed columns
{0,1} and are unreliable; see §3.1.)

### 4.5 Supplementary context (paper's broader robustness narrative)

| Test | ROC-AUC min | max | std | range |
|---|---|---|---|---|
| Correlated features (1→128, total=512) | 0.9781 | 0.9968 | 0.0061 | 0.0186 |
| Sample size (N=100→4000) | 0.8965 (N=200) | 1.000 | 0.0384 | 0.1035 |
| Label noise (0→30%) | 0.9932 | 0.9971 | 0.0012 | 0.0039 |

These frozen numbers support the paper's claims of robustness to correlated features and label
noise, with the expected small dip for tiny N=200.

---

## 5. Claim verdicts & basis

- **C01 (ROC-AUC) — supported**: frozen baseline ROC-AUC = 0.9958 (paper cites 0.974); both ≫ 0.5 and > 0.95.
- **C01 (attention concentration across layers) — partially supported**: last heatmap panel clearly
  more concentrated (pixel KL 0.22 vs ≤0.04); exact layer set {3,6,9,12} unverifiable from the frozen figure.
- **C02 — inconclusive**: no frozen PCA/embedding artifact exists; offline re-run not possible.
- **C03 — supported**: informative features {2,7} carry 98.8% of SHAP importance.
- **C04 (ROC-AUC) — supported**: ROC-AUC std 0.0045, range 0.0126 over F=4…512.
- **C04 (attention metrics) — partially supported**: measured KL1 (F=4,8) > 0.2; attention metrics missing for F≥16.

---

## 6. Known limitations

1. **No TabPFN forward pass was re-run** (no cached weights; downloading prohibited). All
   predictive/attention numbers come from the frozen outputs of the reference reproduction; only
   figures and deterministic data generation were analysed locally.
2. **Attention metrics in the frozen files were computed under a wrong informative-column
   assumption** (columns {0,1} instead of {2,7}) for most rows — noted wherever used.
3. **Heatmap pixel analysis** is approximate (grid segmentation + colourbar calibration) and the
   panel→layer mapping is not machine-readable.
4. Reference pipeline deviations from the paper (from `progress.txt` / `REPRODUCTION_REPORT.md`):
   TabPFN 2.2.0 with default `features_per_group=2` instead of the paper's `feature_group_size=1`;
   attention via SDPA monkey-patching; sample-size and label-noise tests used smaller scales than the paper.

---

## 7. Reproducibility

- All code: `agent_solution/code/` (run `python code/run_all.py`).
- All numbers in tables: `agent_solution/results/evidence_table.csv` and
  `agent_solution/results/metrics.json`.
- Figures: `agent_solution/results/figures/*.png`.
- Environment: system Python 3.13 with numpy, scipy, scikit-learn, matplotlib, pandas, Pillow
  (no TabPFN/torch/shap required).
