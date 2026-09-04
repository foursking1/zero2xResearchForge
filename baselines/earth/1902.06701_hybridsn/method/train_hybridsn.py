"""Train & evaluate the HybridSN 3D-2D CNN on Indian Pines (paper protocol).

Usage (from agent_solution/):
    python method/train_hybridsn.py --seeds 0,1,2 --epochs 100 --device cuda
"""
import argparse
import json
import os
import sys
import numpy as np
import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import DATA_DIR, RESULTS_DIR, WINDOW, N_PCA_BANDS, BATCH_SIZE, LR, WEIGHT_DECAY
from data_utils import preprocess
from models import HybridSN, count_params
from metrics import compute_metrics, save_metrics
from train_utils import train_cnn


def predict_all(model, X, y, device, batch_size=512):
    import torch
    from train_utils import make_loader
    model.eval()
    preds, yt = [], []
    with torch.no_grad():
        for xb, yb in make_loader(X, y, batch_size, False):
            out = model(xb.to(device)).argmax(1).cpu().numpy() + 1
            preds.append(out); yt.append(yb)
    return np.concatenate(preds), np.concatenate(yt) + 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', default='0,1,2')
    ap.add_argument('--epochs', type=int, default=100)
    ap.add_argument('--device', default=os.environ.get('DEVICE', 'cpu'))
    ap.add_argument('--data-dir', default=DATA_DIR)
    args = ap.parse_args()
    device = args.device
    if device == 'cuda' and not __import__('torch').cuda.is_available():
        print('CUDA requested but unavailable -> falling back to cpu')
        device = 'cpu'

    os.makedirs(RESULTS_DIR, exist_ok=True)
    seed0 = int(args.seeds.split(',')[0])
    X_train, y_train, X_test, y_test, meta, raw = preprocess(args.data_dir)
    print(f'[data] train={X_train.shape} test={X_test.shape}')
    print(f'[data] PCA components keep {meta["n_components_variance"]:.3%} variance')

    results = []
    for seed in [int(s) for s in args.seeds.split(',')]:
        model = HybridSN(n_bands=N_PCA_BANDS, n_classes=16, dropout=0.5)
        print(f'[HybridSN] params={count_params(model):,}')
        ckpt, hist, elapsed = train_cnn(
            model, X_train, y_train, X_test, y_test,
            epochs=args.epochs, lr=LR, weight_decay=WEIGHT_DECAY,
            batch_size=BATCH_SIZE, seed=seed, device=device,
            model_name=f'hybridsn', ckpt_dir=os.path.join(RESULTS_DIR, 'checkpoints'))
        model.load_state_dict(torch.load(ckpt, map_location='cpu')['state_dict'])
        preds, yt = predict_all(model.to(device), X_test, y_test, device)
        m = compute_metrics(yt, preds, n_classes=16)
        res = {'method': 'HybridSN', 'seed': seed, 'train_ratio': meta['n_train'] / (meta['n_train'] + meta['n_test']),
               'window': WINDOW, 'bands': N_PCA_BANDS, 'epochs': len(hist['train_loss']),
               'elapsed_s': elapsed, **m}
        results.append(res)
        save_metrics('HybridSN', m, {'seed': seed, 'train_ratio': res['train_ratio'],
                                     'window': WINDOW}, out_dir=RESULTS_DIR)
        print(f'[HybridSN seed={seed}] OA={m["overall_accuracy"]:.4f} '
              f'AA={m["average_accuracy"]:.4f} Kappa={m["kappa"]:.4f}')

    # aggregate across seeds -> mean +/- std
    oas = [r['overall_accuracy'] for r in results]
    aas = [r['average_accuracy'] for r in results]
    kaps = [r['kappa'] for r in results]
    agg = {
        'method': 'HybridSN', 'seeds': [int(s) for s in args.seeds.split(',')],
        'train_ratio': meta['n_train'] / (meta['n_train'] + meta['n_test']),
        'window': WINDOW, 'epochs': args.epochs,
        'OA_mean': float(np.mean(oas)), 'OA_std': float(np.std(oas)),
        'AA_mean': float(np.mean(aas)), 'AA_std': float(np.std(aas)),
        'Kappa_mean': float(np.mean(kaps)), 'Kappa_std': float(np.std(kaps)),
    }
    with open(os.path.join(RESULTS_DIR, 'hybridsn_aggregate.json'), 'w') as f:
        json.dump(agg, f, indent=2, sort_keys=True)
    print('[aggregate] mean OA %.4f +/- %.4f | AA %.4f +/- %.4f | Kappa %.4f +/- %.4f'
          % (agg['OA_mean'], agg['OA_std'], agg['AA_mean'], agg['AA_std'],
             agg['Kappa_mean'], agg['Kappa_std']))


if __name__ == '__main__':
    main()