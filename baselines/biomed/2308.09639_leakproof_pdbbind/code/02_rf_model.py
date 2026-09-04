"""Q2/Q3 anchor: Random Forest (RF-Score-like) with ligand Morgan ECFP4
fingerprints + protein dipeptide-composition features.

Protocol (mirrors the paper):
  * time split: train on LP train (CL1 & non-covalent), early-stop/tune on LP
    val (CL1 & non-covalent), evaluate on LP test CL2 non-covalent (2171).
  * random split control: identical setup but splits reassigned at random with
    a fixed seed (0); evaluated on the SAME LP test CL2 non-covalent subset.

Outputs:
  results/evidence_table.csv (RF rows)
  results/metrics_rf.json
  results/predictions_rf_<split>.csv
"""
import os
import sys
import json

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common  # noqa: E402

OUT = os.path.join(common.ROOT, "agent_solution", "results")
SEED = common.SEED


def select_cl1_noncov(df):
    """Rows satisfying CL1 & non-covalent (paper's training protocol)."""
    return df[(df["CL1"].astype(str) == "True")
              & (df["covalent"].astype(str) == "False")].copy()


def main():
    os.makedirs(OUT, exist_ok=True)
    df = common.load_lp_data()

    te = df[(df["split"] == "test") & (df["CL2"].astype(str) == "True")
            & (df["covalent"].astype(str) == "False")].copy()
    X_te, te_ok = common.rf_features(te)
    X_te = X_te[te_ok]
    y_te = te["pki"].values[te_ok]
    n_test = int(te_ok.sum())
    assert n_test == common.TEST_CL2_NONCOV_N, (n_test, common.TEST_CL2_NONCOV_N)

    rows = []

    for split_type, label_x in [("time", "Time-based split"), ("random", "Random split (seed=%d)" % SEED)]:
        if split_type == "time":
            split_df = df
        else:
            split_df = common.add_random_split(df, seed=SEED)
        trn = select_cl1_noncov(split_df[split_df["split"] == "train"])
        X, ok = common.rf_features(trn)
        X = X[ok]
        y = trn["pki"].values[ok]
        # validation rows: same selection but from val split
        va = select_cl1_noncov(split_df[split_df["split"] == "val"])
        Xval, val_ok = common.rf_features(va)
        Xval = Xval[val_ok]
        yval = va["pki"].values[val_ok]

        rf = RandomForestRegressor(n_estimators=300, random_state=SEED, n_jobs=8)
        rf.fit(X, y)

        pred_tr = rf.predict(X)
        pred_val = rf.predict(Xval)
        pred_te = rf.predict(X_te)

        rmse_tr = common.rmse(y, pred_tr)
        rmse_val = common.rmse(yval, pred_val)
        rmse_te = common.rmse(y_te, pred_te)
        r_te = common.pearson_r(y_te, pred_te)

        rows.append({
            "split_type": split_type,
            "split_label": label_x,
            "model": "rf_ecfp_dipep",
            "train_n": int(len(y)),
            "val_n": int(len(yval)),
            "rmse_train": rmse_tr,
            "rmse_val": rmse_val,
            "rmse_test_cl2_noncov": rmse_te,
            "pearson_r": r_te,
            "n_test_cl2_noncov": n_test,
        })
        os.makedirs(os.path.join(OUT, "models"), exist_ok=True)
        joblib.dump(rf, os.path.join(OUT, "models", f"rf_{split_type}.joblib"))
        pd.DataFrame({
            "pdb_id": te["pdb_id"].values[te_ok],
            "y_true": y_te,
            "y_pred": pred_te,
            "split": split_type,
        }).to_csv(os.path.join(OUT, f"predictions_rf_{split_type}.csv"), index=False)
        print(f"[RF-{split_type}] train={rmse_tr:.3f} val={rmse_val:.3f} "
              f"test={rmse_te:.3f} R={r_te:.3f} (n={n_test})")

    ev = pd.DataFrame(rows)
    path = os.path.join(OUT, "evidence_table.csv")
    if os.path.exists(path):
        prev = pd.read_csv(path)
        prev = prev[prev["model"] != "rf_ecfp_dipep"]
        ev = pd.concat([prev, ev], ignore_index=True)
    ev.to_csv(path, index=False)

    with open(os.path.join(OUT, "metrics_rf.json"), "w") as f:
        json.dump(rows, f, indent=2)
    print("saved evidence_table.csv / metrics_rf.json")


if __name__ == "__main__":
    main()