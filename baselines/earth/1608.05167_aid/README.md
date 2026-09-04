# README — AID Scene Classification reproduction (task `1608.05167_aid`)

This folder reproduces the L1 "critical claim" anchored on **Xia et al. 2017,
" AID: A Benchmark Data Set for Performance Evaluation of Aerial Scene
Classification" (arXiv:1608.05167, IEEE TGRS 55(7))**, Table 6: GoogLeNet
fine-tuned OA of **86.39±0.55 % (20% training) … 94.71±1.33 % (80% training)**
on the single-label 30-class AID benchmark.

The frozen evaluation data is the **AID_MultiLabel mirror** (3,000 images,
17 multi-label classes, CC0) provided by SATIN.

## Contents

```
agent_solution/
├── solution.md                      # concise method + results + verdict
├── report.md                        # full report
├── README.md
├── code/
│   ├── aid_common.py                # constants / shared helpers
│   ├── aid_pipeline.py              # frozen-data loaders, models, splits
│   ├── train_multilabel.py          # 17-class multi-label fine-tune (60/20/20)
│   ├── train_singlelabel.py         # 30-class single-label fine-tune (frozen 50/50)
│   ├── recompute_metrics.py         # parquet->metrics without retraining
│   ├── make_figures.py              # PR curves / per-class AP
│   ├── analyze.py                   # confusion analysis / exports
│   └── run_all.sh                   # end-to-end runner
└── results/
    ├── evidence_table.csv           # per-class binary stats + overall
    ├── metrics_multilabel.json      # mAP / macro-F1 / subset acc / counts
    ├── metrics_singlelabel.json     # single-label OA / per-class
    ├── multilabel_test_preds.npz    # test softmax + GT (600 rows)
    ├── singlelabel_test_preds.npz   # test softmax + GT (5,000 rows)
    └── evidence_*.png               # figures
```

## Requirements

- Python 3.10 (conda env `verovlm`): torch>=2.0, torchvision, pandas,
  pyarrow, numpy, Pillow, scikit-learn, matplotlib.
- Frozen data locations (physical):

  | data | path |
  |---|---|
  | multi-label parquet | `/mnt/f/dataset/earth/1608.05167_aid/data_multilabel_quarantine/train-00000-of-00001-ee58cb5d786e111e.parquet` |
  | original AID 30-class images | `/mnt/f/dataset/earth/1608.05167_aid/data/data/` |
  | frozen 50/50 split | `/mnt/f/dataset/earth/1608.05167_aid/aid_split_50.csv` |

## Reproduce

```bash
cd agent_solution/code
./run_all.sh                 # or:
PY=/path/to/python ./run_all.sh
```

Step-by-step:

```bash
# 1) multi-label 17-class fine-tune ; writes results/evidence_table.csv + metrics_multilabel.json
python train_multilabel.py --epochs 30 --batch-size 32 --size 224 --outdir ../results

# 2) recompute all reported numbers from the frozen parquet w/o retraining
python recompute_metrics.py --results ../results

# 3) single-label 30-class fine-tune on frozen 50/50 split
python train_singlelabel.py --epochs 40 --batch-size 64 --size 224 --outdir ../results

# 4) figures
python make_figures.py && python analyze.py
```

All numbers recompute directly from the frozen parquet / split CSV with a
fixed seed `20260813` (multi-label split 60/20/20 = 1800/600/600).