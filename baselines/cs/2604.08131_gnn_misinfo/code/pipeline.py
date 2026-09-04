"""
Reproduction pipeline for arXiv:2604.08131 (Graph Neural Networks for
Misinformation Detection: Performance-Efficiency Trade-offs).

Verifies the WELFake L1 critical claim:
  GraphSAGE test F1 (anchor 91.9) vs MLP test F1 (anchor 66.8) under the
  paper's unified protocol:
    - frozen WELFake CSV (dropna(text) -> 72,095 rows)
    - stratified 80/10/10 split, random_state=42 (test 10%, then 0.2222 val)
    - TF-IDF with max 5,000 features, vocabulary fitted on TRAIN only
    - k-NN similarity graph K=5 built on TRAIN features only (no test leakage)
    - GraphSAGE (SAGEConv mean, 2 hidden 256/128) vs MLP (2 hidden 256/128),
      Adam lr=1e-3, early stopping (patience=10), results averaged over 3 seeds

Leakage guarantees:
  * TF-IDF vocabulary / idf fitted only on train.
  * k-NN graph built only from train feature vectors.
  * val/test nodes enter the GNN as isolated nodes (identity adjacency),
    so no test/val feature is ever used to build edges or to normalize.
  * test is evaluated exactly once, with the best-checkpoint model chosen
    purely on val.

Usage:
    python pipeline.py --out ../results [--seeds 0 1 2] [--max-epochs 200]
                       [--models both|graphsage|mlp]
                       [--mlp-mode full_batch|minibatch|sklearn]
    CSV path resolution order:
      1. --csv PATH
      2. env WELFAME_CSV
      3. ../data/welfake/WELFake_Dataset.csv  (relative to code/)
      4. /mnt/f/dataset/cs/2604.08131_gnn_misinfo/data/welfake/WELFake_Dataset.csv
"""

import argparse
import hashlib
import json
import os
import sys
import time

import numpy as np
import pandas as pd
import scipy.sparse as sp
import torch
import torch.nn as nn
import torch.nn.functional as F
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import (accuracy_score, f1_score, precision_score,
                             recall_score)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import normalize as sk_normalize

SEED_SPLIT = 42
EXPECTED_SHA256 = "665331424230FC452E9482C3547A6A199A2C29745ADE8D236950D1D105223773"


# --------------------------------------------------------------------------
# CSV location helpers
# --------------------------------------------------------------------------
CANDIDATE_CSV_PATHS = [
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "..", "data", "welfake", "WELFake_Dataset.csv"),
    os.path.abspath(os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "WELFake_Dataset.csv")),
    "/mnt/f/dataset/cs/2604.08131_gnn_misinfo/data/welfake/WELFake_Dataset.csv",
    "F:/dataset/cs/2604.08131_gnn_misinfo/data/welfake/WELFake_Dataset.csv",
]


def resolve_csv_path(override=None):
    if override and os.path.isfile(override):
        return override
    env = os.environ.get("WELFAME_CSV")
    if env and os.path.isfile(env):
        return env
    for p in CANDIDATE_CSV_PATHS:
        if os.path.isfile(p):
            return p
    raise FileNotFoundError(
        "Could not locate frozen WELFake CSV. Pass --csv or set WELFAME_CSV.")


# --------------------------------------------------------------------------
# Data preparation
# --------------------------------------------------------------------------
def load_and_split(csv_path, verify_sha=False):
    """dropna(text) -> stratified 80/10/10-ish split with random_state=42.

    Protocol follows the reproduction repo: first split off 10% as test
    (stratify=label, random_state=42), then split the remaining 90% with
    test_size=0.2222 for the validation set. Returns index arrays.
    """
    if verify_sha:
        h = hashlib.sha256(open(csv_path, "rb").read()).hexdigest().upper()
        if h != EXPECTED_SHA256:
            raise RuntimeError(f"CSV sha256 mismatch: {h}")
    df = pd.read_csv(csv_path)
    df = df.dropna(subset=["text"]).reset_index(drop=True)
    y = df["label"].values.astype(np.int64)
    text = df["text"].values

    rest_idx, test_idx = train_test_split(
        np.arange(len(df)), test_size=0.1, random_state=SEED_SPLIT,
        stratify=y)
    y_rest = y[rest_idx]
    train_idx, val_idx = train_test_split(
        rest_idx, test_size=0.2222, random_state=SEED_SPLIT, stratify=y_rest)
    splits = {"train": train_idx, "val": val_idx, "test": test_idx}
    n = {k: len(v) for k, v in splits.items()}
    print(f"[split] total={len(df)} train={n['train']} val={n['val']} "
          f"test={n['test']}")
    for k in ("train", "val", "test"):
        print(f"[split] {k} labels: 1={int((y[splits[k]] == 1).sum())} "
              f"0={int((y[splits[k]] == 0).sum())}")
    return df, text, y, splits


def build_tfidf(text, splits, max_features=5000):
    """Fit TfidfVectorizer on train text only; transform val/test after."""
    train_text = [text[i] for i in splits["train"]]
    vectorizer = TfidfVectorizer(max_features=max_features)
    X_train = vectorizer.fit_transform(train_text)
    X_val = vectorizer.transform([text[i] for i in splits["val"]])
    X_test = vectorizer.transform([text[i] for i in splits["test"]])
    print(f"[tfidf] vocab={len(vectorizer.vocabulary_)} "
          f"feat={X_train.shape[1]} train_nnz={X_train.nnz}")
    return X_train, X_val, X_test, vectorizer


def _knn_indices_exact(X, k=5, metric="euclidean", block=2048):
    """Exact k-NN (per-row smallest distance) over sparse features, computed
    with a blockwise dense gram matrix (BLAS) to bound memory.

    metric='euclidean' -> L2 distance on the raw feature matrix (this is the
        default distance of torch_geometric.nn.knn_graph);
    metric='cosine'    -> cosine similarity on L2-normalised features
        (cosine(1) = euclidean on unit vectors).
    Self is excluded (PyG knn_graph uses loop=False).
    """
    n = X.shape[0]
    if metric == "cosine":
        Xw = sk_normalize(X).astype(np.float32)
        Xt = np.asarray(Xw.T.todense()).astype(np.float32)
        sq_full = np.ones(n, dtype=np.float32)
    else:
        Xw = X
        Xt = np.asarray(X.T.todense()).astype(np.float32)
        sq_full = np.asarray(X.multiply(X).sum(axis=1)).ravel().astype(np.float32)

    out = []
    for s in range(0, n, block):
        Xb = np.asarray(Xw[s:s + block].toarray()).astype(np.float32)
        G = Xb @ Xt
        if metric == "euclidean":
            sqb = np.einsum("ij,ij->i", Xb, Xb).astype(np.float32)
            D = np.sqrt(np.maximum(sqb[:, None] + sq_full[None, :] - 2.0 * G,
                                   0.0))
        else:
            D = 1.0 - G
        cols = np.arange(s, min(s + block, n))
        D[np.arange(D.shape[0]), cols] = np.inf  # exclude self (global col id)
        kk = min(k, D.shape[1] - 1)
        cand = np.argpartition(D, kth=kk, axis=1)[:, :k]
        out.append(cand)  # column indices are already global
    return np.vstack(out)


def build_knn_graph(X_train, k=5, metric="euclidean"):
    """k-NN similarity graph on TRAIN features only.

    Semantics of torch_geometric.nn.knn_graph (K nearest by pairwise
    distance, self-loop excluded) with an exact (non-approximate) search.
    The graph is symmetrised (undirected), self-loops are added and the
    adjacency is row-normalised (D^-1 (A + I)), which is exactly the mean
    aggregation used by SAGEConv.
    """
    t0 = time.time()
    idx = _knn_indices_exact(X_train, k=k, metric=metric)
    n = X_train.shape[0]
    rows = np.repeat(np.arange(n), k)
    cols = idx.reshape(-1)
    edges = np.concatenate([np.stack([rows, cols], axis=1),
                            np.stack([cols, rows], axis=1)])
    adj = sp.coo_matrix((np.ones(edges.shape[0]),
                         (edges[:, 0], edges[:, 1])),
                        shape=(n, n)).tocsr()
    adj.setdiag(1.0)
    adj = adj.multiply(1.0).tocsr()
    deg = np.asarray(adj.sum(axis=1)).ravel()
    adj_norm = sp.diags(1.0 / deg) @ adj
    print(f"    [knn] K={k} metric={metric} n={n} edges={int((adj > 0).sum())} "
          f"time={time.time() - t0:.1f}s")
    return adj, adj_norm


def to_csr_tensor(m):
    """Convert scipy CSR to a torch CSR tensor (float32)."""
    return torch.sparse_csr_tensor(
        torch.tensor(m.indptr, dtype=torch.int64),
        torch.tensor(m.indices, dtype=torch.int64),
        torch.tensor(m.data, dtype=torch.float32),
        size=m.shape)


# --------------------------------------------------------------------------
# Models
# --------------------------------------------------------------------------
class SAGEConvMean(nn.Module):
    """Mean-aggregator SAGEConv replicating torch_geometric.nn.SAGEConv
    (aggr='mean', root_weight=True, bias=True, add_self_loops=True,
    normalize=False). Uses a pre-normalised adjacency (D^-1 (A + I)) passed
    as a torch CSR tensor.
    """

    def __init__(self, in_channels, out_channels, bias=True):
        super().__init__()
        self.lin_l = nn.Linear(in_channels, out_channels, bias=bias)
        self.lin_r = nn.Linear(in_channels, out_channels, bias=False)

    def forward(self, x, adj_norm):
        if isinstance(x, torch.Tensor) and x.layout == torch.sparse_csr:
            h_l = torch.sparse.mm(x, self.lin_l.weight.T)
            tmp = torch.sparse.mm(x, self.lin_r.weight.T)
            nb = torch.sparse.mm(adj_norm, tmp)
        else:
            h_l = x @ self.lin_l.weight.T
            nb = torch.sparse.mm(adj_norm, x) @ self.lin_r.weight.T
        out = h_l + nb + self.lin_l.bias
        return out


class GraphSAGENet(nn.Module):
    """2-hidden-layer GraphSAGE (256/128) + linear readout (§3.3/§3.4)."""

    def __init__(self, in_dim, hidden=(256, 128), out_dim=2):
        super().__init__()
        self.conv1 = SAGEConvMean(in_dim, hidden[0])
        self.conv2 = SAGEConvMean(hidden[0], hidden[1])
        self.readout = nn.Linear(hidden[1], out_dim)

    def forward(self, x, adj_norm):
        x = F.relu(self.conv1(x, adj_norm))
        x = F.relu(self.conv2(x, adj_norm))
        return self.readout(x)


class MLPNet(nn.Module):
    """2-hidden-layer MLP (256/128, ReLU) matching §3.3."""

    def __init__(self, in_dim, hidden=(256, 128), out_dim=2):
        super().__init__()
        self.fc1 = nn.Linear(in_dim, hidden[0])
        self.fc2 = nn.Linear(hidden[0], hidden[1])
        self.fc3 = nn.Linear(hidden[1], out_dim)

    def forward(self, x):
        if isinstance(x, torch.Tensor) and x.layout == torch.sparse_csr:
            h1 = torch.relu(torch.sparse.mm(x, self.fc1.weight.T) + self.fc1.bias)
        else:
            h1 = torch.relu(x @ self.fc1.weight.T + self.fc1.bias)
        h2 = torch.relu(h1 @ self.fc2.weight.T + self.fc2.bias)
        return h2 @ self.fc3.weight.T + self.fc3.bias


def make_model(model_name, in_dim, hidden=(256, 128)):
    if model_name == "graphsage":
        return GraphSAGENet(in_dim, hidden).eval()
    elif model_name == "mlp":
        return MLPNet(in_dim, hidden).eval()
    raise ValueError(model_name)


# --------------------------------------------------------------------------
# Metrics and training
# --------------------------------------------------------------------------
def metrics(y_true, y_pred):
    return {
        "n": int(len(y_true)),
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "f1": float(f1_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred)),
        "recall": float(recall_score(y_true, y_pred)),
        "f1_weighted": float(f1_score(y_true, y_pred, average="weighted")),
    }


def predict_proba_binary(model, X, adj_norm=None):
    if isinstance(model, (GraphSAGENet,)):
        logits = model(X, adj_norm)
    else:
        logits = model(X)
    return F.softmax(logits, dim=1)


def evaluate(model, X, y, adj_norm=None):
    model.eval()
    with torch.no_grad():
        proba = predict_proba_binary(model, X, adj_norm)
        return metrics(y, proba.argmax(1).numpy())


def train_one_seed(model_name, X_train_csr, y_train, X_val_csr, y_val,
                   X_test_csr, y_test, adj_norm, seed, max_epochs=200,
                   patience=10, lr=1e-3, mlp_mode="full_batch", mlp_n_steps=200,
                   mlp_batch=512, X_train_sp=None, X_test_sp=None):
    torch.manual_seed(seed)
    np.random.seed(seed)
    model = make_model(model_name, X_train_csr.shape[1]).to("cpu")
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    crit = nn.CrossEntropyLoss()

    y_train_t = torch.tensor(y_train, dtype=torch.long)
    y_val_t = torch.tensor(y_val, dtype=torch.long)

    adj_val = to_csr_tensor(sp.identity(X_val_csr.shape[0], format="csr"))
    adj_test = to_csr_tensor(sp.identity(X_test_csr.shape[0], format="csr"))

    best_val, best_state, best_epoch, bad = -1.0, None, -1, 0
    history = []
    n_train = X_train_csr.shape[0]
    t0 = time.time()

    if model_name == "mlp" and mlp_mode == "sklearn":
        from sklearn.neural_network import MLPClassifier
        sk = MLPClassifier(hidden_layer_sizes=(256, 128), activation="relu",
                           max_iter=max_epochs, learning_rate_init=lr,
                           alpha=0.0, solver="adam", batch_size="auto",
                           shuffle=False, random_state=seed)
        sk.fit(X_train_sp, y_train)
        yp = sk.predict(X_test_sp)
        t = metrics(y_test, yp)
        t.update({"seed": seed, "best_epoch": sk.n_iter_, "best_val_f1": np.nan,
                  "time_s": round(time.time() - t0, 1), "mlp_mode": mlp_mode})
        return model, t, pd.DataFrame()
    elif model_name == "mlp" and mlp_mode == "minibatch":
        n_steps = mlp_n_steps  # fixed step budget, one batch each step
    else:
        n_steps = None         # full-batch epoch training (both GraphSAGE & MLP)

    rng_steps = np.random.RandomState(seed + 1)
    for epoch in range(max_epochs if n_steps is None else n_steps):
        model.train()
        opt.zero_grad()
        if n_steps is not None:  # MLP mini-batch, fixed step budget
            idx = rng_steps.choice(n_train, size=min(mlp_batch, n_train),
                                   replace=False)
            logits = model(to_csr_tensor(X_train_sp[idx].astype(np.float32)))
            loss = crit(logits, y_train_t[idx])
        elif model_name == "graphsage":
            logits = model(X_train_csr, adj_norm)
            loss = crit(logits, y_train_t)
        else:
            logits = model(X_train_csr)
            loss = crit(logits, y_train_t)
        loss.backward()
        opt.step()
        model.eval()
        with torch.no_grad():
            v = evaluate(model, X_val_csr, y_val, adj_val)
        history.append({"step": epoch, "train_loss": float(loss.item()),
                        **{k: v[k] for k in
                           ("f1", "accuracy", "precision", "recall")}})
        if v["f1"] > best_val:
            best_val, best_epoch, bad = v["f1"], epoch, 0
            best_state = {k: vv.clone() for k, vv in model.state_dict().items()}
        else:
            bad += 1
            if bad >= patience and epoch > 5:
                break

    model.load_state_dict(best_state)
    t = evaluate(model, X_test_csr, y_test, adj_test)
    vb = evaluate(model, X_val_csr, y_val, adj_val)
    t.update({"seed": seed, "best_epoch": best_epoch, "best_val_f1": vb["f1"],
              "time_s": round(time.time() - t0, 1), "mlp_mode": mlp_mode})
    return model, t, pd.DataFrame(history)


# --------------------------------------------------------------------------
# Orchestration
# --------------------------------------------------------------------------
def run_protocol(args):
    csv_path = resolve_csv_path(args.csv)
    print(f"[csv] {csv_path}")
    df, text, y, splits = load_and_split(csv_path, verify_sha=args.verify_sha)
    X_train, X_val, X_test, vectorizer = build_tfidf(
        text, splits, max_features=args.max_features)
    y_train, y_val, y_test = (y[splits["train"]], y[splits["val"]],
                              y[splits["test"]])

    models = ["graphsage", "mlp"] if args.models == "both" else \
        args.models.split(",")
    adj_csr = adj_norm_csr = adj_t = None
    if "graphsage" in models:
        t0 = time.time()
        adj_csr, adj_norm_csr = build_knn_graph(X_train, k=args.k,
                                                metric=args.knn_metric)
        adj_t = to_csr_tensor(adj_norm_csr)
        print(f"[graph] K={args.k} metric={args.knn_metric} "
              f"edges={int((adj_csr > 0).sum())} "
              f"build_time={time.time() - t0:.1f}s")

    X_train_csr = to_csr_tensor(X_train.astype(np.float32))
    X_val_csr = to_csr_tensor(X_val.astype(np.float32))
    X_test_csr = to_csr_tensor(X_test.astype(np.float32))

    os.makedirs(args.out, exist_ok=True)
    idx_dir = os.path.join(args.out, "splits")
    os.makedirs(idx_dir, exist_ok=True)
    for k, ix in splits.items():
        pd.Series(ix.astype(int)).to_csv(os.path.join(idx_dir, f"{k}_index.csv"),
                                         header=["index"], index=False)

    summary_rows, pred_rows, hist_store = [], [], {}
    models = ["graphsage", "mlp"] if args.models == "both" else \
        args.models.split(",")
    for seed in args.seeds:
        for mname in models:
            if mname not in ("graphsage", "mlp"):
                continue
            print(f"\n=== training {mname} seed={seed} ===")
            model, t, hist = train_one_seed(
                mname, X_train_csr, y_train, X_val_csr, y_val, X_test_csr,
                y_test, adj_t, seed, max_epochs=args.max_epochs,
                patience=args.patience, lr=args.lr, mlp_mode=args.mlp_mode,
                mlp_n_steps=args.mlp_n_steps, mlp_batch=args.mlp_batch,
                X_train_sp=X_train, X_test_sp=X_test)
            for key, val in t.items():
                if isinstance(val, (int, float, np.number)) and key != "seed":
                    summary_rows.append({"model": mname, "seed": seed,
                                         "metric": key, "value": val})
            tag = f"{mname}_seed{seed}"
            if len(hist):
                hist_store[tag] = hist
                hist["model"] = mname
                hist["seed"] = seed
                hist.to_csv(os.path.join(args.out, f"history_{tag}.csv"),
                            index=False)
            with torch.no_grad():
                if mname == "graphsage":
                    proba = predict_proba_binary(model, X_test_csr, adj_test_of(mname, X_test_csr, adj_t))
                else:
                    proba = predict_proba_binary(model, X_test_csr)
            pred_rows.append(pd.DataFrame({
                "model": mname, "seed": seed, "original_index": splits["test"],
                "y_true": y_test, "y_pred": proba.argmax(1).numpy(),
                "p_fake": proba[:, 1].numpy()}))
            print(f"    -> test F1={t['f1']:.4f} P={t['precision']:.4f} "
                  f"R={t['recall']:.4f} best_epoch={t['best_epoch']} "
                  f"valF1={t['best_val_f1']:.4f} time={t['time_s']}s")

    piv = (pd.DataFrame(summary_rows).pivot_table(
        index=["model", "seed"], columns="metric", values="value")
        .reset_index())
    agg = piv.groupby("model").agg(
        **{"f1_mean": ("f1", "mean"), "f1_std": ("f1", "std"),
           "precision_mean": ("precision", "mean"),
           "precision_std": ("precision", "std"),
           "recall_mean": ("recall", "mean"), "recall_std": ("recall", "std"),
           "acc_mean": ("accuracy", "mean"),
           "n_mean": ("n", "mean")}).reset_index()
    print("\n=== aggregate (seeds=all) ===")
    print(agg[["model", "f1_mean", "f1_std", "precision_mean", "recall_mean",
               "n_mean"]].to_string(index=False))

    os.makedirs(args.out, exist_ok=True)
    piv.to_csv(os.path.join(args.out, "metrics_perseed.csv"), index=False)
    agg.to_csv(os.path.join(args.out, "metrics_aggregate.csv"), index=False)
    pd.concat(pred_rows).to_csv(os.path.join(args.out, "predictions.csv"),
                                index=False)

    ev = agg.rename(columns={
        "f1_mean": "f1", "f1_std": "f1_std", "precision_mean": "precision",
        "recall_mean": "recall", "n_mean": "n"})
    ev["split"] = "test"
    ev = ev[["model", "split", "n", "f1", "precision", "recall", "f1_std"]]
    f1_map = dict(zip(ev["model"], ev["f1"]))
    gap = (f1_map.get("graphsage", np.nan) - f1_map.get("mlp", np.nan)) * 100
    ev["f1_gap_pp"] = f"{gap:.2f}"
    for c in ("f1", "precision", "recall", "f1_std"):
        ev[c] = (ev[c] * 100).round(2)
    evpath = os.path.join(args.out, "evidence_table.csv")
    ev.to_csv(evpath, index=False)
    print(f"\n[out] saved evidence table -> {evpath}")
    print(ev[["model", "split", "n", "f1", "precision", "recall",
              "f1_gap_pp"]].to_string(index=False))

    meta = dict(task_id="2604.08131_gnn_misinfo",
                csv_sha256=EXPECTED_SHA256,
                split="stratified 80/10/10 random_state=42 (test 0.1, val 0.2222)",
                tfidf_max_features=args.max_features, knn_k=args.k,
                knn_metric=args.knn_metric, graph_scope="train-only; "
                "self-loops; D^-1 row-normalisation; val/test isolated nodes",
                model_hidden="[256,128]", optimizer="adam lr=%.4f" % args.lr,
                early_stopping="val F1 patience=%d" % args.patience,
                max_epochs=args.max_epochs, seeds=args.seeds,
                mlp_mode=args.mlp_mode)
    with open(os.path.join(args.out, "run_meta.json"), "w") as f:
        json.dump(meta, f, indent=2)
    print(f"[out] run_meta.json")


def adj_test_of(model_name, X, adj):
    if model_name == "graphsage":
        return to_csr_tensor(sp.identity(X.shape[0], format="csr"))
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default=None)
    ap.add_argument("--out", default=os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "results"))
    ap.add_argument("--models", default="both", help="both|graphsage|mlp")
    ap.add_argument("--seeds", default="0,1,2")
    ap.add_argument("--max-epochs", type=int, default=200)
    ap.add_argument("--max-features", type=int, default=5000)
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--knn-metric", default="euclidean",
                    choices=["euclidean", "cosine", "manhattan"])
    ap.add_argument("--patience", type=int, default=10)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--mlp-mode", default="full_batch",
                    choices=["full_batch", "minibatch", "sklearn"])
    ap.add_argument("--mlp-n-steps", type=int, default=200)
    ap.add_argument("--mlp-batch", type=int, default=512)
    ap.add_argument("--verify-sha", action="store_true")
    args = ap.parse_args()
    args.seeds = [int(s) for s in args.seeds.split(",")]
    run_protocol(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())