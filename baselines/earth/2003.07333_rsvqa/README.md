# agent_solution — RSVQA LR VQA reproduction (arXiv:2003.07333)

Offline reproduction of the RSVQA LR visual-question-answering claim
(overall accuracy ≈ 79.08% on LR test) on the **frozen 2,000-QA subset** (100 unique
images). All code runs offline using pretrained backbones cached locally; no network.

## Verdict
**partially_supported** — overall accuracy **67.62%** on a held-out 20-image eval
(420 QAs), relative gap d≈14.5% vs the 79.08% anchor. The model genuinely uses the
imagery (random-image ablation: 31.4%; language-prior baseline: 48.1%), but exact
count prediction (23.9% vs the paper's 67.01%) is the main limiting factor given
the small frozen training budget (1,580 QAs / 80 images).

## Layout

```
agent_solution/
├── solution.md            # concise method & results
├── report.md              # full report (verdict, method, results, ablations, limits)
├── run_all.sh             # end-to-end reproduction (feature extract -> train -> finalize -> analysis)
├── code/
│   ├── dataset.py         # parquet loading, image-level split, question typing
│   ├── features.py        # frozen ResNet18/ViT feature extraction (offline weights)
│   ├── model.py           # CNN-LSTM VQA model + count heads (regress/density/hybrid)
│   ├── train_eval.py      # training loop, prediction, ablations
│   ├── run.py             # experiment driver
│   ├── finalize.py        # writes final evidence_table.csv + metrics.json
│   ├── ensemble.py        # seed/logit ensembling of saved scores
│   └── analysis.py        # figures + baselines
└── results/
    ├── evidence_table.csv # per-question rows (split/type/question/answer/pred/correct)
    ├── metrics.json       # overall OA, by-type, random-image ablation, sizes, seed
    ├── baselines.json     # global majority + language-prior baselines
    ├── accuracy_by_type.png, count_errors.png
    ├── final_model.pt     # champion weights
    ├── eval_scores_*.pkl  # per-row scores for ensembling
    └── _cache/            # cached frozen CNN/ViT features
```

## Reproduce

```bash
cd agent_solution
bash run_all.sh          # ~12-15 min on CPU; deterministic (fixed seeds)
```

Outputs land in `results/`; the key numbers:
`metrics.json -> overall_accuracy`, `accuracy_by_type`,
`random_image_ablation_accuracy`.

## Protocol notes (anti-leakage)

- Image-level 80/20 split (seed 42): 64 train / 16 dev / **20 eval images**; no image
  appears in both training and evaluation.
- Dev used only for model selection; eval touched exactly once at the end.
- Random-image ablation shuffles image features at inference (seed 7).
- No synthetic data; no external data; frozen parquet untouched (SHA-256
  `9db6b030...597c8c`).
