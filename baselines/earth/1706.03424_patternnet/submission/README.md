# PatternNet (1706.03424) Retrieval Reproduction — Submission

Reproduction of Zhou et al., *PatternNet: A Benchmark Dataset for Performance
Evaluation of Remote Sensing Image Retrieval* (arXiv:1706.03424), L1 critical
claim: "deep CNN features achieve mAP ≈ 0.60–0.62 with P@5 > 0.95 for content-
based image retrieval on PatternNet (38 classes × 800 images = 30,400)."

## Conclusion (headline)

**supported** — with ImageNet-pretrained ResNet18 CNN embeddings and a
paper-faithful every-image-as-query retrieval protocol over the full frozen
PatternNet gallery (30,400 images), we reproduce **mAP 0.6233, P@5 0.9518**
(ResNet18; ViT-B/16: mAP 0.6103, P@5 0.9477), consistent with the paper's
anchors (AlexNet_Fc1 mAP 0.6003 / VGGF mAP 0.6195). See `results/metrics.json`.

## Contents

```
submission/
├── report.md                     full report (conclusion, method, evidence)
├── README.md                     this file
├── scripts/
│   ├── extract_features.py       features from frozen parquet shards
│   ├── evaluate_retrieval.py     mAP / P@5 / P@10 per class + overall
│   ├── analysis.py               class-difficulty analysis + figures
│   └── run_all.py                one-command reproducible pipeline
├── results/                      primary (ResNet18) outputs
│   ├── evidence_table.csv        per-class + overall retrieval metrics
│   ├── metrics.json              headline mAP / P@5 / P@10 + protocol fields
│   ├── per_query.csv             per-image AP (30,400 rows)
│   ├── class_summary.csv         per-class metrics sorted by mAP
│   ├── class_centroids.csv       pairwise class-centroid cosine similarities
│   ├── top_confusions.csv        most confusable class pairs
│   └── fig_*.png                 per-class mAP + retrieval-example figures
├── results_vit/                  secondary (ViT-B/16) outputs (same layout)
└── artifacts/                    extracted feature arrays, labels, paths, names
```

## Run the pipeline

```bash
cd submission/scripts

# full protocol (every image as query, gallery = all 30,400, CPU)
python run_all.py --out-root ../ --model resnet18 --device cpu

# quick sanity version (50 queries per class)
python run_all.py --out-root ../ --model resnet18 --seed 0 \
    --sample-per-class 50 --skip-extract   # (feasible once features exist)
```

Dependencies: python ≥ 3.10, numpy, pandas, pyarrow, Pillow, torch (>= 2.x),
torchvision, matplotlib. Pretrained weights are loaded from the local torch hub
cache (`~/.cache/torch/hub/checkpoints/resnet18-f37072fd.pth`).

The frozen parquet directory is auto-detected: `--data-dir` CLI arg → task
`data/data/` → `/mnt/f/dataset/earth/1706.03424_patternnet/data/data/`
(`F:\dataset\earth\1706.03424_patternnet\`).