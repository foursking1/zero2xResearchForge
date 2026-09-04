"""Evaluate a single student's best.pt on its test split and append the result
to workspace/results/students_all.json (idempotent: overwrites that dataset's
entry).  Designed to be launched once per dataset so a single killed process
does not lose all C01 evidence.

Usage:
    python eval_one.py <dataset> <poison>
"""
import json
import os
import sys

import torch

from config import SEED, WORKSPACE
from corrections import load_split, split_root, group_metrics
from models import make_resnet18

SNAP_DIR = os.environ.get("SNAP_DIR", "")


def load_student(dataset, poison):
    m = make_resnet18(2, SEED)
    if SNAP_DIR:
        ckpt = os.path.join(SNAP_DIR, f"{dataset}_{poison}.pt")
    else:
        ckpt = os.path.join(WORKSPACE, "models", "students",
                            f"{dataset}_{poison}", "best.pt")
    m.load_state_dict(torch.load(ckpt, weights_only=False))
    return m


def main(dataset, poison):
    root = split_root(dataset, poison)
    _, _, test = load_split(root)
    model = load_student(dataset, poison)
    emp, aga, wga, gacc = group_metrics(model, test["images"],
                                        test["targets"], test["groups"])
    rec = {"dataset": dataset, "poison": poison,
           "test_emp_acc": emp, "test_aga": aga, "test_wga": wga,
           "test_group_accs": gacc}
    print(f"[{dataset}-{poison}] emp={emp:.4f} aga={aga:.4f} wga={wga:.4f} "
          f"group={[round(g, 4) for g in gacc]}", flush=True)
    out_path = os.path.join(WORKSPACE, "results", "students_all.json")
    data = []
    if os.path.exists(out_path):
        with open(out_path) as f:
            data = json.load(f)
    data = [r for r in data
            if not (r["dataset"] == dataset and r["poison"] == poison)]
    data.append(rec)
    with open(out_path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"WROTE {dataset}-{poison} to students_all.json", flush=True)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
