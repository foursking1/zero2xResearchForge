# Solution — So2Sat LCZ42 local climate zone classification (arXiv:1912.12171)

## Verdict (short)
**Claim supported.** On the frozen So2Sat official `validation.h5` (24,119 patches) split 80/20
(seed=42, stratified), the implemented **ResNeXt-CBAM (Sentinel-2 only)** reaches
**OA = 0.9747, WA = 0.9747, AA = 0.9639, Kappa = 0.9723** on the held-out eval subset
(4,822 patches), far above the paper's anchor **OA = 0.61** and clearly above the
shallow baselines (RBF-SVM OA = 0.675, RF OA = 0.927, kNN OA = 0.867).

> Caveat (must-read): the paper trained on ~380k patches geographically disjoint from the
> validation set. Only the **validation** set is frozen here, so the train/eval subsets are
> necessarily both drawn **from inside** the same validation h5. This validation set is
> spatially auto-correlated (≈84% of eval patches have a same-label nearest training patch in
> band-mean space; 79% within distance 0.01 reflectance), so **absolute OA is inflated** for
> *every* method relative to the paper's cross-city numbers. The **relative** claim (deep CNN
> clearly beats SVM/RF) holds; the absolute 0.61 figure is a *lower bound* that any deep **and**
> even shallow method exceeds under this protocol.

## Method (summary)
- **Data**: frozen `validation.h5` (24,119 × 32 × 32; `sen2` 10 bands, `sen1` 8 bands, 17 LCZ).
- **Split**: stratified random 80/20, `np.random.RandomState(42)`, class-balanced; train 19,297 / eval 4,822.
- **Normalization**: per-band mean/std estimated **on the train subset only**, applied to both.
- **Model**: ResNeXt-CBAM (~0.85M params) — ResNeXt-style grouped-conv backbone with
  CBAM channel+spatial attention and three stages (paper resembles "ResNeXt-CBAM").
- **Training**: SGD lr=0.1, momentum 0.9, cosine schedule, batch 128, data augmentation
  (rot90/flip/shift), 42 epochs. Device: GPU (RTX 4080); CPU supported (`--device cpu --threads`).
- **Metrics**: OA/WA/AA/Kappa exactly as Table V of the paper; WA == OA by design.

## Key numbers
| method | bands | OA | WA | AA | Kappa |
|---|---|---|---|---|---|
| **ResNeXt-CBAM (primary)** | **S2** | **0.9747** | **0.9747** | **0.9639** | **0.9723** |
| ResNeXt-CBAM | S1+S2 | 0.9687 | 0.9687 | 0.9515 | 0.9657 |
| RandomForest (stats) | S2 | 0.9268 | 0.9268 | 0.8738 | 0.9198 |
| RandomForest (stats) | S1+S2 | 0.9341 | 0.9341 | 0.8859 | 0.9277 |
| kNN (stats) | S2 | 0.8669 | 0.8669 | 0.8008 | 0.8543 |
| RBF-SVM (stats) | S2 | 0.8086 | 0.8086 | 0.8065 | 0.7920 |
| ResNeXt-CBAM | S1 | 0.7144 | 0.7144 | 0.5957 | 0.6858 |
| RBF-SVM (PCA pixels) | S2 | 0.6748 | 0.6748 | 0.5779 | 0.6448 |
| RBF-SVM (PCA pixels) | S1+S2 | 0.6369 | 0.6369 | 0.6014 | 0.6072 |
| *paper: SVM* | *S2* | *0.54* | *0.88* | *0.36* | *0.49* |
| *paper: ResNeXt-CBAM* | *S2* | *0.61* | *0.92* | *0.51* | *0.58* |

Data-size scaling (S2 CNN): 10% train → 0.817, 30% → 0.907, 100% → 0.975.

## Reproducibility
```bash
cd agent_solution
python3 code/prep_data.py              # split + normalization from frozen h5 (data/train_*.npy)
python3 code/run_baselines.py          # SVM / RF / kNN baselines (~5 min)
python3 code/train_cnn.py --bands s2 --variant l --epochs 42 --batch-size 128 --lr 0.1 --device cuda
python3 code/train_cnn.py --bands s1s2 --variant l --epochs 38 --batch-size 128 --lr 0.1 --device cuda
python3 code/verify_results.py         # fast OA/WA/AA/Kappa recomputation from saved preds
python3 code/robustness_split.py       # stride-split sensitivity (~2 min)
python3 code/redundancy_analysis.py    # within-validation redundancy quantification
python3 code/make_summary.py           # comparison.csv + figures
```
All numbers are derived **only** from the frozen `validation.h5` (SHA-256
`CAB820B5…C0BB285`); predictions (`results/preds_*.npy`) and checkpoints
(`results/model_*.pt`) are saved so every metric can be re-derived in seconds
via `code/verify_results.py`. See `report.md` for the full account.