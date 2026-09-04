"""End-to-end pipeline: load frozen data + forecasts -> multi-view SMAPE eval
-> results/evidence_table.csv and results/metrics.json (+ figures in
results/figures/).

Expected inputs (produced by baselines/run_classical.py and
method/run_nhits.py): results/forecasts/classical_*.npz, nhits_*.npz.
"""

from __future__ import annotations

import json
import os
import pickle
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from data_loader import load_data
from protocols.evaluation import (ForecastStore, anomaly_mask,
                                  build_evidence_table, difficult_series_mask,
                                  winloss_table)

BASE = os.path.dirname(os.path.abspath(__file__))
RES_DIR = os.path.join(BASE, "results")
FC_DIR = os.path.join(RES_DIR, "forecasts")
FIG_DIR = os.path.join(RES_DIR, "figures")
METHODS = ["NHITS", "SNaive", "Theta", "SES", "ETS", "RWD", "ARIMA"]


def load_forecasts(series_list):
    store = ForecastStore(series_list)
    # classical (per method, grouped by dataset/frequency)
    for method in ["SNaive", "Theta", "SES", "ETS", "RWD", "ARIMA"]:
        path = os.path.join(FC_DIR, f"classical_{method}.npz")
        data = pickle.load(open(path, "rb"))
        bykey = {}
        for k in config.DATASETS:
            for fr in config.FREQUENCIES:
                key = f"{k}_{fr}"
                if key in data:
                    bykey[(k, fr)] = (data[key]["idx"], data[key]["fc"])
        store.add_forecasts(method, bykey)
    # nhits (per frequency, padded to output_horizon; masked by horizon in eval)
    nhits_bykey = {}
    for fr in config.FREQUENCIES:
        path = os.path.join(FC_DIR, f"nhits_{fr}.npz")
        data = pickle.load(open(path, "rb"))
        idx, fcm = data["idx"], data["fc"]
        for k in config.DATASETS:
            sub_pos = [i for i, gi in enumerate(idx)
                       if series_list[int(gi)].frequency == fr]
            # group explicitly by dataset to keep scope keys
            groups = {}
            for p in sub_pos:
                gi = int(idx[p])
                d = series_list[gi].dataset
                groups.setdefault(d, {"idx": [], "fc": []})
                groups[d]["idx"].append(gi)
                groups[d]["fc"].append(fcm[p])
            for d, g in groups.items():
                nhits_bykey[(d, fr)] = (np.array(g["idx"]), np.stack(g["fc"]))
    store.add_forecasts("NHITS", nhits_bykey)
    return store


def main():
    series_list, meta = load_data()
    store = load_forecasts(series_list)
    print("methods:", store.methods())

    # series-level SMAPE matrix (for win-rate and condition definitions)
    per_series = {m: np.array([store.series_smape(m, gi)
                               for gi in range(len(series_list))])
                  for m in store.methods()}

    smapes, thr, diff_mask = difficult_series_mask(series_list, store)

    # ---- evidence table ----------------------------------------------------
    rows = build_evidence_table(store, series_list)
    wl = winloss_table(store, series_list)
    import pandas as pd
    df = pd.DataFrame(rows)
    for key in ("thr_meta",):
        if key in df.columns:
            df[key] = df[key].fillna("")
    wl_df = pd.DataFrame(wl)
    out_csv = os.path.join(RES_DIR, "evidence_table.csv")
    wl_csv = os.path.join(RES_DIR, "winloss_table.csv")
    df.to_csv(out_csv, index=False)
    wl_df.to_csv(wl_csv, index=False)
    print(f"[res] evidence tables -> {out_csv}, {wl_csv}")

    with open(os.path.join(RES_DIR, "per_series_smape.pkl"), "wb") as fh:
        pickle.dump({"per_series": per_series,
                     "difficult_mask": diff_mask,
                     "difficult_threshold": float(thr),
                     "series_keys": [(s.dataset, s.frequency, s.name)
                                     for s in series_list]}, fh)

    # ---- metrics.json ------------------------------------------------------
    metrics = {
        "data_facts": {
            "datasets": config.DATASETS,
            "n_series_total": len(series_list),
            "n_series": {f"{k[0]}:{k[1]}": v["n"] for k, v in meta.items()},
            "horizon": {f"{k[0]}:{k[1]}": v["horizon"] for k, v in meta.items()},
            "test_split": "last H observations per series (H from @horizon)",
            "smape": "100%/n sum |yhat-y| / ((|yhat|+|y|)/2), 0/0 -> 0",
        },
        "view": {},
        "winloss": {},
        "conditions": {
            "difficult_series_snaive_quantile": config.COND_DIFFICULT_QUANTILE,
            "difficult_series_threshold_smape": float(thr),
            "anomaly_ci": config.COND_ANOMALY_CI,
            "n_difficult_series": int(diff_mask.sum()),
            "n_anomaly_points": int(anomaly_mask_count(series_list)),
            "n_total_points": int(sum(s.horizon for s in series_list)),
        },
    }
    overall = {r["method"]: r for r in rows if r["view"] == "overall" and r["dataset"] == "All"}
    metrics["view"]["overall_all"] = {m: d["smape"] for m, d in overall.items()}
    for r in rows:
        key = (r["view"], r.get("dataset", "All"), r.get("condition", ""))
        metrics["view"].setdefault("-".join(map(str, key)), {})[r["method"]] = r["smape"]
    for r in wl:
        metrics["winloss"].setdefault(r["condition"], dict()).setdefault(r["method"], {
            "wins": r["wins"], "losses": r["losses"], "ties": r["ties"],
            "win_rate": round(float(r["win_rate"]), 4)})
    with open(os.path.join(RES_DIR, "metrics.json"), "w") as fh:
        json.dump(metrics, fh, indent=2)
    print("[res] written results/metrics.json")
    return metrics, per_series


def anomaly_mask_count(series_list):
    return int(anomaly_mask(series_list).sum())


if __name__ == "__main__":
    main()