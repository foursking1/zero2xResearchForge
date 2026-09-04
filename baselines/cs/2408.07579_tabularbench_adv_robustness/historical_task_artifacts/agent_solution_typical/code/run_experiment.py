"""TabularBench URL phishing-detection robustness experiment.

Reproduces the key claims of arXiv:2408.07579 (Table 3, URL use case):
  C1: under standard training, ID (clean test) accuracy is similar across deep
      architectures while robust accuracy under a constrained attack differs a lot.
  C2: adversarial training (FGSM-AT) substantially improves robust accuracy while
      keeping clean accuracy nearly unchanged.

Protocol (per task spec):
  - DefaultSplitter: train_test_split(stratify=y, random_state=42, test_size=0.2)
    applied twice -> train 7,315 / val 1,829 / test 2,286.
  - Preprocessing: per-feature min-max scaling fit on train only, clipped to [0,1].
  - Models: 4 MLPs (ReLU, single logit output).
  - Training: Adam (lr=1e-3, wd=1e-4), batch 256, 12 epochs, BCEWithLogits, seed 0.
  - Standard training and FGSM-AT (eps=0.1, L2-normalized step alpha=0.1).
  - Evaluation: clean accuracy + untargeted PGD-L2 (40 steps, eps=0.25, alpha=eps/4,
    project onto L2 ball around original, then clip to [0,1]).

Run:  python run_experiment.py   (from the repo root that contains data/url.csv)
"""

import json
import os

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.model_selection import train_test_split

# ----------------------------------------------------------------------------
# Fixed hyper-parameters
# ----------------------------------------------------------------------------
SEED = 0
EPOCHS = 12
BATCH = 256
LR = 1e-3
WEIGHT_DECAY = 1e-4

AT_EPS = 0.1        # FGSM-AT perturbation budget (L2)
AT_STEPS = 1
AT_ALPHA = 0.1      # L2 step size for AT

EVAL_EPS = 0.25     # PGD-L2 budget used for robustness evaluation
PGD_STEPS = 40
PGD_ALPHA = EVAL_EPS / 4.0

MODELS = ["mlp64", "mlp128_64", "mlp256_128_64", "mlp128_64_drop"]

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "url.csv")
OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "results")


def set_seed(seed):
    np.random.seed(seed)
    torch.manual_seed(seed)


# ----------------------------------------------------------------------------
# Data loading, DefaultSplitter split, and train-only min-max scaling
# ----------------------------------------------------------------------------
def load_and_split():
    df = pd.read_csv(DATA_PATH)
    feat_cols = [c for c in df.columns if c != "is_phishing"]
    y = df["is_phishing"].to_numpy()
    X = df[feat_cols].to_numpy(dtype=float)

    idx = np.arange(len(y))
    idx_train, idx_test = train_test_split(
        idx, random_state=42, shuffle=True, stratify=y[idx], test_size=0.2)
    idx_train, idx_val = train_test_split(
        idx_train, random_state=42, shuffle=True, stratify=y[idx_train], test_size=0.2)

    # Min-max scaler fit on the TRAIN split only (test never contributes).
    lo = X[idx_train].min(0)
    hi = X[idx_train].max(0)
    span = hi - lo
    span[span == 0] = 1.0
    Xm = np.clip((X - lo) / span, 0.0, 1.0)

    return {
        "X_train": Xm[idx_train], "y_train": y[idx_train],
        "X_val": Xm[idx_val], "y_val": y[idx_val],
        "X_test": Xm[idx_test], "y_test": y[idx_test],
        "n_train": len(idx_train), "n_val": len(idx_val), "n_test": len(idx_test),
        "n_feat": X.shape[1],
        "pos_rate": float(y.mean()),
    }


# ----------------------------------------------------------------------------
# Models: simple MLPs with ReLU hidden layers and a single logit output
# ----------------------------------------------------------------------------
class MLP(nn.Module):
    def __init__(self, input_dim, sizes, dropout=0.0):
        super().__init__()
        layers = []
        prev = input_dim
        for h in sizes:
            layers += [nn.Linear(prev, h), nn.ReLU()]
            if dropout > 0:
                layers.append(nn.Dropout(dropout))
            prev = h
        layers.append(nn.Linear(prev, 1))
        self.net = nn.Sequential(*layers)

    def forward(self, x):
        return self.net(x).squeeze(-1)


def make_model(name, input_dim):
    if name == "mlp64":
        return MLP(input_dim, [64])
    if name == "mlp128_64":
        return MLP(input_dim, [128, 64])
    if name == "mlp256_128_64":
        return MLP(input_dim, [256, 128, 64])
    if name == "mlp128_64_drop":
        return MLP(input_dim, [128, 64], dropout=0.3)
    raise ValueError(name)


# ----------------------------------------------------------------------------
# FGSM / PGD-L2 attack: L2-normalized gradient steps, projected back onto the
# L2 ball of radius `eps` around the clean sample, then clipped to [0,1].
# ----------------------------------------------------------------------------
def l2_attack(x, model, y, eps, steps, alpha, loss_fn):
    xadv = x.clone().detach()
    for _ in range(steps):
        xadv.requires_grad_(True)
        loss = loss_fn(model(xadv), y)
        grad = torch.autograd.grad(loss, xadv)[0]
        grad_norm = grad.norm(dim=1, keepdim=True).clamp_min(1e-12)
        xadv = (xadv + alpha * grad / grad_norm).detach()
        delta = xadv - x
        delta_norm = delta.norm(dim=1, keepdim=True).clamp_min(1e-12)
        xadv = x + delta * (torch.clamp(delta_norm, max=eps) / delta_norm)
        xadv = torch.clamp(xadv, 0.0, 1.0)
    return xadv


# ----------------------------------------------------------------------------
# Training (standard and FGSM-AT)
# ----------------------------------------------------------------------------
def train_model(model, Xtr, ytr, at=False):
    model.train()
    opt = torch.optim.Adam(model.parameters(), lr=LR, weight_decay=WEIGHT_DECAY)
    loss_fn = nn.BCEWithLogitsLoss()
    n = len(Xtr)
    for _ in range(EPOCHS):
        perm = torch.randperm(n)
        for b in range(0, n, BATCH):
            idx = perm[b:b + BATCH]
            xb, yb = Xtr[idx], ytr[idx]
            if at:
                xadv = l2_attack(xb, model, yb, eps=AT_EPS, steps=AT_STEPS,
                                 alpha=AT_ALPHA, loss_fn=loss_fn)
                opt.zero_grad()
                loss = loss_fn(model(xadv), yb)
            else:
                opt.zero_grad()
                loss = loss_fn(model(xb), yb)
            loss.backward()
            opt.step()
    return model


# ----------------------------------------------------------------------------
# Evaluation
# ----------------------------------------------------------------------------
@torch.no_grad()
def clean_accuracy(model, Xe, ye):
    model.eval()
    preds = (torch.sigmoid(model(Xe)) > 0.5).float()
    return (preds == ye).float().mean().item()


def robust_accuracy(model, Xe, ye, eps=EVAL_EPS, steps=PGD_STEPS):
    model.eval()
    loss_fn = nn.BCEWithLogitsLoss()
    xadv = l2_attack(Xe, model, ye, eps=eps, steps=steps,
                     alpha=eps / 4.0, loss_fn=loss_fn)
    model.eval()
    preds = (torch.sigmoid(model(xadv)) > 0.5).float()
    return (preds == ye).float().mean().item()


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------
def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    set_seed(SEED)

    data = load_and_split()
    X_train = torch.tensor(data["X_train"], dtype=torch.float32)
    y_train = torch.tensor(data["y_train"], dtype=torch.float32)
    X_test = torch.tensor(data["X_test"], dtype=torch.float32)
    y_test = torch.tensor(data["y_test"], dtype=torch.float32)

    print(f"n_train={data['n_train']} n_val={data['n_val']} "
          f"n_test={data['n_test']} n_feat={data['n_feat']} "
          f"pos_rate={data['pos_rate']:.4f}", flush=True)

    rows = []
    per_model = {}
    for name in MODELS:
        m_std = make_model(name, data["n_feat"])
        m_std = train_model(m_std, X_train, y_train, at=False)
        c_s = clean_accuracy(m_std, X_test, y_test)
        r_s = robust_accuracy(m_std, X_test, y_test)

        m_at = make_model(name, data["n_feat"])
        m_at = train_model(m_at, X_train, y_train, at=True)
        c_a = clean_accuracy(m_at, X_test, y_test)
        r_a = robust_accuracy(m_at, X_test, y_test)

        per_model[name] = {"std": {"clean": c_s, "robust": r_s},
                           "at": {"clean": c_a, "robust": r_a}}
        rows.append({"model": name, "training": "standard", "clean_acc": c_s, "robust_acc": r_s})
        rows.append({"model": name, "training": "adversarial", "clean_acc": c_a, "robust_acc": r_a})
        print(f"{name}: std clean={c_s:.4f} robust={r_s:.4f} | "
              f"AT clean={c_a:.4f} robust={r_a:.4f}", flush=True)

    # --- aggregate metrics -------------------------------------------------
    std_clean = [per_model[k]["std"]["clean"] for k in MODELS]
    std_rob = [per_model[k]["std"]["robust"] for k in MODELS]
    at_clean = [per_model[k]["at"]["clean"] for k in MODELS]
    at_rob = [per_model[k]["at"]["robust"] for k in MODELS]

    def spread(a):
        return float(max(a) - min(a))

    def mean(a):
        return float(np.mean(a))

    robust_gain_mean = mean(at_rob) - mean(std_rob)
    clean_delta_mean = mean(at_clean) - mean(std_clean)

    # claim verdicts (structural criteria, see task rubric)
    c1_ok = (spread(std_clean) * 100 <= 5.0) and (spread(std_rob) * 100 >= 15.0)
    c2_ok = (robust_gain_mean * 100 >= 20.0) and (-clean_delta_mean * 100 <= 5.0)

    metrics = {
        "n_train": data["n_train"],
        "n_val": data["n_val"],
        "n_test": data["n_test"],
        "n_feat": data["n_feat"],
        "pos_rate": data["pos_rate"],
        "attack": {"name": "PGD-L2", "eps": EVAL_EPS, "steps": PGD_STEPS,
                   "alpha": PGD_ALPHA},
        "at": {"name": "FGSM-AT", "eps": AT_EPS, "steps": AT_STEPS, "alpha": AT_ALPHA},
        "standard": {
            "clean_range": [min(std_clean), max(std_clean)],
            "robust_range": [min(std_rob), max(std_rob)],
            "clean_mean_pct": mean(std_clean) * 100,
            "robust_mean_pct": mean(std_rob) * 100,
            "clean_spread_pp": spread(std_clean) * 100,
            "robust_spread_pp": spread(std_rob) * 100,
        },
        "adversarial": {
            "clean_range": [min(at_clean), max(at_clean)],
            "robust_range": [min(at_rob), max(at_rob)],
            "clean_mean_pct": mean(at_clean) * 100,
            "robust_mean_pct": mean(at_rob) * 100,
            "clean_spread_pp": spread(at_clean) * 100,
            "robust_spread_pp": spread(at_rob) * 100,
        },
        "at_vs_std": {
            "robust_improvement_mean_pp": robust_gain_mean * 100,
            "clean_change_mean_pp": clean_delta_mean * 100,
        },
        "per_model": per_model,
        "verdicts": {
            "C1": "supported" if c1_ok else "partially_supported",
            "C2": "supported" if c2_ok else "partially_supported",
            "criteria": {
                "C1_clean_spread_pp": spread(std_clean) * 100,
                "C1_robust_spread_pp": spread(std_rob) * 100,
                "C2_robust_gain_pp": robust_gain_mean * 100,
                "C2_clean_change_pp": clean_delta_mean * 100,
            },
        },
    }

    pd.DataFrame(rows).to_csv(os.path.join(OUT_DIR, "evidence_table.csv"), index=False)
    with open(os.path.join(OUT_DIR, "metrics.json"), "w") as f:
        json.dump(metrics, f, indent=2)

    print(json.dumps(metrics, indent=2), flush=True)


if __name__ == "__main__":
    main()
