"""Squares synthetic dataset generator (paper section 3.1.1).

Dataset spec from the paper:
  * 64x64 RGB images.
  * Foreground intensity = brightness of a small red square (CAUSAL feature).
      Class A (t=0): foreground intensity in [0.0, 0.5)
      Class B (t=1): foreground intensity in [0.5, 1.0]
  * Background intensity (CONFOUNDER). q=1 iff background < 0.5 (dark),
    q=0 iff background >= 0.5 (bright).
  * Mild Gaussian noise added to all images.
  * Group = (t, q):  A- (t=0,q=0), A+ (t=0,q=1), B- (t=1,q=0), B+ (t=1,q=1)

Poisoned distributions (train and validation):
  symmetric : [A- 49%, A+ 1%, B- 1%, B+ 49%]
  asymmetric: [A- 25%, A+ 25%, B- 49%, B+ 1%]
  unpoisoned: [25%, 25%, 25%, 25%]

Test splits are balanced (25% per group).
"""
import os
import numpy as np
import torch

from config import (
    TRAIN_N, VAL_N, SEED, group_sizes, conf_to_group, save_pt, WORKSPACE,
)

IMAGE_SIZE = 64
# Reference rendering (pytorch_explain_and_adapt latent_to_square_image):
# an 8x8 red inner square framed by a 2px mid-gray (127/255) border, on a
# uniform gray background, with additive gaussian noise of std 20/255.
SQUARE_SIDE = int(os.environ.get("SQUARE_SIDE", "8"))
SQUARE_BORDER = int(os.environ.get("SQUARE_BORDER", "2"))
BORDER_VALUE = float(os.environ.get("BORDER_VALUE", "0.498"))
NOISE_STD = float(os.environ.get("NOISE_STD", str(20.0 / 255.0)))


def render_square(fg_intensity, bg_intensity, size=IMAGE_SIZE, rng=None):
    """Render one 64x64 image matching the reference implementation.

    A small red inner square (side ``square_side``) framed by a 2px mid-gray
    border is placed at a random location; the red-channel brightness of the
    inner square is ``fg_intensity`` and the border is a fixed mid-gray.  The
    rest of the image is filled with a gray background of brightness
    ``bg_intensity``.
    """
    if rng is None:
        rng = np.random.default_rng()
    square_side = SQUARE_SIDE
    border = SQUARE_BORDER
    total = square_side + 2 * border
    img = np.full((size, size, 3), bg_intensity, dtype=np.float64)
    # random top-left corner for the (bordered) square
    x = rng.integers(0, size - total)
    y = rng.integers(0, size - total)
    # mid-gray border ring (constant, class-independent)
    img[y:y + total, x:x + total, :] = BORDER_VALUE
    # red inner square: RGB = (fg_intensity, 0, 0)
    img[y + border:y + border + square_side,
        x + border:x + border + square_side, 0] = fg_intensity
    img[y + border:y + border + square_side,
        x + border:x + border + square_side, 1] = 0.0
    img[y + border:y + border + square_side,
        x + border:x + border + square_side, 2] = 0.0
    return img


def make_squares_split(poison, n, seed):
    """Generate a single split with prescribed group sizes.

    Returns dict with images (float32 [N,3,64,64]), targets, group_labels.
    """
    rng = np.random.default_rng(seed)
    sizes = group_sizes(n, poison)
    images, targets, groups = [], [], []
    for g, n_g in enumerate(sizes):
        t, q = divmod(g, 2)  # g = 2*t + q
        for _ in range(n_g):
            if t == 0:
                fg = rng.uniform(0.0, 0.5)
            else:
                fg = rng.uniform(0.5, 1.0)
            if q == 0:
                bg = rng.uniform(0.5, 1.0)   # bright background
            else:
                bg = rng.uniform(0.0, 0.5)   # dark background
            img = render_square(fg, bg, rng=rng)
            # mild gaussian noise
            img += rng.normal(0.0, NOISE_STD, img.shape)
            img = np.clip(img, 0.0, 1.0)
            images.append(img.astype(np.float32))
            targets.append(t)
            groups.append(g)
    images = np.stack(images)          # [N,64,64,3]
    images = images.transpose(0, 3, 1, 2)  # [N,3,64,64]
    targets = np.array(targets, dtype=np.int64)
    groups = np.array(groups, dtype=np.int64)
    # shuffle
    perm = rng.permutation(n)
    return {
        "images": images[perm],
        "targets": targets[perm],
        "group_labels": groups[perm],
    }


def generate_squares(out_root=None):
    """Generate symmetric, asymmetric, unpoisoned splits for train/val/test.

    Train/val follow the paper (800/200) with poisoned group sizes.
    Test is balanced: 400 samples per group (1600 total).
    """
    out_root = out_root or os.path.join(WORKSPACE, "squares")
    os.makedirs(out_root, exist_ok=True)
    test_sizes = group_sizes(1600, "unpoisoned")  # 400/400/400/400

    variants = {}
    for poison in ["symmetric", "asymmetric", "unpoisoned"]:
        train = make_squares_split(poison, TRAIN_N, seed=SEED * 100 + 0)
        val = make_squares_split(poison, VAL_N, seed=SEED * 100 + 1)
        test = make_squares_split("unpoisoned", 1600, seed=SEED * 100 + 2)
        variants[poison] = {"train": train, "val": val, "test": test}
        for split_name, data in [("train", train), ("val", val), ("test", test)]:
            save_pt(data, os.path.join(out_root, poison, f"{split_name}.pt"))
        print(f"[squares] {poison}: train sizes={np.bincount(train['group_labels'])}")
    return variants


if __name__ == "__main__":
    generate_squares()
