#!/usr/bin/env python3
"""Compute and cache per-graph aggregated atom-feature vectors for the
non-graph baselines (used by baselines.py and run_experiments.py)."""

import os
import sys

import torch

import config
from models import graph_features

CACHE = os.path.join(config.results_dir(), "graph_features_cache.pt")


def get_cached():
    if os.path.isfile(CACHE):
        return torch.load(CACHE, weights_only=False)
    out = {}
    for split in ("train", "valid", "test"):
        graphs = torch.load(f"/tmp/molhiv/{split}.pt", weights_only=False)
        feats, ys = graph_features(graphs)
        out[split] = (feats.float(), ys.float())
    torch.save(out, CACHE)
    return out


if __name__ == "__main__":
    d = get_cached()
    for k, (f, y) in d.items():
        print(k, f.shape, y.shape, "pos_rate", float(y.mean()), file=sys.stderr)