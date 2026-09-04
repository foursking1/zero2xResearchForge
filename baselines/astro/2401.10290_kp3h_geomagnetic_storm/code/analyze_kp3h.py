# -*- coding: utf-8 -*-
"""
3-hour-ahead Kp prediction -- RF regression on frozen OMNI + GFZ Kp + Kyoto Dst.

Task: 2401.10290_kp3h_geomagnetic_storm
Paper anchor: arXiv:2401.10290 (Yan 2024) reports 82.55% +/-1 accuracy on
2021 Oct-Dec test with top-50 features + downsampling (L=2) + RF 100 trees.

All metrics are recomputed from the frozen data:
  F:/dataset/astro/2401.10290_kp3h_geomagnetic_storm/
"""
import os
import json
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error

DATA = r"F:/dataset/astro/2401.10290_kp3h_geomagnetic_storm"
RNG = 42
rng = np.random.default_rng(RNG)

# ----------------------------------------------------------------------------
# 1. Load
# ----------------------------------------------------------------------------
omni = pd.read_csv(os.path.join(DATA, "omni_hro_5min_2021", "omni_5min_2021.csv"))
kp = pd.read_csv(os.path.join(DATA, "kp_gfz", "kp_gfz_2021.csv"))
dst = pd.read_csv(os.path.join(DATA, "dst_kyoto_2021", "dst_kyoto_2021.csv"))
aux = pd.read_csv(os.path.join(DATA, "aux_omni_hourly_2021.csv"))

SW_VARS = ["F", "BX_GSE", "BY_GSE", "BZ_GSE", "flow_speed", "proton_density", "T"]

omni["dt"] = pd.to_datetime(dict(year=omni["YR"], month=omni["MO"], day=omni["DY"],
                                 hour=omni["HR"], minute=omni["MN"]))
kp["dt_start"] = pd.to_datetime(dict(year=kp["YR"], month=kp["MO"], day=kp["DY"],
                                     hour=kp["HR_START"].astype(int)))
dst["dt"] = pd.to_datetime(dict(year=dst["YR"], month=dst["MO"], day=dst["DY"],
                                hour=dst["HR"]))

# ----------------------------------------------------------------------------
# 2. Data scale / coverage statistics
# ----------------------------------------------------------------------------
scale = {
    "omni_rows": int(len(omni)),
    "omni_nan_frac": {v: float(omni[v].isna().mean()) for v in SW_VARS},
    "kp_rows": int(len(kp)),
    "dst_rows": int(len(dst)),
    "aux_rows": int(len(aux)),
    "omni_time_start": str(omni["dt"].min()),
    "omni_time_end": str(omni["dt"].max()),
    "kp_2021_nov4_peak": float(kp[(kp["MO"] == 11) & (kp["DY"] == 4)]["Kp"].max()),
    "dst_2021_nov4_min": int(dst[(dst["MO"] == 11) & (dst["DY"] == 4)]["Dst"].min()),
}
kp_check = kp[(kp["MO"] == 11) & (kp["DY"] == 4) & (kp["HR_START"] == 9.0)]["Kp"].iloc[0]
aux_kp = aux.loc[aux["datetime"].between("2021-11-04 09:00", "2021-11-04 09:59"), "kp_index"].iloc[0]
dst_check = dst[(dst["MO"] == 11) & (dst["DY"] == 4) & (dst["HR"] == 13)]["Dst"].iloc[0]
aux_dst = aux.loc[aux["datetime"].between("2021-11-04 13:00", "2021-11-04 13:59"), "dst_index_nt"].iloc[0]
scale["cross_validate"] = {
    "gfz_kp_11-04_09": float(kp_check),
    "aux_kp_index_over10_11-04_09": float(aux_kp) / 10.0,
    "kyoto_dst_11-04_13": int(dst_check),
    "aux_dst_11-04_13": float(aux_dst),
}

# ----------------------------------------------------------------------------
# 3. Vectorized feature construction on the 3-hour prediction grid
# ----------------------------------------------------------------------------
grid = pd.date_range("2021-01-01 00:00", "2021-12-31 21:00", freq="3h")
target_start = grid + pd.Timedelta(hours=3)   # Kp interval that we predict

# ---- OMNI (solar wind) ----------------------------------------------------
omni = omni.sort_values("dt").reset_index(drop=True)
omni_min = omni["dt"].min()
omni_mat0 = omni[SW_VARS].ffill().to_numpy()
# global median fill for remaining leading NaNs
for j in range(omni_mat0.shape[1]):
    col = omni_mat0[:, j]
    omni_mat0[:, j] = np.where(np.isnan(col), np.nanmedian(col), col)

omni_minutes = (omni["dt"] - omni_min).dt.total_seconds().to_numpy() / 60.0
omni_row_int = np.round(omni_minutes / 5.0).astype(int)
# dict from 5-min bucket to row
min_to_row = {int(m / 5.0): i for i, m in enumerate(omni_minutes)}

grid_minutes = (grid - omni_min).total_seconds().to_numpy() / 60.0   # (N,)
N = len(grid)
N_LAG = 108
lag_min = 5 * np.arange(N_LAG)   # (108,)

# target minutes = grid_minutes[:, None] - lag_min[None, :]
tm = grid_minutes[:, None] - lag_min[None, :]          # (N, 108)
valid = (tm >= 0) & (tm <= omni_minutes.max())
bucket = np.round(tm / 5.0).astype(int)
# build row lookup vectorized
row_idx = np.full(bucket.shape, -1, dtype=int)
flat_bucket = bucket[valid].astype(int)
flat_row = np.array([min_to_row.get(b, -1) for b in flat_bucket])  # still python loop but small-ish
row_idx[valid] = flat_row
sw_feats = np.full((N, N_LAG * len(SW_VARS)), np.nan)
for vi, v in enumerate(SW_VARS):
    vals = omni_mat0[:, vi]
    # only assign where row valid
    ri = row_idx.copy()
    good = ri >= 0
    cols = sw_feats[:, vi * N_LAG:(vi + 1) * N_LAG]
    for k in range(N_LAG):
        sel = good[:, k]
        if sel.any():
            cols[sel, k] = vals[ri[sel, k]]

# ---- Dst ------------------------------------------------------------------
dst = dst.sort_values("dt")
dst_dt = dst["dt"].to_numpy()
dst_vals = dst["Dst"].to_numpy()
dst_all = np.full((N, 3), np.nan)
for hi, hh in enumerate((1, 2, 3)):
    need = grid - pd.Timedelta(hours=hh)
    idx = np.searchsorted(dst_dt, need.to_numpy())
    idx = np.clip(idx, 0, len(dst_dt) - 1)
    hit = dst_dt[idx] == need.to_numpy()
    dst_all[hit, hi] = dst_vals[idx[hit]]

# ---- Kp -------------------------------------------------------------------
kp = kp.sort_values("dt_start")
kp_dt = kp["dt_start"].to_numpy()
kp_vals = kp["Kp"].to_numpy()
# Target Kp: interval starting at target_start
target_idx = np.searchsorted(kp_dt, target_start.to_numpy())
target_idx = np.clip(target_idx, 0, len(kp_dt) - 1)
has_t = kp_dt[target_idx] == target_start.to_numpy()
y = np.full(N, np.nan)
y[has_t] = kp_vals[target_idx[has_t]]

# Kp lags 3..24 h (8 lags)
kp_feats = np.full((N, 8), np.nan)
for hi, hh in enumerate(range(3, 27, 3)):
    need = grid - pd.Timedelta(hours=hh)
    idx = np.searchsorted(kp_dt, need.to_numpy())
    idx = np.clip(idx, 0, len(kp_dt) - 1)
    hit = kp_dt[idx] == need.to_numpy()
    kp_feats[hit, hi] = kp_vals[idx[hit]]

# Assemble design matrix (drop rows with missing target -> year end)
mask = ~np.isnan(y)
X = np.hstack([sw_feats, dst_all, kp_feats])[mask]
y = y[mask]
grid_used = grid[mask]

feature_names = []
for v in SW_VARS:
    for k in range(N_LAG):
        feature_names.append(f"{v}_lag{5*k}min")
feature_names += ["Dst_lag1h", "Dst_lag2h", "Dst_lag3h"]
feature_names += [f"Kp_lag{hh}h" for hh in range(3, 27, 3)]
assert X.shape[1] == len(feature_names)

# ----------------------------------------------------------------------------
# 4. Train/test split (Jan-Sep / Oct-Dec) with median imputation
# ----------------------------------------------------------------------------
test_mask = grid_used >= pd.Timestamp("2021-10-01")
train_mask = ~test_mask
med = np.nanmedian(X[train_mask], axis=0)
med = np.where(np.isnan(med), 0.0, med)

def impute(Xi):
    Xo = Xi.copy()
    for j in range(Xi.shape[1]):
        col = Xi[:, j]
        Xo[:, j] = np.where(np.isnan(col), med[j], col)
    return Xo

Xtr = impute(X[train_mask])
Xte = impute(X[test_mask])
ytr = y[train_mask]
yte = y[test_mask]

# ----------------------------------------------------------------------------
# 5. Models
# ----------------------------------------------------------------------------
def accuracy_kp(ytrue, ypred):
    return float(np.mean(np.abs(ytrue - ypred) <= 1.0))

results = {}
def add(name, ypred):
    results[name] = {
        "accuracy_pm1": accuracy_kp(yte, ypred),
        "rmse": float(np.sqrt(mean_squared_error(yte, ypred))),
        "n_test": int(len(yte)),
    }

# Baselines
kp_lag3_for_test = np.full(len(yte), np.nan)
for i, t in enumerate(grid_used[test_mask]):
    need = t - pd.Timedelta(hours=3)
    idx = np.searchsorted(kp_dt, need.to_numpy())
    if idx < len(kp_dt) and kp_dt[idx] == need.to_numpy():
        kp_lag3_for_test[i] = kp_vals[idx]
persist = np.where(np.isnan(kp_lag3_for_test), np.nanmedian(ytr), kp_lag3_for_test)
mean_pred = np.full_like(yte, np.mean(ytr))
median_pred = np.full_like(yte, np.nanmedian(ytr))
add("persistence", persist)
add("mean", mean_pred)
add("median", median_pred)

rf_full = RandomForestRegressor(n_estimators=100, max_features=len(feature_names) // 3,
                                n_jobs=4, random_state=RNG)
rf_full.fit(Xtr, ytr)
pred_full = rf_full.predict(Xte)
add("rf_full", pred_full)

imp = rf_full.feature_importances_
top100 = np.argsort(imp)[::-1][:100]
rf100 = RandomForestRegressor(n_estimators=100, max_features=100 // 3, n_jobs=4, random_state=RNG)
rf100.fit(Xtr[:, top100], ytr)
add("rf_top100", rf100.predict(Xte[:, top100]))

top50 = np.argsort(imp)[::-1][:50]
rf50 = RandomForestRegressor(n_estimators=100, max_features=50 // 3, n_jobs=4, random_state=RNG)
rf50.fit(Xtr[:, top50], ytr)
add("rf_top50", rf50.predict(Xte[:, top50]))

# top-50 + downsample L=2 (drop half of training samples with Kp < 3)
low = ytr < 3.0
drop_idx = rng.choice(np.where(low)[0], size=int(low.sum() // 2), replace=False)
keep = np.setdiff1d(np.arange(len(ytr)), drop_idx)
rf50ds = RandomForestRegressor(n_estimators=100, max_features=50 // 3, n_jobs=4, random_state=RNG)
rf50ds.fit(Xtr[keep][:, top50], ytr[keep])
add("rf_top50_downsample", rf50ds.predict(Xte[:, top50]))

# ---- Feature-importance decay ----------------------------------------------
def lag_of(n):
    if "_lag" in n and n.endswith("min"):
        return int(n.split("lag")[1].replace("min", ""))
    return None
near_idx = [i for i, n in enumerate(feature_names) if lag_of(n) is not None and 0 <= lag_of(n) <= 15]
far_idx = [i for i, n in enumerate(feature_names) if lag_of(n) is not None and 495 <= lag_of(n) <= 505]
near_imp = float(imp[near_idx].mean())
far_imp = float(imp[far_idx].mean())
kp_lag_imps = [float(imp[feature_names.index(f"Kp_lag{hh}h")]) for hh in range(3, 27, 3)]

# ----------------------------------------------------------------------------
# 6. Outputs
# ----------------------------------------------------------------------------
outdir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
os.makedirs(outdir, exist_ok=True)

test_events = pd.DataFrame({
    "time": grid_used[test_mask].astype(str),
    "actual_kp": yte,
    "predicted_kp": pred_full,
})
summary = pd.DataFrame([{
    "period": "2021-10-01..2021-12-31", "n": len(yte),
    "base_rate": float(np.mean(yte >= 5.0)),
    "accuracy": accuracy_kp(yte, pred_full),
    "rmse": float(np.sqrt(mean_squared_error(yte, pred_full))),
}])
summary.to_csv(os.path.join(outdir, "evidence_summary.csv"), index=False)
summary_rows = summary.copy()
summary_rows["time"] = "summary"
summary_rows["actual_kp"] = np.nan
summary_rows["predicted_kp"] = np.nan
ev = pd.concat([test_events, summary_rows], axis=0, ignore_index=True)
ev.to_csv(os.path.join(outdir, "evidence_table.csv"), index=False)

metrics = {
    "data_scale": scale,
    "features": {
        "n_features": int(X.shape[1]),
        "n_sw_lag": 7 * N_LAG,
        "n_dst": 3,
        "n_kp": 8,
        "n_grid_events_total": int(len(y)),
        "n_train": int(train_mask.sum()),
        "n_test": int(test_mask.sum()),
    },
    "models": results,
    "feature_importance_decay": {
        "near_mean_imp": near_imp,
        "far_mean_imp": far_imp,
        "near_far_ratio": float(near_imp / far_imp) if far_imp > 0 else None,
        "kp_lag_importances": kp_lag_imps,
        "n_near_feats": int(len(near_idx)),
        "n_far_feats": int(len(far_idx)),
    },
    "paper_anchor": {
        "paper_accuracy": 0.8255,
        "paper_features": 780,
        "paper_events": 2679,
        "compiler_probe_full": 0.7456,
        "compiler_probe_top50": 0.7374,
        "compiler_probe_top50_ds": 0.7075,
        "compiler_probe_persistence": 0.7252,
        "compiler_probe_mean": 0.5850,
    },
}
with open(os.path.join(outdir, "metrics.json"), "w", encoding="utf-8") as f:
    json.dump(metrics, f, indent=2, default=float)

# ---- Figure ----------------------------------------------------------------
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
fig, axes = plt.subplots(1, 2, figsize=(12, 5))
ax = axes[0]
tt = pd.to_datetime(test_events["time"])
ax.plot(tt, test_events["actual_kp"], lw=0.7, label="actual Kp", color="black")
ax.plot(tt, test_events["predicted_kp"], lw=0.7, label="RF predicted", color="steelblue", alpha=0.8)
ax.set_xlabel("Test period (2021 Oct-Dec)")
ax.set_ylabel("Kp")
ax.set_title("3h-ahead Kp: actual vs RF full-feature")
ax.legend()
ax.tick_params(axis="x", rotation=45, labelsize=7)

ax2 = axes[1]
lag_map = {}
for n, im in zip(feature_names, imp):
    if "_lag" in n and n.endswith("min"):
        m = int(n.split("lag")[1].replace("min", ""))
        lag_map.setdefault(m, []).append(float(im))
lag_vals = sorted(lag_map)
lag_mean = [np.mean(lag_map[m]) for m in lag_vals]
ax2.plot(lag_vals, lag_mean, "o-", markersize=3)
ax2.axvline(15, color="gray", ls="--", label="near cutoff (15 min)")
ax2.axvline(495, color="gray", ls=":", label="far range (495-505 min)")
ax2.set_xlabel("Lag (minutes before prediction time)")
ax2.set_ylabel("Mean RF importance")
ax2.set_title("Solar-wind feature importance vs lag")
ax2.legend()
fig.tight_layout()
fig.savefig(os.path.join(outdir, "figure.svg"))
fig.savefig(os.path.join(outdir, "figure.png"), dpi=150)

print(json.dumps(metrics, indent=2, default=float))
