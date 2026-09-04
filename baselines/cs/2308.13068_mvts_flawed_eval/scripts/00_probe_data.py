"""Probe and verify the frozen datasets (sanity + frozen-fact checks).

Outputs:
  evidence/data_facts.json  -- shapes, NaN counts, label ratio, event segmentation
"""
import json
import numpy as np
import pandas as pd
from pathlib import Path

DATA = Path("/mnt/f/dataset/cs/2308.13068_mvts_flawed_eval")
OUT = Path(__file__).resolve().parent.parent / "evidence"
OUT.mkdir(parents=True, exist_ok=True)


def label_props(lbl: np.ndarray) -> dict:
    n_anom = int((lbl == 1).sum())
    return {
        "n_total": int(lbl.size),
        "n_anomaly": n_anom,
        "anomaly_ratio": float(n_anom / lbl.size),
    }


def events(lbl: np.ndarray) -> dict:
    d = np.diff(np.concatenate([[0], (lbl == 1).astype(int), [0]]))
    starts = np.where(d == 1)[0]
    ends = np.where(d == -1)[0]
    lengths = ends - starts
    return {
        "n_events": int(len(starts)),
        "event_lengths_min": int(lengths.min()) if len(lengths) else None,
        "event_lengths_max": int(lengths.max()) if len(lengths) else None,
        "event_lengths_mean": float(lengths.mean()) if len(lengths) else None,
        "event_lengths_median": float(np.median(lengths)) if len(lengths) else None,
        "total_anomaly_mass": int(lengths.sum()),
    }


facts = {}

# ---- SWaT ----
swat_tr = np.load(DATA / "SWaT_SWaT_train.npy", mmap_mode="r")
swat_te = np.load(DATA / "SWaT_SWaT_test.npy", mmap_mode="r")
swat_lbl = np.load(DATA / "SWaT_SWaT_test_label.npy", mmap_mode="r")

facts["SWaT"] = {
    "train_shape": list(swat_tr.shape),
    "test_shape": list(swat_te.shape),
    "label_shape": list(swat_lbl.shape),
    "train_dtype": str(swat_tr.dtype),
    "test_dtype": str(swat_te.dtype),
    "label_dtype": str(swat_lbl.dtype),
    "train_nan_count": int(swat_tr[:100000].size - np.isfinite(swat_tr[:100000]).sum()),
    "test_nan_count": int(swat_te[:100000].size - np.isfinite(swat_te[:100000]).sum()),
    "label": label_props(np.asarray(swat_lbl)),
    "events": events(np.asarray(swat_lbl)),
}
# global stats (sample a slice for NaN detection; npy float32 should be finite)
full_lbl = np.asarray(swat_lbl)
facts["SWaT"]["label_props_anomaly_ratio"] = (
    facts["SWaT"]["label"]["anomaly_ratio"]
)

# ---- PSM ----
psm_tr = pd.read_csv(DATA / "PSM_train.csv")
psm_te = pd.read_csv(DATA / "PSM_test.csv")
psm_lb = pd.read_csv(DATA / "PSM_test_label.csv")

psm_num_tr = psm_tr.drop(columns=["timestamp_(min)"], errors="ignore")
psm_num_te = psm_te.drop(columns=["timestamp_(min)"], errors="ignore")
lbl = psm_lb.iloc[:, 1].to_numpy().astype(int)

facts["PSM"] = {
    "train_csv_shape": list(psm_tr.shape),
    "test_csv_shape": list(psm_te.shape),
    "label_csv_shape": list(psm_lb.shape),
    "train_columns": list(psm_tr.columns),
    "train_nan_count": int(psm_tr.isna().sum().sum()),
    "test_nan_count": int(psm_te.isna().sum().sum()),
    "train_nan_ratio": float(psm_tr.isna().sum().sum() / psm_tr.size),
    "n_channels": int(psm_num_te.shape[1]),
    "label": label_props(lbl),
    "events": events(np.asarray(lbl, dtype=int)),
}

with open(OUT / "data_facts.json", "w") as f:
    json.dump(facts, f, indent=2, default=str)

print(json.dumps(facts["SWaT"]["label_props_anomaly_ratio"], indent=2))
print(json.dumps(facts["SWaT"]["events"], indent=2))
print("PSM anomaly ratio:", facts["PSM"]["label"]["anomaly_ratio"], "-> ratio x100:",
      round(100 * facts["PSM"]["label"]["anomaly_ratio"], 2), "%")
print(json.dumps(facts["PSM"]["events"], indent=2))
print("Done ->", OUT / "data_facts.json")