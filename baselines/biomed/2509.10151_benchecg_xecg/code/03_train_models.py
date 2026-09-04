#!/usr/bin/env python3
"""Step 3 - train two supervised models on the ONLY targets present in the
frozen PTB-XL package (sex, age>=65) and evaluate on the frozen validation split.

Models
  1. "cnn_multitask"        - lightweight 1-D CNN, multi-label binary heads
     (demonstrates the paper's macro-AUROC / macro-F1 multi-label machinery).
  2. "logreg_manual_feats"  - logistic regression on hand-crafted per-lead
     summary features (weak shallow baseline).

The comparison mirrors the *structure* of the xECG-vs-ST-MEM (deep vs shallow)
gap but is, by construction, NOT the diagnostic superclass task - the frozen
data contains no diagnostic labels. See claim.md/report.md for the reasoning.

All normalisation statistics were fitted on the train split only (step 2).
Seeds are fixed. Runs on CPU.
"""
import os
import sys

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
from sklearn.linear_model import LogisticRegression

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common import (
    SEED,
    Simple1DCNN,
    f1_optimized_threshold,
    macro_auroc,
    macro_f1,
    manual_features,
    save_json,
    set_seed,
)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "results")
os.makedirs(CACHE, exist_ok=True)

SEEDS = [42, 2024, 7]
EPOCHS = 30
BATCH = 32
LR = 1e-3
DECAY = 1e-4
TARGET_NAMES = ["sex", "age_ge65"]
DEVICE = "cpu"


def load_cache():
    d = np.load(os.path.join(CACHE, "preprocessed.npz"), allow_pickle=False)
    # signals are stored as (n, T=1000, ch=12); CNN expects (n, ch, T)
    Xtr = np.transpose(d["Xtrain"], (0, 2, 1)).astype(np.float32)
    Xva = np.transpose(d["Xval"], (0, 2, 1)).astype(np.float32)
    return Xtr, d["ttrain"].astype(np.float32), Xva, d["tval"].astype(np.float32)


def train_cnn_seed(Xtr, ttr, Xva, tva, seed):
    set_seed(seed)
    n_out = ttr.shape[1]
    model = Simple1DCNN(in_channels=12, hidden=64, n_out=n_out).to(DEVICE)
    ds = TensorDataset(torch.from_numpy(Xtr), torch.from_numpy(ttr))
    dl = DataLoader(ds, batch_size=BATCH, shuffle=True, drop_last=False, num_workers=0)
    opt = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=DECAY)
    lossf = nn.BCEWithLogitsLoss()
    model.train()
    for ep in range(EPOCHS):
        tot = 0.0
        for xb, yb in dl:
            opt.zero_grad()
            loss = lossf(model(xb), yb)
            loss.backward()
            opt.step()
            tot += loss.item() * len(xb)
        if (ep + 1) % 10 == 0:
            print(f"    seed={seed} epoch={ep+1}/{EPOCHS} loss={tot/len(ds):.4f}")
    model.eval()
    with torch.no_grad():
        pval = torch.sigmoid(model(torch.from_numpy(Xva))).numpy()
    return model, pval


def evaluate_block(y_true, y_score, target_names):
    out = {}
    auroc = macro_auroc(y_true, y_score)
    f1_thr05 = macro_f1(y_true, y_score)
    f1opt, thr = f1_optimized_threshold(y_true, y_score)
    for j, c in enumerate(target_names):
        out[f"{c}:auroc"] = round(macro_auroc(y_true[:, j], y_score[:, j]), 4)
        out[f"{c}:f1@0.5"] = round(macro_f1(y_true[:, j], y_score[:, j]), 4)
        out[f"{c}:f1_best_thr"] = round(
            f1_optimized_threshold(y_true[:, j], y_score[:, j])[0], 4
        )
    out["macro_auroc"] = round(auroc, 4)
    out["macro_f1@0.5"] = round(f1_thr05, 4)
    out["macro_f1_best_thr"] = round(f1opt, 4)
    out["selected_thresholds"] = [round(float(t), 4) for t in thr]
    return out


def main() -> None:
    Xtr, ttr, Xva, tva = load_cache()
    print("shapes: train", Xtr.shape, ttr.shape, "| val", Xva.shape, tva.shape)

    # ---- CNN, repeated over seeds
    cnn_rows, cnn_preds = [], {}
    for seed in SEEDS:
        print(f"[CNN] training seed {seed}")
        _, pval = train_cnn_seed(Xtr, ttr, Xva, tva, seed)
        row = {"seed": seed, "model": "cnn_multitask"}
        row.update(evaluate_block(tva, pval, TARGET_NAMES))
        cnn_rows.append(row)
        cnn_preds[seed] = pval.tolist()

    # ---- shallow baseline (deterministic given features)
    Ftr = manual_features(Xtr.transpose(0, 2, 1)).astype(np.float64)
    Fva = manual_features(Xva.transpose(0, 2, 1)).astype(np.float64)
    lr_rows = []
    for j, c in enumerate(TARGET_NAMES):
        clf = LogisticRegression(C=1.0, max_iter=2000, random_state=SEED)
        clf.fit(Ftr, ttr[:, j])
        p = clf.predict_proba(Fva)[:, 1]
        # re-fold into a single (n,2) score matrix per seed for uniformity
        if j == 0:
            pva = np.zeros((len(Fva), len(TARGET_NAMES)), dtype=np.float64)
        pva[:, j] = p
    row = {"seed": "n/a", "model": "logreg_manual_feats"}
    row.update(evaluate_block(tva, pva, TARGET_NAMES))
    lr_rows.append(row)

    # ---- aggregate (mean +/- std over seeds) for CNN
    agg = {}
    for key in cnn_rows[0]:
        if key in ("seed", "model"):
            continue
        vals = np.array([r[key] for r in cnn_rows])
        agg[key] = {
            "mean": round(float(vals.mean()), 4),
            "std": round(float(vals.std(ddof=0)), 4),
        }
    cnn_agg = {"model": "cnn_multitask", "seeds": [f"{s}" for s in SEEDS], **agg}

    all_rows = [*cnn_rows, *lr_rows]
    out = {
        "task_note": (
            "Auxiliary targets only - frozen parquet has no diagnostic label "
            "column; these numbers are a valid end-to-end run of the exact "
            "multi-label macro-AUROC/macro-F1 pipeline on real frozen signals, "
            "and are NOT comparable to the paper's diagnostic anchors."
        ),
        "cnn_seed_summary": cnn_agg,
        "results": {r["model"]: {k: v for k, v in r.items() if k != "model"} for r in all_rows},
        "device": DEVICE,
        "epochs": EPOCHS,
    }
    save_json(out, os.path.join(CACHE, "model_metrics.json"))

    # persisted predictions for the judge / figure step
    save_json(
        {"tva": tva.tolist(), "cnn_preds_seed42": cnn_preds[SEEDS[0]], "lr_preds": pva.tolist()},
        os.path.join(CACHE, "predictions_for_figs.json"),
    )
    print("\n===== aggregate (CNN, seeds=%s) =====" % SEEDS)
    for k, v in cnn_agg.items():
        if isinstance(v, dict) and "mean" in v:
            print(f"  {k}: {v['mean']} ± {v['std']}")
    print("===== logistic regression baseline =====")
    for k, v in lr_rows[0].items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()