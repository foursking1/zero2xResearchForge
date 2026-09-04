# agent_solution — μ-Bench microscope-perception claim verification

Task: `2407.01791_ubench_microscopy` (L1 critical claim)
Dataset: frozen shard `ubench-test-00000-of-00007.arrow` (perception test split,
shard 1 of 7) — see `../data/README.md` for provenance/checksums.

## Layout

```
agent_solution/
├── solution.md            # short method + headline results (score-sheet oriented)
├── report.md              # full report (method, results, limitations, verdict)
├── claim.md               # the three questions + four-level verdict label
├── code/                  # reproducible pipeline, fully offline, CPU-first
│   ├── _common.py              # arrow parsing, shared constants
│   ├── 01_stats.py             # dataset statistics
│   ├── 02_extract_features.py  # frozen ViT-B/16 & ResNet-18 features
│   ├── 03_evaluate.py          # grouped 5-fold CV closed-VQA eval (LR probe + kNN)
│   ├── 04_figures.py           # evidence figures
│   ├── finalize_docs.py        # renders solution/claim/report from results
│   ├── verify_one_cell.py      # independent spot-check of one accuracy cell
│   └── run_all.sh              # end-to-end runner
├── results/
│   ├── evidence_table.csv      # REQUIRED: model × {coarse,fine} accuracy (+n_items)
│   ├── metrics.json            # REQUIRED: stats, models, paper anchors, verdict
│   ├── per_type_accuracy.csv / per_dataset_accuracy.csv / baselines.csv
│   ├── predictions.parquet     # full per-question predictions (compact)
│   └── dataset_stats.json, task_counts.csv, questions_long.csv
├── evidence/               # figures (coarse_fine_acc.png, per_type_acc.png, dataset_composition.png)
└── features/               # cached image features + image_id keys (regenerable)
```

## Reproduce

```bash
PYTHON=/home/dministrator/miniconda3/bin/python bash code/run_all.sh
```

or step by step (destination inside `code/`). Everything runs offline; the only
slow step is feature extraction (~20–40 min CPU; use `--device cuda` for the
extraction step to finish in ~10 min — features are deterministic enough for the
2pp recompute tolerance). Once `features/*.npy` exist, `01 → 03 → 04` finish in
≈3 minutes. Requires: `python≥3.10, torch, torchvision, timm, pyarrow, pandas,
scikit-learn, scipy, matplotlib`.

`run_all.sh` uses the file `code/01_stats.py` etc. from any POSIX shell; set the
`PYTHON` env var if your interpreter differs. The frozen Arrow path can be
overridden with `UBENCH_ARROW=/abs/path/to/ubench-test-00000-of-00007.arrow`.

Weight dependency: feature extraction loads two locally cached ImageNet
pretrained encoders (`timm vit_base_patch16_224.augreg2_in21k_ft_in1k` and
`torchvision resnet18`), both already present in this machine's caches
(`~/.cache/huggingface/hub/models--timm--vit_base_patch16_224.augreg2_in21k_ft_in1k` and
`~/.cache/torch/hub/checkpoints/resnet18-f37072fd.pth`). No network access is
needed if these are present; if a cached features/ directory exists, evaluation
can run without them.

## Headline numbers (this run, all computed by code on the frozen shard)

Closed-VQA multiple-choice accuracy, grouped 5-fold CV (seed 42). `coarse` =
macro average over modality/submodality/domain/subdomain/stain; `fine` =
classification.

| model | coarse | fine |
|---|---|---|
| ViT-B/16 linear-probe | 100.0% | 81.8% |
| ViT-B/16 kNN | ~100.0% | 67.6% |
| ResNet-18 linear-probe | 100.0% | 75.8% |
| ResNet-18 kNN | ~100.0% | 58.6% |
| majority baseline | 52.0% | 16.4% |

Paper reference (comparison only, not measured): GPT-4o coarse **62.6%**,
fine **51.7%**, cognition **62.0%** (arXiv:2407.01791, Table 1).

## Verdict

**partially_supported** — the "models struggle on microscope perception (<70%)"
claim holds for the fine-grained classification task, where the near-zero-shot
kNN baseline reaches only 58.6–67.6% and the supervised linear probe 75.8–81.8%.
The five coarse-grained question types saturate (~100%) on this shard because
their labels coincide with dataset/imaging-protocol identity, so this single
shard does not recapitulate the paper's 62.6% coarse difficulty (shard
limitation, not counter-evidence for the paper-level claim).

## Important caveats

* Only 1 of 7 perception test shards was frozen; counts/coverage are for that
  shard only and are not the full benchmark.
* No VLM/CLIP weights are available offline (HF cache holds only tokenizer files
  for Qwen3-VL), so the models run are frozen ImageNet-pretrained perception
  encoders evaluated as (i) a supervised linear probe and (ii) a k-NN similarity
  baseline under grouped CV — proxies sanctioned by the task protocol's "open
  small models / linear probing" allowance. GPT-4o numbers come from the paper
  and are used for comparison only.
* All metrics are computed by running code on the frozen data; no paper numbers
  are transcribed as own results.