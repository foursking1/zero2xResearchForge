# Code for `2505.06646_chexnet_reproduction`

End-to-end fine-tuning of an ImageNet-pretrained **DenseNet-121** (CheXNet
architecture: global-avg-pool + 14 sigmoid outputs) on the frozen NIH
ChestX-ray14 subset for 14-class multi-label disease classification.

## Files

| file | purpose |
|---|---|
| `common.py` | data discovery, image decoding, multi-hot labels, fixed train/val split (seed 42), DenseNet-121 builder (local ImageNet weights), losses, metrics |
| `train.py` | train one model (`--model repro|enhanced`), validate, snapshot-ensemble the tail of training, save checkpoint + frozen probabilities |
| `merge_seeds.py` | average per-seed predictions into the official `checkpoints/{model}_pred.npz`; re-tune enhanced thresholds on the merged validation probs |
| `evaluate.py` | load checkpoints, write `results/evidence_table.csv`, `results/metrics.json`, `results/per_class_summary.csv` (deterministic) |
| `analysis_plots.py` | per-class AUC/F1 bars + example ROC curves -> `evidence/*.png` |
| `run.sh` | end-to-end multi-seed wrapper |
| `weights/` | cached ImageNet `densenet121-a639ec97.pth` (torchvision URL) |

## Data

Reads `nih_train-00000.parquet`, `nih_test-00000.parquet` (columns
`image` = {bytes,...}, `labels` = list of class indices). The parquet root is
located automatically (see `common.find_data_dir`), or pointed to with
`PB_DATA_DIR`.

- 1082 train / 162 val (15% split, seed 42, carved from the train shard) /
  640 official test.
- Label index 14 (`No Finding`) is ignored; only the 14 disease classes are
  target bits.

## Run

```bash
# full multi-seed training + evaluation (GPU ~30-40 min; several hours on CPU)
bash code/run.sh

# or step by step (official protocol)
python3 code/train.py --model repro    --epochs 22 --lr 3e-5 --seed 42 --ema 0.999 --label-smoothing 0.05 --aug strong --tag s42
python3 code/train.py --model repro    --epochs 22 --lr 3e-5 --seed 43 --ema 0.999 --label-smoothing 0.05 --aug strong --tag r43
python3 code/train.py --model enhanced --epochs 24 --lr 3e-5 --seed 42 --ema 0.999 --label-smoothing 0.05 --aug strong --focal-alpha 0.75 --tag en_s42b
python3 code/train.py --model enhanced --epochs 24 --lr 3e-5 --seed 43 --ema 0.999 --label-smoothing 0.05 --aug strong --focal-alpha 0.75 --tag en_s43
python3 code/train.py --model enhanced --epochs 24 --lr 3e-5 --seed 44 --ema 0.999 --label-smoothing 0.05 --aug strong --focal-alpha 0.75 --tag en_s44
python3 code/merge_seeds.py     # official repro = avg(s42,r43); enhanced = avg(s42b,s43,s44)
python3 code/evaluate.py        # writes results/
python3 code/analysis_plots.py  # evidence/*.png

# pure evaluation from stored checkpoints (fast, no training)
python3 code/evaluate.py
```

Variables for CPU runs: `DEVICE=cpu EPOCHS=6 bash code/run.sh`
(epochs can be shrunk to trade runtime vs. fidelity).

## Protocol summary

- **repro** arm = CheXNet replica: BCE loss, threshold 0.5 for F1.
- **enhanced** arm = modern tricks: Focal Loss (γ=2, α=0.75), ColorJitter +
  RandomAffine + RandomErasing augmentation, AdamW + cosine, weight EMA,
  per-class thresholds tuned to maximize F1 on the validation split only.
- Test shard never used for training, model selection, or threshold tuning.
- Reported test predictions = per-seed **snapshot-ensemble** of the last ~25% of
  epochs (fixed recipe, no test-driven selection) averaged over 2 seeds (repro,
  seeds 42 & 43) / 3 seeds (enhanced, seeds 42, 43 & 44).
- Train/val split fixed at seed 42; model shuffle seeds vary per run.
- Committed `code/checkpoints/` holds the merged official artifacts so
  `evaluate.py` reproduces `results/` deterministically without retraining.