"""Train & evaluate the 2D-CNN baseline on Indian Pines (same protocol as HybridSN)."""
import argparse
import json
import os
import sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import DATA_DIR, RESULTS_DIR, WINDOW, N_PCA_BANDS, BATCH_SIZE, LR, WEIGHT_DECAY
from data_utils import preprocess
from models import CNN2D, count_params
from metrics import compute_metrics, save_metrics
from train_utils import train_cnn


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', default='0,1,2')
    ap.add_argument('--epochs', type=int, default=100)
    ap.add_argument('--device', default=os.environ.get('DEVICE', 'cpu'))
    ap.add_argument('--data-dir', default=DATA_DIR)
    args = ap.parse_args()
    device = args.device
    if device == 'cuda' and not __import__('torch').cuda.is_available():
        print('CUDA unavailable -> cpu'); device = 'cpu'

    os.makedirs(RESULTS_DIR, exist_ok=True)
    X_train, y_train, X_test, y_test, meta, _ = preprocess(args.data_dir)

    results = []
    for seed in [int(s) for s in args.seeds.split(',')]:
        model = CNN2D(n_bands=N_PCA_BANDS, n_classes=16, dropout=0.5)
        print(f'[CNN2D] params={count_params(model):,}')
        ckpt, hist, elapsed = train_cnn(
            model, X_train, y_train, X_test, y_test,
            epochs=args.epochs, lr=LR, weight_decay=WEIGHT_DECAY,
            batch_size=BATCH_SIZE, seed=seed, device=device,
            model_name='cnn2d', ckpt_dir=os.path.join(RESULTS_DIR, 'checkpoints'))
        model.load_state_dict(torch_state(ckpt)['state_dict'])
        preds, yt = predict_loader(model, X_test, y_test, device)
        m = compute_metrics(yt, preds, n_classes=16)
        res = {'method': 'CNN2D', 'seed': seed,
               'train_ratio': meta['n_train'] / (meta['n_train'] + meta['n_test']),
               'window': WINDOW, 'elapsed_s': elapsed, **m}
        results.append(res)
        save_metrics('CNN2D', m, {'seed': seed, 'train_ratio': res['train_ratio'],
                                  'window': WINDOW}, out_dir=RESULTS_DIR)
        print(f'[CNN2D seed={seed}] OA={m["overall_accuracy"]:.4f} '
              f'AA={m["average_accuracy"]:.4f} Kappa={m["kappa"]:.4f}')

    oas = [r['overall_accuracy'] for r in results]
    aas = [r['average_accuracy'] for r in results]
    kaps = [r['kappa'] for r in results]
    agg = {'method': 'CNN2D', 'seeds': [int(s) for s in args.seeds.split(',')],
           'train_ratio': meta['n_train'] / (meta['n_train'] + meta['n_test']),
           'window': WINDOW,
           'OA_mean': float(np.mean(oas)), 'OA_std': float(np.std(oas)),
           'AA_mean': float(np.mean(aas)), 'AA_std': float(np.std(aas)),
           'Kappa_mean': float(np.mean(kaps)), 'Kappa_std': float(np.std(kaps))}
    with open(os.path.join(RESULTS_DIR, 'cnn2d_aggregate.json'), 'w') as f:
        json.dump(agg, f, indent=2, sort_keys=True)
    print('[aggregate] mean OA %.4f +/- %.4f' % (agg['OA_mean'], agg['OA_std']))


def torch_state(path):
    import torch
    return torch.load(path, map_location='cpu')


def predict_loader(model, X, y, device, batch_size=512):
    import torch
    from train_utils import make_loader
    model = model.to(device); model.eval()
    preds, yt = [], []
    with torch.no_grad():
        for xb, yb in make_loader(X, y, batch_size, False):
            out = model(xb.to(device)).argmax(1).cpu().numpy() + 1
            preds.append(out); yt.append(yb)
    return np.concatenate(preds), np.concatenate(yt) + 1


if __name__ == '__main__':
    main()