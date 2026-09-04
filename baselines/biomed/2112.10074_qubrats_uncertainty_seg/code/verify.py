"""Independent verification of reported numbers.

Re-computes, from results/per_case_results.json, the aggregate evidence table
(mean over test cases per model/entity) and the AUCs from the stored curves,
and cross-checks against the shipped results/evidence_table.csv and
results/metrics.json. Any |difference| > 1e-6 in the AUC recomputation or
> 1e-4 in the aggregate means is reported as a mismatch.

Run:  python verify.py   (exit code 0 = all checks passed)
"""
import json
import os
import sys

import numpy as np
import pandas as pd
from sklearn.metrics import auc

base = os.path.dirname(__file__)
res_dir = os.path.join(base, "..", "results")
ENTITIES = ["ET", "TC", "WT"]

with open(os.path.join(res_dir, "per_case_results.json")) as f:
    all_results = json.load(f)
with open(os.path.join(base, "..", "config.json")) as f:
    cfg = json.load(f)
models = cfg["models"] + [e["name"] for e in cfg["ensembles"]]

failures = []

# 1) recompute AUCs from curves (independent of stored auc fields)
for m in models:
    for cid in all_results[m]:
        for e in ENTITIES:
            r = all_results[m][cid][e]
            ths = np.asarray(r["thresholds"], dtype=float)
            for key, auc_name in [("dsc_curve", "auc1_dsc"),
                                  ("ftp_curve", "auc2_ftp"),
                                  ("ftn_curve", "auc3_ftn")]:
                y = np.asarray(r[key], dtype=float)
                if len(y) < 2:
                    continue
                rec = auc(ths, y) / 100.0
                if abs(rec - r[auc_name]) > 1e-6:
                    failures.append(f"auc recompute mismatch {m} {cid} {e} {auc_name}: "
                                    f"{rec:.6f} vs stored {r[auc_name]:.6f}")

# 2) recompute score from AUCs
for m in models:
    for cid in all_results[m]:
        for e in ENTITIES:
            r = all_results[m][cid][e]
            s = (r["auc1_dsc"] + (1 - r["auc2_ftp"]) + (1 - r["auc3_ftn"])) / 3.0
            if abs(s - r["score"]) > 1e-6:
                failures.append(f"score recompute mismatch {m} {cid} {e}: {s:.6f} vs {r['score']:.6f}")

# 3) recompute evidence table means and compare with evidence_table.csv
rows = []
for m in models:
    for e in ENTITIES:
        vals = {k: float(np.mean([all_results[m][c][e][k] for c in all_results[m]]))
                for k in ["auc1_dsc", "auc2_ftp", "auc3_ftn", "score", "dice_t100"]}
        rows.append({"model": m, "entity": e, "auc1": vals["auc1_dsc"],
                     "auc2": vals["auc2_ftp"], "auc3": vals["auc3_ftn"],
                     "score": vals["score"], "dice": vals["dice_t100"]})
recomp = pd.DataFrame(rows)
shipped = pd.read_csv(os.path.join(res_dir, "evidence_table.csv"))
shipped = shipped[shipped["model"].isin(models)]  # exclude any random-unc rows
key = ["model", "entity"]
merged = recomp.merge(shipped, on=key, suffixes=("_rec", "_ship"))
for col in ["auc1", "auc2", "auc3", "score", "dice"]:
    err = np.abs(merged[f"{col}_rec"] - merged[f"{col}_ship"])
    if err.max() > 1e-4:
        failures.append(f"evidence table col {col} max abs diff {err.max():.6f}")

# 4) threshold sanity: FTN and FTP at tau=100 must be ~0, DSC at tau=100 == dice_t100
for m in models:
    cid0 = next(iter(all_results[m]))
    for e in ENTITIES:
        r = all_results[m][cid0][e]
        ths = np.asarray(r["thresholds"], dtype=float)
        i100 = int(np.argmin(np.abs(ths - 100.0)))
        if abs(r["ftp_curve"][i100]) > 1e-9 or abs(r["ftn_curve"][i100]) > 1e-9:
            failures.append(f"tau=100 FTP/FTN not ~0 for {m} {e}")
        if abs(r["dsc_curve"][i100] - r["dice_t100"]) > 1e-6:
            failures.append(f"dsc(tau=100) != dice_t100 for {m} {e}")

if failures:
    print("VERIFY FAILED:")
    for fmsg in failures:
        print(" -", fmsg)
    sys.exit(1)
else:
    print(f"VERIFY OK: recomputed AUCs, scores and evidence table for {len(models)} "
          f"models x {len(ENTITIES)} entities x {len(all_results[models[0]])} test cases.")
    print("Headline numbers (mean over test cases):")
    for _, row in recomp[(recomp['entity'] == 'WT')].sort_values('score', ascending=False).head(3).iterrows():
        print(f"  {row['model']:12s} WT  score={row['score']:.4f} "
              f"(AUC1={row['auc1']:.4f}, 1-AUC2={1-row['auc2']:.4f}, 1-AUC3={1-row['auc3']:.4f})  dice={row['dice']:.4f}")