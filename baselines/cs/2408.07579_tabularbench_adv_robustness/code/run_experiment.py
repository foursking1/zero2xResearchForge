#!/usr/bin/env python3
"""TabularBench arXiv:2408.07579 — URL phishing-detection robustness replication (L1 critical claim).

Reproduces the two headline claims of the paper on the frozen URL use case:
  C1  Standard-trained deep models have near-identical clean (ID) accuracy but very
      different adversarial-robust accuracy ("ID close != robust close").
  C2  Adversarial training (AT) strongly improves robust accuracy while keeping clean
      accuracy essentially unchanged.

Protocol (see TASK.md):
  * Split  : official DefaultSplitter -> train_test_split(random_state=42, shuffle=True,
             stratify=y, test_size=0.2) applied twice (test 20%, then val 20% of train).
  * Scaling: per-feature min-max to [0,1]; statistics fitted on the train split ONLY; clipped.
  * Models : 4 feed-forward MLPs with ReLU and a single logit output.
  * Training: Adam (lr=1e-3, weight_decay=1e-4), batch 256, 12 epochs, BCEWithLogits.
             Standard  -> clean batches.
             AT        -> FGSM (1 step, eps=0.1, alpha=0.1, L2-normalised step + L2-ball
                          projection + [0,1] clip) inside each batch (FGSM-AT).
  * Attack : untargeted PGD-L2 on the full test set, eps=0.25, 40 steps, step=eps/4,
             grad-sign-free L2-normalised steps, projection to the L2 ball centred on the
             original sample, then clip to [0,1].
  * Metrics : clean accuracy and robust accuracy in %.

Everything is seeded and deterministic (seed=0); the code runs on CPU.
Run:  python3 run_experiment.py --data ../data/url.csv --out ../results
"""

import argparse
import json
import os
import time

HERE = os.path.dirname(os.path.abspath(__file__))
# agent_solution/code/ -> task root (contains frozen data/)
DEFAULT_DATA = os.path.join(HERE, "..", "..", "data", "url.csv")
DEFAULT_OUT = os.path.join(HERE, "..", "results")

os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
from sklearn.model_selection import train_test_split

SEED = 0
EVAL_EPS = 0.25
PGD_STEPS = 40
PGD_ALPHA = EVAL_EPS / 4.0
AT_EPS = 0.1
AT_STEPS = 1
AT_ALPHA = 0.1
EPOCHS = 12
BATCH = 256
LR = 1e-3
WD = 1e-4
EVAL_BATCH = 512

MODELS = {
    "mlp64": dict(sizes=[64], dropout=0.0),
    "mlp128_64": dict(sizes=[128, 64], dropout=0.0),
    "mlp256_128_64": dict(sizes=[256, 128, 64], dropout=0.0),
    "mlp128_64_drop": dict(sizes=[128, 64], dropout=0.3),
}


def set_seed(seed: int) -> None:
    torch.manual_seed(seed)
    np.random.seed(seed)


def load_data(path: str):
    df = pd.read_csv(path)
    feat_cols = [c for c in df.columns if c != "is_phishing"]
    y = df["is_phishing"].to_numpy().astype(np.int64)
    X = df[feat_cols].to_numpy(dtype=float)
    return X, y, feat_cols


def default_split(X, y):
    """Official TabularBench DefaultSplitter: 80/20 twice -> train/val/test."""
    idx = np.arange(len(y))
    i_tr, i_te = train_test_split(idx, random_state=42, shuffle=True,
                                  stratify=y, test_size=0.2)
    i_tr, i_va = train_test_split(i_tr, random_state=42, shuffle=True,
                                  stratify=y[i_tr], test_size=0.2)
    return i_tr, i_va, i_te


def fit_minmax(Xtr):
    lo = Xtr.min(axis=0)
    hi = Xtr.max(axis=0)
    span = hi - lo
    span[span == 0] = 1.0
    return lo, hi, span


def apply_minmax(X, lo, hi, span):
    return np.clip((X - lo) / span, 0.0, 1.0)


def to_t(x):
    return torch.as_tensor(x, dtype=torch.float32)


class MLP(nn.Module):
    def __init__(self, n_in, sizes, dropout=0.0):
        super().__init__()
        layers = []
        prev = n_in
        for h in sizes:
            layers += [nn.Linear(prev, h), nn.ReLU()]
            if dropout > 0:
                layers.append(nn.Dropout(dropout))
            prev = h
        layers.append(nn.Linear(prev, 1))
        self.net = nn.Sequential(*layers)

    def forward(self, x):
        return self.net(x).squeeze(-1)


def build_model(name, n_in):
    cfg = MODELS[name]
    return MLP(n_in, cfg["sizes"], cfg["dropout"])


def train_model(model, Xtr, ytr, at=False, seed=SEED):
    """minibatch Adam training; optionally with FGSM adversarial training."""
    set_seed(seed)
    opt = torch.optim.Adam(model.parameters(), lr=LR, weight_decay=WD)
    lossf = nn.BCEWithLogitsLoss()
    n = Xtr.shape[0]
    Xf = to_t(Xtr)
    yf = to_t(ytr).float()
    model.train()
    for _ in range(EPOCHS):
        perm = torch.randperm(n)
        for b in range(0, n, BATCH):
            idx = perm[b:b + BATCH]
            xb, yb = Xf[idx], yf[idx]
            if at:
                xadv = xb.clone().detach()
                for _ in range(AT_STEPS):
                    xadv.requires_grad_(True)
                    loss = lossf(model(xadv), yb)
                    grad = torch.autograd.grad(loss, xadv)[0]
                    gnorm = grad.norm(dim=1, keepdim=True).clamp_min(1e-12)
                    xadv = (xadv + AT_ALPHA * grad / gnorm).detach()
                    delta = xadv - xb
                    dn = delta.norm(dim=1, keepdim=True).clamp_min(1e-12)
                    xadv = xb + delta * (torch.clamp(dn, max=AT_EPS) / dn)
                    xadv = torch.clamp(xadv, 0.0, 1.0)
                opt.zero_grad()
                loss = lossf(model(xadv), yb)
            else:
                opt.zero_grad()
                loss = lossf(model(xb), yb)
            loss.backward()
            opt.step()
    return model


@torch.no_grad()
def accuracy(model, Xe, ye):
    model.eval()
    preds = torch.sigmoid(model(to_t(Xe))) > 0.5
    return float((preds.float() == to_t(ye).float()).float().mean().item())


def pgd_robust_accuracy(model, Xe, ye, eps=EVAL_EPS, steps=PGD_STEPS, batch=EVAL_BATCH):
    """Untargeted PGD-L2 maximizing BCE logits loss; projected + clipped per step."""
    model.eval()
    Xt = to_t(Xe)
    yt = to_t(ye).float()
    adv_all = []
    n = Xe.shape[0]
    for s in range(0, n, batch):
        x_orig = Xt[s:s + batch].clone()
        yb = yt[s:s + batch]
        xadv = x_orig.clone()
        for _ in range(steps):
            xadv.requires_grad_(True)
            loss = F.binary_cross_entropy_with_logits(model(xadv), yb)
            grad = torch.autograd.grad(loss, xadv)[0]
            gnorm = grad.norm(dim=1, keepdim=True).clamp_min(1e-12)
            xadv = (xadv + PGD_ALPHA * grad / gnorm).detach()
            delta = xadv - x_orig
            dn = delta.norm(dim=1, keepdim=True).clamp_min(1e-12)
            xadv = x_orig + delta * (torch.clamp(dn, max=eps) / dn)
            xadv = torch.clamp(xadv, 0.0, 1.0)
        adv_all.append(xadv)
    xadv_all = torch.cat(adv_all, dim=0)
    model.eval()
    with torch.no_grad():
        preds = torch.sigmoid(model(xadv_all)) > 0.5
        robust = float((preds.float() == yt).float().mean().item())
    return robust


def pearson(a, b):
    return float(np.corrcoef(a, b)[0, 1])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=DEFAULT_DATA)
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--device", default="cpu")
    args = ap.parse_args()

    set_seed(SEED)
    if args.device == "cpu":
        torch.set_num_threads(os.cpu_count() or 1)
        torch.set_default_device("cpu")

    X, y, feat_cols = load_data(args.data)
    assert X.shape[0] == 11430 and len(feat_cols) == 63, "unexpected data shape"
    i_tr, i_va, i_te = default_split(X, y)

    lo, hi, span = fit_minmax(X[i_tr])
    Xm = apply_minmax(X, lo, hi, span)
    Xtr, ytr = Xm[i_tr], y[i_tr]
    Xte, yte = Xm[i_te], y[i_te]

    print(f"train/val/test = {len(i_tr)}/{len(i_va)}/{len(i_te)}  "
          f"(pos rate total = {y.mean():.4f}) | n_feat = {len(feat_cols)}")

    t0 = time.time()
    per_model = {}
    for name in MODELS:
        print(f"--- {name} ---", flush=True)
        m_std = train_model(build_model(name, len(feat_cols)), Xtr, ytr, at=False)
        c_s = accuracy(m_std, Xte, yte)
        r_s = pgd_robust_accuracy(m_std, Xte, yte)
        m_at = train_model(build_model(name, len(feat_cols)), Xtr, ytr, at=True)
        c_a = accuracy(m_at, Xte, yte)
        r_a = pgd_robust_accuracy(m_at, Xte, yte)
        per_model[name] = {
            "std": {"clean_acc": c_s, "robust_acc": r_s},
            "at": {"clean_acc": c_a, "robust_acc": r_a},
        }
        print(f"  std clean={c_s*100:.4f}% robust={r_s*100:.4f}% | "
              f"at clean={c_a*100:.4f}% robust={r_a*100:.4f}% | "
              f"elapsed {time.time()-t0:.1f}s", flush=True)

    std_clean = [per_model[k]["std"]["clean_acc"] for k in per_model]
    std_rob = [per_model[k]["std"]["robust_acc"] for k in per_model]
    at_clean = [per_model[k]["at"]["clean_acc"] for k in per_model]
    at_rob = [per_model[k]["at"]["robust_acc"] for k in per_model]

    def spread(v):
        return max(v) - min(v)

    robust_imp = float(np.mean(at_rob) - np.mean(std_rob))
    clean_chg = float(np.mean(at_clean) - np.mean(std_clean))

    # C1 verdict: clean spread <= 5pp AND robust spread >= 15pp
    c1 = "supported" if (spread(std_clean) * 100 <= 5.0 and spread(std_rob) * 100 >= 15.0) else "not_supported"
    # C2 verdict: mean robust improvement >= 20pp AND mean clean drop <= 5pp
    c2 = "supported" if (robust_imp * 100 >= 20.0 and -clean_chg * 100 <= 5.0) else "not_supported"

    metrics = {
        "n_total": int(len(y)),
        "n_train": int(len(i_tr)),
        "n_val": int(len(i_va)),
        "n_test": int(len(i_te)),
        "n_features": int(len(feat_cols)),
        "pos_rate": float(y.mean()),
        "protocol": {
            "scaler": "minmax_to_01_train_fitted",
            "optimizer": "adam_lr1e-3_wd1e-4",
            "batch": int(BATCH), "epochs": int(EPOCHS),
            "at": {"type": "fgsm_at", "eps": AT_EPS, "alpha": AT_ALPHA, "steps": int(AT_STEPS)},
            "attack": {"type": "pgd_l2", "eps": EVAL_EPS, "alpha": PGD_ALPHA, "steps": int(PGD_STEPS)},
        },
        "per_model": {
            k: {
                "std": {"clean_acc": per_model[k]["std"]["clean_acc"],
                        "robust_acc": per_model[k]["std"]["robust_acc"]},
                "at": {"clean_acc": per_model[k]["at"]["clean_acc"],
                       "robust_acc": per_model[k]["at"]["robust_acc"]},
            }
            for k in per_model
        },
        "std": {
            "clean_range": [round(min(std_clean) * 100, 4), round(max(std_clean) * 100, 4)],
            "robust_range": [round(min(std_rob) * 100, 4), round(max(std_rob) * 100, 4)],
            "clean_mean": float(np.mean(std_clean) * 100),
            "robust_mean": float(np.mean(std_rob) * 100),
            "clean_spread": spread(std_clean) * 100,
            "robust_spread": spread(std_rob) * 100,
            "pearson_id_robust": pearson(std_clean, std_rob),
        },
        "at": {
            "clean_range": [round(min(at_clean) * 100, 4), round(max(at_clean) * 100, 4)],
            "robust_range": [round(min(at_rob) * 100, 4), round(max(at_rob) * 100, 4)],
            "clean_mean": float(np.mean(at_clean) * 100),
            "robust_mean": float(np.mean(at_rob) * 100),
            "clean_spread": spread(at_clean) * 100,
            "robust_spread": spread(at_rob) * 100,
            "pearson_id_robust": pearson(at_clean, at_rob),
            "robust_improvement_mean_pp": robust_imp * 100,
            "clean_change_mean_pp": clean_chg * 100,
        },
        "conclusion": {
            "C1": c1,
            "C2": c2,
            "note": ("C1/C2 both measured on our trained models (4 MLPs). "
                     "'supported' = pattern holds; see report for numbers."),
        },
    }

    os.makedirs(args.out, exist_ok=True)
    ev_rows = []
    for k in per_model:
        ev_rows.append({"model": k, "training": "standard",
                        "clean_acc": per_model[k]["std"]["clean_acc"],
                        "robust_acc": per_model[k]["std"]["robust_acc"]})
        ev_rows.append({"model": k, "training": "adversarial",
                        "clean_acc": per_model[k]["at"]["clean_acc"],
                        "robust_acc": per_model[k]["at"]["robust_acc"]})
    ev = pd.DataFrame(ev_rows)[["model", "training", "clean_acc", "robust_acc"]]
    ev.to_csv(os.path.join(args.out, "evidence_table.csv"), index=False)

    with open(os.path.join(args.out, "metrics.json"), "w") as f:
        json.dump(metrics, f, indent=2)

    print("\n=== SUMMARY ===")
    print(json.dumps(metrics, indent=2, default=float))
    print(f"\n>>> C1 spell: clean spread={spread(std_clean)*100:.2f}pp (<={5}) | "
          f"robust spread={spread(std_rob)*100:.2f}pp (>={15})  -> {c1}")
    print(f">>> C2 spell: robust improv={robust_imp*100:.2f}pp (>={20}) | "
          f"clean change={clean_chg*100:.2f}pp (>={-5}) -> {c2}")


if __name__ == "__main__":
    main()