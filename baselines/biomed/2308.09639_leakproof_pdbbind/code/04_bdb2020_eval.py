"""Supplementary: evaluate the LP-time-split-trained RF on the external
BDB2020+ benchmark (115 complexes). Affinity target = pKa (-log10(IC50/M)),
the paper's BDB2020+ evaluation scale (paper Table 2; note paper reports the
structural model IGN best: R=0.54, RMSE=1.38; RF-Score retrained: R=0.51,
RMSE=1.61 and DeepDTA retrained: R=0.26, RMSE=1.72).

This is an EXTERNAL, independent benchmark: BDB2020+ is never used for
training or tuning.
"""
import os
import sys
import json

import joblib
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common  # noqa: E402

OUT = os.path.join(common.ROOT, "agent_solution", "results")


def main():
    bdb = common.load_bdb_data()
    # keep all 115 high-quality matches; also report accurate-only for reference
    X, ok = common.rf_features(bdb)
    X = X[ok]
    y = bdb["pka"].values[ok]
    pdb = bdb["pdbid"].values[ok]
    accurate = bdb["accurate"].values[ok]

    results = {}
    rows = []
    for split_type in ["time", "random"]:
        path = os.path.join(OUT, "models", f"rf_{split_type}.joblib")
        if not os.path.exists(path):
            print(f"skip {split_type}: model {path} not found")
            continue
        rf = joblib.load(path)
        pred = rf.predict(X)
        rmse_all = common.rmse(y, pred)
        r_all = common.pearson_r(y, pred)
        acc = accurate.astype(bool)
        rmse_acc = common.rmse(y[acc], pred[acc])
        r_acc = common.pearson_r(y[acc], pred[acc])
        results[split_type] = {
            "n": int(len(y)),
            "rmse_bdb2020plus": rmse_all,
            "pearson_r_bdb2020plus": r_all,
            "rmse_bdb2020plus_accurate": rmse_acc,
            "pearson_r_bdb2020plus_accurate": r_acc,
        }
        rows.append({
            "split_type": "time",
            "model": "rf_ecfp_dipep",
            "dataset": "BDB2020+",
            "rmse_bdb2020plus": rmse_all,
            "pearson_r_bdb2020plus": r_all,
        })
        pd.DataFrame({"pdb_id": pdb, "y_true": y, "y_pred": pred}).to_csv(
            os.path.join(OUT, f"predictions_rf_bdb2020plus_{split_type}.csv"), index=False)
        print(f"[RF-{split_type} on BDB2020+] n={len(y)} RMSE={rmse_all:.3f} R={r_all:.3f} "
              f"(accurate-only RMSE={rmse_acc:.3f} R={r_acc:.3f})")

    with open(os.path.join(OUT, "metrics_bdb2020plus.json"), "w") as f:
        json.dump(results, f, indent=2)


if __name__ == "__main__":
    main()