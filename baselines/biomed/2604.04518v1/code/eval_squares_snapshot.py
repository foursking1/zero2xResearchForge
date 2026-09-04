"""Evaluate the two squares snapshot students (students_final) on the balanced
test split of squares_ref/<poison>.  Fast (test N=1600).  Writes
workspace/results/students_squares.json.
"""
import json
import os

import numpy as np
import torch

from config import WORKSPACE, compute_group_metrics
from models import make_resnet18

torch.set_num_threads(4)

STUDENTS = {
    "squares_symmetric": os.path.join(WORKSPACE, "squares_ref", "symmetric"),
    "squares_asymmetric": os.path.join(WORKSPACE, "squares_ref", "asymmetric"),
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
    for name, root in STUDENTS.items():
        pt = os.path.join(WORKSPACE, "models", "students_final", f"{name}.pt")
        if not os.path.exists(pt):
            print(f"{name}: no snapshot {pt}", flush=True)
            continue
        model = make_resnet18(2, 42)
        model.load_state_dict(torch.load(pt, weights_only=False))
        test = load_test(root)
        emp, aga, wga, ga = evaluate(model, test["images"],
                                     test["targets"], test["groups"])
        rec = {"dataset": "squares",
               "poison": name.split("_", 1)[1],
               "model": name, "root": root, "ckpt": pt,
               "test_emp_acc": emp, "test_aga": aga, "test_wga": wga,
               "test_group_accs": ga}
        out.append(rec)
        print(f"{name}: emp={emp:.3f} AGA={aga:.3f} WGA={wga:.3f} "
              f"groups={[round(g, 3) for g in ga]}", flush=True)
    os.makedirs(os.path.join(WORKSPACE, "results"), exist_ok=True)
    json.dump(out, open(os.path.join(WORKSPACE, "results",
                                     "students_squares.json"), "w"),
              indent=2)


if __name__ == "__main__":
    main()
