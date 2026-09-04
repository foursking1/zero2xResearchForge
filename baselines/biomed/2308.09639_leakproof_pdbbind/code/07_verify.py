"""07_verify.py -- cheap judge-side verification of the two B-spot-check fields
without re-running the CNN:

  field 1: results/evidence_table.csv  -> RF time-split rmse_test_cl2_noncov
  field 2: leakage_stats.csv           -> ligand cross train/test hit counts

It re-derives BOTH numbers straight from the frozen data:
  * leakage: recomputes ligand(train->test) for time & random split (fast)
  * RF time-model RMSE: re-fits the RF on time split (CL1 & non-covalent) and
    evaluates on LP test CL2 non-covalent (2-4 min on CPU).

Exit code 0 if the reproduced numbers match the submitted files (>0.1% abs).
"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common  # noqa: E402
from sklearn.ensemble import RandomForestRegressor  # noqa: E402

OUT = os.path.join(common.ROOT, "agent_solution", "results")


def recompute_leakage():
    df = common.load_lp_data()
    errs = []
    for tag in ["time", "random"]:
        d = df if tag == "time" else common.add_random_split(df, seed=0)
        d = common.add_ligand_ids(d)
        tr = set(d.loc[d["split"] == "train", "_lig"].dropna())
        te = d.loc[d["split"] == "test"]
        hit = int(te["_lig"].isin(tr).sum())
        # match submitted leakage_stats.csv values
        lc = pd.read_csv(os.path.join(OUT, "leakage_stats.csv"))
        sub = int(lc.loc[lc["tag"] == tag, "train->test_lig_hit"].iloc[0])
        errs.append(abs(hit - sub) / max(sub, 1))
        print(f"  leakage ligand train->test [{tag}] reproduced={hit} submitted={sub}")
    return max(errs) if errs else 1


def recompute_rf_time_rmse():
    df = common.load_lp_data()
    trn = common.select_cl1_noncov(df[df["split"] == "train"])
    X, ok = common.rf_features(trn)
    y = trn["pki"].values[ok]
    rf = RandomForestRegressor(n_estimators=300, random_state=0, n_jobs=8)
    rf.fit(X[ok], y)
    te = df[(df["split"] == "test") & (df["CL2"].astype(str) == "True")
            & (df["covalent"].astype(str) == "False")]
    Xte, okte = common.rf_features(te)
    pred = rf.predict(Xte[okte])
    rmse = common.rmse(te["pki"].values[okte], pred)
    ev = pd.read_csv(os.path.join(OUT, "evidence_table.csv"))
    sub = float(ev[(ev["model"] == "rf_ecfp_dipep") & (ev["split_type"] == "time")]
                ["rmse_test_cl2_noncov"].iloc[0])
    rel = abs(rmse - sub) / abs(sub)
    print(f"  RF time RMSE(test CL2 non-cov) reproduced={rmse:.4f} submitted={sub:.4f} rel={rel:.4%}")
    return rel


def main():
    e1 = recompute_leakage()
    e2 = recompute_rf_time_rmse()
    ok = e1 < 0.001 and e2 < 0.001
    print("VERIFY:", "PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()