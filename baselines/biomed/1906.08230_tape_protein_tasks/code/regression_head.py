"""Train regression heads on fixed representations, evaluate Spearman rho on test.

Represents handled here (all share the same frozen train/valid/test split and the
same evaluation protocol -- Spearman rank correlation + RMSE on the test split):

  * onehot-linear      : one-hot (20-dim per residue, mean-pooled) + ridge regression
  * onehot-mlp         : one-hot flattened + 2-layer MLP trained from scratch
                         (a "learnable, no-pretraining" baseline, cf. TAPE "No Pretrain")
  * aa-compound-gbdt   : amino-acid composition (20 + 400 dipeptide counts) + HistGradientBoosting
  * esm2_t6_8M-emd     : frozen ESM-2 t6(8M) mean-pooled embeddings + ridge / MLP head
  * esm2_t33_650M-emd  : frozen ESM-2 t33(650M) mean-pooled embeddings + ridge / MLP head
  * esm2_*_mlp         : same embeddings, 2-layer MLP regression head (early-stopped on valid)

Anti-leakage: only train labels are used to fit heads; valid split used for early
stopping / ridge-alpha selection; test used solely for the final metric.

Outputs:
  results/evidence_table.csv   (task, representation, model, spearman_rho, rmse)
  results/metrics.json         (full summary incl. deltas vs one-hot and paper anchors)
"""
import json
import os
import sys
import time

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from scipy.stats import spearmanr
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_squared_error
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import CSV_FILES, EMBED_DIR, EVIDENCE_DIR, MODEL_SHORT, RESULTS_DIR, SEED, find_data_dir  # noqa: E402

torch.manual_seed(SEED)
np.random.seed(SEED)

AA = "ACDEFGHIKLMNPQRSTVWY"
AA2IDX = {a: i for i, a in enumerate(AA)}
N_AA = len(AA)


def encode_onehot(seqs, L=None):
    if L is None:
        L = max(len(s) for s in seqs)
    X = np.zeros((len(seqs), L, N_AA), dtype=np.float32)
    for i, s in enumerate(seqs):
        for j, aa in enumerate(s):
            if aa in AA2IDX:
                X[i, j, AA2IDX[aa]] = 1.0
    return X


def encode_composition(seqs):
    X = np.zeros((len(seqs), N_AA + N_AA * N_AA), dtype=np.float32)
    for i, s in enumerate(seqs):
        cnt = np.zeros(N_AA)
        for aa in s:
            if aa in AA2IDX:
                cnt[AA2IDX[aa]] += 1
        X[i, :N_AA] = cnt / max(len(s), 1)
        for j in range(len(s) - 1):
            a, b = AA2IDX.get(s[j], -1), AA2IDX.get(s[j + 1], -1)
            if a >= 0 and b >= 0:
                X[i, N_AA + a * N_AA + b] += 1
    return X


class MLP(nn.Module):
    def __init__(self, d_in, hidden=256, d_out=1, dropout=0.1):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(d_in, hidden), nn.ReLU(), nn.Dropout(dropout),
            nn.Linear(hidden, hidden), nn.ReLU(), nn.Dropout(dropout),
            nn.Linear(hidden, d_out),
        )

    def forward(self, x):
        return self.net(x).squeeze(-1)


def train_mlp(Xtr, ytr, Xva, yva, d_in, hidden=256, epochs=60, lr=1e-3, bs=512,
              patience=12, device="cpu"):
    ytr = np.asarray(ytr, dtype=np.float32)
    yva = np.asarray(yva, dtype=np.float32)
    scaler = StandardScaler().fit(Xtr)
    Xtr_s = scaler.transform(Xtr).astype(np.float32)
    Xva_s = scaler.transform(Xva).astype(np.float32)
    model = MLP(d_in, hidden=hidden).to(device)
    opt = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-4)
    mse = nn.MSELoss()
    n = len(Xtr_s)
    best = {"loss": float("inf"), "state": None}
    bad = 0
    for ep in range(epochs):
        model.train()
        idx = torch.randperm(n)
        for i in range(0, n, bs):
            b = idx[i:i + bs].numpy()
            xb = torch.from_numpy(Xtr_s[b]).to(device)
            yb = torch.from_numpy(ytr[b]).float().to(device)
            opt.zero_grad()
            loss = mse(model(xb), yb)
            loss.backward()
            opt.step()
        model.eval()
        with torch.no_grad():
            xv = torch.from_numpy(Xva_s).to(device)
            pv = model(xv).cpu().numpy()
        lv = np.asarray(yva)
        rv = spearmanr(pv, lv).correlation
        loss_v = ((pv - lv) ** 2).mean()
        if loss_v < best["loss"] - 1e-5:
            best["loss"] = loss_v
            best["state"] = {k: v.clone() for k, v in model.state_dict().items()}
            best["valid_spearman"] = float(rv)
            bad = 0
        else:
            bad += 1
            if bad >= patience:
                break
    model.load_state_dict(best["state"])
    model.eval()
    with torch.no_grad():
        xt = torch.from_numpy(scaler.transform(Xva).astype(np.float32)).to(device)
        pva = model(xt).cpu().numpy()
    return model, scaler, best, float(spearmanr(pva, np.asarray(yva)).correlation)


def predict_mlp(model, scaler, X, device="cpu"):
    model.eval()
    with torch.no_grad():
        x = torch.from_numpy(scaler.transform(X).astype(np.float32)).to(device)
        return model(x).cpu().numpy()


def eval_pred(task, model_key, ytest, pred):
    rho = float(spearmanr(ytest, pred).correlation)
    rmse = float(np.sqrt(mean_squared_error(ytest, pred)))
    return {
        "task": task,
        "representation": model_key.split("|")[0],
        "model": model_key.split("|")[1],
        "spearman_rho": round(rho, 6),
        "rmse": round(rmse, 6),
        "n_test": int(len(ytest)),
    }


def fit_ridge_select_alpha(Xtr, ytr, Xva, yva):
    """Ridge with alpha chosen on the validation split (early-stopping-style model selection)."""
    sc = StandardScaler().fit(Xtr)
    Xtr_s, Xva_s = sc.transform(Xtr), sc.transform(Xva)
    ytr_v = ytr.values if hasattr(ytr, "values") else np.asarray(ytr)
    yva_v = yva.values if hasattr(yva, "values") else np.asarray(yva)
    best = {"alpha": None, "rho": -1, "model": None, "rmse": None}
    for alpha in [1e3, 3e2, 1e2, 3e1, 1e1, 3e0, 1e0, 1e-1]:
        r = Ridge(alpha=alpha)
        r.fit(Xtr_s, ytr_v)
        p = r.predict(Xva_s)
        rho = float(spearmanr(p, yva_v).correlation)
        if rho > best["rho"]:
            best = {"alpha": alpha, "rho": rho, "model": r, "rmse": float(
                np.sqrt(mean_squared_error(yva_v, p)))}
    return best["model"], sc, best["alpha"]


def load_esm(task, short):
    order = json.load(open(os.path.join(EMBED_DIR, f"{task}_{short}_order.json")))
    arr = np.load(os.path.join(EMBED_DIR, f"{task}_{short}_embeddings.npy"))
    return order["order"], arr


def main():
    data_dir = find_data_dir()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print("device:", device, flush=True)
    rows = []
    meta = {"seed": SEED, "device": device, "evaluated_at": time.strftime("%Y-%m-%d %H:%M:%S")}
    pred_store = {}  # task -> DataFrame with columns seq,label,pred_<method>

    for task, fname in CSV_FILES.items():
        df = pd.read_csv(os.path.join(data_dir, fname))
        dftr = df[df.stage == "train"].reset_index(drop=True)
        dfva = df[df.stage == "valid"].reset_index(drop=True)
        dfte = df[df.stage == "test"].reset_index(drop=True)
        ytr, yva, yte = dftr.label, dfva.label, dfte.label.values
        t0 = time.time()
        pred_store[task] = pd.DataFrame({"seq": dfte.protein.values, "label": yte})
        pmethods = []

        print(f"\n=== {task} === n_train={len(dftr)} n_valid={len(dfva)} n_test={len(dfte)}", flush=True)

        # ---- one-hot + ridge (hand-crafted representation, shallow head) ----
        L_max = int(df["protein"].str.len().max())
        Xtr = encode_onehot(dftr.protein, L_max).reshape(len(dftr), -1)
        Xva = encode_onehot(dfva.protein, L_max).reshape(len(dfva), -1)
        Xte = encode_onehot(dfte.protein, L_max).reshape(len(dfte), -1)
        ridge, sc, alpha = fit_ridge_select_alpha(Xtr, ytr, Xva, yva)
        pred = ridge.predict(sc.transform(Xte))
        rows.append(eval_pred(task, "one-hot|ridge-linear", yte, pred))
        rows[-1]["selected_alpha"] = alpha
        pmethods.append(("onehot_ridge", pred))
        print("  onehot-ridge rho=%.4f rmse=%.4f alpha=%g (%.0fs)" % (
            rows[-1]["spearman_rho"], rows[-1]["rmse"], alpha, time.time()-t0), flush=True)

        # ---- one-hot + MLP (learnable, no pretraining) ----
        mlp, scaler, best, _ = train_mlp(Xtr, ytr, Xva, yva, Xtr.shape[1], device=device, epochs=50)
        pred = predict_mlp(mlp, scaler, Xte, device)
        rows.append(eval_pred(task, "one-hot|mlp-from-scratch", yte, pred))
        pmethods.append(("onehot_mlp", pred))
        print("  onehot-mlp rho=%.4f rmse=%.4f (%.0fs)" % (rows[-1]["spearman_rho"], rows[-1]["rmse"], time.time()-t0), flush=True)
        del mlp, Xtr, Xva, Xte, sc, ridge

        # ---- amino-acid composition + GBDT (hand-crafted, non-linear) ----
        Ztr = encode_composition(dftr.protein)
        Zva = encode_composition(dfva.protein)
        Zte = encode_composition(dfte.protein)
        # trained on train+valid, internal validation derived only from those (no test seen)
        gb = HistGradientBoostingRegressor(max_iter=400, learning_rate=0.05,
                                           max_depth=5, min_samples_leaf=20,
                                           random_state=SEED,
                                           validation_fraction=0.125,
                                           early_stopping=True)
        Ztr_big = np.vstack([Ztr, Zva])
        ytr_big = np.concatenate([ytr, yva])
        gb.fit(Ztr_big, ytr_big)
        pred = gb.predict(Zte)
        rows.append(eval_pred(task, "aa-composition|gradient-boosted-trees", yte, pred))
        pmethods.append(("aa_composition_gbdt", pred))
        print("  aa-gbdt rho=%.4f rmse=%.4f (%.0fs)" % (rows[-1]["spearman_rho"], rows[-1]["rmse"], time.time()-t0), flush=True)
        del gb, Ztr, Zva, Zte

        # ---- pretrained ESM-2 embeddings (frozen) + ridge & + MLP head ----
        for mfull in MODEL_SHORT:
            short = MODEL_SHORT[mfull]
            esm_seqs, arr = load_esm(task, short)
            if esm_seqs != df["protein"].tolist():
                # match by position in CSV order (order.json stores the same CSV order)
                arr = arr[np.array([esm_seqs.index(p) for p in df["protein"].tolist()])]
            etr = arr[np.array(df.stage.values == "train")]
            eva = arr[np.array(df.stage.values == "valid")]
            ete = arr[np.array(df.stage.values == "test")]
            sc = StandardScaler().fit(etr)
            ridge, sc, alpha = fit_ridge_select_alpha(etr, ytr, eva, yva)
            pred = ridge.predict(sc.transform(ete))
            rows.append(eval_pred(task, f"esm2-{short}|ridge-linear", yte, pred))
            rows[-1]["selected_alpha"] = alpha
            pmethods.append((f"esm2_{short}_ridge", pred))
            print(f"  {short}-ridge rho=%.4f rmse=%.4f alpha=%g (%.0fs)" % (
                rows[-1]["spearman_rho"], rows[-1]["rmse"], alpha, time.time()-t0), flush=True)

            mlp, scaler, best, _ = train_mlp(etr, ytr, eva, yva, etr.shape[1], device=device, epochs=80)
            pred = predict_mlp(mlp, scaler, ete, device)
            rows.append(eval_pred(task, f"esm2-{short}|mlp-head", yte, pred))
            pmethods.append((f"esm2_{short}_mlp", pred))
            print(f"  {short}-mlp rho=%.4f rmse=%.4f (%.0fs)" % (rows[-1]["spearman_rho"], rows[-1]["rmse"], time.time()-t0), flush=True)
            del mlp, ridge, sc

        for method, pred in pmethods:
            pred_store[task][method] = pred
        pred_store[task].to_csv(os.path.join(RESULTS_DIR, f"test_predictions_{task}.csv"), index=False)

        meta[task] = {"n_train": int(len(dftr)), "n_valid": int(len(dfva)),
                      "n_test": int(len(dfte)),
                      "train_time_s": round(time.time() - t0, 1)}

    table = pd.DataFrame(rows)
    os.makedirs(RESULTS_DIR, exist_ok=True)
    table.to_csv(os.path.join(RESULTS_DIR, "evidence_table.csv"), index=False)
    print("\nSummary table:\n", table.to_string(index=False), flush=True)

    import make_metrics
    make_metrics.main()
    print("metrics.json written.", flush=True)


if __name__ == "__main__":
    main()