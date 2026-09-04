"""Run all classical (local) forecasters over the full frozen panel.

Outputs per-method forecast arrays (length-H test forecast for every series)
into results/forecasts/ as numpy .npz files, plus a series manifest.
"""

from __future__ import annotations

import os
import pickle
import sys
import time
from multiprocessing import Pool

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from baselines.classical import METHOD_FNS, forecast_series
from data_loader import load_data

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results", "forecasts")


def _one(args):
    series, method = args
    fc = forecast_series(series, method)
    return series.dataset, series.frequency, fc


def run_classical(series_list, methods=None, workers=12):
    methods = methods or config.CLASSICAL_METHODS
    os.makedirs(OUT_DIR, exist_ok=True)
    metadata = {
        "n_series": len(series_list),
        "series": [
            {"idx": i, "name": s.name, "dataset": s.dataset,
             "frequency": s.frequency, "horizon": s.horizon,
             "len": int(len(s.values))}
            for i, s in enumerate(series_list)
        ],
    }
    with open(os.path.join(OUT_DIR, "series_manifest.pkl"), "wb") as fh:
        pickle.dump(metadata, fh)

    for method in methods:
        out_path = os.path.join(OUT_DIR, f"classical_{method}.npz")
        if os.path.exists(out_path):
            print(f"[classical] {method}: cached ({os.path.basename(out_path)})")
            continue
        t0 = time.time()
        args_list = [(s, method) for s in series_list]
        with Pool(workers) as pool:
            res = pool.map(_one, args_list, chunksize=8)
        n_ok = 0
        buckets = {}
        for (i, s) in enumerate(series_list):
            fc = res[i][2]
            if fc is None:
                continue
            n_ok += 1
            key = (s.dataset, s.frequency)
            b = buckets.setdefault(key, {"idx": [], "fc": []})
            b["idx"].append(i)
            b["fc"].append(fc)
        out = {"n_ok": n_ok}
        for key, b in buckets.items():
            out[f"{key[0]}_{key[1]}"] = {
                "idx": np.array(b["idx"], dtype=np.int64),
                "fc": np.concatenate([f.reshape(1, -1) for f in b["fc"]], axis=0),
            }
        with open(out_path, "wb") as fh:
            pickle.dump(out, fh)
        print(f"[classical] {method:6s}: {n_ok}/{len(series_list)} series  "
              f"({time.time() - t0:.1f}s) -> {os.path.basename(out_path)}")
    return True


if __name__ == "__main__":
    series_list, meta = load_data()
    run_classical(series_list, workers=config.ARIMA_WORKERS)