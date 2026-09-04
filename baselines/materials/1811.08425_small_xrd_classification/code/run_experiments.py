"""Run all experiments and write evidence tables + saved arrays.

Experiments:
  1. 5-fold CV (Case 3) WITH physics-informed augmentation   -> cv_aug
  2. 5-fold CV (Case 3) WITHOUT augmentation (ablation)      -> cv_noaug
  3. Coarsening sweep (0.08 / 0.12 / 0.16 / 0.32 deg)        -> coarse_*

Each experiment saves a JSON + npy immediately after finishing so partial
progress survives interruptions.
"""

import json
import os
import sys
import time

import numpy as np

import config
from data_loader import load_data
from train_eval import cross_validate, coarsen


def _save(tag, agg, folds):
    agg = dict(agg, overall_cm=np.asarray(agg["overall_cm"]).tolist())
    out = {
        "agg": agg,
        "per_fold": [
            {"fold": f["fold"], "accuracy": f["accuracy"],
             "f1_micro": f["f1_micro"], "f1_macro": f["f1_macro"],
             "test_idx": [int(i) for i in f["test_idx"]],
             "pred": [int(i) for i in f["pred"]],
             "true": [int(i) for i in f["true"]]}
            for f in folds],
    }
    with open(os.path.join(config.RESULTS_DIR, f"{tag}.json"), "w") as fp:
        json.dump(out, fp, indent=2, default=float)
    np.save(os.path.join(config.RESULTS_DIR, f"{tag}.npy"), out,
            allow_pickle=True)
    return out


def main():
    device = sys.argv[1] if len(sys.argv) > 1 else "cpu"
    if device == "auto":
        import torch
        device = "cuda" if torch.cuda.is_available() else "cpu"
    only = sys.argv[2:] if len(sys.argv) > 2 else []
    print(f"device={device} only={only}", flush=True)

    d = load_data()
    X_exp, y_exp = d["X_exp"], d["y_exp"]
    X_sim, y_sim = d["X_theo"], d["y_theo"]
    tw = d["tw"]

    jobs = {
        "aug": lambda: cross_validate(X_exp, y_exp, X_sim, y_sim, tw,
                                      use_aug=True, device=device),
        "noaug": lambda: cross_validate(X_exp, y_exp, X_sim, y_sim, tw,
                                        use_aug=False, device=device),
    }
    for factor, tag in ((2, "coarse_0.08"), (3, "coarse_0.12"),
                        (4, "coarse_0.16"), (8, "coarse_0.32")):
        Xc, twc = coarsen(X_exp, factor, tw)
        Xsc, _ = coarsen(X_sim, factor)
        jobs[tag] = lambda f=factor, Xc=Xc, twc=twc, Xsc=Xsc: \
            cross_validate(Xc, y_exp, Xsc, y_sim, twc, use_aug=True,
                           device=device, verbose=False)

    for tag, fn in jobs.items():
        if only and tag not in only:
            continue
        t0 = time.time()
        print(f"=== running {tag} ===", flush=True)
        agg, folds = fn()
        _save(tag, agg, folds)
        print(f"=== {tag}: acc {agg['accuracy_mean']:.4f} +/- "
              f"{agg['accuracy_std']:.4f}  f1_macro "
              f"{agg['f1_macro_mean']:.4f}  ({time.time()-t0:.0f}s)", flush=True)


if __name__ == "__main__":
    main()
