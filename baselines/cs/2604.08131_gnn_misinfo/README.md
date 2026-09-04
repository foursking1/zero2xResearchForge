# 2604.08131_gnn_misinfo — GNN vs MLP for Misinformation Detection (WELFake)

Reproduction of the L1 critical claim from
*Graph Neural Networks for Misinformation Detection: Performance–Efficiency
Trade-offs* (arXiv:2604.08131): on WELFake, a k-NN GraphSAGE reaches F1 ≈ 91.9 %
while a strong traditional MLP baseline reaches ≈ 66.8 %, i.e. a ~25 pp GNN advantage.

**Verdict: the GraphSAGE number reproduces (92.10 %); the claimed MLP
under-performance and the ≥15 pp GNN advantage do not reproduce with a
fairly-trained MLP (92.87 %).** Detailed reasoning in `report.md`.

## Layout

```
agent_solution/
├── data/welfake/WELFake_Dataset.csv   # frozen official CSV (sha256 verified)
├── code/
│   ├── pipeline.py                    # main reproduction pipeline (CPU, leak-free)
│   ├── probe_mlp.py                   # MLP training-regime probes
│   ├── verify_evidence.py             # independent F1 recomputation from saved preds
│   ├── analyze_results.py             # figures + claim verdicts
│   └── requirements.txt
├── results/                           # primary protocol outputs (see below)
├── results_cosine/                    # robustness run (cosine k-NN graph)
├── evidence/                          # curated copies of key tables/figures
├── solution.md                        # summary + verdicts
└── report.md                          # full report (method, leakage, results, limits)
```

## Requirements

Python 3.10+, `numpy`, `pandas`, `scipy`, `scikit-learn`, `torch` (CPU is fine),
`matplotlib` (for figures). No `torch_geometric`/`torch_cluster` needed.

```
pip install numpy pandas scipy scikit-learn torch matplotlib
```

## Reproduce

```bash
cd agent_solution

# 1) main protocol (GraphSAGE + MLP, 3 seeds) -> results/evidence_table.csv
python code/pipeline.py --out results --seeds 0,1,2 --max-epochs 200 \
    --models both --verify-sha
# ~40–60 CPU-minutes. CSV found via --csv | $WELFAME_CSV | ./data/welfake | F:/dataset fallback.

# 2) MLP baseline probes (optional, supports §3.2 of the report)
python code/probe_mlp.py --only mlp_200step --seeds 0,1,2
python code/probe_mlp.py --only mlp_sklearn --seeds 0,1,2

# 3) independent verification of the evidence table (fast, no training)
python code/verify_evidence.py --results results

# 4) figures (results/figures/*.png) + printed claim verdicts
python code/analyze_results.py --results results
```

## Key protocol points (leak-free)

- Split: `dropna(text)` → stratified 80/10/10, random_state=42
  (test `test_size=0.1`, then val `test_size=0.2222`) → 50467/14418/7210.
- TF-IDF `max_features=5000`, vocabulary/idf fit on **train only**.
- k-NN graph K=5 built on **train features only** (exact neighbour search,
  same semantics as `torch_geometric.nn.knn_graph`); val/test = isolated nodes.
- GraphSAGE = 2× `SAGEConv` mean (256→128, ReLU) + linear head; MLP = 2×256/128 ReLU.
- Adam lr=1e-3, early stop on **validation F1** (patience 10), max 200 epochs,
  best-val checkpoint → single test evaluation; 3 seeds averaged.