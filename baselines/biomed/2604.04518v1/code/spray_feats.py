"""Compute + save SpRAy attribution features for a dataset/layer.

Saves z-scored feature matrix (and metadata) to
workspace/spray_features/{ds}_{poison}/l{layer}.npy so the clustering step
(spray_labels_from_feats.py) can be re-run cheaply without recomputing
attributions.  Crash-safe: if features already exist, exits immediately.
"""
import os
import sys

import numpy as np
import torch

from config import SEED, WORKSPACE
from corrections import load_split, split_root
from models import make_resnet18
from spray import attributions
from debug_spray2 import featurize


def main(dataset, poison, layer):
    layer = int(layer)
    feat_dir = os.path.join(WORKSPACE, "spray_features", f"{dataset}_{poison}")
    os.makedirs(feat_dir, exist_ok=True)
    out_npy = os.path.join(feat_dir, f"l{layer}.npy")
    if os.path.exists(out_npy):
        print(f"[spray-feats] {dataset}-{poison} l{layer} already saved; skipping",
              flush=True)
        return
    root = split_root(dataset, poison)
    train, val, test = load_split(root)
    model = make_resnet18(2, SEED)
    model.load_state_dict(torch.load(
        os.path.join(WORKSPACE, "models", "students", f"{dataset}_{poison}",
                     "best.pt"), weights_only=False))
    x = torch.cat([train["images"], val["images"]])
    targets = torch.cat([train["targets"], val["targets"]])
    groups = torch.cat([train["groups"], val["groups"]])
    print(f"[spray-feats] {dataset}-{poison} l{layer} computing attributions...",
          flush=True)
    attr, preds = attributions(model, x, layer)
    np.save(out_npy, attr.astype(np.float32))
    meta = np.stack([targets.numpy(), groups.numpy()], 1)
    np.save(os.path.join(feat_dir, f"l{layer}_meta.npy"), meta)
    print(f"[spray-feats] {dataset}-{poison} l{layer} saved {out_npy} "
          f"{attr.shape} t={targets.numpy().tolist()}", flush=True)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], int(sys.argv[3]))
