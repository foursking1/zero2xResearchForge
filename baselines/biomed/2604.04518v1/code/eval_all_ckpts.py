"""Fresh evaluation of all student checkpoints on their (best-matched) data root.

Memory-efficient: loads only val (root selection) or only test (final metrics),
one split at a time.

Usage:
    python eval_all_ckpts.py [student_dir_glob]
"""
import glob
import os
import sys

import numpy as np
import torch

from config import WORKSPACE, compute_group_metrics
from models import make_resnet18

torch.set_num_threads(4)


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


def cand_roots(dataset, poison):
    if dataset == "squares":
        return [(os.path.join(WORKSPACE, base, poison), base)
                for base in ("squares", "squares_ref", "squares_s4")]
    return [(os.path.join(WORKSPACE, "real_tensors", f"{dataset}_{poison}"),
             "real")]


def evaluate(model, x, y, g, bs=128):
    model.eval()
    preds = []
    with torch.no_grad():
        for i in range(0, x.size(0), bs):
            preds.append(model(x[i:i + bs]).argmax(1).cpu().numpy())
    return compute_group_metrics(np.concatenate(preds), y.numpy(), g.numpy())


def main(pattern):
    dirs = sorted(glob.glob(pattern))
    for d in dirs:
        name = os.path.basename(d)
        if name.startswith("squares"):
            dataset, poison = "squares", "asymmetric" if "asymmetric" in name \
                else "symmetric"
        else:
            parts = name.split("_")
            dataset, poison = parts[0], parts[1]
        best_path = os.path.join(d, "best.pt")
        if not os.path.exists(best_path):
            print(f"== {name}: no best.pt ==")
            continue
        roots = cand_roots(dataset, poison)
        # root selection: only val split (small)
        best_tag, best_val = None, -1
        for root, tag in roots:
            sp = load_split(root, ["val"])
            model = make_resnet18(2, 42)
            st = torch.load(best_path, weights_only=False)
            if isinstance(st, dict) and "state_dict" in st:
                st = st["state_dict"]
            try:
                model.load_state_dict(st)
            except Exception:
                continue
            emp, _, _, _ = evaluate(model, sp["val_images"], sp["val_targets"],
                                    sp["val_groups"])
            if emp > best_val:
                best_val, best_tag = emp, tag
        if best_tag is None:
            print(f"== {name}: no root matched ==")
            continue
        root = os.path.join(WORKSPACE, best_tag, poison) if best_tag != "real" \
            else os.path.join(WORKSPACE, "real_tensors", f"{dataset}_{poison}")
        print(f"== {name} (root={best_tag}, val_acc={best_val:.3f}) ==", flush=True)
        sp = load_split(root, ["test"])
        model = make_resnet18(2, 42)
        st = torch.load(best_path, weights_only=False)
        if isinstance(st, dict) and "state_dict" in st:
            st = st["state_dict"]
        model.load_state_dict(st)
        emp, aga, wga, ga = evaluate(model, sp["test_images"],
                                     sp["test_targets"], sp["test_groups"])
        print(f"   TEST emp={emp:.3f} AGA={aga:.3f} WGA={wga:.3f} "
              f"groups={[round(g, 3) for g in ga]}", flush=True)
        del sp
        torch.cuda.empty_cache()
        ckpts = sorted(int(f[5:-3]) for f in os.listdir(d)
                       if f.startswith("ckpt_") and f.endswith(".pt"))
        sp = load_split(root, ["test"])
        for ep in ckpts[-3:]:
            cst = torch.load(os.path.join(d, f"ckpt_{ep}.pt"),
                             weights_only=False)
            if isinstance(cst, dict) and "state_dict" in cst:
                cst = cst["state_dict"]
            m = make_resnet18(2, 42)
            try:
                m.load_state_dict(cst)
            except Exception:
                continue
            e, a, w, g = evaluate(m, sp["test_images"], sp["test_targets"],
                                  sp["test_groups"])
            print(f"   ckpt_{ep}  emp={e:.3f} AGA={a:.3f} WGA={w:.3f}", flush=True)


if __name__ == "__main__":
    pat = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        WORKSPACE, "models", "students", "*")
    main(pat)
