"""Main runner: for every frozen series and every model, train (deep models)
or fit (IsolationForest) on the training period, calibrate on validation,
detect on the test period and return NAB-style raw scores.

All random components are seeded; the whole run is embarrassingly parallel
over CPU cores (torch threads pinned to 1 per worker) so it stays CPU-friendly.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import zlib
from multiprocessing import Pool

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common import (default_data_root, load_nab_series, load_microsoft_series,
                    prepare_series, time_split, zscore_fit, zscore_apply)
import nab_scorer as ns
import train as tr
from models import build_model
from isolation_forest import fit_if, compute_per_point_if_score

DEEP_MODELS = ["GRU", "TCN", "Transformer", "TSMixer"]
ALL_MODELS = DEEP_MODELS + ["IsolationForest"]

GLOBAL_SEED = int(os.environ.get("NAB_SEED", "0"))


def serialize_raw(series_raw):
    return {
        "tp": float(series_raw.tp), "fp": float(series_raw.fp),
        "tn": float(series_raw.tn), "fn": int(series_raw.fn),
        "n_windows": int(series_raw.n_windows),
        "weighted": float(series_raw.weighted),
    }


def _run_one(job):
    series, model, seed, th_grid = job
    cal_kw = {}
    if th_grid is not None:
        cal_kw["th_grid"] = th_grid
    try:
        prep = prepare_series(series)
        vals = prep["values"]
        n = prep["n"]
        tr_lo, tr_hi = prep["train"].start, prep["train"].stop
        vl_lo, vl_hi = prep["val"].start, prep["val"].stop
        te_lo, te_hi = prep["test"].start, prep["test"].stop
        n_train = tr_hi - tr_lo
        val_len = vl_hi - vl_lo
        test_windows_full = prep["test_windows"]
        test_windows_local = [(s - te_lo, e - te_lo) for (s, e) in test_windows_full]
        n_test = te_hi - te_lo

        mu, sd = zscore_fit(vals[tr_lo:tr_hi])
        z_all = zscore_apply(vals, mu, sd)

        wlen = tr.fit_early_stopping_window_sizes(n_train, val_len)

        if model == "IsolationForest":
            m = fit_if(z_all[tr_lo:tr_hi], wlen, seed=seed)
            scores_full = compute_per_point_if_score(m, z_all, wlen)
            calib = tr.calibrate(scores_full, vl_lo, vl_hi, te_lo, n_test,
                                 test_windows_full, model_tag=model, **cal_kw)
        else:
            mdl = build_model(model, wlen, seed=seed)
            mdl, best_nll = tr.train_ae(mdl, z_all[tr_lo:tr_hi], z_all[vl_lo:vl_hi],
                                        seed=seed)
            scores_full = tr.compute_per_point_nll(mdl, z_all)
            calib = tr.calibrate(scores_full, vl_lo, vl_hi, te_lo, n_test,
                                 test_windows_full, model_tag=model, **cal_kw)

        test_scores = scores_full[te_lo:te_hi]
        detections = tr.apply_detector(calib["rule"], test_scores)
        # detections are offsets in test space; map to test-local reality
        score = ns.score_series(detections, test_windows_local, n_test)
        null = ns.null_score(test_windows_local, n_test)
        ideal = ns.ideal_score(test_windows_local, n_test)
        per_series_nab = ns.aggregate_and_normalize([score], [null], [ideal])

        return {
            "dataset": series["dataset"],
            "subgroup": series["subgroup"],
            "file": series["file"],
            "model": model,
            "has_anomaly_in_test": bool(prep["has_anomaly_in_test"]),
            "n_test": int(n_test),
            "n_train": int(n_train),
            "wlen": int(wlen),
            "W": int(calib["W"]), "Wp": int(calib["Wp"]),
            "theta": float(calib["theta"]),
            "val_metric": float(calib["val_metric"]),
            "n_detections": int(len(detections)),
            "n_windows_test": int(len(test_windows_local)),
            "nab_score": float(per_series_nab),
            "raw": serialize_raw(score),
            "null": serialize_raw(null),
            "ideal": serialize_raw(ideal),
            "ok": True,
        }
    except Exception as ex:  # noqa: BLE001
        return {
            "dataset": series["dataset"],
            "subgroup": series["subgroup"],
            "file": series["file"],
            "model": model,
            "has_anomaly_in_test": None,
            "n_test": None, "n_train": None, "wlen": None,
            "W": None, "Wp": None, "theta": None,
            "val_metric": None, "n_detections": None, "n_windows_test": None,
            "nab_score": None, "raw": None, "null": None, "ideal": None,
            "ok": False, "error": repr(ex),
        }


def raw_to_score(r):
    return ns.SeriesRawScore(**{k: r[k] for k in ("tp", "fp", "tn", "fn", "n_windows")})


def aggregate_by_subgroup(rows):
    """Aggregate raw scores per (dataset, subgroup, model) and normalize as
    NAB does over a group of files."""
    out = {}
    for r in rows:
        key = (r["dataset"], r["subgroup"], r["model"])
        out.setdefault(key, []).append(r)
    aggregated = []
    for (dataset, subgroup, model), rlist in out.items():
        ok = [r for r in rlist if r["ok"] and r["raw"] is not None]
        if not ok:
            continue
        tot = ns.SeriesRawScore()
        null = ns.SeriesRawScore()
        ideal = ns.SeriesRawScore()
        for r in ok:
            tot = tot + raw_to_score(r["raw"])
            null = null + raw_to_score(r["null"])
            ideal = ideal + raw_to_score(r["ideal"])
        nab = ns.aggregate_and_normalize(
            [raw_to_score(r["raw"]) for r in ok],
            [raw_to_score(r["null"]) for r in ok],
            [raw_to_score(r["ideal"]) for r in ok])
        has_any_anom = int(any(r["has_anomaly_in_test"] for r in ok))
        rows_ok = len(ok)
        rows_all = len(rlist)
        aggregated.append({
            "dataset": dataset, "subgroup": subgroup, "model": model,
            "nab_score": nab,
            "n_series": rows_ok,
            "has_anomaly_in_test_any": has_any_anom,
            "raw_total": serialize_raw(tot),
            "null_total": serialize_raw(null),
            "ideal_total": serialize_raw(ideal),
            "n_failed": rows_all - rows_ok,
        })
    return aggregated


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", default=",".join(ALL_MODELS))
    ap.add_argument("--datasets", default="nab,microsoft")
    ap.add_argument("--only-subgroups", default="")
    ap.add_argument("--jobs", type=int, default=16)
    ap.add_argument("--seed", type=int, default=GLOBAL_SEED)
    ap.add_argument("--outdir", default=os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "results"))
    ap.add_argument("--th-grid", default="", help="comma list of detection thresholds; "
                    "empty = default grid")
    ap.add_argument("--smoke", action="store_true",
                    help="run only a single series/model to time the pipeline")
    args = ap.parse_args()

    th_grid = None
    if args.th_grid:
        th_grid = [float(x) for x in args.th_grid.split(",")]

    models = [m for m in args.models.split(",") if m]
    datasets = args.datasets.split(",")
    only_sub = [s for s in args.only_subgroups.split(",") if s]

    series_all = []
    if "nab" in datasets:
        series_all += load_nab_series()
    if "microsoft" in datasets:
        series_all += load_microsoft_series()
    if only_sub:
        series_all = [s for s in series_all if s["subgroup"] in only_sub]

    jobs = [(s, m, args.seed + zlib.crc32(s["file"].encode()), th_grid)
            for s in series_all for m in models]

    if args.smoke:
        jobs = jobs[:8]

    os.makedirs(args.outdir, exist_ok=True)
    t0 = time.time()
    results = []
    csv_path = os.path.join(args.outdir, "series_raw.csv")
    partial_path = csv_path + ".partial"
    if len(jobs) <= args.jobs * 2:
        for j in jobs:
            results.append(_run_one(j))
    else:
        with Pool(args.jobs, maxtasksperchild=1) as pool:
            for i, res in enumerate(pool.imap_unordered(_run_one, jobs, chunksize=2)):
                results.append(res)
                if (i + 1) % 40 == 0:
                    el = time.time() - t0
                    print(f"[{i+1}/{len(jobs)}] elapsed {el:.0f}s "
                          f"eta {(el/(i+1))*(len(jobs)-i-1):.0f}s", flush=True)
                    pd.DataFrame(results).to_csv(partial_path, index=False)
    total_time = time.time() - t0

    df = pd.DataFrame(results)
    df.to_csv(csv_path, index=False)
    if os.path.exists(partial_path):
        os.remove(partial_path)

    agg = aggregate_by_subgroup(results)
    agg_with_calib = []
    for a in agg:
        sub = df[(df["dataset"] == a["dataset"]) & (df["subgroup"] == a["subgroup"])
                 & (df["model"] == a["model"]) & df["W"].notna()]
        if len(sub):
            med = lambda c: float(np.median(sub[c].to_numpy()))
            cal = f"W={med('W'):g},W'={med('Wp'):g},theta={med('theta'):.2f} (grid on val)"
        else:
            cal = "grid on val"
        a = dict(a)
        a["calibration"] = cal
        agg_with_calib.append(a)

    evidence_df = pd.DataFrame([
        {"dataset": a["dataset"], "subgroup": a["subgroup"], "model": a["model"],
         "nab_score": round(float(a["nab_score"]), 4),
         "has_anomaly_in_test": int(a["has_anomaly_in_test_any"]),
         "calibration": a["calibration"]}
        for a in agg_with_calib])
    evidence_df = evidence_df.sort_values(["dataset", "subgroup", "model"])
    evidence_path = os.path.join(args.outdir, "evidence_table.csv")
    evidence_df.to_csv(evidence_path, index=False)

    metrics = {
        "seed": args.seed,
        "models": models,
        "th_grid": args.th_grid,
        "n_jobs": len(jobs),
        "n_ok": int(df["ok"].sum()),
        "n_failed": int((~df["ok"]).sum()),
        "elapsed_seconds": round(total_time, 1),
        "frozen_data_facts": {
            "nab_series_csv": 58,
            "nab_subgroups": 7,
            "microsoft_series_csv": 60,
            "microsoft_domains": 9,
            "microsoft_total_rows": 225445,
            "microsoft_label1": 4555,
        },
        "subgroup_summary": agg_with_calib,
        "failed": [json.dumps(r) for r in results if not r["ok"]],
    }
    with open(os.path.join(args.outdir, "metrics.json"), "w") as fh:
        json.dump(metrics, fh, indent=2, default=str)

    print(f"\nFinished in {total_time:.1f}s. wrote "
          f"{csv_path}, {evidence_path}, metrics.json")


if __name__ == "__main__":
    main()