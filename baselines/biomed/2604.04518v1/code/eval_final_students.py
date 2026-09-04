"""Evaluate the five trained student models used for the C01 table.

Reads best.pt snapshots from workspace/models/students_final/ and evaluates on
the matching data root.  Writes workspace/results/students_final_metrics.json.

Squares models were trained on squares_ref (verified by matching val accuracy);
real models on real_tensors/<ds>_<poison>.
"""
import json
import os

import numpy as np
import torch

from config import WORKSPACE, compute_group_metrics
from models import make_resnet18

torch.set_num_threads(4)

STUDENTS = {
    "squares_symmetric": {"root": os.path.join(WORKSPACE, "squares_ref", "symmetric")},
    "squares_asymmetric": {"root": os.path.join(WORKSPACE, "squares_ref", "asymmetric")},
    "smiling_symmetric": {"root": os.path.join(WORKSPACE, "real_tensors", "smiling_symmetric")},
    "smiling_asymmetric": {"root": os.path.join(WORKSPACE, "real_tensors", "smiling_asymmetric")},
    "blond_symmetric": {"root": os.path.join(WORKSPACE, "real_tensors", "blond_symmetric")},
}


def _as_tensor(v):
    if isinstance(v, np.ndarray):
        return torch.from_numpy(v).float() if v.dtype.kind == "f" \
            else torch.from_numpy(v).long()
    return v


def load_split(root, names):
    out = {}
    for name in names:
        d = torch.load(os.path.join(root, f"{name}.pt"), weights_only=False)
        for k, v in d.items():
            v = _as_tensor(v)
            if k == "group_labels":
                k = "groups"
            out[f"{name}_{k}"] = v
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
        pt = os.path.join(WORKSPACE, "models", "students_final", f"{name}.pt")
        if not os.path.exists(pt):
            print(f"{name}: no snapshot", flush=True)
            continue
        model = make_resnet18(2, 42)
        model.load_state_dict(torch.load(pt, weights_only=False))
        sp = load_split(cfg["root"], ["test"])
        emp, aga, wga, ga = evaluate(model, sp["test_images"],
                                     sp["test_targets"], sp["test_groups"])
        rec = {"dataset": name.split("_")[0],
               "poison": name.split("_", 1)[1],
               "model": name, "root": cfg["root"],
               "test_emp_acc": emp, "test_aga": aga, "test_wga": wga,
               "test_group_accs": ga}
        out.append(rec)
        print(f"{name}: emp={emp:.3f} AGA={aga:.3f} WGA={wga:.3f} "
              f"groups={[round(g, 3) for g in ga]}", flush=True)
        del sp
    os.makedirs(os.path.join(WORKSPACE, "results"), exist_ok=True)
    json.dump(out, open(os.path.join(WORKSPACE, "results",
                                     "students_final_metrics.json"), "w"),
              indent=2)


if __name__ == "__main__":
    main()
