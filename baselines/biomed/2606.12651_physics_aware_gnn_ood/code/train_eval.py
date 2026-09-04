"""Single (variant, seed) GINE training + OOD evaluation on COCONUT.

Frozen splits:
  * OOD test = COCONUT 30k subset (band-dropped). Never seen during training:
    no loss, no validation, no hyper-parameter selection.
  * train / val = HIV + Tox21 (band-dropped). val = first 10%% of graph ids
    (deterministic, seed=0); the remaining 90%% are the training pool.

Mini-batches are *contiguous ranges* of graph ids so every batch is a single
contiguous node/edge slice of the flat feature tensors (pure tensor ops, fast CPU).
"""
import argparse
import json
import os
import time
import warnings

import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F
from sklearn.metrics import roc_auc_score

from config import ATOM_D, BOND_D, MODEL, RESULT_DIR, SEEDS, TRAIN, TORCH_THREADS
from data_pipeline import main as build_data
from model import GINE, get_pos_weights

warnings.filterwarnings("ignore")
torch.set_num_threads(TORCH_THREADS)
torch.manual_seed(0)

VARIANTS = {
    "baseline":  dict(num_aux=0, targets=[]),
    "complexity": dict(num_aux=1, targets=["comp_z"]),
    "strain":    dict(num_aux=1, targets=["strain_z"]),
    "both":      dict(num_aux=2, targets=["comp_z", "strain_z"]),
}
AUX_META = {}

forDescriptionIfo = "gpu_or_cpu"


def rauc(y_true, y_score):
    return float(roc_auc_score(np.asarray(y_true), np.asarray(y_score)))


class FlatGraphs:
    """Flat contiguous multi-graph container. graph ids are dense and contiguous."""

    def __init__(self, X, edge_index, edge_attr, node_off, labels, aux):
        self.X = torch.from_numpy(np.ascontiguousarray(X, dtype=np.float32))
        self.edge_index = torch.from_numpy(np.asarray(edge_index, dtype=np.int64))
        self.edge_attr = torch.from_numpy(np.ascontiguousarray(edge_attr, dtype=np.float32))
        self.node_off = node_off
        self.labels = labels
        self.aux = {k: torch.from_numpy(np.asarray(v, dtype=np.float32)).clone() for k, v in aux.items()}
        self.n_graphs = int(len(labels))
        self.node_off_np = node_off.numpy()
        self._edge_off = self._edge_offsets()

    def _edge_offsets(self):
        n = self.n_graphs
        counts = np.zeros(n, dtype=np.int64)
        sink = self.edge_index[1].numpy()
        ids = np.searchsorted(self.node_off_np, sink, side="right") - 1
        np.add.at(counts, ids, 1)
        return np.concatenate([[0], np.cumsum(counts)])  # length n+1

    def range(self, g0, g1):
        """Contiguous sample covering graphs [g0, g1)."""
        na, nb = int(self.node_off[g0]), int(self.node_off[g1])
        ea, eb = int(self._edge_off[g0]), int(self._edge_off[g1])
        X = self.X[na:nb]
        eg = self.edge_index[:, ea:eb] - na
        ea_t = self.edge_attr[ea:eb]
        counts = np.diff(self.node_off_np[g0:g1 + 1])
        b = torch.from_numpy(np.repeat(np.arange(g1 - g0, dtype=np.int64), counts)).long()
        y = torch.from_numpy(np.ascontiguousarray(self.labels[g0:g1], dtype=np.float32))
        aux = {k: v[g0:g1] for k, v in self.aux.items()}
        return X, eg, ea_t, b, y, aux


def make_flat(art, split):
    g = art["g" + split]
    frame = art[split + "_frame"]
    aux = {k: frame[k].values for k in ("comp_z", "strain_z")}
    return FlatGraphs(g["X"], g["edge_index"], g["edge_attr"],
                      torch.from_numpy(g["node_off"]), g["label"], aux)


def evaluate(model, ds, g0, g1, device="cpu"):
    model.eval()
    preds, ys = [], []
    with torch.no_grad():
        step = 2048
        for s in range(g0, g1, step):
            e = min(s + step, g1)
            X, eg, ea, b, y, _ = ds.range(s, e)
            X, eg, ea, b = X.to(device), eg.to(device), ea.to(device), b.to(device)
            logit, _ = model(X, eg, ea, b)
            preds.append(torch.sigmoid(logit[:, 0]).cpu().numpy())
            ys.append(y)
    return rauc(np.concatenate(ys), np.concatenate(preds))


def train_variant(var, seed, art, device="cpu", max_epochs=None, batch_size=None):
    cfg = dict(TRAIN)
    if max_epochs:
        cfg["max_epochs"] = max_epochs
    if batch_size:
        cfg["batch_size"] = batch_size
    vcfg = VARIANTS[var]
    num_aux = vcfg["num_aux"]

    tr = make_flat(art, "tr")
    te = make_flat(art, "te")
    n_val = max(1, int(tr.n_graphs * cfg["val_frac"]))
    g_val = (0, n_val)
    g_train = (n_val, tr.n_graphs)

    y_tr = tr.labels[g_train[0]:g_train[1]]
    pos_w = get_pos_weights(torch.from_numpy(np.asarray(y_tr, dtype=np.float32))) if cfg["pos_weight"] else None

    torch.manual_seed(seed)
    np.random.seed(seed)
    rng = np.random.default_rng(seed)
    model = GINE(ATOM_D, BOND_D, hidden=64, layers=3, num_aux=num_aux)
    model.to(device)
    opt = torch.optim.Adam(model.parameters(), lr=cfg["lr"], weight_decay=cfg["weight_decay"])

    n_train = g_train[1] - g_train[0]
    chunk_ids = list(range(0, n_train, cfg["batch_size"]))

    best_val, best_state, best_ep, patience = -1.0, None, -1, 0
    curves = dict(epoch=[], loss=[], val_auc=[])
    t0 = time.time()
    for ep in range(cfg["max_epochs"]):
        model.train()
        order = rng.permutation(len(chunk_ids))
        ep_loss = 0.0
        for ci in order:
            s = chunk_ids[ci]
            e = min(s + cfg["batch_size"], n_train)
            X, eg, ea, b, y, aux = tr.range(s + n_val, e + n_val)
            X, eg, ea, b, y = X.to(device), eg.to(device), ea.to(device), b.to(device), y.to(device)
            at = []
            for tk in vcfg["targets"]:
                tv = aux[tk].to(device)
                at.append((tv, ~torch.isnan(tv)))
            opt.zero_grad()
            logit, auxo = model(X, eg, ea, b)
            loss = aux_loss_fn(logit, y, auxo, at, cfg["aux_weight"], pos_w)
            loss.backward()
            opt.step()
            ep_loss += float(loss.item())
        val = evaluate(model, tr, g_val[0], g_val[1], device=device)
        curves["epoch"].append(ep)
        curves["loss"].append(round(ep_loss / len(chunk_ids), 4))
        curves["val_auc"].append(round(val, 5))
        if val > best_val:
            best_val, best_ep, patience = val, ep, 0
            best_state = {k: v.detach().clone() for k, v in model.state_dict().items()}
        else:
            patience += 1
        if ep % 1 == 0 or patience >= cfg["patience"]:
            print("  [%s seed=%d] ep%02d loss=%.3f val_auc=%.4f (best %.4f)" %
                  (var, seed, ep, ep_loss / len(chunk_ids), val, best_val), flush=True)
        if patience >= cfg["patience"]:
            break

    model.load_state_dict(best_state)
    ood = evaluate(model, te, 0, te.n_graphs, device=device)
    print("  [%s seed=%d] OOD AUC(COCONUT) = %.5f  (val best %.4f @ep %d)" %
          (var, seed, ood, best_val, best_ep), flush=True)
    return dict(variant=var, seed=int(seed), ood_auc=round(float(ood), 5),
                val_auc_best=round(float(best_val), 5), best_epoch=int(best_ep),
                n_epochs=int(ep + 1), time_s=round(time.time() - t0, 1),
                pos_weight=bool(cfg["pos_weight"]), aux_w=float(cfg["aux_weight"]),
                hidden=MODEL["hidden"])


def aux_loss_fn(logit, y, auxo, at, aux_w, pos_w):
    y = y.to(logit.dtype).view(-1, 1)
    if pos_w is not None:
        pos_w = pos_w.to(logit.device) if isinstance(pos_w, torch.Tensor) else None
        loss_main = F.binary_cross_entropy_with_logits(logit, y, pos_weight=pos_w)
    else:
        loss_main = F.binary_cross_entropy_with_logits(logit, y)
    aux_r = []
    for o, (tv, valid) in zip(auxo, at):
        if valid.all():
            aux_r.append(F.mse_loss(o, tv))
        else:
            aux_r.append(F.mse_loss(o[valid], tv[valid]))
    loss_aux = aux_r[0] if aux_r else torch.zeros((), device=y.device)
    for a in aux_r[1:]:
        loss_aux = loss_aux + a
    return loss_main + aux_w * loss_aux


def resolve_device(device):
    if device == "cuda" and not torch.cuda.is_available():
        print("CUDA requested but unavailable - falling back to CPU", flush=True)
        return "cpu"
    return device


def run_all(variants=None, seeds=None, device="cpu", out=None, max_epochs=None, batch_size=None):
    if variants is None:
        variants = list(VARIANTS.keys())
    if seeds is None:
        seeds = SEEDS
    device = resolve_device(device)
    art = build_data()
    rows = []
    for v in variants:
        for s in seeds:
            rows.append(train_variant(v, s, art, device=device, max_epochs=max_epochs, batch_size=batch_size))
    df = pd.DataFrame(rows)
    if out:
        path = os.path.join(RESULT_DIR, out)
        df.to_json(path, orient="records", indent=1)
        csv_path = os.path.join(RESULT_DIR, "raw_evals.csv")
        df.to_csv(csv_path, index=False)
        print("saved", path, "and", csv_path)
    return df


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--variants", nargs="*", default=None)
    ap.add_argument("--seeds", type=int, nargs="*", default=None)
    ap.add_argument("--out", default="raw_evals.json")
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--max_epochs", type=int, default=None)
    ap.add_argument("--batch_size", type=int, default=None)
    ap.add_argument("--pos_weight", type=int, default=None, help="0/1 override TRAIN pos_weight")
    ap.add_argument("--aux_w", type=float, default=None, help="override TRAIN aux_weight")
    a = ap.parse_args()
    if a.pos_weight is not None:
        TRAIN["pos_weight"] = bool(a.pos_weight)
    if a.aux_w is not None:
        TRAIN["aux_weight"] = a.aux_w
    run_all(a.variants, a.seeds, a.device, out=a.out, max_epochs=a.max_epochs, batch_size=a.batch_size)