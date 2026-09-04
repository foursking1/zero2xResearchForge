"""Patient-level feature building for the TJH early-mortality task.

Two feature representations are built from the shared 3 lab features:
  1. `build_aggregate` - vectorised per-patient summary statistics over the
     early window (basis for RF / LightGBM / logistic baselines).
  2. `build_sequence`  - fixed-bin time series with observed/missing masks
     (basis for the GRU / GRU-TA sequence models).

Anti-leakage contract
-----------------------
Every statistic that has to be carried over to the test set (per-feature
means used to fill never-measured patients) is computed **only on the
training split**.  The test set never contributes to any fitted quantity.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler

from common import SHARED_FEATURES, early_window, usable_patients

#: default early-prediction window (hours from admission)
DEFAULT_WINDOW_HOURS = 72.0


def _last_obs(s: pd.Series) -> float:
    v = s.dropna()
    return v.iloc[-1] if len(v) else np.nan


def _first_obs(s: pd.Series) -> float:
    v = s.dropna()
    return v.iloc[0] if len(v) else np.nan


def _slope(hour: np.ndarray, vals: np.ndarray) -> float:
    v = vals[~np.isnan(vals)]
    h = hour[~np.isnan(vals)]
    if len(v) < 2 or np.ptp(h) <= 1e-9:
        return np.nan
    lr = LinearRegression().fit(h.reshape(-1, 1), v)
    return float(lr.coef_[0])


class AggregateBuilder:
    """Per-patient summary statistics over the early window.

    Returns numpy arrays ready for ML models plus the train-fitted metadata
    (per-feature median for missing-fill, and a StandardScaler).
    """

    def __init__(self, feats=SHARED_FEATURES, window_hours=DEFAULT_WINDOW_HOURS):
        self.feats = list(feats)
        self.window_hours = window_hours

    def build(self, train_df, test_df):
        tr = usable_patients(early_window(train_df, self.window_hours))
        te = usable_patients(early_window(test_df, self.window_hours))
        A_tr, y_tr = self._frame_aggs(tr)
        A_te, y_te = self._frame_aggs(te)
        # Align test frame to the train feature columns (empty test => empty frame)
        for c in set(A_tr.columns) - set(A_te.columns):
            A_te[c] = np.nan
        A_te = A_te[A_tr.columns]
        pid_te = None
        if "pid" in A_te.columns:
            pid_te = A_te.pop("pid").to_numpy()
        if "pid" in A_tr.columns:
            A_tr = A_tr.drop(columns=["pid"])
        feat_cols = list(A_tr.columns)
        med = A_tr[feat_cols].median()
        mask_tr = A_tr[feat_cols].isna().astype(int)
        mask_te = A_te[feat_cols].isna().astype(int)
        A_tr[feat_cols] = A_tr[feat_cols].fillna(med)
        A_te[feat_cols] = A_te[feat_cols].fillna(med)
        mask_cols = [f"{c}__missing" for c in feat_cols]
        A_tr[mask_cols] = mask_tr.values
        A_te[mask_cols] = mask_te.values
        all_cols = feat_cols + mask_cols
        scaler = StandardScaler().fit(np.asarray(A_tr[feat_cols], dtype=float))
        X_tr = A_tr[all_cols].to_numpy(dtype=float)
        X_te = A_te[all_cols].to_numpy(dtype=float)
        return (X_tr, y_tr.to_numpy(), X_te, y_te.to_numpy(), pid_te,
                scaler, list(mask_cols), list(all_cols))

    # ------------------------------------------------------------------
    def _frame_aggs(self, pdf):
        rows = []
        labels = []
        for pid, g in pdf.groupby("pid"):
            rec = {"pid": pid}
            y = int(g["outcome"].iloc[0])
            hour = g["hour"].to_numpy(dtype=float)
            for f in self.feats:
                vals = g[f].to_numpy(dtype=float)
                has = ~np.isnan(vals)
                rec[f"{f}_last"] = _last_obs(g[f])
                rec[f"{f}_first"] = _first_obs(g[f])
                rec[f"{f}_mean"] = float(np.nanmean(vals)) if has.sum() else np.nan
                rec[f"{f}_min"] = float(np.nanmin(vals)) if has.sum() else np.nan
                rec[f"{f}_max"] = float(np.nanmax(vals)) if has.sum() else np.nan
                rec[f"{f}_slope"] = _slope(hour, vals)
                rec[f"{f}_n"] = int(has.sum())
                rec[f"{f}_sd"] = float(np.nanstd(vals)) if has.sum() > 1 else np.nan
                rec[f"{f}_hlast"] = float(hour[has][-1]) if has.any() else np.nan
            rec["any_obs"] = int(any(g[f].notna().any() for f in self.feats))
            l0, l1, l2 = self.feats
            last = {f: rec.get(f"{f}_last") for f in self.feats}
            def safe_div(a, b):
                if a is None or b is None:
                    return np.nan
                if np.isnan(a) or np.isnan(b) or b == 0:
                    return np.nan
                return a / b
            a, b = last.get(l0), last.get(l1)
            rec["LDH_x_CRP"] = (a * b) if (a is not None and b is not None
                                           and not (np.isnan(a) or np.isnan(b))) else np.nan
            rec["CRP_div_lymph"] = safe_div(last.get(l1), last.get(l2))
            rec["LDH_div_lymph"] = safe_div(last.get(l0), last.get(l2))
            rows.append(rec)
            labels.append(y)
        return pd.DataFrame(rows), pd.Series(labels, name="outcome")


class SequenceBuilder:
    """Bin the longitudinal rows into `n_bins` equal bins over the window.

    Per (bin, feature): stores the last observed value inside the bin and a
    0/1 observed-mask.  Missing *bins* are filled with pure LOCF across bins;
    any residual gaps use the train-set feature mean (mask stays 0 so the
    model can discriminate measured vs imputed).

    Output per patient:  X (n_bins, 2*n_feats) with channels
    [value_0, mask_0, value_1, mask_1, ...]
    """

    def __init__(self, feats=SHARED_FEATURES, window_hours=DEFAULT_WINDOW_HOURS,
                 n_bins=12):
        self.feats = list(feats)
        self.window_hours = float(window_hours)
        self.n_bins = int(n_bins)
        self.bin_width = self.window_hours / self.n_bins

    def fit_transform(self, train_df, test_df):
        """Train-fit the feature means, then encode both splits."""
        means = {f: (float(train_df[f].mean())
                     if train_df[f].notna().any() else 0.0)
                 for f in self.feats}
        Xtr, Ytr, pids_tr = self._encode(train_df, means)
        Xte, Yte, pids_te = self._encode(test_df, means)
        return Xtr, Ytr, pids_tr, Xte, Yte, pids_te

    def _encode(self, pdf, gmeans):
        pdf = usable_patients(early_window(pdf, self.window_hours))
        pids = pdf["pid"].unique()
        X = np.full((len(pids), self.n_bins, 2 * len(self.feats)), 0.0)
        Y = np.zeros(len(pids), dtype=int)
        out_pid = np.empty(len(pids), dtype=int)
        for i, pid in enumerate(pids):
            g = pdf[pdf["pid"] == pid].sort_values("hour")
            Y[i] = int(g["outcome"].iloc[0])
            out_pid[i] = pid
            hour = g["hour"].to_numpy()
            bin_id = np.clip(np.floor(hour / self.bin_width).astype(int),
                             0, self.n_bins - 1)
            vals = g[self.feats].to_numpy(dtype=float)
            for b in range(self.n_bins):
                sel = bin_id == b
                if not sel.any():
                    continue
                for j in range(len(self.feats)):
                    col = vals[sel, j]
                    obs = ~np.isnan(col)
                    if obs.any():
                        X[i, b, 2 * j] = col[obs][-1]
                        X[i, b, 2 * j + 1] = 1.0
            # LOCF across bins then train-mean for leading gaps
            for j in range(len(self.feats)):
                last_val = np.nan
                for b in range(self.n_bins):
                    if X[i, b, 2 * j + 1] > 0:
                        last_val = X[i, b, 2 * j]
                    else:
                        X[i, b, 2 * j] = (last_val if not np.isnan(last_val)
                                          else gmeans[self.feats[j]])
        return X, Y, out_pid