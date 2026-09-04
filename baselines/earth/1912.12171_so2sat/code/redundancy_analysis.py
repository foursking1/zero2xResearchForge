"""Quantify the intrinsic within-validation redundancy of the frozen
validation.h5 -> demonstrates why internal split OA exceeds the paper's
cross-city numbers.

Output: data/redundancy_nn.json
"""
import json
import os

import numpy as np
from scipy.spatial import cKDTree

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA = os.path.join(ROOT, "data")
H5 = "/mnt/f/dataset/earth/1912.12171_so2sat/data/official_h5/validation.h5"


def read_signatures():
    import h5py
    cached = os.path.join(DATA, "_sig.npy")
    if os.path.exists(cached):
        return np.load(cached)
    with h5py.File(H5, "r") as f:
        n = f["sen2"].shape[0]
        sig = np.zeros((n, 10), np.float32)
        for i in range(0, n, 1000):
            blk = f["sen2"][i:i + 1000]
            sig[i:i + blk.shape[0]] = blk.reshape(blk.shape[0], -1, 10).mean(1)
    np.save(cached, sig)
    return sig


def main():
    import h5py
    with h5py.File(H5, "r") as f:
        labs = np.asarray(f["label"]).argmax(1)
    sig = read_signatures()
    tr_idx = np.load(os.path.join(DATA, "train_idx.npy"))
    ev_idx = np.load(os.path.join(DATA, "val_idx.npy"))
    tree = cKDTree(sig[tr_idx])
    d, idx = tree.query(sig[ev_idx], k=1)

    lab_t = labs[tr_idx]
    lab_e = labs[ev_idx]
    same = lab_t[idx] == lab_e
    out = {
        "train_size": int(len(tr_idx)),
        "eval_size": int(len(ev_idx)),
        "eval_frac_nearest_train_same_label": float(same.mean()),
        "median_nn_distance": float(np.median(d)),
        "eval_frac_nn_dist_below": {round(th, 3): float((d < th).mean()) for th in
                                    [0.01, 0.02, 0.05]},
        "same_label_rate_nn_dist_below": {round(th, 3): float(same[(d < th)].mean())
                                          for th in [0.01, 0.02, 0.05]},
        "exact_duplicate_patch_signatures": int(0),  # filled below
    }
    # exact duplicate band-mean signature count across the whole file
    q = (sig * 1000).astype(np.int32)
    uniq, cts = np.unique(q, axis=0, return_counts=True)
    out["exact_duplicate_patch_signatures"] = int((cts - 1).sum())
    with open(os.path.join(DATA, "redundancy_nn.json"), "w") as fh:
        json.dump(out, fh, indent=2)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()