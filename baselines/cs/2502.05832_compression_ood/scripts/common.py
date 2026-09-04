"""Shared utilities for the few-shot compression OOD reproduction (arXiv:2502.05832).

- Loads the frozen CIFAR-10 pickle batches from data/.
- Verifies dataset facts (B-check #1: train 5000/class, test 1000/class).
- Defines the fixed subset-construction protocol (balanced / long-tailed imbalanced,
  equal total size, fixed seeds).  No test_batch is ever touched during construction.
"""
import os
import pickle
import numpy as np

DATA_DIR_ENV = "FROZEN_CIFAR10_DIR"
DEFAULT_DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data", "cifar-10-batches-py",
)

META = ["airplane", "automobile", "bird", "cat", "deer", "dog", "frog", "horse", "ship", "truck"]
NUM_CLASSES = 10

INIT_SEED = 0          # deterministic init/global seed inside scripts
SUBSET_SEEDS = [42, 7, 2024, 5, 8, 13]   # repeat id -> subset sampling seed (primary = 42)


def get_data_dir():
    return os.environ.get(DATA_DIR_ENV, DEFAULT_DATA_DIR)


def load_cifar_batch(path):
    with open(path, "rb") as f:
        d = pickle.load(f, encoding="bytes")
    data = d[b"data"] if b"data" in d else d["data"]  # (N, 3072) uint8
    labels = np.asarray(d[b"labels"] if b"labels" in d else d["labels"], dtype=np.int64)
    imgs = data.reshape(-1, 3, 32, 32).transpose(0, 2, 3, 1)  # (N, 32, 32, 3) uint8
    return imgs, labels


def load_frozen_cifar10(data_dir=None, train_only=False):
    """Load all training batches (concatenated) and, optionally, the test batch.

    Returns dict with 'train_x', 'train_y' and (if not train_only) 'test_x','test_y'.
    """
    data_dir = data_dir or get_data_dir()
    xs, ys = [], []
    for i in range(1, 6):
        x, y = load_cifar_batch(os.path.join(data_dir, f"data_batch_{i}"))
        xs.append(x)
        ys.append(y)
    train_x = np.concatenate(xs, axis=0)
    train_y = np.concatenate(ys, axis=0)
    out = {"train_x": train_x, "train_y": train_y}
    if not train_only:
        test_x, test_y = load_cifar_batch(os.path.join(data_dir, "test_batch"))
        out["test_x"] = test_x
        out["test_y"] = test_y
    return out


def verify_global_stats(data_dir=None):
    """B-check #1: decode frozen pickles and verify per-class counts / shape."""
    data = load_frozen_cifar10(data_dir)
    train_counts = np.bincount(data["train_y"], minlength=NUM_CLASSES)
    test_counts = np.bincount(data["test_y"], minlength=NUM_CLASSES)
    return {
        "train_total": int(len(data["train_y"])),
        "test_total": int(len(data["test_y"])),
        "train_per_class": train_counts.tolist(),
        "test_per_class": test_counts.tolist(),
        "img_shape": list(data["train_x"][0].shape),
        "dtype": str(data["train_x"].dtype),
    }


# ---------------------------------------------------------------------------
# Subset construction protocol
# ---------------------------------------------------------------------------
def longtail_per_class_sizes(total, num_classes=10, ratio=100.0, floor=1):
    """Exponentially-decaying per-class sizes summing exactly to `total`.

    sizes_j ~ ratio^(-j/(num_classes-1)), j=0..9.  All classes receive at
    least `floor` sample(s); rounding residual is absorbed by the majority class
    so that the sum is exactly `total` (equal-total fairness constraint).
    """
    q = ratio ** (-1.0 / (num_classes - 1))
    w = np.array([q ** j for j in range(num_classes)])  # j=0 -> 1, j=9 -> 1/ratio
    s = w / w.sum()
    sizes = np.maximum(np.floor(s * total + 0.5), floor).astype(np.int64)
    residual = int(total - sizes.sum())
    sizes[0] += residual  # majority class absorbs rounding residual
    return sizes


def sample_subset(xs, ys, per_class_n, seed, rng=None):
    """Draw, per class, exactly per_class_n[c] indices using a fixed seed.

    RNG strategy: a single np.random.RandomState seeded with `seed` is used so
    the whole subset is reproducible from one integer.
    """
    if rng is None:
        rng = np.random.default_rng(seed)
    idx = []
    for c in range(NUM_CLASSES):
        cls_idx = np.where(ys == c)[0]
        if per_class_n[c] > len(cls_idx):
            raise ValueError(f"class {c}: requested {per_class_n[c]} > available {len(cls_idx)}")
        chosen = rng.choice(cls_idx, size=per_class_n[c], replace=False)
        idx.append(chosen)
    idx = np.concatenate(idx)
    rng.shuffle(idx)
    return idx


def build_subsets(n_values, ratio=100.0, data=None, seeds=SUBSET_SEEDS):
    """Build balanced/imbalanced subsets for each N.  Returns a list of dicts.

    Balanced : N per class  (total 10*N)
    Imbalanced: long-tail ratio 100, same total 10*N.
    Each repeat (seed from `seeds`) rebuilds the whole subset deterministically.
    """
    if data is None:
        data = load_frozen_cifar10(train_only=True)
    xs, ys = data["train_x"], data["train_y"]
    subsets = []
    for N in n_values:
        total = NUM_CLASSES * N
        bal_sizes = np.full(NUM_CLASSES, N, dtype=np.int64)
        imb_sizes = longtail_per_class_sizes(total)
        for seed in seeds:
            rng_bal = np.random.default_rng(seed)
            rng_imb = np.random.default_rng(seed)
            bal_idx = sample_subset(xs, ys, bal_sizes, seed, rng=rng_bal)
            imb_idx = sample_subset(xs, ys, imb_sizes, seed, rng=rng_imb)
            subsets.append({
                "N": N, "total": total, "seed": seed,
                "balanced_sizes": bal_sizes.tolist(), "imbalanced_sizes": imb_sizes.tolist(),
                "balanced_idx": bal_idx, "imbalanced_idx": imb_idx,
            })
    return subsets


def fit_normalization(x):
    """Per-channel mean/std from a training(-subset) tensor.  Train-only statistic."""
    xf = x.astype(np.float32) / 255.0
    mean = xf.mean(axis=(0, 1, 2))
    std = xf.std(axis=(0, 1, 2))
    return mean.astype(np.float32), std.astype(np.float32)