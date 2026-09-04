"""Shared utilities for the PEER Solubility reproduction pipeline.

Everything below is deterministic once a global seed is set via `set_seed`
(fixed seeds are hard-coded in every entry-point script). Model training uses
GPU (CUDA) when available and quiet/offline, otherwise CPU; both paths are
validated to be reproducible with the chosen backend (cudnn.deterministic + a
fixed seed namespace).
"""

import os
import json
import random
import numpy as np
import pandas as pd

# cublas workspace size affects split-k atomics; pin it up-front so every
# process uses the same workspace and matmul reductions are reproducible.
os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":16:8")

# --------------------------------------------------------------------------- #
# Paths
# --------------------------------------------------------------------------- #
_AA20 = "ACDEFGHIKLMNPQRSTVWY"
AA2IDX = {aa: i for i, aa in enumerate(_AA20)}

_DEFAULT_DATA_DIRS = [
    "data",
    os.path.join(os.path.dirname(__file__), "..", "data"),
    os.path.join(os.path.dirname(__file__), "..", "..", "data"),
    "/mnt/f/dataset/biomed/2206.02096_peer_protein_bench",
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "data"),
]


def find_data_dir():
    env = os.environ.get("PEER_DATA_DIR")
    if env and os.path.isdir(env):
        return env
    for d in _DEFAULT_DATA_DIRS:
        if os.path.isdir(d) and os.path.isfile(os.path.join(d, "solubility_train.csv")):
            return d
    raise FileNotFoundError(
        "Could not locate the frozen PEER data directory. Set PEER_DATA_DIR to "
        "the folder containing solubility_{train,valid,test}.csv"
    )


def load_split(split):
    d = find_data_dir()
    df = pd.read_csv(os.path.join(d, f"solubility_{split}.csv"))
    alphabet = set("ACDEFGHIKLMNPQRSTVWY")
    bad = df[~df.sequence.map(lambda s: set(s) <= alphabet)]
    if len(bad):
        raise ValueError(f"{split}: {len(bad)} sequences outside the 20-AA alphabet")
    return df


def set_seed(seed):
    """Seed the whole stack. `torch` is imported lazily so that scripts that do
    not use it (feature engineering) work too.

    For bit-exact reproducibility on CUDA we additionally disable TF32 and
    tensor-core path selection (the accumulation-order nondeterminism there
    makes training trajectories diverge run-to-run) and force cuDNN
    deterministic algorithms (see the determinism self-check 07)."""
    random.seed(seed)
    np.random.seed(seed)
    import torch

    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    torch.backends.cuda.matmul.allow_tf32 = False
    if hasattr(torch.backends, "cudnn"):
        torch.backends.cudnn.allow_tf32 = False
    try:
        torch.use_deterministic_algorithms(True, warn_only=True)
    except (AttributeError, TypeError, RuntimeError):
        pass


def get_device():
    """Prefer GPU when it is available AND has >= 6 GB free; otherwise CPU.
    Returns a torch.device and the n_workers hint."""
    try:
        import torch, subprocess
    except ImportError:
        return None, 0
    if torch.cuda.is_available():
        free = torch.cuda.mem_get_info()[0] / 1e9
        if free >= 6.0:
            return torch.device("cuda"), 4
        print(f"[common] GPU free memory {free:.1f} GB < 6 GB, falling back to CPU")
    return torch.device("cpu"), 8


# --------------------------------------------------------------------------- #
# Sequence encoding
# --------------------------------------------------------------------------- #
def seq_to_ids(s, max_len=None):
    """Map a protein sequence to integer AA ids (20-letter alphabet)."""
    ids = [AA2IDX[a] for a in s]
    if max_len is not None and len(ids) > max_len:
        ids = ids[:max_len]
    return ids


def collate_ids(seqs, max_len, pad_id=20):
    """One-hot-free numeric batch: N x L int64, padded with pad_id(20)."""
    import torch

    out = torch.full((len(seqs), max_len), pad_id, dtype=torch.long)
    lens = torch.zeros(len(seqs), dtype=torch.long)
    for i, s in enumerate(seqs):
        ids = seq_to_ids(s, max_len)
        out[i, : len(ids)] = torch.tensor(ids, dtype=torch.long)
        lens[i] = len(ids)
    return out, lens


def accuracy_from_logits(logits, y):
    preds = logits.argmax(dim=1)
    return (preds == y).float().mean().item()


# --------------------------------------------------------------------------- #
# JSON helpers
# --------------------------------------------------------------------------- #
def save_json(obj, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
    return path


def ensure_dir(p):
    os.makedirs(p, exist_ok=True)
    return p