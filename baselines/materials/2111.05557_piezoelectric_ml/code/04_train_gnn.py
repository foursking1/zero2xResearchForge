"""04_train_gnn.py
Lightweight graph neural network (message-passing) over COMPOSITION graphs,
plus an MLP-on-features deep baseline. No crystal structures are available in
the frozen package (no CIF files), so the graph is built from composition:
nodes = elements, edges = fully connected with weight = min(fraction_i, fraction_j).
This is a composition-GNN proxy for the paper's structure-based CGCNN/SchNet.

Protocol: same fixed 5-fold CV (seed 42) as the ML models; early stopping on the
validation fold; CPU training.
Outputs: results/gnn_results.csv + evidence_table rows appended + results/gnn_oof.csv
"""
import os
import sys
import json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F

from common import (parse_formula, load_labels, ELEM, PROPERTY_NAMES, SEED,
                    fixed_folds, mae_rmse_r2, RESULTS_DIR)

torch.set_num_threads(8)
torch.manual_seed(SEED)
np.random.seed(SEED)
DEVICE = torch.device("cpu")
print("device:", DEVICE)

df = load_labels()
comps = df["Materials"].map(parse_formula)
keep = comps.notna().to_numpy()
df = df.loc[keep].reset_index(drop=True)
comps = comps.loc[keep].tolist()
y = df["Piezoelectric_Modulus"].to_numpy(dtype=float)

# ---- build graphs ---------------------------------------------------------
PROP_IDX = {p: i for i, p in enumerate(PROPERTY_NAMES)}
PROP_MATRIX = {e: [v for v in ELEM[e][: len(PROPERTY_NAMES)]] for e in ELEM}

graphs = []  # (node_feat[N,12], edge_index[2,E], edge_attr[E], frac[N], n_elements)
for comp in comps:
    els = sorted(comp.keys())
    tot = sum(comp.values())
    fr = np.array([comp[e] / tot for e in els], dtype=np.float32)
    nf = np.array([PROP_MATRIX[e] for e in els], dtype=np.float32)
    ei = []
    ea = []
    for i in range(len(els)):
        for j in range(len(els)):
            if i != j:
                ei.append((i, j))
                ea.append(min(fr[i], fr[j]))
    edge_index = np.array(ei, dtype=np.int64).T if ei else np.zeros((2, 0), dtype=np.int64)
    edge_attr = np.array(ea, dtype=np.float32)
    graphs.append((nf, edge_index, edge_attr, fr, len(els)))

N_PROP = len(PROPERTY_NAMES)


class MPNN(nn.Module):
    """Simple message passing net: node mlp, T hops, fraction-weighted readout."""

    def __init__(self, d_node=N_PROP, hidden=64, T=3):
        super().__init__()
        self.T = T
        self.node_mlp = nn.Sequential(
            nn.Linear(d_node, hidden), nn.SiLU(),
            nn.Linear(hidden, hidden), nn.SiLU(),
        )
        self.msg = nn.Sequential(
            nn.Linear(hidden + 1, hidden), nn.SiLU(),
            nn.Linear(hidden, hidden),
        )
        self.readout = nn.Sequential(
            nn.Linear(hidden, hidden), nn.SiLU(),
            nn.Linear(hidden, hidden), nn.SiLU(),
            nn.Linear(hidden, 1),
        )

    def forward(self, nf, ei, ea, fr):
        h = self.node_mlp(nf)                       # [N, hidden]
        for _ in range(self.T):
            src, dst = ei[0], ei[1]
            m = self.msg(torch.cat([h[src], ea[:, None]], dim=1))  # [E, hidden]
            agg = torch.zeros_like(h)
            agg.index_add_(0, dst, m)
            h = h + agg
        g = torch.sum(h * fr[:, None], dim=0)       # [hidden]
        return self.readout(g).squeeze()


class MLPBaseline(nn.Module):
    def __init__(self, d_in, hidden=128):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(d_in, hidden), nn.SiLU(),
            nn.Linear(hidden, hidden), nn.SiLU(),
            nn.Linear(hidden, hidden), nn.SiLU(),
            nn.Linear(hidden, 1),
        )

    def forward(self, x):
        return self.net(x).squeeze()


def build_batch(indices, feats=None):
    """Return tensors for a batch of graphs (MPNN) + optional feature matrix."""
    nf_l, ei_l, ea_l, fr_l, ndim = [], [], [], [], []
    for i in indices:
        nf, ei, ea, fr, n = graphs[i]
        nf_l.append(torch.tensor(nf))
        ei_l.append(torch.tensor(ei))
        ea_l.append(torch.tensor(ea))
        fr_l.append(torch.tensor(fr))
        ndim.append(n)
    nf_b = torch.cat(nf_l)
    fr_b = torch.cat(fr_l)
    # offset edges
    off = 0
    ei_off = []
    for k, ei in enumerate(ei_l):
        if ei.numel() > 0:
            ei_off.append(ei + off)
        off += ndim[k]
    ei_b = torch.cat(ei_off, dim=1) if ei_off else torch.zeros((2, 0), dtype=torch.int64)
    ea_b = torch.cat(ea_l)
    return nf_b, ei_b, ea_b, fr_b


def train_eval_split(model, tr, va, epochs=60, lr=1e-3, bs=64, patience=12):
    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-5)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=epochs)
    best = (1e9, None)
    bad = 0
    for ep in range(epochs):
        model.train()
        idx = torch.randperm(len(tr))
        for b in range(0, len(tr), bs):
            bi = tr[idx[b:b + bs]]
            nf, ei, ea, fr = build_batch(bi)
            opt.zero_grad()
            loss = F.smooth_l1_loss(model(nf, ei, ea, fr), torch.tensor(y[bi]))
            loss.backward()
            opt.step()
        model.eval()
        with torch.no_grad():
            va_pred = []
            for i in va:
                nf, ei, ea, fr, _ = graphs[i]
                p = model(torch.tensor(nf), torch.tensor(ei), torch.tensor(ea),
                          torch.tensor(fr)).item()
                va_pred.append(p)
            mae = float(np.mean(np.abs(y[va] - np.array(va_pred))))
        sched.step()
        if mae < best[0] - 1e-6:
            best = (mae, va_pred)
            bad = 0
        else:
            bad += 1
        if bad >= patience:
            break
    return best[1]


def run_gnn_cv(model_fn, folds, label):
    oof = np.zeros(len(y))
    per_fold = []
    for k, (tr, va) in enumerate(folds):
        model = model_fn()
        pred = train_eval_split(model, tr, va)
        oof[va] = np.array(pred)
        m = mae_rmse_r2(y[va], np.array(pred))
        per_fold.append({"fold": k, **m})
        print(f"[{label}] fold {k}: MAE {m['MAE']:.4f} R2 {m['R2']:.4f}")
    pooled = mae_rmse_r2(y, oof)
    return per_fold, pooled, oof


# ---- load feature matrix for the MLP baseline ------------------------------
d = np.load(os.path.join(RESULTS_DIR, "features.npz"), allow_pickle=True)
Xb = d["Xb"].astype(np.float32)
Xe = d["Xe"].astype(np.float32)

folds = fixed_folds(len(y), n_splits=5, seed=SEED)

results = []

# MPNN on composition graphs
per_fold, pooled, oof_gnn = run_gnn_cv(lambda: MPNN(), folds, "MPNN")
print(f"MPNN pooled -> MAE {pooled['MAE']:.4f} R2 {pooled['R2']:.4f}")
results.append({"model": "mpnn", "feature_set": "composition_graph",
                "per_fold": per_fold, "pooled": pooled})
np.save(os.path.join(RESULTS_DIR, "mpnn_oof.npy"), oof_gnn)

# MLP baseline on basic features
def train_mlp(X, tr, va):
    model = MLPBaseline(X.shape[1])
    opt = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-5)
    xt = torch.tensor(X[tr]); yt = torch.tensor(y[tr])
    best, bad = 1e9, 0
    for ep in range(200):
        model.train(); opt.zero_grad()
        loss = F.smooth_l1_loss(model(xt), yt)
        loss.backward(); opt.step()
        model.eval()
        with torch.no_grad():
            p = model(torch.tensor(X[va])).numpy()
        mae = float(np.mean(np.abs(y[va] - p)))
        if mae < best - 1e-6:
            best = mae; bad = 0
        else:
            bad += 1
            if bad >= 20: break
    return model

for fname, X in [("basic", Xb), ("enhanced", Xe)]:
    oof = np.zeros(len(y))
    per_fold = []
    for k, (tr, va) in enumerate(folds):
        m = train_mlp(X, tr, va)
        with torch.no_grad():
            pred = m(torch.tensor(X[va])).numpy()
        oof[va] = pred
        per_fold.append({"fold": k, **mae_rmse_r2(y[va], pred)})
        print(f"[mlp_{fname}] fold {k}: MAE {per_fold[-1]['MAE']:.4f} R2 {per_fold[-1]['R2']:.4f}")
    pooled = mae_rmse_r2(y, oof)
    print(f"[mlp_{fname}] pooled -> MAE {pooled['MAE']:.4f} R2 {pooled['R2']:.4f}")
    results.append({"model": "mlp", "feature_set": fname,
                    "per_fold": per_fold, "pooled": pooled})
    np.save(os.path.join(RESULTS_DIR, f"mlp_{fname}_oof.npy"), oof)

# ---- serialize --------------------------------------------------------------
rows = []
for r in results:
    for m in ["MAE", "RMSE", "R2", "Spearman"]:
        vals = [f[m] for f in r["per_fold"]]
        rows.append({"model": r["model"], "feature_set": r["feature_set"],
                     "split": "5fold_cv_mean", "metric": m,
                     "value": float(np.mean(vals)), "value_std": float(np.std(vals))})
        rows.append({"model": r["model"], "feature_set": r["feature_set"],
                     "split": "5fold_cv_pooled", "metric": m,
                     "value": float(r["pooled"][m]), "value_std": float("nan")})
    for f in r["per_fold"]:
        rows.append({"model": r["model"], "feature_set": r["feature_set"],
                     "split": f"5fold_cv_fold{f['fold']}", "metric": "MAE",
                     "value": float(f["MAE"]), "value_std": float("nan")})
        rows.append({"model": r["model"], "feature_set": r["feature_set"],
                     "split": f"5fold_cv_fold{f['fold']}", "metric": "R2",
                     "value": float(f["R2"]), "value_std": float("nan")})

gnn_ev = pd.DataFrame(rows)
ev_path = os.path.join(RESULTS_DIR, "evidence_table.csv")
if os.path.exists(ev_path):
    ev = pd.read_csv(ev_path)
    ev = pd.concat([ev, gnn_ev], ignore_index=True)
else:
    ev = gnn_ev
ev.to_csv(ev_path, index=False)
print("appended GNN rows to evidence_table.csv; total rows:", len(ev))

gnn_summary = {}
for r in results:
    key = f"{r['model']}__{r['feature_set']}"
    gnn_summary[key] = {"pooled": r["pooled"],
                        "mean": {m: float(np.mean([f[m] for f in r["per_fold"]]))
                                 for m in ["MAE", "R2"]}}
with open(os.path.join(RESULTS_DIR, "gnn_metrics.json"), "w") as f:
    json.dump(gnn_summary, f, indent=2)
print("saved results/gnn_metrics.json")
print("done.")