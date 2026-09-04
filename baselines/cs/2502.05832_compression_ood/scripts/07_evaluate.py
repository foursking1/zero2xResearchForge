#!/usr/bin/env python3
"""07_evaluate.py — independent final evaluation of every saved student on the
frozen test set.  Recomputes test top-1 from scratch (nothing cached), so the
reported numbers can be audited end-to-end.

Reads:  results/students/*/student.pt  (+ the per-config normalization)
Writes: results/eval_all.json (test_acc for every run) and prints a comparison
        against the numbers stored during training (results/students/*/metrics.json).
"""
import json
import os
import sys
import numpy as np
import torch
import torchvision.transforms as T
from PIL import Image
from torch.utils.data import DataLoader

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import load_frozen_cifar10, fit_normalization, build_subsets, SUBSET_SEEDS
from teacher_models import StudentNet

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results")
SEEDS = SUBSET_SEEDS
N_VALUES = [10, 50, 100]

class TestSet(torch.utils.data.Dataset):
    def __init__(self, x, y, tf):
        self.x, self.y, self.tf = x, y, tf
    def __len__(self):
        return len(self.y)
    def __getitem__(self, i):
        img = Image.fromarray(self.x[i])
        return self.tf(img), int(self.y[i])

def main():
    data = load_frozen_cifar10()
    subs = build_subsets(N_VALUES, data={"train_x": data["train_x"], "train_y": data["train_y"]})
    device = "cuda" if torch.cuda.is_available() else "cpu"
    out = {"device": device, "runs": {}}
    for cfg in ["balanced", "imbalanced"]:
        for N in N_VALUES:
            for seed in SEEDS:
                run_dir = os.path.join(RES, "students", f"{cfg}_N{N}_seed{seed}")
                student_path = os.path.join(run_dir, "student.pt")
                mpath = os.path.join(run_dir, "metrics.json")
                if not (os.path.exists(student_path) and os.path.exists(mpath)):
                    continue
                with open(mpath) as f:
                    m = json.load(f)
                sub = next(x for x in subs if x["N"] == N and x["seed"] == seed)
                idx = sub["balanced_idx"] if cfg == "balanced" else sub["imbalanced_idx"]
                mean, std = fit_normalization(data["train_x"][idx])
                tf = T.Compose([T.ToTensor(), T.Normalize(mean.tolist(), std.tolist())])
                loader = DataLoader(TestSet(data["test_x"], data["test_y"], tf),
                                    batch_size=256, shuffle=False, num_workers=2)
                net = StudentNet(num_classes=10)
                net.load_state_dict(torch.load(student_path, map_location=device))
                net = net.to(device).eval()
                correct = total = 0
                with torch.no_grad():
                    for xb, yb in loader:
                        xb, yb = xb.to(device), yb.to(device)
                        correct += (net(xb).argmax(1) == yb).sum().item()
                        total += yb.size(0)
                acc = 100.0 * correct / total
                out["runs"][f"{cfg}_N{N}_seed{seed}"] = {
                    "test_acc_reeval": round(acc, 3),
                    "test_acc_from_training": m["test_acc"],
                    "match": abs(acc - m["test_acc"]) < 0.05,
                }
    with open(os.path.join(RES, "eval_all.json"), "w") as f:
        json.dump(out, f, indent=2)
    n_ok = sum(1 for v in out["runs"].values() if v["match"])
    print(f"[eval] re-evaluated {len(out['runs'])} students on frozen test set; "
          f"{n_ok} match training-time numbers.")
    for k, v in list(out["runs"].items())[:6]:
        print(f"  {k}: reeval={v['test_acc_reeval']} train_time={v['test_acc_from_training']} match={v['match']}")

if __name__ == "__main__":
    main()