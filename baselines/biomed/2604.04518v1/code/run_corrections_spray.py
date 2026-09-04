"""Run corrections using SpRAy-derived group labels (C04).

The same correction methods as run_corrections.py, but the confounder labels
q used for DFR / Group DRO / CAV computation are taken from SpRAy instead of
ground truth.

Usage:
    python run_corrections_spray.py <dataset> <poison> <layer> [method]
"""
import json
import os
import sys
import time

import torch

from config import SEED, WORKSPACE
from corrections import (load_split, split_root, predict, group_metrics,
                         run_dfr, run_group_dro, run_pclarc, run_rrclarc)
from models import make_resnet18

FT_EPOCHS = int(os.environ.get("CORR_EPOCHS", "30"))


def load_student(dataset, poison):
    m = make_resnet18(2, SEED)
    m.load_state_dict(torch.load(
        os.path.join(WORKSPACE, "models", "students",
                     f"{dataset}_{poison}", "best.pt"), weights_only=False))
    return m


def with_spray_labels(split, q_hat):
    """Return a new split dict with groups replaced by t*2+q_hat."""
    t = split["targets"].numpy()
    g_hat = t * 2 + q_hat
    out = {k: v for k, v in split.items()}
    out["groups"] = torch.from_numpy(g_hat).long()
    out["confs"] = torch.from_numpy(q_hat).long()
    return out


def run(dataset, poison, layer, method):
    root = split_root(dataset, poison)
    train, val, test = load_split(root)
    q_all = torch.load(os.path.join(
        WORKSPACE, "spray_labels", f"{dataset}_{poison}",
        f"labels_l{layer}.pt"), weights_only=False)
    q_hat = q_all["q_hat"].numpy()
    n_tr = len(train["targets"])
    train = with_spray_labels(train, q_hat[:n_tr])
    val = with_spray_labels(val, q_hat[n_tr:])
    student = load_student(dataset, poison)

    u_emp, u_aga, u_wga, u_gacc = group_metrics(
        student, test["images"], test["targets"], test["groups"])
    base = {"dataset": dataset, "poison": poison, "spray_layer": layer,
            "uncorrected_emp": u_emp, "uncorrected_aga": u_aga,
            "uncorrected_wga": u_wga}
    out_dir = os.path.join(WORKSPACE, "results", "corrections_spray",
                           f"{dataset}_{poison}")
    os.makedirs(out_dir, exist_ok=True)

    methods = [method] if method else ["dfr", "gdro", "pclarc", "rrclarc"]
    # crash-resume: skip methods whose JSON already exists
    methods = [m for m in methods
               if not os.path.exists(os.path.join(out_dir, f"{m}.json"))]
    if not methods:
        print(f"[spray-{dataset}-{poison}] all methods already done, skipping")
        return

    if "dfr" in methods:
        t0 = time.time()
        m, info = run_dfr(student, train, val, test, epochs=100)
        emp, aga, wga, gacc = group_metrics(m, test["images"],
                                            test["targets"], test["groups"])
        json.dump({**base, "method": "dfr", "test_emp": emp, "test_aga": aga,
                   "test_wga": wga, "group_accs": gacc, **info,
                   "time_s": time.time() - t0},
                  open(os.path.join(out_dir, "dfr.json"), "w"), indent=2)
        print(f"[spray-{dataset}-{poison}] DFR test_aga={aga:.3f}")

    if "gdro" in methods:
        t0 = time.time()
        m, info = run_group_dro(student, train, val, test,
                                wd_grid=(0.1,), epochs=150)
        emp, aga, wga, gacc = group_metrics(m, test["images"],
                                            test["targets"], test["groups"])
        json.dump({**base, "method": "gdro", "test_emp": emp, "test_aga": aga,
                   "test_wga": wga, "group_accs": gacc, **info,
                   "time_s": time.time() - t0},
                  open(os.path.join(out_dir, "gdro.json"), "w"), indent=2)
        print(f"[spray-{dataset}-{poison}] GDRO test_aga={aga:.3f}")

    if "pclarc" in methods:
        best = (-1, None)
        for lyr in (layer,):
            t0 = time.time()
            m, info = run_pclarc(student, train, val, test, layer=lyr,
                                 target_class=1, cav_mode="pca",
                                 epochs=FT_EPOCHS)
            emp, aga, wga, gacc = group_metrics(m, test["images"],
                                                test["targets"],
                                                test["groups"])
            print(f"[spray-{dataset}-{poison}] P-ClArC l={lyr} "
                  f"test_aga={aga:.3f}")
            if info["best_val_aga"] > best[0]:
                best = (info["best_val_aga"],
                        {"emp": emp, "aga": aga, "wga": wga, "gacc": gacc,
                         "layer": lyr, "val_aga": info["best_val_aga"]})
        r = best[1]
        json.dump({**base, "method": "pclarc", "test_emp": r["emp"],
                   "test_aga": r["aga"], "test_wga": r["wga"],
                   "group_accs": r["gacc"], "layer": r["layer"],
                   "best_val_aga": r["val_aga"]},
                  open(os.path.join(out_dir, "pclarc.json"), "w"), indent=2)
        print(f"[spray-{dataset}-{poison}] P-ClArC best test_aga={r['aga']:.3f}")

    if "rrclarc" in methods:
        best = (-1, None)
        for lyr in (layer,):
            for lam in (1.0,):
                t0 = time.time()
                m, info = run_rrclarc(student, train, val, test, layer=lyr,
                                      target_class=1, cav_mode="pca",
                                      lam=lam, epochs=FT_EPOCHS)
                emp, aga, wga, gacc = group_metrics(m, test["images"],
                                                    test["targets"],
                                                    test["groups"])
                print(f"[spray-{dataset}-{poison}] RR-ClArC l={lyr} "
                      f"test_aga={aga:.3f}")
                if info["best_val_aga"] > best[0]:
                    best = (info["best_val_aga"],
                            {"emp": emp, "aga": aga, "wga": wga,
                             "gacc": gacc, "layer": lyr, "lam": lam,
                             "val_aga": info["best_val_aga"]})
        r = best[1]
        json.dump({**base, "method": "rrclarc", "test_emp": r["emp"],
                   "test_aga": r["aga"], "test_wga": r["wga"],
                   "group_accs": r["gacc"], "layer": r["layer"],
                   "lam": r["lam"], "best_val_aga": r["val_aga"]},
                  open(os.path.join(out_dir, "rrclarc.json"), "w"), indent=2)
        print(f"[spray-{dataset}-{poison}] RR-ClArC best test_aga={r['aga']:.3f}")


if __name__ == "__main__":
    d = sys.argv[1]
    p = sys.argv[2]
    l = int(sys.argv[3])
    m = sys.argv[4] if len(sys.argv) > 4 else None
    run(d, p, l, m)
