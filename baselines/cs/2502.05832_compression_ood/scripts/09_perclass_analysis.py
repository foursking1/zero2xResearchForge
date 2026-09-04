#!/usr/bin/env python3
"""09_perclass_analysis.py — mechanism check: per-class test top-1 of compressed
students (balanced vs imbalanced), aggregated over all repeat seeds.

Fast path: numpy uint8 -> (x/255-mean)/std directly, no per-image PIL / transforms.
Writes results/per_class_accuracy.json.
"""
import json
import os
import sys
import numpy as np
import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import load_frozen_cifar10, build_subsets, fit_normalization, SUBSET_SEEDS, META
from teacher_models import StudentNet

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results")
device = "cuda" if torch.cuda.is_available() else "cpu"


def per_class_acc(net, tr_x, te_x, te_y, idx_norm):
    mean, std = fit_normalization(tr_x[idx_norm])
    x = (te_x.astype(np.float32) / 255.0 - mean) / std
    x = x.transpose(0, 3, 1, 2)
    per = np.zeros((10, 2), dtype=np.int64)
    net.eval()
    net = net.to(device)
    with torch.no_grad():
        for i in range(0, len(x), 512):
            xb = torch.from_numpy(x[i:i + 512].copy()).to(device)
            o = net(xb).argmax(1).cpu().numpy()
            yb = te_y[i:i + 512]
            for a, l in zip(o, yb):
                per[l][0] += (a == l)
                per[l][1] += 1
    return per[:, 0].astype(float) / per[:, 1]


def main():
    data = load_frozen_cifar10()
    tr = {"train_x": data["train_x"], "train_y": data["train_y"]}
    tr_x, tr_y = data["train_x"], data["train_y"]
    te_x, te_y = data["test_x"], data["test_y"]
    subs = build_subsets([10, 50, 100], data=tr)
    out = {}
    for N in [10, 50, 100]:
        acc_b = np.zeros(10)
        acc_i = np.zeros(10)
        cnt = 0
        for seed in SUBSET_SEEDS:
            s = next(x for x in subs if x["N"] == N and x["seed"] == seed)
            nb = torch.load(os.path.join(RES, "students", f"balanced_N{N}_seed{seed}", "student.pt"),
                            map_location="cpu")
            ni = torch.load(os.path.join(RES, "students", f"imbalanced_N{N}_seed{seed}", "student.pt"),
                            map_location="cpu")
            netb = StudentNet(num_classes=10)
            neti = StudentNet(num_classes=10)
            netb.load_state_dict(nb)
            neti.load_state_dict(ni)
            acc_b += per_class_acc(netb, tr_x, te_x, te_y, s["balanced_idx"]) * 100
            acc_i += per_class_acc(neti, tr_x, te_x, te_y, s["imbalanced_idx"]) * 100
            cnt += 1
        out[str(N)] = {
            "imbalanced_n_per_class": s["imbalanced_sizes"],
            "balanced_mean_per_class_acc": [round(float(v) / cnt, 2) for v in acc_b],
            "imbalanced_mean_per_class_acc": [round(float(v) / cnt, 2) for v in acc_i],
            "mean_bal": round(float(acc_b.mean() / cnt), 2),
            "mean_imb": round(float(acc_i.mean() / cnt), 2),
        }
    with open(os.path.join(RES, "per_class_accuracy.json"), "w") as f:
        json.dump({"classes": META, "per_N": out}, f, indent=2)
    print("[perclass] wrote results/per_class_accuracy.json")


if __name__ == "__main__":
    main()