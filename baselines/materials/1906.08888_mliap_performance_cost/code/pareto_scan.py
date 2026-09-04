"""Accuracy vs. model expense (degrees of freedom) scan on the Mo system,
mirroring the paper's Figure 2 (Pareto front view).

Expensive = trainable parameter count proxy:
  - linear SNAP proxy:         D + 1
  - quadratic SNAP proxy:      D + D(D+1)/2 + 2
  - kernel GAP proxy:          n_basis + 2 (swept over basis sizes)
  - MLP NNP proxy:             (# params of 64-64-4 MLP incl. both heads)  [single point]

Each model refit here uses the same inner-validation-tuned hyper-parameters as
run_pipeline.py for Mo (only the n_basis changes for the kernel scan).
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import energy_models as EM
from dataset import SplitData

RESULTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results")
CACHE = os.path.join(RESULTS, "_cache")
SEED = 0
D_DIM = 15


def main():
    tr = SplitData("Mo", "train", CACHE)
    te = SplitData("Mo", "test", CACHE)
    out = {}

    def add(name, npar, testE, testF, trE=None):
        out[name] = dict(n_params=int(npar), test_energy_mae=float(testE),
                         test_force_mae=float(testF), train_energy_mae=float(trE) if trE else None)

    # linear (tuned on Mo) and quadratic (tuned on Mo)
    mL = EM.LinearEQModel(alpha=0.04961947603002908, lambda_f=0.1).fit(tr, list(range(tr.n_configs)))
    mE, mF, _, _ = EM.batch_metrics_eval(mL, te, list(range(te.n_configs)))
    add("linear_snap_proxy", D_DIM + 1, mE, mF)

    mQ = EM.QuadEQModel(alpha=0.04961947603002908).fit(tr, list(range(tr.n_configs)))
    mE, mF, _, _ = EM.batch_metrics_eval(mQ, te, list(range(te.n_configs)))
    add("quad_snap_proxy", D_DIM + D_DIM * (D_DIM + 1) // 2 + 2, mE, mF)

    for nb in [50, 100, 200, 400, 600, 800]:
        mk = EM.KernelEQModel(gamma=0.003, alpha=0.01, n_basis=nb, seed=SEED)
        mk.fit(tr, list(range(tr.n_configs)))
        mE, mF, _, _ = EM.batch_metrics_eval(mk, te, list(range(te.n_configs)))
        add(f"kernel_gap_proxy_n{nb}", nb + 2, mE, mF)

    # MLP point: count parameters of the two MLP heads (64-64-... + output)
    mM = EM.MLPForceModel(hidden=(64, 64), max_iter=500, seed=SEED)
    mM.fit(tr, list(range(tr.n_configs)))
    mE, mF, _, _ = EM.batch_metrics_eval(mM, te, list(range(te.n_configs)))
    p1 = sum(np.prod(w.shape) for w in mM.mlpF.coefs_) + sum(len(b) for b in mM.mlpF.intercepts_)
    p2 = sum(np.prod(w.shape) for w in mM.mlpE.coefs_) + sum(len(b) for b in mM.mlpE.intercepts_)
    add("mlp_nnp_proxy", p1 + p2, mE, mF)

    with open(os.path.join(RESULTS, "mo_pareto_scan.json"), "w") as f:
        json.dump(out, f, indent=2)
    for k, v in out.items():
        print(f"  {k:22s} params={v['n_params']:7d}  testE={v['test_energy_mae']:8.2f} meV  "
              f"testF={v['test_force_mae']:.3f}")


if __name__ == "__main__":
    main()