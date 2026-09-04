"""SVM (RBF) baseline — spectral pixel-wise classifier, HybridSN Table II baseline (SVM 91.70±1.1).

Statistics (PCA fit + z-score) fitted on training pixels only.
Grid search over C & gamma on a stratified CV of the training set, then final eval on the held-out test set.
"""
import argparse
import json
import os
import sys
import numpy as np
from sklearn.svm import SVC
from sklearn.model_selection import GridSearchCV, StratifiedKFold, cross_val_score
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from scipy.io import loadmat

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import DATA_DIR, RESULTS_DIR, N_PCA_BANDS
from metrics import compute_metrics, save_metrics


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', default='0,1,2')
    ap.add_argument('--data-dir', default=DATA_DIR)
    args = ap.parse_args()

    os.makedirs(RESULTS_DIR, exist_ok=True)
    data_dir = args.data_dir
    img = loadmat(os.path.join(data_dir, 'Indian_pines_corrected.mat'))
    ik = [k for k in img if not k.startswith('__')][0]
    image = img[ik].astype(np.float64)
    gt = loadmat(os.path.join(data_dir, 'Indian_pines_gt.mat'))
    gk = [k for k in gt if not k.startswith('__')][0]
    gt_arr = gt[gk].astype(int)

    results = []
    for seed in [int(s) for s in args.seeds.split(',')]:
        d = np.load(os.path.join(RESULTS_DIR, 'splits', f'split_seed{seed}_r30.npz'))
        pixels = d['pixels']; train_idx = d['train_idx']; test_idx = d['test_idx']
        X = image[pixels[:, 0], pixels[:, 1]]                     # pixel spectra (10249, 200)
        y = gt_arr[pixels[:, 0], pixels[:, 1]]
        Xtr, ytr = X[train_idx], y[train_idx]
        Xte, yte = X[test_idx], y[test_idx]

        pca = PCA(n_components=N_PCA_BANDS).fit(Xtr)
        Xtr_p = pca.transform(Xtr); Xte_p = pca.transform(Xte)
        sc = StandardScaler().fit(Xtr_p)
        Xtr_s, Xte_s = sc.transform(Xtr_p), sc.transform(Xte_p)
        print(f'[SVM seed={seed}] train={len(Xtr_s)} test={len(Xte_s)}')

        svc = SVC(kernel='rbf', cache_size=400)
        grid = GridSearchCV(svc, {'C': [1e2, 1e3, 1e4, 5e4, 1e5],
                                  'gamma': [0.005, 0.01, 0.03, 0.1, 'scale']},
                            cv=StratifiedKFold(5), scoring='accuracy', n_jobs=14, verbose=0)
        grid.fit(Xtr_s, ytr)
        print(f'[SVM seed={seed}] best C={grid.best_params_} cv_OA={grid.best_score_:.4f}')

        preds = grid.predict(Xte_s)
        m = compute_metrics(yte, preds, n_classes=16)
        res = {'method': 'SVM_RBF', 'seed': seed,
               'train_ratio': len(Xtr) / (len(Xtr) + len(Xte)),
               'window': 1, 'n_pca': N_PCA_BANDS, 'best_params': grid.best_params_, **m}
        results.append(res)
        save_metrics('SVM_RBF', m, {'seed': seed, 'train_ratio': res['train_ratio'],
                                    'best_params': grid.best_params_}, out_dir=RESULTS_DIR)
        print(f'[SVM seed={seed}] OA={m["overall_accuracy"]:.4f} '
              f'AA={m["average_accuracy"]:.4f} Kappa={m["kappa"]:.4f}')

    oas = [r['overall_accuracy'] for r in results]
    aas = [r['average_accuracy'] for r in results]
    kaps = [r['kappa'] for r in results]
    agg = {'method': 'SVM_RBF', 'seeds': [int(s) for s in args.seeds.split(',')],
           'OA_mean': float(np.mean(oas)), 'OA_std': float(np.std(oas)),
           'AA_mean': float(np.mean(aas)), 'AA_std': float(np.std(aas)),
           'Kappa_mean': float(np.mean(kaps)), 'Kappa_std': float(np.std(kaps))}
    with open(os.path.join(RESULTS_DIR, 'svm_aggregate.json'), 'w') as f:
        json.dump(agg, f, indent=2, sort_keys=True)
    print('[aggregate] mean OA %.4f +/- %.4f | AA %.4f +/- %.4f | Kappa %.4f +/- %.4f'
          % (agg['OA_mean'], agg['OA_std'], agg['AA_mean'], agg['AA_std'],
             agg['Kappa_mean'], agg['Kappa_std']))


if __name__ == '__main__':
    main()