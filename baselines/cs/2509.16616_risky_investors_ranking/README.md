# agent_solution — reproduce arXiv:2509.16616 Appendix D

Frozen data lives in `../data/` (creditcard + jobprofit CSVs). Everything is
offline / CPU-friendly.

## Layout
```
code/            pipeline (python, no external downloads)
  common.py            datasets, labels, seed, folds, groups, metrics
  data_facts.py        evidence/data_facts.json  (judge B-checks)
  run_one_fold_baseline.py  LightGBM/XGB/RF/lambdaMART per (ds,fold)
  train_pa.py          PA-RiskRanker (PA-BCE + cross-trader attention + aux)
                       and Rankformer baseline (ListNet); 3-seed ensemble
  aggregate.py         -> results/evidence_table.csv, metrics.json, summary.md
results/        evidence_table.csv . metrics.json . means_table.csv . summary.md
                scores/ (per-seed PA test scores .npy)
evidence/       data_facts.json
```

## Reproduce (CPU, ~1-2 h; ~25 min with 16+ cores)
```bash
cd agent_solution/code
python3 common.py                 # build labels/splits/groups (cached)
python3 data_facts.py             # judge-facing data facts
# baselines (both datasets, 3 folds; parallel workers OK)
for ds in creditcard jobprofit; do for f in 1 2 3; do
  python3 run_one_fold_baseline.py $ds $f; done; done
# ranking models
for ds in creditcard jobprofit; do for f in 1 2 3; do
  python3 train_pa.py --model rankformer --dataset $ds --fold $f --epochs 40; done; done
# PA-RiskRanker: 3 seeds (10/20/30) per fold — the FINAL parameter set used
for ds in creditcard jobprofit; do for f in 1 2 3; do for s in 10 20 30; do
  python3 train_pa.py --model pabce --dataset $ds --fold $f --seed $s \
    --epochs 60 --aux 1.0 --pos-lambda 40 --w-cap 3.0 --lr 1e-3 --wd 0.02 \
    --dropout 0.1 --clip 5.0 --batch 32 --mode seq --threads 3 --tag FA; done; done; done
python3 aggregate.py              # evidence_table.csv / metrics.json / summary.md
python3 plot_summary.py           # evidence/with_prior_f1_compare.png
```

## Protocol summary (details in report.md §2)
- creditcard label = top-1% `Amount` (excluded from features as label leak but
  used as impact probe); jobprofit = top-1% `Jobs_Gross_Margin` after dropping
  the 7 future-info columns.
- 3 stratified 70/10/20 splits (seed 2026 + fold seeds 1/7/42), ≈1%/99%.
- ranking groups: 1 positive + 99 normals, train-only.
- with-prior = top-1% selection; financial loss = Σ misclassified Amount /
  max(margin,0).
- PA-RiskRanker reported as 3-seed ensemble (seeds 10/20/30).

## Time-outs / reproducibility
All random generators are seeded. Training runs on CPU (`--device cpu`).
GPU is intentionally avoided per environment constraints.