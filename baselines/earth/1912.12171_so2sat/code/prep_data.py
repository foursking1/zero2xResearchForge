"""Pre-processing of the frozen So2Sat validation.h5 into train/eval numpy arrays.

Splits the official validation split (24,119 samples) 80/20 (stratified, fixed
seed) into train/eval subsets, since the paper's ~380k-patch training split is
NOT frozen for this task. All normalization statistics (mean/std) are estimated
on the TRAIN subset only and applied to both, to avoid label/data leakage.

Outputs (saved as float32 npy):
  data/train_s2.npy, data/train_s1.npy, data/train_y.npy
  data/val_s2.npy,   data/val_s1.npy,   data/val_y.npy
  data/class_counts_train.npy, data/mean_s2.npy, data/std_s2.npy, ...
"""
import os
import sys
import numpy as np
import h5py

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_OUT = os.path.join(ROOT, "data")
FROZEN = "/mnt/f/dataset/earth/1912.12171_so2sat/data/official_h5/validation.h5"

SEED = 42
VAL_FRAC = 0.20
N_CLASSES = 17


def main():
    os.makedirs(DATA_OUT, exist_ok=True)
    rng = np.random.RandomState(SEED)

    with h5py.File(FROZEN, "r") as f:
        labels = np.asarray(f["label"], dtype=np.float64).argmax(axis=1).astype(np.int64)
        n = labels.shape[0]
        sen2 = np.asarray(f["sen2"], dtype=np.float32)
        sen1 = np.asarray(f["sen1"], dtype=np.float32)

    assert n == 24119, n

    # ---- stratified 80/20 split with fixed seed ----
    per_class_idx = [np.where(labels == c)[0] for c in range(N_CLASSES)]
    train_idx, val_idx = [], []
    for c, idx in enumerate(per_class_idx):
        idx = rng.permutation(idx)
        n_val = int(round(len(idx) * VAL_FRAC))
        val_idx.append(idx[:n_val])
        train_idx.append(idx[n_val:])
    train_idx = np.concatenate(train_idx)
    val_idx = np.concatenate(val_idx)
    rng.shuffle(train_idx)

    # ---- normalization stats from TRAIN only ----
    mean_s2 = sen2[train_idx].mean(axis=(0, 1, 2))
    std_s2 = sen2[train_idx].std(axis=(0, 1, 2))
    mean_s1 = sen1[train_idx].mean(axis=(0, 1, 2))
    std_s1 = sen1[train_idx].std(axis=(0, 1, 2))

    def norm(x, mean, std):
        return (x - mean.reshape(1, 1, 1, -1)) / std.reshape(1, 1, 1, -1)

    train_s2 = norm(sen2[train_idx], mean_s2, std_s2).astype(np.float32)
    val_s2 = norm(sen2[val_idx], mean_s2, std_s2).astype(np.float32)
    train_s1 = norm(sen1[train_idx], mean_s1, std_s1).astype(np.float32)
    val_s1 = norm(sen1[val_idx], mean_s1, std_s1).astype(np.float32)

    np.save(os.path.join(DATA_OUT, "train_s2.npy"), train_s2)
    np.save(os.path.join(DATA_OUT, "val_s2.npy"), val_s2)
    np.save(os.path.join(DATA_OUT, "train_s1.npy"), train_s1)
    np.save(os.path.join(DATA_OUT, "val_s1.npy"), val_s1)
    np.save(os.path.join(DATA_OUT, "train_y.npy"), labels[train_idx])
    np.save(os.path.join(DATA_OUT, "val_y.npy"), labels[val_idx])
    np.save(os.path.join(DATA_OUT, "train_idx.npy"), train_idx)
    np.save(os.path.join(DATA_OUT, "val_idx.npy"), val_idx)
    np.save(os.path.join(DATA_OUT, "mean_s2.npy"), mean_s2)
    np.save(os.path.join(DATA_OUT, "std_s2.npy"), std_s2)
    np.save(os.path.join(DATA_OUT, "mean_s1.npy"), mean_s1)
    np.save(os.path.join(DATA_OUT, "std_s1.npy"), std_s1)
    np.save(os.path.join(DATA_OUT, "class_counts_train.npy"), np.bincount(labels[train_idx], minlength=N_CLASSES))
    np.save(os.path.join(DATA_OUT, "class_counts_val.npy"), np.bincount(labels[val_idx], minlength=N_CLASSES))

    print("train size:", train_idx.shape[0], "val size:", val_idx.shape[0])
    print("train class counts:", np.bincount(labels[train_idx], minlength=N_CLASSES).tolist())
    print("val class counts:", np.bincount(labels[val_idx], minlength=N_CLASSES).tolist())
    print("saved to", DATA_OUT)


if __name__ == "__main__":
    main()