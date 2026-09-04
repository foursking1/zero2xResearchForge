"""Evaluate all current ERM student best.pt models on their test splits.

Writes workspace/results/students_all.json with per-dataset
(emp, aga, wga, group_accs) for the uncorrected baseline (C01).

Usage:
    python eval_all_students.py
"""
import json
import os
import sys

import torch

from config import SEED, WORKSPACE
from corrections import load_split, split_root, group_metrics
from models import make_resnet18

# Optional: read student .pt from a snapshot dir (e.g. on another drive)
# to avoid racing the in-place writes of a running training job.
SNAP_DIR = os.environ.get("SNAP_DIR", "")

DATASETS = [
    ("squares", "symmetric"),
    ("squares", "asymmetric"),
    ("smiling", "symmetric"),
    ("smiling", "asymmetric"),
    ("blond", "symmetric"),
    ("blond", "asymmetric"),
    ("camelyon", "symmetric"),
    ("camelyon", "asymmetric"),
]


def load_student(dataset, poison):
    m = make_resnet18(2, SEED)
    if SNAP_DIR:
        ckpt = os.path.join(SNAP_DIR, f"{dataset}_{poison}.pt")
    else:
        ckpt = os.path.join(WORKSPACE, "models", "students",
                            f"{dataset}_{poison}", "best.pt")
    m.load_state_dict(torch.load(ckpt, weights_only=False))
    return m


def main():
    out = []
    for dataset, poison in DATASETS:
        root = split_root(dataset, poison)
        try:
            _, _, test = load_split(root)
        except FileNotFoundError as e:
            print(f"[skip] {dataset}-{poison}: {e}")
            continue
        try:
            model = load_student(dataset, poison)
        except FileNotFoundError as e:
            print(f"[skip] {dataset}-{poison}: no student {e}")
            continue
        emp, aga, wga, gacc = group_metrics(model, test["images"],
                                            test["targets"], test["groups"])
        print(f"[{dataset}-{poison}] emp={emp:.4f} aga={aga:.4f} "
              f"wga={wga:.4f} group={[round(g, 4) for g in gacc]}",
              flush=True)
        out.append({"dataset": dataset, "poison": poison,
                    "test_emp_acc": emp, "test_aga": aga, "test_wga": wga,
                    "test_group_accs": gacc})
    os.makedirs(os.path.join(WORKSPACE, "results"), exist_ok=True)
    with open(os.path.join(WORKSPACE, "results", "students_all.json"), "w") as f:
        json.dump(out, f, indent=2)
    print(f"WROTE {len(out)} students to results/students_all.json")


if __name__ == "__main__":
    main()
