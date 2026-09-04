"""Evaluate every periodic checkpoint of a trained student on the test split.

Shows the emp/AGA/WGA trajectory across epochs so we can see whether/when the
student enters the Clever Hans (shortcut) regime. Read-only analysis.

Usage:
    python eval_ckpts.py <dataset_key> <poison>
"""
import os
import sys

import numpy as np
import torch

from config import WORKSPACE, compute_group_metrics
from models import make_resnet18
from train_student import load_split, split_root

torch.set_num_threads(1)


def main(dataset, poison):
    train, val, test = load_split(split_root(dataset, poison))
    out_dir = os.path.join(WORKSPACE, "models", "students", f"{dataset}_{poison}")
    if not os.path.isdir(out_dir):
        print("no dir", out_dir)
        return
    eps = []
    for f in os.listdir(out_dir):
        if f.startswith("ckpt_") and f.endswith(".pt"):
            eps.append(int(f[5:-3]))
    eps = sorted(eps)
    print(f"{dataset} {poison} checkpoints: {eps}", flush=True)
    for ep in eps:
        path = os.path.join(out_dir, f"ckpt_{ep}.pt")
        state = torch.load(path, weights_only=False)
        if isinstance(state, dict) and "state_dict" in state:
            state = state["state_dict"]
        model = make_resnet18(num_classes=2, seed=42)
        model.load_state_dict(state)
        model.eval()
        preds, tgts, gs = [], [], []
        with torch.no_grad():
            for i in range(0, test["images"].size(0), 128):
                out = model(test["images"][i:i + 128])
                preds.append(out.argmax(1).numpy())
                tgts.append(test["targets"][i:i + 128].numpy())
                gs.append(test["groups"][i:i + 128].numpy())
        emp, aga, wga, ga = compute_group_metrics(
            np.concatenate(preds), np.concatenate(tgts), np.concatenate(gs))
        print(f"ep {ep:4d} emp={emp:.3f} AGA={aga:.3f} WGA={wga:.3f} "
              f"groups={[round(g, 2) for g in ga]}", flush=True)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
