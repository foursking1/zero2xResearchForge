"""Data loading and preprocessing for Indian Pines.

Pipeline (mirrors the paper's preprocessing):
  1. Load Indian_pines_corrected.mat (145x145x200) and Indian_pines_gt.mat.
  2. Keep only labeled pixels (gt > 0). PCA (30 components) is fitted on the
     TRAINING subset only   <-- no information leakage into training statistics.
  3. Per-band standardization (mean/std) also computed on training pixels only.
  4. For every labeled pixel, extract a 25x25 patch centered on the pixel
     (zero-padded at image borders) from the PCA-reduced, standardized image.

The 30/70 split comes from protocols/split_data.py (fixed seeds).
"""
import os
import numpy as np
from scipy.io import loadmat
from sklearn.decomposition import PCA

from config import N_PCA_BANDS, WINDOW, SPLIT_DIR


def load_data(data_dir):
    """Returns corrected image (145,145,200) and gt (145,145)."""
    img = loadmat(os.path.join(data_dir, 'Indian_pines_corrected.mat'))
    ik = [k for k in img if not k.startswith('__')][0]
    image = img[ik].astype(np.float64)
    gt = loadmat(os.path.join(data_dir, 'Indian_pines_gt.mat'))
    gk = [k for k in gt if not k.startswith('__')][0]
    gt_arr = gt[gk].astype(int)
    return image, gt_arr


def load_split(seed, ratio=0.3):
    path = os.path.join(SPLIT_DIR, f'split_seed{seed}_r{int(ratio * 100)}.npz')
    d = np.load(path)
    return d['pixels'], d['labels'], d['train_idx'], d['test_idx']


def extract_patch(img, r, c, window=WINDOW):
    """Zero-padded (window x window) patch centered at (r, c)."""
    H, W = img.shape[0], img.shape[1]
    half = window // 2
    patch = np.zeros((window, window, img.shape[2]), dtype=img.dtype)
    r_s, r_e = max(0, r - half), min(H, r + half + 1)
    c_s, c_e = max(0, c - half), min(W, c + half + 1)
    patch[r_s - (r - half): r_e - (r - half),
          c_s - (c - half): c_e - (c - half)] = img[r_s:r_e, c_s:c_e]
    return patch


def preprocess(data_dir):
    """Build (X_patch_train, y_train, X_patch_test, y_test, meta) with all
    statistics fitted on the training subset only."""
    image, gt = load_data(data_dir)
    pixels, labels, train_idx, test_idx = load_split(meta_seed(), TRAIN_RATIO())

    X_all = image.reshape(-1, image.shape[2])       # (21025, 200)
    tr_pix = pixels[train_idx]
    X_tr_pix = image[tr_pix[:, 0], tr_pix[:, 1]]    # training pixels only

    pca = PCA(n_components=N_PCA_BANDS, whiten=False)
    pca.fit(X_tr_pix)
    X_all_pca = pca.transform(X_all).reshape(image.shape[0], image.shape[1], N_PCA_BANDS)
    X_tr_pca = pca.transform(X_tr_pix)

    # per-band standardization using TRAINING statistics (on the reduced features)
    mean = X_tr_pca.mean(axis=0); std = X_tr_pca.std(axis=0) + 1e-8
    Xp = (X_all_pca - mean) / std

    H, W = Xp.shape[0], Xp.shape[1]
    # pad image for vectorized patch extraction
    half = WINDOW // 2
    padded = np.zeros((H + 2 * half, W + 2 * half, N_PCA_BANDS))
    padded[half:half + H, half:half + W] = Xp

    def patches(px):
        rr, cc = px[:, 0] + half, px[:, 1] + half
        out = np.stack([padded[r - half:r + half + 1, c - half:c + half + 1]
                        for r, c in zip(rr, cc)])
        return out.transpose(0, 3, 1, 2).astype(np.float32)   # (N, bands, H, W)

    X_train = patches(pixels[train_idx])
    y_train = labels[train_idx]
    X_test = patches(pixels[test_idx])
    y_test = labels[test_idx]
    meta = {
        'n_bands': N_PCA_BANDS, 'window': WINDOW,
        'n_train': len(train_idx), 'n_test': len(test_idx),
        'n_components_variance': float(pca.explained_variance_ratio_.sum()),
    }
    return X_train, y_train, X_test, y_test, meta, (image, gt, pixels, labels)


def TRAIN_RATIO():
    import config
    return config.TRAIN_RATIO


def meta_seed():
    import config
    return config.SEEDS[0]