"""Merge per-element results into a single comprehensive results/metrics.json
(including the paper-anchor comparison and the final claim labels)."""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_analysis import anchor_comparison, claim_verdict, ELEMENTS, MODELS

RESULTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results")


def main():
    elems = {}
    rows = []
    ev_models = ["linear_snap_proxy", "quad_snap_proxy", "kernel_gap_proxy",
                 "mlp_nnp_proxy", "reference_energy_baseline"]
    for el in ELEMENTS:
        with open(os.path.join(RESULTS, "elements_raw", f"{el}.json")) as f:
            rec = json.load(f)
        elems[el] = {"n_train": rec["dataset"]["n_train"],
                     "n_test": rec["dataset"]["n_test"],
                     "n_train_atoms": rec["dataset"]["n_train_atoms"],
                     "n_test_atoms": rec["dataset"]["n_test_atoms"],
                     "train_counts_per_group": rec["dataset"]["train_group_counts"],
                     "test_counts_per_group": rec["dataset"]["test_group_counts"],
                     "models": rec["models"]}
        for model in ev_models:
            md = rec["models"][model]
            for split, ekey, fkey in [("train", "train_energy_mae", "train_force_mae"),
                                      ("test", "test_energy_mae", "test_force_mae")]:
                if model == "reference_energy_baseline":
                    rows.append(dict(element=el, model=model, split=split,
                                     metric="energy_mae_meV_per_atom", value=md[ekey]))
                    continue
                rows.append(dict(element=el, model=model, split=split,
                                 metric="energy_mae_meV_per_atom", value=md[ekey]))
                rows.append(dict(element=el, model=model, split=split,
                                 metric="force_mae_eV_ang", value=md[fkey]))
    import pandas as pd
    pd.DataFrame(rows).to_csv(os.path.join(RESULTS, "evidence_table.csv"), index=False)

    m = {"elements": elems, "protocol": {
        "descriptor": "Behler-Parrinello: 6 G2 radial + 7 shell + 2 angular features, cutoff 5 A, "
                      "all periodic images enumerated, analytic gradients (FD-verified to 1e-9)",
        "models": {"linear_snap_proxy": "SNAP-class linear readout (energy-conserving)",
                   "quad_snap_proxy": "qSNAP-class quadratic readout (energy-conserving)",
                   "kernel_gap_proxy": "GAP-class RBF kernel ridge, 600 basis atoms (energy-conserving)",
                   "mlp_nnp_proxy": "NNP-class 64-64 MLP (direct force + energy heads, non-conservative)"},
        "leakage_protection": "fixed seed=0 80/20 fit/val split for hyper-parameter selection; "
                              "re-fit on full frozen train; frozen test used exactly once",
        "metric_definition": "energy MAE in meV/atom (per-config); force MAE in eV/A (per component)",
        "compute": "CPU, numpy/scipy/sklearn; no external weights or data used beyond the frozen package",
    }}
    ac = anchor_comparison(m)
    out, overall = claim_verdict(ac)
    m["anchor_comparison"] = ac
    m["verdict"] = {"overall": overall,
                    "claims": {k: {"label": v, "note": note} for k, v, note in out}}
    with open(os.path.join(RESULTS, "metrics.json"), "w") as f:
        json.dump(m, f, indent=2, default=lambda o: (
            int(o) if isinstance(o, np.integer) else float(o)
            if isinstance(o, np.floating) else o.tolist() if isinstance(o, np.ndarray)
            else str(o)))
    print("merged metrics.json written; overall verdict:", overall)


if __name__ == "__main__":
    main()