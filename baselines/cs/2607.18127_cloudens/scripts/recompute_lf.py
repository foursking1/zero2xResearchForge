"""Recompute the LF (likelihood) rows of grid/evidence files with the corrected
global-pooled median/IQR normalisation, reusing the cached MD rows + recon errors.

    python scripts/recompute_lf.py [outdir]
"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "."))

import run_repro as R
from scoring import likelihood_scores
from utils import get_full_nab_result, detection_dict_to_columns, fmt_id_list

LF_THRESHOLDS = R.LF_THRESHOLDS


def main():
    outdir = sys.argv[1] if len(sys.argv) > 1 else R.RESULTS
    bundle, split, *_ = R.get_split(device="cpu", batch=32)
    for mn in ("GRU", "ClouDens"):
        recon = np.load(os.path.join(outdir, f"recon_errors_{mn}.npy"))
        lik = likelihood_scores(recon, long_window=30, short_window=2, topk=1)
        rows = []
        for lt in LF_THRESHOLDS:
            alarms = (lik > lt).astype(int)
            res_s = get_full_nab_result(alarms, split["test_labels"], split["test_index"],
                                        bundle.anomaly_windows_test)["standard"]
            res_r = get_full_nab_result(alarms, split["test_labels"], split["test_index"],
                                        bundle.anomaly_windows_test)["reward_fn"]
            d = detection_dict_to_columns(res_s["detection_counters"])
            rows.append({
                "strategy": "likelihood", "threshold": lt,
                "TP": res_s["TP"], "TN": res_s["TN"], "FP": res_s["FP"], "FN": res_s["FN"],
                "tp_windows": res_s["tp_windows"],
                "nab_standard": res_s["normalized"], "nab_lowfn": res_r["normalized"],
                "detected_issue_total": 3, "detected_im_total": 9, "detected_testlog_total": 7,
                "detected_issue_ids": fmt_id_list(d["issue_ids"]),
                "detected_im_ids": fmt_id_list(d["im_ids"]),
                "detected_testlog_ids": fmt_id_list(d["testlog_ids"]),
                "n_alarms": int(alarms.sum()), "lt": lt, "perc": np.nan,
            })
        lf_df = pd.DataFrame(rows)
        gpath = os.path.join(outdir, f"grid_{mn}.csv")
        g = pd.read_csv(gpath)
        g = g[g["strategy"] != "likelihood"]
        g["lt"] = np.nan
        g = pd.concat([g, lf_df], ignore_index=True)
        g.to_csv(gpath, index=False)
        print(f"[{mn}] LF rows updated ->\n{lf_df[['threshold','TP','FP','nab_standard','nab_lowfn']].to_string(index=False)}")
    R.build_evidence(
        {"GRU": pd.read_csv(os.path.join(outdir, "grid_GRU.csv")),
         "ClouDens": pd.read_csv(os.path.join(outdir, "grid_ClouDens.csv"))},
        os.path.join(outdir, "evidence_table.csv"))


if __name__ == "__main__":
    main()