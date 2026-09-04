"""Evaluate the three C01 students not covered by the students_final snapshots:
blond_asymmetric, camelyon_symmetric, camelyon_asymmetric.

Uses the ref0 best.pt checkpoints from workspace/models/students/<name>/best.pt
and evaluates on the balanced test split of the matching data root
(real_tensors/<ds>_<poison>).  Writes workspace/results/students_missing.json.

Runs one dataset at a time and frees memory after each (large test.pt files).
"""
import gc
import json
import os

import numpy as np
import torch

from config import WORKSPACE, compute_group_metrics
from models import make_resnet18

torch.set_num_threads(4)

STUDENTS = {
    "blond_asymmetric": {"root": os.path.join(WORKSPACE, "real_tensors",
                                              "blond_asymmetric")},
    "camelyon_symmetric": {"root": os.path.join(WORKSPACE, "real_tensors",
                                                "camelyon_symmetric")},
    "camelyon_asymmetric": {"root": os.path.join(WORKSPACE, "real_tensors",
                                                 "camelyon_asymmetric")},
}


def _as_tensor(v):
    if isinstance(v, np.ndarray):
        return torch.from_numpy(v).float() if v.dtype.kind == "f" \
            else torch.from_numpy(v).long()
    return v


def load_test(root):
    d = torch.load(os.path.join(root, "test.pt"), weights_only=False)
    out = {}
    for k, v in d.items():
        v = _as_tensor(v)
        if k == "group_labels":
            k = "groups"
        out[k] = v
    return out


def evaluate(model, x, y, g, bs=64):
    model.eval()
    preds = []
    with torch.no_grad():
        for i in range(0, x.size(0), bs):
            preds.append(model(x[i:i + bs]).argmax(1).cpu().numpy())
    return compute_group_metrics(np.concatenate(preds), y.numpy(), g.numpy())


def main():
    out = []
    for name, cfg in STUDENTS.items():
        pt = os.path.join(WORKSPACE, "models", "students", name, "best.pt")
        if not os.path.exists(pt):
            print(f"{name}: no checkpoint {pt}", flush=True)
            continue
        model = make_resnet18(2, 42)
        model.load_state_dict(torch.load(pt, weights_only=False))
        test = load_test(cfg["root"])
        emp, aga, wga, ga = evaluate(model, test["images"],
                                     test["targets"], test["groups"])
        rec = {"dataset": name.split("_")[0],
               "poison": name.split("_", 1)[1],
               "model": name, "root": cfg["root"],
               "ckpt": pt,
               "test_emp_acc": emp, "test_aga": aga, "test_wga": wga,
               "test_group_accs": ga}
        out.append(rec)
        print(f"{name}: emp={emp:.3f} AGA={aga:.3f} WGA={wga:.3f} "
              f"groups={[round(g, 3) for g in ga]}", flush=True)
        del test
        gc.collect()
    os.makedirs(os.path.join(WORKSPACE, "results"), exist_ok=True)
    json.dump(out, open(os.path.join(WORKSPACE, "results",
                                     "students_missing.json"), "w"),
              indent=2)


if __name__ == "__main__":
    main()
