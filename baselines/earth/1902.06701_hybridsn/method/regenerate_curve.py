"""Regenerate a genuine HybridSN training-convergence curve for evidence figures.

Retrains HybridSN on the seed-0 30/70 split and saves per-epoch train loss + test
OA to results/checkpoints/history_hybridsn_seed0.npz (does NOT overwrite the
submitted hybridsn_seed0.pt checkpoint used for the main results).

Usage: python method/regenerate_curve.py --epochs 100 --device cuda
"""
import argparse
import os
import sys
import numpy as np
import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import DATA_DIR, RESULTS_DIR, N_PCA_BANDS, BATCH_SIZE, LR, WEIGHT_DECAY
from data_utils import preprocess
from models import HybridSN
from train_utils import train_cnn, set_seed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--epochs', type=int, default=100)
    ap.add_argument('--device', default='cpu')
    ap.add_argument('--seed', type=int, default=0)
    args = ap.parse_args()

    X_train, y_train, X_test, y_test, meta, _ = preprocess(DATA_DIR)
    model = HybridSN(n_bands=N_PCA_BANDS, n_classes=16, dropout=0.5)
    tmp = os.path.join(RESULTS_DIR, 'checkpoints', '_tmp_curve')
    _, hist, _ = train_cnn(model, X_train, y_train, X_test, y_test,
                           epochs=args.epochs, lr=LR, weight_decay=WEIGHT_DECAY,
                           batch_size=BATCH_SIZE, seed=args.seed, device=args.device,
                           model_name='hybridsn_curve', ckpt_dir=tmp)
    np.savez(os.path.join(RESULTS_DIR, 'checkpoints', f'history_hybridsn_seed{args.seed}.npz'),
             **hist)
    import shutil
    shutil.rmtree(tmp, ignore_errors=True)
    print('[curve] saved history_hybridsn_seed%d.npz, final test OA=%.4f'
          % (args.seed, hist['test_oa'][-1]))


if __name__ == '__main__':
    main()