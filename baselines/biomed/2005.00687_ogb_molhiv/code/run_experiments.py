#!/usr/bin/env python3
"""Full reproducible pipeline for the OGBG-MOLHIV benchmark reproduction.

Reads the frozen jsonl files (via prepare_data.py / cached PyG objects),
trains GNN models (GIN / GCN, +/- virtual node) and non-graph baselines
(LogReg / RF / MLP on aggregated atom features), and writes:

  results/evidence_table.csv   one row per model (mean over seeds for GNNs)
  results/model_results.json   per-seed and aggregated results
  results/runs/*.json          each individual run
  results/predictions/*.npz    test-set predicted probabilities

Usage:
  python run_experiments.py --seeds 42,7,1 --models gin,gin-vn,gcn,gcn-vn
                            [--device cuda] [--hidden 256] [--dropout 0.3]
                            [--epochs 80] [--patience 15] [--batch 128]
"""

import argparse
import csv
import json
import os
import time

import numpy as np
import torch
import torch.nn.functional as F
from sklearn.metrics import roc_auc_score
from torch_geometric.loader import DataLoader

import config
from models import GCNModel, GINModel, MLPBaseline
from features_cache import get_cached
from baselines import fit_predict_logreg, fit_predict_rf

IN_DIM = 9

GNN_ARCH = {"gin": GINModel, "gin-vn": GINModel, "gcn": GCNModel, "gcn-vn": GCNModel}


def set_seed(seed):
    np.random.seed(seed)
    torch.manual_seed(seed)


def eprint(*a):
    print(*a, flush=True)


def load_splits():
    if not all(os.path.isfile(f"/tmp/molhiv/{n}.pt") for n in ("train", "valid", "test")):
        eprint("PyG cache not found; running prepare_data.py first ...")
        import subprocess, sys
        subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                     "prepare_data.py")], check=True)
    return {n: torch.load(f"/tmp/molhiv/{n}.pt", weights_only=False)
            for n in ("train", "valid", "test")}


def evaluate(model, loader, device):
    model.eval()
    preds, ys = [], []
    with torch.no_grad():
        for batch in loader:
            if isinstance(batch, (list, tuple)):
                x, y = batch
                b = type("B", (), {})()
                b.x = x.to(device)
                b.y = y.to(device)
                b.batch = None
                b.edge_index = None
            else:
                b = batch.to(device)
            if getattr(model, "is_feature_mlp", False):
                logits = model(b.x)
            else:
                logits = model(b.x, b.edge_index, b.batch)
            preds.append(torch.sigmoid(logits).view(-1))
            ys.append(b.y.view(-1).float())
    preds = torch.cat(preds).cpu().numpy()
    ys = torch.cat(ys).cpu().numpy()
    return roc_auc_score(ys, preds), preds, ys


def train_model(model, train_loader, valid_loader, device, epochs, patience, lr,
                label):
    model = model.to(device)
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    sched = torch.optim.lr_scheduler.ReduceLROnPlateau(opt, mode="max", factor=0.5,
                                                       patience=max(3, patience // 3))
    best_auc, best_state, best_ep, bad = -1.0, None, 0, 0
    for epoch in range(1, epochs + 1):
        model.train()
        loss_sum, nb = 0.0, 0
        for batch in train_loader:
            if isinstance(batch, (list, tuple)):
                x, y = batch
                b = type("B", (), {})()
                b.x = x.to(device); b.y = y.to(device); b.batch = None; b.edge_index = None
            else:
                b = batch.to(device)
            opt.zero_grad()
            if getattr(model, "is_feature_mlp", False):
                logits = model(b.x)
            else:
                logits = model(b.x, b.edge_index, b.batch)
            loss = F.binary_cross_entropy_with_logits(logits.view(-1), b.y.view(-1).float())
            loss.backward()
            opt.step()
            loss_sum += loss.item(); nb += 1
        va, _, _ = evaluate(model, valid_loader, device)
        sched.step(va)
        if va > best_auc:
            best_auc, best_ep, bad = va, epoch, 0
            best_state = {k: v.detach().clone() for k, v in model.state_dict().items()}
        else:
            bad += 1
        if epoch == 1 or epoch % 5 == 0:
            eprint(f"  [{label}] ep {epoch:3d} loss {loss_sum/nb:.4f} "
                   f"validAUC {va:.4f} best {best_auc:.4f} @{best_ep}")
        if bad >= patience:
            eprint(f"  [{label}] early stop @ {epoch}, best validAUC {best_auc:.4f} @ {best_ep}")
            break
    model.load_state_dict(best_state)
    return best_auc, best_ep


def run_gnn(model_name, virtual_node, hidden, layers, dropout, splits, seed,
            args, device):
    set_seed(seed)
    torch.manual_seed(seed)
    gen = torch.Generator().manual_seed(seed)
    train_loader = DataLoader(splits["train"], batch_size=args.batch, shuffle=True,
                              generator=gen)
    valid_loader = DataLoader(splits["valid"], batch_size=args.batch, shuffle=False)
    test_loader = DataLoader(splits["test"], batch_size=args.batch, shuffle=False)
    arch = GNN_ARCH[model_name]
    model = arch(IN_DIM, hidden, layers, dropout, virtual_node=virtual_node)
    label = model_name
    t0 = time.time()
    best_va, best_ep = train_model(model, train_loader, valid_loader, device,
                                   args.epochs, args.patience, args.lr, label)
    test_auc, preds_test, yte = evaluate(model, test_loader, device)
    eprint(f"  [{label}] seed {seed} -> test ROC-AUC {test_auc:.4f}")
    return {
        "model": model_name,
        "virtual_node": virtual_node,
        "seed": seed,
        "valid_roc_auc": round(float(best_va), 4),
        "test_roc_auc": round(float(test_auc), 4),
        "best_epoch": int(best_ep),
        "train_seconds": round(time.time() - t0, 1),
        "params": {"hidden": hidden, "layers": layers, "dropout": dropout, "lr": args.lr},
        "pred_test": preds_test.tolist(),
        "y_test": yte.tolist(),
    }


def run_mlp(feat_key, out_feat_dim, hidden, dropout, splits, seed, args, device):
    set_seed(seed)
    cache = get_cached()
    Xtr, ytr = cache["train"]; Xva, yva = cache["valid"]; Xte, yte = cache["test"]
    if feat_key == "mean9":  # strict 'mean-pooling only' baseline: first 9 cols = means
        Xtr, Xva, Xte = Xtr[:, :9], Xva[:, :9], Xte[:, :9]
        out_feat_dim = 9

    model = MLPBaseline(out_feat_dim, hidden, dropout=dropout)
    model.is_feature_mlp = True
    tr = torch.utils.data.TensorDataset(Xtr, ytr)
    va = torch.utils.data.TensorDataset(Xva, yva)
    te = torch.utils.data.TensorDataset(Xte, yte)
    train_loader = DataLoader(tr, batch_size=args.batch, shuffle=True,
                              generator=torch.Generator().manual_seed(seed))
    valid_loader = DataLoader(va, batch_size=args.batch, shuffle=False)
    test_loader = DataLoader(te, batch_size=args.batch, shuffle=False)
    t0 = time.time()
    best_va, best_ep = train_model(model, train_loader, valid_loader, device,
                                   epochs=min(50, args.epochs), patience=args.patience,
                                   lr=args.lr, label=f"mlp-{feat_key}")
    test_auc, preds_test, yte_s = evaluate(model, test_loader, device)
    eprint(f"  [mlp-{feat_key}] seed {seed} -> test ROC-AUC {test_auc:.4f}")
    return {"model": f"mlp-{feat_key}", "virtual_node": False, "seed": seed,
            "valid_roc_auc": round(float(best_va), 4),
            "test_roc_auc": round(float(test_auc), 4),
            "best_epoch": int(best_ep),
            "train_seconds": round(time.time() - t0, 1),
            "pred_test": preds_test.tolist(), "y_test": yte_s.tolist()}


def save_predictions(rec):
    pred_dir = os.path.join(config.results_dir(), "predictions")
    os.makedirs(pred_dir, exist_ok=True)
    tag = f"{rec['model']}__s{rec['seed']}"
    np.savez_compressed(os.path.join(pred_dir, f"{tag}.npz"),
                        pred_test=np.asarray(rec["pred_test"]),
                        y_test=np.asarray(rec["y_test"]))
    runs_dir = os.path.join(config.results_dir(), "runs")
    os.makedirs(runs_dir, exist_ok=True)
    with open(os.path.join(runs_dir, f"{tag}.json"), "w") as f:
        json.dump({k: v for k, v in rec.items() if k not in ("pred_test", "y_test")},
                  f, indent=2)


def write_outputs(records, baselines):
    # aggregate GNN models across seeds
    agg = {}
    for r in records:
        agg.setdefault(r["model"], []).append(r)
    table_rows = []
    for name, runs in agg.items():
        best_tr = max(r["test_roc_auc"] for r in runs)
        mean_te = float(np.mean([r["test_roc_auc"] for r in runs]))
        std_te = float(np.std([r["test_roc_auc"] for r in runs]))
        mean_va = float(np.mean([r["valid_roc_auc"] for r in runs]))
        table_rows.append({"model": f"{name} (seed-mean)",
                           "virtual_node": runs[0]["virtual_node"],
                           "valid_roc_auc": round(mean_va, 4),
                           "test_roc_auc": round(mean_te, 4)})
    for b in baselines:
        table_rows.append({"model": b["model"], "virtual_node": False,
                           "valid_roc_auc": round(b["valid_roc_auc"], 4),
                           "test_roc_auc": round(b["test_roc_auc"], 4)})
    csv_path = os.path.join(config.results_dir(), "evidence_table.csv")
    with open(csv_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["model", "virtual_node", "valid_roc_auc",
                                          "test_roc_auc"])
        w.writeheader()
        for row in table_rows:
            w.writerow(row)
    eprint("wrote", csv_path)

    # full detail (per-seed too)
    detail = {"gnn": [], "baselines": []}
    for r in records:
        detail["gnn"].append({k: v for k, v in r.items()
                              if k not in ("pred_test", "y_test")})
    for b in baselines:
        detail["baselines"].append({k: v for k, v in b.items()
                                    if k not in ("pred_test", "y_test")})
    with open(os.path.join(config.results_dir(), "model_results.json"), "w") as f:
        json.dump(detail, f, indent=2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", default="auto", help="auto|cuda|cpu")
    ap.add_argument("--seeds", default="42,7,1", help="comma-separated seeds")
    ap.add_argument("--models", default="gin,gin-vn,gcn,gcn-vn",
                    help="comma-separated: gin,gin-vn,gcn,gcn-vn")
    ap.add_argument("--batch", type=int, default=128)
    ap.add_argument("--hidden", type=int, default=256)
    ap.add_argument("--layers", type=int, default=5)
    ap.add_argument("--dropout", type=float, default=0.3)
    ap.add_argument("--epochs", type=int, default=80)
    ap.add_argument("--patience", type=int, default=15)
    ap.add_argument("--lr", type=float, default=1e-3)
    args = ap.parse_args()

    if args.device == "auto" or args.device == "cuda":
        device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    else:
        device = torch.device("cpu")
    if device.type == "cuda":
        torch.cuda.init()
        eprint("using GPU:", torch.cuda.get_device_name(device))
    else:
        torch.set_num_threads(min(8, os.cpu_count() or 4))
        eprint("using CPU")

    seeds = [int(s) for s in args.seeds.split(",")]
    models = args.models.split(",")
    eprint("data dir:", config.DATA_DIR)
    splits = load_splits()
    eprint(f"train {len(splits['train'])} valid {len(splits['valid'])} "
           f"test {len(splits['test'])}")

    records, baselines = [], []
    runs_dir = os.path.join(config.results_dir(), "runs")
    if os.path.isdir(runs_dir):
        for f in os.listdir(runs_dir):
            if not f.endswith(".json"):
                continue
            m = f.split("__s")[0]
            if m in models:
                with open(os.path.join(runs_dir, f)) as fh:
                    rec = json.load(fh)
                if rec.get("model") == m and rec not in records:
                    eprint(f"  preloaded run {f}")
                    records.append(rec)

    def existing_seeds(model):
        """Return seeds already completed (previously saved runs)."""
        out = []
        if os.path.isdir(runs_dir):
            for f in os.listdir(runs_dir):
                if f.startswith(f"{model}__s") and f.endswith(".json"):
                    out.append(int(f.split("__s")[1][:-5]))
        return set(out)

    for m in models:
        vn = m.endswith("-vn")
        base = m[:3]
        done = existing_seeds(m)
        for seed in seeds:
            if seed in done:
                eprint(f"=== {m} seed {seed} (already done, resuming) ===")
                continue
            eprint(f"=== {m} seed {seed} ===")
            rec = run_gnn(m, vn, args.hidden, args.layers, args.dropout,
                          splits, seed, args, device)
            save_predictions(rec)
            records.append(rec)

    # non-graph baselines from cached aggregate features
    cache = get_cached()
    Xtr, ytr = cache["train"]; Xva, yva = cache["valid"]; Xte, yte = cache["test"]
    eprint("=== logreg / rf on 46-d aggregated features ===")
    for fn in (fit_predict_logreg, fit_predict_rf):
        r = fn(Xtr.numpy(), ytr.numpy(), Xva.numpy(), yva.numpy(),
               Xte.numpy(), yte.numpy(), seed=42)
        r.pop("prototype", None)
        r["seed"] = 42
        baselines.append(r)

    # strict 'mean-pooling only' non-graph baselines
    eprint("=== mlp on mean-pooled 9-d atom features ===")
    rec = run_mlp("mean9", 9, 64, 0.25, splits, seeds[0], args, device)
    rec["model"] = "mlp-mean9"
    save_predictions(rec)
    baselines.append(rec)
    eprint("=== mlp on 46-d aggregated features ===")
    rec = run_mlp("ext", 46, 64, 0.25, splits, 42, args, device)
    rec["model"] = "mlp-ext"
    save_predictions(rec)
    baselines.append(rec)

    write_outputs(records, baselines)


if __name__ == "__main__":
    main()