# agent_solution — 1509.03602 DeepSat SAT-6 (L1 critical claim)

Reproduction package for the falsifiable claim:
**"A learned framework reaches ≈93.9% OA on 6-class SAT-6 land-cover classification."**

Headline result: **test OA = 99.65%** (macro-F1 0.9946), majority-class baseline 37.12%,
relative difference vs anchor `d = 6.1%` → **verdict `supported`**.
Every number is recomputable from the frozen parity data + committed code/checkpoint.

## Artifacts

| path | what |
|---|---|
| `solution.md` | short method + result summary |
| `report.md` | full report (conclusion, protocol, evidence tables, leakage, limitations) |
| `submission/` | the TASK.md-required `submission/` tree: |
| `submission/src/` | all code: `prepare_data.py`, `train.py`, `reproduce_metrics.py`, `analyze_baselines.py`, `common.py`, `run_all.sh` |
| `submission/results/` | `evidence_table.csv`, `metrics.json`, `confusion_matrix.{csv,npy}`, `baselines.json` |
| `submission/figure/` | `confusion_matrix.png` |
| `submission/model_sat6.pt` | best-epoch CNN checkpoint (used by fast reproduction) |
| `submission/data_cache/` | fixed-seed split indices + train-only normalization stats (~237 KB) |
| `evidence/` | key evidence exports (same CSV/JSON/figures) |
| `EVAL_REPORT.md` | evaluation-harness report (external) |

## Quick reproduction (verification path, ~1–4 min)

```bash
cd submission
./run_all.sh /path/to/frozen/train-00000-of-00001-....parquet auto
# or step-wise:
python3 src/reproduce_metrics.py --data PATH --device auto   # recompute all metrics+table
```

Full retrain from scratch (validated end-to-end, deterministic on this box):
`python3 src/prepare_data.py --data PATH && python3 src/train.py --device auto --epochs 30`.
GPU (~4 min) preferred; CPU fallback supported but slow.

Frozen data: `/mnt/f/dataset/earth/1509.03602_deepsat/data/data/train-00000-of-00001-c47ada2c92f814d2.parquet`
(81,000 × 28×28 RGB tiles, 6 classes; SHA-256 `a1382370...70cc` verified).