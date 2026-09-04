"""CFKD proxy from snapshot students (students_final).  Writes to
workspace/results/cfkd_final/.
"""
import json
import os
import sys

import numpy as np
import torch

from config import SEED, WORKSPACE, compute_group_metrics
from corrections import load_split, split_root, group_metrics
from models import make_resnet18
from cfkd import (make_cf_squares, make_cf_smiling, fine_tune_last_layer)

torch.set_num_threads(4)


def load_student(dataset, poison):
    pt = os.path.join(WORKSPACE, "models", "students_final",
                      f"{dataset}_{poison}.pt")
    m = make_resnet18(2, SEED)
    m.load_state_dict(torch.load(pt, weights_only=False))
    return m


def run_cfkd_squares(poison):
    root = split_root("squares", poison)
    train, val, test = load_split(root)
    model = load_student("squares", poison)
    x_orig, x_cf = make_cf_squares(train)
    y_orig = train["targets"].clone()
    x_aug = torch.cat([x_orig, x_cf])
    y_aug = torch.cat([y_orig, y_orig])
    res = fine_tune_last_layer(model, x_aug, y_aug, val, test)
    print(f"[cfkd-squares-{poison}] {res}", flush=True)
    return res


def run_cfkd_smiling(poison):
    root = split_root("smiling", poison)
    train, val, test = load_split(root)
    model = load_student("smiling", poison)
    x_cf = make_cf_smiling(poison)
    y_cf = train["targets"].clone()
    x_aug = torch.cat([train["images"], x_cf])
    y_aug = torch.cat([train["targets"], y_cf])
    res = fine_tune_last_layer(model, x_aug, y_aug, val, test)
    print(f"[cfkd-smiling-{poison}] {res}", flush=True)
    return res


def main(dataset, poison):
    if dataset == "squares":
        res = run_cfkd_squares(poison)
    elif dataset == "smiling":
        res = run_cfkd_smiling(poison)
    else:
        raise NotImplementedError
    out_dir = os.path.join(WORKSPACE, "results", "cfkd_final")
    os.makedirs(out_dir, exist_ok=True)
    json.dump({"dataset": dataset, "poison": poison, **res},
              open(os.path.join(out_dir, f"{dataset}_{poison}.json"), "w"),
              indent=2)
    print(f"DONE {dataset}_{poison} -> {os.path.join(out_dir, f'{dataset}_{poison}.json')}",
          flush=True)
    return res


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
