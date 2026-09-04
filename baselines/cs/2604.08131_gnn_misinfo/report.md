# Report — Graph Neural Networks for Misinformation Detection: Performance–Efficiency Trade-offs (arXiv:2604.08131)

## Verifying WELFake GraphSAGE-vs-MLP critical claim

- task_id: `2604.08131_gnn_misinfo` (L1 critical claim)
- claims tested (per task): (a) GraphSAGE test F1 ≈ 91.9 % (±5 pp);
  (b) GraphSAGE advantage over MLP ≥ 15 pp; (c) direction GNN > MLP.
- All experiments are run **on the frozen official WELFake CSV** (Zenodo record
  4561253; sha256 `66533142…223773` verified at load) with CPU only.

---

## 1. Summary of findings

| Claim | Verdict | Evidence |
|---|---|---|
| (a) GraphSAGE F1 near 91.9 % (within ±5 pp) | **supported** | 92.10 % ± 0.04 % (3 seeds) |
| (b) GraphSAGE − MLP ≥ 15 pp (same TF-IDF, same split, **well-trained MLP**) | **contradicted** | MLP 92.87 % ± 0.02 % → gap **−0.77 pp** |
| (c) direction GNN > MLP | **contradicted** under a well-trained baseline | MLP is slightly higher than GraphSAGE |

The **GraphSAGE anchor (A1 = 91.9 %) reproduces cleanly** (92.10 ± 0.04 %).
The **MLP anchor (A2 = 66.8 ± 29.1 %) does NOT reproduce** under any
reasonable, leak-free training regime we tried (full-batch Adam, 200 epochs,
early stopping → 92.9 %; mini-batch 200-step budget → 93.9 %; sklearn
`MLPClassifier` 256/128 → 95.9 %). A correctly trained nonlinear MLP on the
same TF-IDF features performs **at parity with (or slightly better than)** the
k-NN GraphSAGE model on this dataset. The paper's large "GNN > MLP by ~25 pp"
superiority therefore does not hold for a strong, fairly-tuned MLP baseline.

---

## 2. Protocol (faithful to the paper's unified pipeline)

### 2.1 Data
- File: `data/welfake/WELFake_Dataset.csv` (245,086,152 bytes),
  sha256 `665331424230FC452E9482C3547A6A199A2C29745ADE8D236950D1D105223773`.
- `pandas.read_csv` → 72,134 rows; **`dropna(subset=['text'])` → 72,095 rows**
  (39 empty-text rows removed). Columns: `title`, `text`, `label` (1=fake,
  0=real); labels roughly balanced (37,067 fake / 35,028 real after dropna).

### 2.2 Split (exactly as the reproduction repo)
- `train_test_split(..., test_size=0.1, random_state=42, stratify=label)` →
  hold out the **test** set (10 %).
- On the remaining 90 %: `train_test_split(..., test_size=0.2222,
  random_state=42, stratify=label)` → **val**.
- Resulting sizes: **train 50,467 / val 14,418 / test 7,210** (72,095 total).
- Only `train` participates in training/validation selection; `test` is
  touched exactly once, at the very end.

### 2.3 Features (leak-free)
- `TfidfVectorizer(max_features=5000)` fitted **only on the train texts**;
  val/test texts are transformed with the fitted vectorizer (no refit).
- No other feature normalisation is applied.

### 2.4 k-NN similarity graph (GNN only; leak-free)
- Built **only from train TF-IDF vectors** (`k-NN`, K = 5), exactly the
  semantics of `torch_geometric.nn.knn_graph` (nearest neighbours by pairwise
  distance, self excluded), implemented with an **exact** block-wise Gram
  computation (no approximation). Symmetrised to an undirected graph,
  self-loops added, adjacency row-normalised `D⁻¹(A + I)` — precisely the
  mean aggregation used by `SAGEConv`.
- Val/test nodes are fed to the GNN as **isolated single nodes** (identity
  adjacency), so no val/test feature ever participates in graph construction
  or normalisation (no information leakage).

### 2.5 Models
- **GraphSAGE**: two `SAGEConv` mean-aggregation blocks, 256 → 128 hidden
  units, ReLU, plus a linear readout head (2-class logits). Equivalent to
  `torch_geometric.nn.SAGEConv(aggr='mean', root_weight=True, bias=True,
  add_self_loops=True)` — implemented self-contained so the pipeline runs
  without compiled PyG extensions.
- **MLP**: two ReLU hidden layers 256 → 128 + linear head (§3.3).
- Optimiser Adam `lr=1e-3`; loss cross-entropy; **early stopping on validation
  F1, patience 10**; maximum **200 epochs**; the best-val checkpoint is used
  for the single test evaluation.
- **All results are 3-seed averages (seeds 0,1,2)** with fixed global
  `torch`/`numpy` seeds; the split seed stays fixed at 42.

---

## 3. Results

### 3.1 Evidence table (primary protocol)

| model | split | n | F1 (%) | Precision (%) | Recall (%) | f1_gap_pp |
|---|---|---|---|---|---|---|
| graphsage | test | 7210 | **92.10 ± 0.04** | 90.99 ± 0.43 | 93.25 ± 0.41 | — |
| mlp | test | 7210 | **92.87 ± 0.02** | 92.31 ± 0.03 | 93.44 ± 0.08 | **−0.77** |

`f1_gap_pp = Graphsage − MLP`; negative ⇒ MLP higher. (Binary F1, positive
class = label 1 = fake; consistent with `sklearn.f1_score(y_true, y_pred)`.)

Per-seed detail:

| model | seed | n | F1 | P | R | best_epoch | val F1 |
|---|---|---|---|---|---|---|---|
| graphsage | 0 | 7210 | 92.07 | 90.88 | 93.28 | 51 | 92.58 |
| graphsage | 1 | 7210 | 92.14 | 91.47 | 92.82 | 52 | 92.51 |
| graphsage | 2 | 7210 | 92.11 | 90.63 | 93.63 | 50 | 92.59 |
| mlp | 0 | 7210 | 92.90 | 92.28 | 93.53 | 64 | 93.14 |
| mlp | 1 | 7210 | 92.87 | 92.30 | 93.44 | 83 | 93.27 |
| mlp | 2 | 7210 | 92.85 | 92.34 | 93.36 | 82 | 93.22 |

### 3.2 MLP-baseline regime analysis (explains why the paper's MLP anchor is odd)

The paper reports MLP F1 = **66.8 ± 29.1 %**. MLPs can only be driven down to
~67 % if they are severely under-trained. We probed the three most plausible
configurations consistent with the text of §3.3 ("max 200 iterations",
2×256/128, ReLU, early stopping):

| MLP setting | mean test F1 (seeds 0,1,2) | note |
|---|---|---|
| full-batch Adam, ≤200 epochs, early stop (primary) | **92.87 %** | converges |
| mini-batch (batch 512) with a **fixed 200-step budget** | **93.90 %** (94.21/93.87/93.61) | 200 "iterations" = 200 update steps |
| `sklearn.MLPClassifier` 256/128, max_iter 200 | **95.92 %** (seed 0; converges in 27 iters) | TASK.md-suggested baseline |

None of these approaches the paper's 66.8 %; all show an **extremely low
variance across seeds** (paper's ±29.1 % variance is not reproduced either).
⇒ The 25 pp GNN-vs-MLP gap in Table 2 appears to stem from an under-fitted /
unstable baseline setup rather than an intrinsic property of the data. When
the MLP is actually trained to converge (or even to a modest 200-step budget),
it matches the GNN.

### 3.3 Robustness (graph-construction sensitivity)

| k-NN metric | GraphSAGE test F1 |
|---|---|
| euclidean (knn_graph default; primary) | **92.10 ± 0.04 %** |
| cosine (L2-normalised TF-IDF features) | **91.91 ± 0.07 %** (91.83/91.94/91.95) |

Both graph-construction variants reproduce the paper's 91.9 % value within a
few hundredths of a percentage point; the conclusion is insensitive to the
k-NN distance metric. (Cosine run outputs: `results_cosine/`.)

---

## 4. Leakage audit

- TF-IDF vocabulary + idf: fitted on **train only** (checked in code). ✓
- k-NN adjacency: built from **train feature rows only**. ✓
- Val/test nodes are isolated single nodes in the GNN (identity adjacency):
  their features are **never** used to create edges or compute any statistic
  used during training. ✓
- Model selection / early stop: **validation only**; test used exactly once
  for the final row. ✓
- Random seeds fixed (split seed 42; training seeds 0,1,2). ✓

---

## 5. Conclusion

On the frozen WELFake subset (72,095 usable rows) with the specified
TF-IDF-5000 features and stratified 80/10/10 split:

1. **GraphSAGE reproduces the paper's headline value** (92.10 % vs 91.9 %)
   → claim (a) **SUPPORTED**.
2. A **well-trained MLP reaches 92.9 %** and beats GraphSAGE slightly on the
   same features and split → claim (b) (≥ 15 pp GNN superiority) and claim
   (c) (GNN > MLP direction) are **CONTRADICTED** under a strong baseline.
3. The paper's MLP value (66.8 ± 29.1 %) is consistent only with a
   poorly-trained / unstable baseline and could not be reproduced under any
   fair configuration; the claimed ~25 pp advantage therefore appears to be
   an artefact of baseline under-training, not of the GNN's graph inductive
   bias on this dataset.

Overall verdict for the composite claim "GNN significantly beats a strong
nonlinear traditional baseline on WELFake": **partially supported on the GNN
number, but the superiority claim is contradicted once the MLP baseline is
fairly trained.**

---

## 6. Differences from the paper's full experiment / limitations

- 3 seeds vs paper's 3-seed averaging — same number of seeds (paper §3.4),
  but our training budget is 200 epochs with patience-10 early stopping; the
  paper's GNN used pretraining (5 epochs) + up to 500 epochs. We observed
  essentially converged models by ≈ epoch 50–80, so the extra budget is
  unlikely to change results.
- The graph is train-only with isolated val/test nodes (anti-leak);
  if the paper's code built the graph over train+test nodes instead, our
  GraphSAGE could differ slightly (val/test nodes would gain neighbours).
- TF-IDF uses sklearn defaults (word unigrams, default tokeniser);
  the paper's exact tokenisation/normalisation may differ marginally.
- The MLP is trained with a manual torch loop (to use *our* val split for
  early stopping); `sklearn.MLPClassifier` is also reported and is fully
  consistent (95.9 %).
- We use the full 72,095-row WELFake corpus (no subsampling); test n = 7,210.
- Runtime: the full protocol (graph build + 2 models × 3 seeds) takes
  ≈ 40–60 CPU-minutes; all code is CPU-only and reproducible.