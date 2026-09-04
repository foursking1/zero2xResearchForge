"""Reference / simple baselines (persistence, moving-average, naive trend) under
the same rolling protocol. These are diagnostics for the report; they show the
data's intrinsic predictability floor and place the learned models in context.

  python run_baselines.py
"""
from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common  # noqa: E402
from common import (HORIZON, LEADS, N_DAYS, TEST_LO, TEST_HI, TARGETS)

RESULTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")


def run(model_id: str, pred_fn) -> pd.DataFrame:
    df = common.load_data()
    common.verify_dataframe(df)
    Y = df[TARGETS].astype(np.float64).to_numpy()
    rows = []
    for t in range(TEST_LO, TEST_HI):
        yctx = Y[max(0, t - 100): t]                      # past 100 target observations
        for si in range(HORIZON):
            if t + si < N_DAYS:
                yhat = pred_fn(yctx, si)
                for j, st in enumerate(TARGETS):
                    rows.append({"model": model_id, "lead": si + 1, "station": st,
                                 "mae": float(abs(yhat[j] - Y[t + si, j])),
                                 "rmse": float((yhat[j] - Y[t + si, j]) ** 2),
                                 "n": 1})
    fr = pd.DataFrame(rows)
    agg = pd.DataFrame([
        {"model": model_id, "lead_time": lead,
         "overall_mae": float(fr[fr.lead == lead].groupby("station")["mae"].mean().mean()),
         "overall_rmse": float(np.sqrt(fr[fr.lead == lead].groupby("station")["rmse"].mean().mean())),
         }
        for lead in LEADS])
    return fr, agg


def main() -> None:
    baselines = {
        "persistence": lambda yc, si: yc[-1],
        "mean_last7": lambda yc, si: yc[-7:].mean(axis=0),
        "mean_last30": lambda yc, si: yc[-30:].mean(axis=0),
    }
    os.makedirs(RESULTS_DIR, exist_ok=True)
    agg_all = []
    for mid, fn in baselines.items():
        fr, agg = run(mid, fn)
        fr.to_csv(os.path.join(RESULTS_DIR, f"metrics_{mid}.csv"), index=False)
        agg_all.append(agg)
    allagg = pd.concat(agg_all, ignore_index=True)
    allagg.to_csv(os.path.join(RESULTS_DIR, "evidence_baselines.csv"), index=False)
    print(allagg.to_string(index=False))


if __name__ == "__main__":
    main()