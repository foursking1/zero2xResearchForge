# Reproducing the SAT-6 reproduction (run instructions)

Environment: Python 3.12, `torch`, `pandas`, `pyarrow`, `PIL`, `numpy`, `scikit-learn`, `matplotlib`.

Data path is resolved automatically by `src/common.py` from, in order:
1. `--data PATH` argument,
2. `DSAT_DATA` environment variable,
3. default locations incl. the frozen `/mnt/f/dataset/earth/1509.03602_deepsat/data/data/train-00000-of-00001-c47ada2c92f814d2.parquet`.

## Fast evidence rebuild (recommended for verification, ~2–5 min, CPU or GPU)

Directly from the frozen parquet: re-derives the fixed-seed 70/15/15 split, re-decodes all 81,000
images, loads the shipped checkpoint (`model_sat6.pt`), and recomputes the entire evidence table +
`metrics.json` + confusion matrix. Asserted cross-check that the reproduced split equals the trained split.

```bash
cd agent_solution/submission
python3 src/reproduce_metrics.py --data /path/to/frozen.parquet --device auto
# device: auto|cpu|cuda:0 ; auto picks cuda only if >=2.5GB VRAM free
```

## Full re-training from scratch (slow on CPU)

```bash
cd agent_solution/submission
python3 src/prepare_data.py --data /path/to/frozen.parquet --seed 42
python3 src/train.py --device auto --epochs 30 --patience 7 --seed 42
```

- Default device is `auto` (GPU if ≥2.5 GB VRAM free, else CPU; total peak GPU memory ≈ 0.6 GB for bs=512).
- On CPU expect roughly an hour-scale run (30 epochs over 56,700 28×28 tiles); reduce with `--epochs 15`.
- Emits `results/evidence_table.csv`, `results/metrics.json`, `results/confusion_matrix.{csv,npy}`,
  `figure/confusion_matrix.png`, `model_sat6.pt`.

## Shallow baseline contrast (optional)

```bash
python3 src/analyze_baselines.py --data /path/to/frozen.parquet
```

## One-shot helper

```bash
./run_all.sh /path/to/frozen.parquet   # prepare (if no cache) -> train or reproduce -> baselines
```