"""Zero-shot Chronos evaluation (chronos-t5-small, local frozen checkpoint).

  python run_chronos.py [--context 100|512] [--device gpu]

Protocol: for each day in the test segment, feed the previous `context`
observations of the station's own water level (raw values, strictly past) into
Chronos and take the median of `num_samples` sampled 28-step futures. No
fine-tuning, no test data touched during any fitting step.
"""
from __future__ import annotations

import argparse
import os
import sys

import numpy as np
import pandas as pd
import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common  # noqa: E402
from common import (CONTEXT_LEN, HORIZON, LEADS, N_DAYS, TEST_LO, TEST_HI, TARGETS)

MODEL_DIR = os.environ.get(
    "CHRONOS_DIR",
    "/mnt/c/Users/Administrator/.cache/chronos-local/chronos-t5-small",
)
RESULTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")


def point_forecast(pipeline, series: np.ndarray, context_len: int,
                   prediction_length: int, num_samples: int, device) -> np.ndarray:
    """One univariate forecast -> median over samples, (prediction_length,) raw units."""
    ctx = torch.from_numpy(series.astype(np.float32))  # tokenizer runs on CPU
    with torch.no_grad():
        preds = pipeline.predict(
            inputs=ctx.view(1, -1), prediction_length=prediction_length,
            num_samples=num_samples, limit_prediction_length=False)
    pred = preds.median(dim=1).values[0].cpu().numpy()  # (prediction_length,)
    return pred


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--context", type=int, default=100, choices=[100, 512])
    ap.add_argument("--device", choices=["cpu", "gpu"], default="cpu")
    ap.add_argument("--num-samples", type=int, default=20)
    args = ap.parse_args()

    dev = torch.device("cuda" if args.device == "gpu" and torch.cuda.is_available() else "cpu")
    print(f"[chronos] device={dev}", flush=True)

    from chronos import ChronosPipeline
    pipeline = ChronosPipeline.from_pretrained(MODEL_DIR)
    if dev.type == "cuda":
        pipeline.model = pipeline.model.to(dev)

    df = common.load_data()
    common.verify_dataframe(df)
    Y = df[TARGETS].astype(np.float64).to_numpy()

    ctx_max = min(args.context, TEST_LO - 1)  # enough history for first test day
    preds_all = np.zeros((TEST_HI - TEST_LO, HORIZON, len(TARGETS)), dtype=np.float32)
    for j, st in enumerate(TARGETS):
        series = Y[:, j]
        for i, t in enumerate(range(TEST_LO, TEST_HI)):
            past = series[max(0, t - ctx_max): t]           # strictly before origin t
            p = point_forecast(pipeline, past, ctx_max, HORIZON, args.num_samples, dev)
            preds_all[i, :, j] = p[:HORIZON]

    # --- error aggregation identical to task-specific models -----------------
    rows = []
    for si in range(HORIZON):
        lead = si + 1
        if lead not in LEADS:
            continue
        avail = np.where(TEST_LO + np.arange(preds_all.shape[0]) + si < N_DAYS)[0]
        f = preds_all[avail, si, :]
        td = TEST_LO + avail + si
        y = Y[td]
        err = f - y
        for j, st in enumerate(TARGETS):
            e = err[:, j]
            rows.append({"model": f"Chronos_c{args.context}", "lead": lead, "station": st,
                         "mae": float(np.abs(e).mean()),
                         "rmse": float(np.sqrt((e ** 2).mean())), "n": int(len(e))})
    frame = pd.DataFrame(rows)
    os.makedirs(RESULTS_DIR, exist_ok=True)
    name = f"chronos_c{args.context}"
    frame.to_csv(os.path.join(RESULTS_DIR, f"metrics_{name}.csv"), index=False)
    agg = frame.groupby(["model", "lead"])[["mae", "rmse"]].mean().reset_index()
    agg.to_csv(os.path.join(RESULTS_DIR, f"evidence_{name}.csv"), index=False)
    np.savez_compressed(os.path.join(RESULTS_DIR, f"predictions_{name}.npz"),
                        preds=preds_all, dates=df["date"].values[TEST_LO:TEST_HI],
                        targets=TARGETS)
    print(agg.to_string(index=False))


if __name__ == "__main__":
    main()