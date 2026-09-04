# agent_solution — 1811.08425_small_xrd_classification

Reproduction package for Oviedo et al. (npj Comput. Mater. 5, 60 (2019)).

## Layout
- `code/` — runnable Python source (entrypoints below).
  - `code/exploration/` — development/diagnostic scripts (not part of the
    evidence chain).
- `results/` — generated evidence: per-experiment JSONs + evidence tables.
- `evidence/` — frozen snapshot of the key evidence (JSONs, figures, tables).
- `figures/` — publication-style figures.
- `solution.md` — concise method + answers.
- `report.md` — full report (methods, hyper-parameters, seeds, comparisons,
  Case-3 conformance, limitations).

## Data
The frozen data physically live in
`F:\dataset\materials\1811.08425_small_xrd_classification\`
(`/mnt/f/dataset/materials/1811.08425_small_xrd_classification/` here).
`code/config.py` resolves the data dir (env `XRD_DATA_DIR`, then the F: path,
then `../data`). Core-file SHA-256s are verified by `verify_data.py`.

## Entry points
```
cd code
python3 verify_data.py            # integrity checks (5 min max)
python3 run_final.py --aug  --model mlp --seeds 3 --tag mlp_aug_s3
python3 run_final.py --noaug --model mlp --seeds 3 --tag mlp_noaug_s3
python3 run_final.py --aug --model mlp --seeds 3 --coarse 4 --tag mlp_aug_s3_coarse4   # & coarse 2,3,8
python3 run_experiments.py cuda aug      # faithful a-CNN (paper arch) -> results/acnn_aug.json
python3 run_experiments.py cuda noaug    # -> results/acnn_noaug.json
python3 make_evidence.py          # -> results/evidence_table.{md,csv}
python3 make_figures.py           # -> figures/
```

## Requirements
Python ≥3.10, numpy, pandas, scipy, scikit-learn, matplotlib, torch ≥2.
Device is auto-detected (`--device cuda|cpu`; the reported numbers were
produced on an RTX 4080 / CUDA; a CPU rerun with the same fixed seeds may flip
at most a borderline sample but keeps the mean ≥0.86).

## Headline result (fixed seeds)
5-fold CV SG accuracy, Case 3 + physics-informed augmentation, 3-seed MLP
ensemble: **0.8654 ± 0.0916** (paper ≈0.89). Without augmentation:
**0.761 ± 0.095**. At 0.16° step: **0.865 ± 0.062**. Reproducible exactly
(same per-fold values on rerun).