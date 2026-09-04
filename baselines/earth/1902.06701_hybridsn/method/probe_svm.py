"""Probe SVM preprocessing/params variants on seed-0 split to better match the
paper's reported SVM baseline (91.70 +/- 1.1 on IP, RBF)."""
import os, sys, time
import numpy as np
from scipy.io import loadmat
from sklearn.svm import SVC
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split, StratifiedKFold, GridSearchCV

data_dir = '/mnt/d/project/paper-bench/tasks/earth/1902.06701_hybridsn/data'
results = '/mnt/d/project/paper-bench/tasks/earth/1902.06701_hybridsn/agent_solution/results'

img = loadmat(os.path.join(data_dir, 'Indian_pines_corrected.mat'))
ik = [k for k in img if not k.startswith('__')][0]
image = img[ik].astype(np.float64)
gt = loadmat(os.path.join(data_dir, 'Indian_pines_gt.mat'))
gk = [k for k in gt if not k.startswith('__')][0]
gt_arr = gt[gk].astype(int)

d = np.load(os.path.join(results, 'splits', 'split_seed0_r30.npz'))
pixels, train_idx, test_idx = d['pixels'], d['train_idx'], d['test_idx']
X = image[pixels[:, 0], pixels[:, 1]]
y = gt_arr[pixels[:, 0], pixels[:, 1]]
Xtr, ytr, Xte, yte = X[train_idx], y[train_idx], X[test_idx], y[test_idx]
print('train/test', len(Xtr), len(Xte))

configs = {}
# A: PCA30 + standardize, big C/gamma
for name, n_comp, std in [('a_pca30_std', 30, True), ('b_pca30_std_full200', 200, True),
                           ('c_pca8_std', 8, True), ('d_pca30_raw', 30, False),
                           ('e_pca12_std', 12, True)]:
    pca = PCA(n_components=None if n_comp == 200 else n_comp).fit(Xtr)
    Xtr_p, Xte_p = pca.transform(Xtr), pca.transform(Xte)
    if std:
        sc = StandardScaler().fit(Xtr_p); Xtr_p, Xte_p = sc.transform(Xtr_p), sc.transform(Xte_p)
    grid = {'C': [1e2, 1e3, 1e4, 1e5, 1e6], 'gamma': [0.001, 0.005, 0.01, 0.03, 0.1, 0.3, 1.0]}
    svc = SVC(kernel='rbf', cache_size=300)
    gs = GridSearchCV(svc, grid, cv=StratifiedKFold(3), scoring='accuracy', n_jobs=14)
    t0 = time.time()
    gs.fit(Xtr_p, ytr)
    oa = gs.score(Xte_p, yte)
    print(f'{name}: best={gs.best_params_} trainOA={gs.best_score_:.4f} testOA={oa:.4f} ({time.time()-t0:.0f}s)')