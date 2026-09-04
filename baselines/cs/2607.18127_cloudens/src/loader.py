"""Data loading and preprocessing for the IBM Cloud telemetry dataset.

Implements the paper's official protocol (ClouDens §V-B / reproduction package
src/ibm_dataset_loader.py + preprocessing.py):

* Feature subset: 5xx HTTP status codes x count aggregation (2,406 features),
  columns selected by regex  r'_5\\d\\d_.*count'  over the parquet schema.
* NaN imputation: zero-fill (Table III, best for 5xx count).
* Split      : train 2024-01-26..2024-02-29 (rows inside annotated anomaly
  windows removed), validation = last 20% of the windowed train segment,
  test 2024-03-01..2024-05-31.
* Scaling    : MinMaxScaler fit on the (cleaned) training segment only.
* Windowing  : slide_win w=6, single-step forecast (target = next point);
  test windows zero the look-back by repeating the first test row w times.
* Context graph (ClouDens only): edge between two nodes iff they share the
  same endpoint + component; weight 0.8 if also same method, 0.6 if same
  communication role otherwise, 0.2 otherwise (Fig. 3); self-loop added by
  the GCN (add_self_loops=True => weight 1).
"""
import json
import os
import re

import numpy as np
import pandas as pd
import torch
from sklearn.preprocessing import MinMaxScaler

MINUTES_BEFORE = 20
W = 6  # sliding window

START_DATE = pd.Timestamp("2024-01-26")
TRAIN_END = pd.Timestamp("2024-02-29")
TEST_START = pd.Timestamp("2024-03-01")
END_DATE = pd.Timestamp("2024-05-31") + pd.Timedelta(days=1)


# --------------------------------------------------------------------------
# adjacency / context graph
# --------------------------------------------------------------------------
def parse_node_token(node_id):
    toks = node_id.split("_")
    return dict(location=toks[0], role=toks[1], component=toks[2],
                method=toks[3], status=toks[4], endpoint=toks[5])


def build_context_edges(node_ids):
    """context-aware adjacency: edge iff shared endpoint+component."""
    n = len(node_ids)
    feat = [parse_node_token(nid) for nid in node_ids]
    rows, cols, weights = [], [], []
    for i in range(n):
        fi = feat[i]
        for j in range(i + 1, n):
            fj = feat[j]
            if fi["endpoint"] == fj["endpoint"] and fi["component"] == fj["component"]:
                if fi["method"] == fj["method"]:
                    w = 0.8
                elif fi["role"] == fj["role"]:
                    w = 0.6
                else:
                    w = 0.2
                rows += [i, j]
                cols += [j, i]
                weights += [w, w]
    edge_index = np.array([rows, cols], dtype=np.int64)
    edge_weight = np.array(weights, dtype=np.float32)
    return edge_index, edge_weight


# --------------------------------------------------------------------------
# anomaly windows
# --------------------------------------------------------------------------
def load_anomaly_windows(csv_path):
    gt = pd.read_csv(csv_path)
    gt["anomaly_start"] = pd.to_datetime(gt["anomaly_start"], utc=True)
    gt["anomaly_end"] = pd.to_datetime(gt["anomaly_end"], utc=True)
    gt["anomaly_window_start"] = (gt["anomaly_start"] - pd.Timedelta(minutes=MINUTES_BEFORE)).dt.tz_localize(None)
    gt["anomaly_window_end"] = gt["anomaly_end"].dt.tz_localize(None)
    return gt[["number", "anomaly_window_start", "anomaly_window_end", "anomaly_source"]]


def filter_anomaly_windows(gt, start_date, end_date, test_start_date):
    train_windows = gt[(gt["anomaly_window_start"] >= start_date) &
                       (gt["anomaly_window_end"] <= end_date)]
    test_windows = train_windows[(train_windows["anomaly_window_start"] >= test_start_date) &
                                 (train_windows["anomaly_window_end"] <= end_date)]
    return train_windows, test_windows


# --------------------------------------------------------------------------
# main loader
# --------------------------------------------------------------------------
def load_subset(parquet_path, cache_dir):
    """5xx count subset (2,406 feats) with zero imputation, cached to disk."""
    data_file = os.path.join(cache_dir, "X_5xx_count.npy")
    idx_file = os.path.join(cache_dir, "index.npy")
    cols_file = os.path.join(cache_dir, "cols.json")
    if all(os.path.exists(p) for p in (data_file, idx_file, cols_file)):
        X = np.load(data_file)
        ts64 = np.load(idx_file)
        with open(cols_file) as f:
            cols = json.load(f)
        print(f"[cached] 5xx count subset shape={X.shape}")
        return X, ts64, cols

    import pyarrow.parquet as pq
    pf = pq.ParquetFile(parquet_path)
    names = pf.schema.names
    regex = re.compile(r"_5\d\d_.*count")
    cols = [c for c in names if regex.search(c)]
    assert len(cols) == 2406, f"expected 2406 5xx-count features, got {len(cols)}"
    assert names[0] == "interval_start"

    df_all = pd.read_parquet(parquet_path, columns=["interval_start"] + cols, engine="pyarrow")
    ts = pd.to_datetime(df_all["interval_start"], unit="s")
    X = df_all[cols].to_numpy(dtype=np.float32)
    nan_frac = float(np.isnan(X).mean())
    X = np.nan_to_num(X, nan=0.0)
    np.save(data_file, X)
    np.save(idx_file, ts.values.astype("datetime64[ns]").astype(np.int64))
    with open(cols_file, "w") as f:
        json.dump(cols, f)
    print(f"5xx count subset: shape={X.shape}, NaN fraction={nan_frac:.4f}")
    return X, ts.values.astype("datetime64[ns]").astype(np.int64), cols


def build_bundle(parquet_path, anomaly_csv, cache_dir):
    X, ts64, cols = load_subset(parquet_path, cache_dir)
    index = pd.DatetimeIndex(ts64.astype("datetime64[ns]"))
    df = pd.DataFrame(X, index=index, columns=cols)

    gt = load_anomaly_windows(anomaly_csv)
    anomaly_windows, anomaly_windows_test = filter_anomaly_windows(
        gt, START_DATE, END_DATE, TEST_START)
    print(f"anomaly windows: {len(anomaly_windows)} (train-clean), "
          f"{len(anomaly_windows_test)} (test)")

    labels = pd.Series(0, index=df.index)
    for _, r in anomaly_windows.iterrows():
        m = (df.index >= r["anomaly_window_start"]) & (df.index <= r["anomaly_window_end"])
        labels.loc[m] = 1.0

    return DfBundle(df=df, cols=cols,
                    anomaly_windows=anomaly_windows,
                    anomaly_windows_test=anomaly_windows_test,
                    labels=labels)


class DfBundle:
    __slots__ = ["df", "cols", "anomaly_windows", "anomaly_windows_test", "labels"]

    def __init__(self, df, cols, anomaly_windows, anomaly_windows_test, labels):
        self.df = df
        self.cols = cols
        self.anomaly_windows = anomaly_windows
        self.anomaly_windows_test = anomaly_windows_test
        self.labels = labels


def prepare_split(bundle, slide_win=W, train_val_ratio=0.8, seed=42):
    """Scaler + windowed train/val/test tensors, test labels (leakage-safe)."""
    df = bundle.df

    train_df = df.loc[START_DATE:TRAIN_END]
    mask = np.zeros(len(train_df), dtype=bool)
    for _, r in bundle.anomaly_windows.iterrows():
        m = (train_df.index >= r["anomaly_window_start"]) & (train_df.index <= r["anomaly_window_end"])
        mask |= np.asarray(m, dtype=bool)
    train_df = train_df[~mask]
    print(f"training rows: raw={df.loc[START_DATE:TRAIN_END].shape[0]} -> "
          f"cleaned={train_df.shape[0]} (removed {int(mask.sum())})")

    test_df = df.loc[TEST_START:END_DATE]
    print(f"test rows = {test_df.shape[0]} (expected ~26,488)")

    scaler = MinMaxScaler()
    X_train_scaled = scaler.fit_transform(train_df.to_numpy()).astype(np.float32)
    X_test_scaled = scaler.transform(test_df.to_numpy()).astype(np.float32)

    def make_windows(Xs_2d, pad):
        if pad:
            Xs_2d = np.concatenate([np.repeat(Xs_2d[0:1], slide_win, axis=0), Xs_2d], axis=0)
        wd = torch.tensor(Xs_2d).unfold(dimension=0, size=slide_win + 1, step=1)
        wd = wd.permute(0, 2, 1).reshape(-1, slide_win + 1, Xs_2d.shape[1]).contiguous()
        return wd

    w_train = make_windows(X_train_scaled, False)              # [K, slide_win+1, D]
    off = int(train_val_ratio * w_train.shape[0])
    feats_tr = w_train[:off, :slide_win, :].numpy().astype(np.float32)
    targets_tr = w_train[:off, slide_win, :].numpy().astype(np.float32)
    feats_va = w_train[off:, :slide_win, :].numpy().astype(np.float32)
    targets_va = w_train[off:, slide_win, :].numpy().astype(np.float32)

    w_test = make_windows(X_test_scaled, True)                 # [T, slide_win+1, D]
    feats_te = w_test[:, :slide_win, :].numpy().astype(np.float32)
    targets_te = w_test[:, slide_win, :].numpy().astype(np.float32)

    N, F = feats_tr.shape[-1], 1
    feats_tr = feats_tr.reshape(-1, slide_win, N, F)
    targets_tr = targets_tr.reshape(-1, N, F)
    feats_va = feats_va.reshape(-1, slide_win, N, F)
    targets_va = targets_va.reshape(-1, N, F)
    feats_te = feats_te.reshape(-1, slide_win, N, F)
    targets_te = targets_te.reshape(-1, N, F)

    labels_test = bundle.labels.loc[test_df.index].to_numpy()
    print(f"test labels: {int(labels_test.sum())} anomaly points "
          f"({100*labels_test.mean():.2f}%), test windows {len(feats_te)}")
    return dict(X_train_scaled=X_train_scaled, X_test_scaled=X_test_scaled,
                feats_tr=feats_tr, targets_tr=targets_tr,
                feats_va=feats_va, targets_va=targets_va,
                feats_te=feats_te, targets_te=targets_te,
                scaler=scaler, test_index=test_df.index,
                test_labels=labels_test,
                num_nodes=N, node_feat=F)


def make_loaders(pairs, batch_size=32):
    from torch.utils.data import DataLoader, TensorDataset
    loaders = {}
    for name, (x, y) in pairs.items():
        loaders[name] = DataLoader(TensorDataset(torch.FloatTensor(x), torch.FloatTensor(y)),
                                   batch_size=batch_size, shuffle=False)
    return loaders