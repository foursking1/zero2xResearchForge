# DeepSat SAT-6 scene classification — solution summary

- **Task**: arXiv:1509.03602 (DeepSat). Falsifiable claim: "SAT-6 6-class land-cover classification OA ≈ 93.9%".
- **Data**: frozen official SAT-6 *Test split* (HF mirror `TerraMoon/DeepSat`, 81,000 × 28×28 RGB tiles, 6 classes).
- **Method**: fixed-seed (42) stratified 70/15/15 split of the frozen data → train a small 0.58M-param CNN (conv64/64/128/128 + FC256) for 30 epochs (AdamW, cosine LR, flip augmentation) on the train subset, choosing the best epoch by the *val subset only*; the model is evaluated **once** on the held-out test subset.
- **Result**: test OA = **99.65%** (macro-F1 0.9946), majority-class baseline 37.12%, per-class F1 ≥ 0.991.
- **Verdict vs anchor 93.9%**: OA abs. diff = +5.75 pp, relative `d = 6.1%` (≤10% → top rubric band). Therefore the claim "high-accuracy (≈94%) SAT-6 land-cover classification" is **supported** — reproduced and in fact exceeded with a standard modern CNN.
- **Reproducibility**: every number is recomputable from the frozen parquet:
  - `python src/reproduce_metrics.py` (fast, uses shipped checkpoint `model_sat6.pt`) → re-derives split by seed, re-decodes data, recomputes all metrics (verified identical OA = 0.996543);
  - `python src/prepare_data.py && python src/train.py` (full re-training from scratch; GPU in ~4 min, CPU several hours).
- Evidence/figures under `submission/results/` + `submission/figure/`; details in `report.md`.

## Layout
```
submission/
├─ report.md                full report (also mirrored at agent_solution/report.md)
├─ src/                     all code (prepare_data.py, train.py, reproduce_metrics.py, analyze_baselines.py, common.py, run_all.sh)
├─ data_cache/              fixed-seed split indices + train-only normalization stats (~237 KB)
├─ model_sat6.pt            best-epoch CNN checkpoint
├─ results/                 evidence_table.csv, metrics.json, confusion_matrix.{csv,npy}, baselines.json
└─ figure/confusion_matrix.png
```