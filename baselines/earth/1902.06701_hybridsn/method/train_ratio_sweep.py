"""Q3: training-ratio sensitivity experiment.

Runs the HybridSN classifier (and the 2D-CNN baseline) under 10% / 30% / 70%
training protocols (paper protocol applies fixed-seed overall-random splits) and
reports OA / AA / Kappa per ratio.

Usage:
    python method/train_ratio_sweep.py --ratios 10,30,70 --epochs 60 --device cuda
"""
import argparse
import json
import os
import sys
import numpy as np
import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import (DATA_DIR, RESULTS_DIR, N_PCA_BANDS, BATCH_SIZE, LR, WEIGHT_DECAY,
                    SEEDS, WINDOW)
from data_utils import load_data, load_split, extract_patch
from models import HybridSN, CNN2D
from metrics import compute_metrics
from train_utils import train_cnn, make_loader


def build_arrays(gt, pixels, labels, train_idx, test_idx, Xp, window=WINDOW):
    half = window // 2
    H, W = gt.shape
    pad = np.zeros((H + 2 * half, W + 2 * half, Xp.shape[2]))
    pad[half:half + H, half:half + W] = Xp

    def pat(px):
        rr, cc = px[:, 0] + half, px[:, 1] + half
        out = np.stack([pad[r - half:r + half + 1, c - half:c + half + 1]
                        for r, c in zip(rr, cc)])
        return out.transpose(0, 3, 1, 2).astype(np.float32)

    return pat(pixels[train_idx]), labels[train_idx], \
        pat(pixels[test_idx]), labels[test_idx]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--ratios', default='10,30,70')
    ap.add_argument('--epochs', type=int, default=60)
    ap.add_argument('--device', default=os.environ.get('DEVICE', 'cpu'))
    ap.add_argument('--data-dir', default=DATA_DIR)
    args = ap.parse_args()
    device = args.device
    if device == 'cuda' and not torch.cuda.is_available():
        device = 'cpu'

    os.makedirs(RESULTS_DIR, exist_ok=True)
    image, gt = load_data(args.data_dir)

    from sklearn.decomposition import PCA
    sweep = {}
    for ratio in [int(r) for r in args.ratios.split(',')]:
        res_row = {'ratio_pct': ratio}
        seed0 = SEEDS[0]
        pixels, labels, tr_idx, te_idx = load_split(seed0, ratio / 100.0)
        # preprocessing fitted on training pixels only (per ratio)
        from sklearn.preprocessing import StandardScaler
        X_tr_pix = image[pixels[tr_idx][:, 0], pixels[tr_idx][:, 1]]
        pca = PCA(n_components=N_PCA_BANDS).fit(X_tr_pix)
        Xp = pca.transform(image.reshape(-1, image.shape[2])).reshape(
            image.shape[0], image.shape[1], N_PCA_BANDS)
        sc = StandardScaler().fit(pca.transform(X_tr_pix))
        Xp = sc.transform(Xp.reshape(-1, N_PCA_BANDS)).reshape(*Xp.shape)

        Xtr, ytr, Xte, yte = build_arrays(gt, pixels, labels, tr_idx, te_idx, Xp)
        print(f'[ratio={ratio}%] train={len(Xtr)} test={len(Xte)}')

        records = {}
        for name, cls in [('HybridSN', HybridSN), ('CNN2D', CNN2D)]:
            model = cls(n_bands=N_PCA_BANDS, n_classes=16)
            ckpt, hist, _ = train_cnn(
                model, Xtr, ytr, Xte, yte, epochs=args.epochs, lr=LR,
                weight_decay=WEIGHT_DECAY, batch_size=BATCH_SIZE, seed=seed0,
                device=device, model_name=f'{name.lower()}_r{ratio}',
                ckpt_dir=os.path.join(RESULTS_DIR, 'checkpoints'))
            model.load_state_dict(torch.load(ckpt, map_location='cpu')['state_dict'])
            model = model.to(device); model.eval()
            preds, y_hat = [], []
            with torch.no_grad():
                for xb, yb in make_loader(Xte, yte, 256, False):
                    out = model(xb.to(device)).argmax(1).cpu().numpy() + 1
                    preds.append(out); y_hat.append(yb)
            y_hat = np.concatenate(y_hat) + 1
            m = compute_metrics(y_hat, np.concatenate(preds), n_classes=16)
            records[name] = {k: m[k] for k in ('overall_accuracy', 'average_accuracy', 'kappa')}
            print(f'  [{name}] ratio={ratio}% OA={m["overall_accuracy"]:.4f} '
                  f'AA={m["average_accuracy"]:.4f} K={m["kappa"]:.4f}')
        res_row.update(records)
        res_row['n_train'] = len(Xtr); res_row['n_test'] = len(Xte)
        sweep[str(ratio)] = res_row

    with open(os.path.join(RESULTS_DIR, 'ratio_sweep.json'), 'w') as f:
        json.dump(sweep, f, indent=2, sort_keys=True)
    print('ratio_sweep.json saved:', sweep)


if __name__ == '__main__':
    main()