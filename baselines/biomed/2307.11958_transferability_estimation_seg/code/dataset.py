"""dataset.py -- torch Dataset over the cached 2-D slices with augmentation."""
import os
import sys
import numpy as np
import torch
from torch.utils.data import Dataset

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import CACHE_DIR, SPLITS, from_uint8

TORCH_DEVICE = torch.device("cpu")


class SliceDataset(Dataset):
    def __init__(self, organ, cases, max_slices=None, seed=0, augment=False, size=None, fg_only=False):
        xs, ys = [], []
        for c in cases:
            npz = os.path.join(CACHE_DIR, f"{organ}_{c}.npz")
            img = np.load(npz)["img"]
            lab = np.load(npz)["lab"]
            if fg_only:  # keep only slices that contain the organ (source pretraining)
                keep = lab.sum(axis=(1, 2)) > 0
                img, lab = img[keep], lab[keep]
            if max_slices is not None and img.shape[0] > max_slices:
                rng = np.random.RandomState(seed + hash(c) % 1000)
                pick = rng.choice(img.shape[0], max_slices, replace=False)
                img, lab = img[pick], lab[pick]
            if len(img) == 0:
                continue
            xs.append(img)
            ys.append(lab)
        self.images = np.concatenate(xs).astype(np.float32) / 255.0
        self.labels = (np.concatenate(ys) > 0).astype(np.float32)
        self.size = size
        if size is not None:
            self.images = np.array([cv_resize(i, size, 1) for i in self.images]).astype(np.float32)
            self.labels = np.array([cv_resize(i, size, 0) for i in self.labels]).astype(np.float32)
        self.augment = augment
        self.seed = seed

    def __len__(self):
        return len(self.images)

    def __getitem__(self, i):
        x = self.images[i][None]
        y = self.labels[i][None]
        if self.augment:
            # deterministic seed per index for reproducibility
            rng = np.random.RandomState(self.seed * 100000 + i)
            if rng.rand() < 0.5:
                x = x[:, ::-1]
                y = y[:, ::-1]
            if rng.rand() < 0.5:
                x = x[:, :, ::-1]
                y = y[:, :, ::-1]
            if rng.rand() < 0.4:  # random shift up to 12px
                sh = int(rng.uniform(-12, 12))
                sw = int(rng.uniform(-12, 12))
                x, y = _shift(x, y, sh, sw)
            if rng.rand() < 0.3:  # mild gaussian noise
                x = (x + rng.randn(*x.shape) * 0.02).astype(np.float32)
        return torch.from_numpy(np.ascontiguousarray(x, dtype=np.float32)), torch.from_numpy(np.ascontiguousarray(y, dtype=np.float32))


def _shift(x, y, dh, dw):
    ph, pw = abs(dh), abs(dw)
    x = np.pad(x, ((0, 0), (ph, ph), (pw, pw)), mode="constant")
    y = np.pad(y, ((0, 0), (ph, ph), (pw, pw)), mode="constant")
    y0 = ph - dh if dh > 0 else ph  # slice start; shift content opposite to pad
    x0 = pw - dw if dw > 0 else pw
    return x[:, y0:y0 + x.shape[1] - 2 * ph, x0:x0 + x.shape[2] - 2 * pw], \
           y[:, y0:y0 + y.shape[1] - 2 * ph, x0:x0 + y.shape[2] - 2 * pw]


def cv_resize(im, size, order):
    from scipy import ndimage
    return ndimage.zoom(im, (size / im.shape[0], size / im.shape[1]), order=order)


def make_loader(organ, cases, batch_size, shuffle=True, seed=0, max_slices=None, augment=False, size=None, fg_only=False):
    ds = SliceDataset(organ, cases, max_slices=max_slices, seed=seed, augment=augment, size=size, fg_only=fg_only)
    g = torch.Generator().manual_seed(seed)
    return torch.utils.data.DataLoader(ds, batch_size=batch_size, shuffle=shuffle, generator=g)


def get_train_test_cases(organ):
    return SPLITS[organ][0], SPLITS[organ][1]