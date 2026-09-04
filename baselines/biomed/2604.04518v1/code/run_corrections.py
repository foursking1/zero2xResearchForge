"""Run all correction methods on a dataset with ground-truth labels.

For each dataset/poison:
  * DFR        (balanced last-layer reweighting)
  * Group DRO  (post-hoc, wd in {0.1, 1.0})
  * P-ClArC    (layers {6,12}, fine-tune 40 epochs)
  * RR-ClArC   (layers {6,12}, lam in {1.0, 0.1}, fine-tune 40 epochs)

Model selection on validation AGA, evaluation on balanced test split.

Usage:
    python run_corrections.py <dataset> <poison> [method]
    method in {dfr, gdro, pclarc, rrclarc} (default: all)
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
GDRO_EPOCHS = int(os.environ.get("GDRO_EPOCHS", "100"))
PCLARC_LAYERS = tuple(int(x) for x in
                      os.environ.get("PCLARC_LAYERS", "6,12").split(","))
RRCLARC_LAYERS = tuple(int(x) for x in
                       os.environ.get("RRCLARC_LAYERS", "6,12").split(","))
RRCLARC_LAMS = tuple(float(x) for x in
                     os.environ.get("RRCLARC_LAMS", "1.0,0.1").split(","))
GDRO_WDS = tuple(float(x) for x in
                 os.environ.get("GDRO_WDS", "0.1,1.0").split(","))


def load_student(dataset, poison):
    m = make_resnet18(2, SEED)
    m.load_state_dict(torch.load(
        os.path.join(WORKSPACE, "models", "students",
                     f"{dataset}_{poison}", "best.pt"), weights_only=False))
    return m


def evaluate_test(model, test):
    return group_metrics(model, test["images"], test["targets"],
                         test["groups"])


def run(dataset, poison, method):
    root = split_root(dataset, poison)
    train, val, test = load_split(root)
    student = load_student(dataset, poison)
    # uncorrected baseline
    u_emp, u_aga, u_wga, u_gacc = evaluate_test(student, test)
    base = {"dataset": dataset, "poison": poison,
            "uncorrected_emp": u_emp, "uncorrected_aga": u_aga,
            "uncorrected_wga": u_wga, "uncorrected_group_accs": u_gacc}
    print(f"[{dataset}-{poison}] uncorrected emp={u_emp:.3f} aga={u_aga:.3f} "
          f"wga={u_wga:.3f}")
    out_dir = os.path.join(WORKSPACE, "results", "corrections",
                           f"{dataset}_{poison}")
    os.makedirs(out_dir, exist_ok=True)

    methods = [method] if method else ["dfr", "gdro", "pclarc", "rrclarc"]
    # skip methods whose JSON already exists (crash-resume support)
    methods = [m for m in methods
               if not os.path.exists(os.path.join(out_dir, f"{m}.json"))]
    if not methods:
        print(f"[{dataset}-{poison}] all methods already done, skipping")
        return

    if "dfr" in methods:
        t0 = time.time()
        m, info = run_dfr(student, train, val, test, epochs=100)
        emp, aga, wga, gacc = evaluate_test(m, test)
        json.dump({**base, "method": "dfr", "test_emp": emp, "test_aga": aga,
                   "test_wga": wga, "group_accs": gacc, **info,
                   "time_s": time.time() - t0},
                  open(os.path.join(out_dir, "dfr.json"), "w"), indent=2)
        print(f"[{dataset}-{poison}] DFR test_aga={aga:.3f} wga={wga:.3f}")

    if "gdro" in methods:
        t0 = time.time()
        m, info = run_group_dro(student, train, val, test,
                                wd_grid=GDRO_WDS, epochs=GDRO_EPOCHS)
        emp, aga, wga, gacc = evaluate_test(m, test)
        json.dump({**base, "method": "gdro", "test_emp": emp, "test_aga": aga,
                   "test_wga": wga, "group_accs": gacc, **info,
                   "time_s": time.time() - t0},
                  open(os.path.join(out_dir, "gdro.json"), "w"), indent=2)
        print(f"[{dataset}-{poison}] GDRO test_aga={aga:.3f} wga={wga:.3f}")

    if "pclarc" in methods:
        best = (-1, None)
        for layer in PCLARC_LAYERS:
            t0 = time.time()
            m, info = run_pclarc(student, train, val, test, layer=layer,
                                 target_class=1, cav_mode="pca",
                                 epochs=FT_EPOCHS)
            emp, aga, wga, gacc = evaluate_test(m, test)
            print(f"[{dataset}-{poison}] P-ClArC l={layer} "
                  f"val_aga={info['best_val_aga']:.3f} test_aga={aga:.3f}")
            if info["best_val_aga"] > best[0]:
                best = (info["best_val_aga"],
                        {"emp": emp, "aga": aga, "wga": wga, "gacc": gacc,
                         "layer": layer, "val_aga": info["best_val_aga"]})
        r = best[1]
        json.dump({**base, "method": "pclarc", "test_emp": r["emp"],
                   "test_aga": r["aga"], "test_wga": r["wga"],
                   "group_accs": r["gacc"], "layer": r["layer"],
                   "best_val_aga": r["val_aga"]},
                  open(os.path.join(out_dir, "pclarc.json"), "w"), indent=2)
        print(f"[{dataset}-{poison}] P-ClArC best test_aga={r['aga']:.3f}")

    if "rrclarc" in methods:
        best = (-1, None)
        for layer in RRCLARC_LAYERS:
            for lam in RRCLARC_LAMS:
                t0 = time.time()
                m, info = run_rrclarc(student, train, val, test, layer=layer,
                                      target_class=1, cav_mode="pca",
                                      lam=lam, epochs=FT_EPOCHS)
                emp, aga, wga, gacc = evaluate_test(m, test)
                print(f"[{dataset}-{poison}] RR-ClArC l={layer} lam={lam} "
                      f"val_aga={info['best_val_aga']:.3f} test_aga={aga:.3f}")
                if info["best_val_aga"] > best[0]:
                    best = (info["best_val_aga"],
                            {"emp": emp, "aga": aga, "wga": wga,
                             "gacc": gacc, "layer": layer, "lam": lam,
                             "val_aga": info["best_val_aga"]})
        r = best[1]
        json.dump({**base, "method": "rrclarc", "test_emp": r["emp"],
                   "test_aga": r["aga"], "test_wga": r["wga"],
                   "group_accs": r["gacc"], "layer": r["layer"],
                   "lam": r["lam"], "best_val_aga": r["val_aga"]},
                  open(os.path.join(out_dir, "rrclarc.json"), "w"), indent=2)
        print(f"[{dataset}-{poison}] RR-ClArC best test_aga={r['aga']:.3f}")


if __name__ == "__main__":
    d = sys.argv[1]
    p = sys.argv[2]
    m = sys.argv[3] if len(sys.argv) > 3 else None
    run(d, p, m)
