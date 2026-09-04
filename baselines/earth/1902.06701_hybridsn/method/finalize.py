"""Post-training finalization.

Builds the required deliverables from the trained checkpoints:
  - results/evidence_table.csv  (per-class accuracy rows + overall OA/AA/Kappa rows)
  - results/metrics.json        (overall_accuracy, average_accuracy, kappa, train_ratio,
                                 seed, window_size)
  - evidence/classification_maps.png   (GT vs HybridSN prediction over labeled pixels)
  - evidence/training_curves.png       (train loss / test OA curves)

Usage: python method/finalize.py --device cpu
"""
import argparse
import csv
import json
import os
import sys
import numpy as np
import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import DATA_DIR, RESULTS_DIR, N_PCA_BANDS, SEEDS, WINDOW, TRAIN_RATIO
from data_utils import preprocess, load_split
from models import HybridSN
from metrics import compute_metrics
from train_utils import make_loader
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--device', default='cpu')
    ap.add_argument('--data-dir', default=DATA_DIR)
    args = ap.parse_args()
    device = args.device
    if device == 'cuda' and not torch.cuda.is_available():
        device = 'cpu'

    evidence_dir = os.path.abspath(os.path.join(RESULTS_DIR, '..', 'evidence'))
    os.makedirs(evidence_dir, exist_ok=True)

    X_train, y_train, X_test, y_test, meta, raw = preprocess(args.data_dir)
    image, gt, pixels, labels = raw
    n_train = meta['n_train']; n_test = meta['n_test']
    ratio = meta['n_train'] / (meta['n_train'] + meta['n_test'])
    print(f'[finalize] train={n_train} test={n_test} ratio={ratio:.4f}')

    # ---- evaluate all seeds ----
    seed_results = {}
    for seed in SEEDS:
        ckpt = os.path.join(RESULTS_DIR, 'checkpoints', f'hybridsn_seed{seed}.pt')
        model = HybridSN(n_bands=N_PCA_BANDS, n_classes=16)
        model.load_state_dict(torch.load(ckpt, map_location='cpu')['state_dict'])
        model = model.to(device); model.eval()
        preds, yt = [], []
        with torch.no_grad():
            for xb, yb in make_loader(X_test, y_test, 256, False):
                out = model(xb.to(device)).argmax(1).cpu().numpy() + 1
                preds.append(out); yt.append(yb)
        yt = np.concatenate(yt) + 1
        preds = np.concatenate(preds)
        m = compute_metrics(yt, preds, n_classes=16)
        m['seed'] = seed
        seed_results[seed] = m
        print(f'[finalize seed={seed}] OA={m["overall_accuracy"]:.4f} '
              f'AA={m["average_accuracy"]:.4f} Kappa={m["kappa"]:.4f}')

    oas = [seed_results[s]['overall_accuracy'] for s in SEEDS]
    aas = [seed_results[s]['average_accuracy'] for s in SEEDS]
    kaps = [seed_results[s]['kappa'] for s in SEEDS]

    # ---- metrics.json (task requirement) ----
    metrics = {
        'overall_accuracy': float(np.mean(oas)),
        'overall_accuracy_std': float(np.std(oas)),
        'average_accuracy': float(np.mean(aas)),
        'average_accuracy_std': float(np.std(aas)),
        'kappa': float(np.mean(kaps)),
        'kappa_std': float(np.std(kaps)),
        'overall_accuracy_seed0': float(oas[0]),
        'train_ratio': float(ratio),
        'seed': SEEDS,
        'window_size': WINDOW,
        'n_train': n_train,
        'n_test': n_test,
        'method': 'HybridSN (3D-2D CNN)',
        'paper_anchor_OA': 99.75,
    }
    with open(os.path.join(RESULTS_DIR, 'metrics.json'), 'w') as f:
        json.dump(metrics, f, indent=2, sort_keys=True)
    print('[finalize] wrote metrics.json')

    # merge baseline aggregates into metrics.json (informative extras)
    try:
        for tag, name in [('cnn2d_aggregate', 'CNN2D_baseline'),
                          ('svm_aggregate', 'SVM_RBF_baseline')]:
            p = os.path.join(RESULTS_DIR, f'{tag}.json')
            if os.path.exists(p):
                agg = json.load(open(p))
                metrics[f'{name}_OA'] = agg['OA_mean']
                metrics[f'{name}_AA'] = agg.get('AA_mean')
                metrics[f'{name}_Kappa'] = agg.get('Kappa_mean')
        with open(os.path.join(RESULTS_DIR, 'metrics.json'), 'w') as f:
            json.dump(metrics, f, indent=2, sort_keys=True)
    except Exception as e:
        print('[finalize] warning: baseline merge skipped:', e)

    # ---- evidence_table.csv ----
    cols = ['method', 'seed', 'train_ratio', 'window', 'class', 'n_test', 'accuracy']
    rows = []
    for seed in SEEDS:
        pc = seed_results[seed]['per_class']
        for c in sorted(pc, key=lambda k: int(k)):
            rows.append({'method': 'HybridSN', 'seed': seed, 'train_ratio': ratio,
                         'window': WINDOW, 'class': c, 'n_test': pc[c]['n_test'],
                         'accuracy': pc[c]['accuracy']})
        rows.append({'method': 'HybridSN', 'seed': seed, 'train_ratio': ratio,
                     'window': WINDOW, 'class': 'OA', 'n_test': n_test,
                     'accuracy': m_of(seed_results[seed], 'overall_accuracy')})
        rows.append({'method': 'HybridSN', 'seed': seed, 'train_ratio': ratio,
                     'window': WINDOW, 'class': 'AA', 'n_test': n_test,
                     'accuracy': m_of(seed_results[seed], 'average_accuracy')})
        rows.append({'method': 'HybridSN', 'seed': seed, 'train_ratio': ratio,
                     'window': WINDOW, 'class': 'Kappa', 'n_test': n_test,
                     'accuracy': m_of(seed_results[seed], 'kappa')})
    for key, val in [('OA', np.mean(oas)), ('AA', np.mean(aas)), ('Kappa', np.mean(kaps))]:
        rows.append({'method': 'HybridSN (mean, 3 seeds)', 'seed': 'mean',
                     'train_ratio': ratio, 'window': WINDOW, 'class': key,
                     'n_test': n_test, 'accuracy': float(val)})
    csv_path = os.path.join(RESULTS_DIR, 'evidence_table.csv')
    with open(csv_path, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    print('[finalize] wrote', csv_path)

    # ---- classification map (representative seed = SEEDS[1]) ----
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap

    rep = SEEDS[1]
    ckpt = os.path.join(RESULTS_DIR, 'checkpoints', f'hybridsn_seed{rep}.pt')
    model = HybridSN(n_bands=N_PCA_BANDS, n_classes=16)
    model.load_state_dict(torch.load(ckpt, map_location='cpu')['state_dict'])
    model = model.to(device); model.eval()

    Xall, yall = all_labeled_patches(args.data_dir)
    preds_list = []
    with torch.no_grad():
        for xb, _ in make_loader(Xall, yall, 512, False):
            out = model(xb.to(device)).softmax(1).argmax(1).cpu().numpy() + 1
            preds_list.append(out)
    preds_all = np.zeros(gt.shape, dtype=np.uint8)
    labeled_rc = pixels
    preds_all[labeled_rc[:, 0], labeled_rc[:, 1]] = np.concatenate(preds_list)

    cmap = ListedColormap(np.vstack([[0.95, 0.95, 0.95, 1.0], plt.cm.tab20(np.arange(16))]))
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.6))
    axes[0].imshow(gt, cmap=cmap, interpolation='nearest')
    axes[0].set_title('Ground truth')
    axes[1].imshow(preds_all, cmap=cmap, interpolation='nearest')
    axes[1].set_title(f'HybridSN prediction (seed={rep})')
    corr = np.ones_like(gt) * np.nan
    corr[gt > 0] = (preds_all[gt > 0] == gt[gt > 0]).astype(float)
    axes[2].imshow(corr, cmap='RdYlGn', interpolation='nearest', vmin=0, vmax=1)
    axes[2].set_title('Per-pixel correctness (green=correct, red=wrong)')
    for a in axes:
        a.set_xticks([]); a.set_yticks([])
    fig.tight_layout()
    fig.savefig(os.path.join(evidence_dir, 'classification_maps.png'), dpi=150)
    plt.close(fig)
    print('[finalize] wrote', os.path.join(evidence_dir, 'classification_maps.png'))

    # ---- training curves (seed 0) ----
    hist_path = os.path.join(RESULTS_DIR, 'history_hybridsn_seed0.npz')
    if os.path.exists(hist_path):
        h = np.load(hist_path)
        fig, ax = plt.subplots(1, 2, figsize=(9, 3.4))
        ax[0].plot(h['train_loss'])
        ax[0].set_title('Training loss (seed 0)'); ax[0].set_xlabel('epoch')
        ax[1].plot(h['test_oa'])
        ax[1].set_title('Test OA (seed 0)'); ax[1].set_xlabel('epoch')
        fig.tight_layout()
        fig.savefig(os.path.join(evidence_dir, 'training_curves.png'), dpi=120)
        plt.close(fig)
        print('[finalize] wrote', os.path.join(evidence_dir, 'training_curves.png'))

    # ---- split counts figure (30% protocol) ----
    _, _, tr_idx, te_idx = load_split(SEEDS[0], TRAIN_RATIO)
    tr_cnt = np.bincount(labels[tr_idx], minlength=17)
    te_cnt = np.bincount(labels[te_idx], minlength=17)
    fig, ax = plt.subplots(figsize=(7, 3.6))
    x = np.arange(1, 17)
    ax.bar(x - 0.2, tr_cnt[1:], 0.4, label='train (30%)')
    ax.bar(x + 0.2, te_cnt[1:], 0.4, label='test (70%)')
    ax.set_xticks(x); ax.set_ylabel('# pixels'); ax.set_xlabel('class')
    ax.legend(); ax.set_title('Per-class train/test counts, seed=0, 30/70 split')
    fig.tight_layout()
    fig.savefig(os.path.join(evidence_dir, 'split_counts.png'), dpi=120)
    plt.close(fig)
    print('[finalize] wrote', os.path.join(evidence_dir, 'split_counts.png'))

    print('[finalize] DONE. mean OA=%.4f±%.4f AA=%.4f Kappa=%.4f'
          % (np.mean(oas), np.std(oas), np.mean(aas), np.mean(kaps)))


def m_of(rec, key):
    return rec[key]


def all_labeled_patches(data_dir):
    """25x25 patches for every labeled pixel using seed-0 preprocessing stats."""
    image, gt, pixels, labels = load_raw(data_dir)
    _, _, tr_idx, _ = load_split(SEEDS[0], TRAIN_RATIO)
    X_tr_pix = image[pixels[tr_idx][:, 0], pixels[tr_idx][:, 1]]
    pca = PCA(n_components=N_PCA_BANDS).fit(X_tr_pix)
    Xp = pca.transform(image.reshape(-1, image.shape[2])).reshape(*image.shape[:2], N_PCA_BANDS)
    sc = StandardScaler().fit(pca.transform(X_tr_pix))
    Xp = sc.transform(Xp.reshape(-1, N_PCA_BANDS)).reshape(*Xp.shape)
    from data_utils import extract_patch
    pat = np.stack([extract_patch(Xp, r, c) for r, c in zip(pixels[:, 0], pixels[:, 1])])
    return pat.transpose(0, 3, 1, 2).astype(np.float32), labels


def load_raw(data_dir):
    from data_utils import load_data, load_split
    image, gt = load_data(data_dir)
    pixels, labels, _, _ = load_split(SEEDS[0], TRAIN_RATIO)
    return image, gt, pixels, labels


if __name__ == '__main__':
    main()