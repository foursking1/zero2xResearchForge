"""Final experiment runner: Case 3 5-fold CV, augmentation ablation,
ensembling, and 2theta coarsening.

Usage:
  python3 run_final.py [--aug/--noaug] [--model mlp|mlp_big|cnn] [--seeds 3]
                       [--coarse {None,2,3,4,8}] [--tag NAME] [--device cpu|cuda]
"""
import argparse
import json
import os
import time

import numpy as np
import torch
import torch.nn as nn
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import f1_score, confusion_matrix

import config
from data_loader import load_data
from augmentation import make_augmented

torch.set_num_threads(max(1, min(20, os.cpu_count())))


# ---------------------------------------------------------------- models ----
def build_model(name, n_in=1499):
    n_out = config.NUM_CLASSES
    n_in = int(n_in)
    if name == "mlp":
        return nn.Sequential(
            nn.Linear(n_in, 512), nn.ReLU(), nn.Dropout(0.4),
            nn.Linear(512, 256), nn.ReLU(), nn.Dropout(0.4),
            nn.Linear(256, n_out))
    if name == "mlp_big":
        return nn.Sequential(
            nn.Linear(n_in, 1024), nn.ReLU(), nn.Dropout(0.4),
            nn.Linear(1024, 512), nn.ReLU(), nn.Dropout(0.4),
            nn.Linear(512, 256), nn.ReLU(), nn.Dropout(0.4),
            nn.Linear(256, n_out))
    if name == "cnn_pool":
        filters = 64
        conv = nn.Sequential(
            nn.Conv1d(1, filters, 8, 2, padding=4), nn.BatchNorm1d(filters),
            nn.ReLU(),
            nn.Conv1d(filters, filters, 5, 2, padding=2), nn.BatchNorm1d(filters),
            nn.ReLU(),
            nn.Conv1d(filters, filters, 3, 2, padding=1), nn.BatchNorm1d(filters),
            nn.ReLU(),
            nn.AdaptiveAvgPool1d(1), nn.Flatten())
        model = nn.Sequential(
            nn.Sequential(conv), nn.Sequential(
                nn.Linear(filters, 128), nn.ReLU(), nn.Dropout(0.3),
                nn.Linear(128, n_out)))
        return model
    raise ValueError(name)


class _ModelWrap(nn.Module):
    """Decorator: CNN models take (B, L); MLP take (B, L)."""
    def __init__(self, core, is_cnn):
        super().__init__()
        self.core = core
        self.is_cnn = is_cnn

    def forward(self, x, training=None):
        if self.is_cnn:
            x = x.unsqueeze(1)
        return self.core(x)


# ------------------------------------------------------------ training ------
def train_one(Xtr, ytr, Xval, yval, Xte, yte, model_name, epochs, device,
              seed):
    n_in = Xtr.shape[1]
    model = _ModelWrap(build_model(model_name, n_in=n_in),
                       model_name.startswith("cnn"))
    model.to(device)
    torch.manual_seed(seed)
    opt = torch.optim.Adam(model.parameters(), lr=config.LR, weight_decay=1e-4)
    n = len(Xtr)
    Xt = torch.from_numpy(Xtr.astype(np.float32)).to(device)
    yt = torch.from_numpy(ytr.astype(np.int64)).to(device)
    Xv = torch.from_numpy(Xval.astype(np.float32)).to(device)
    Xte_t = torch.from_numpy(Xte.astype(np.float32)).to(device)
    best, best_state, bad = 0.0, None, 0
    for epoch in range(epochs):
        model.train()
        perm = torch.randperm(n)
        for i in range(0, n, config.BATCH_SIZE):
            idx = perm[i:i + config.BATCH_SIZE]
            xb, yb = Xt[idx], yt[idx]
            opt.zero_grad()
            lo = nn.functional.cross_entropy(model(xb), yb)
            lo.backward()
            opt.step()
        model.eval()
        with torch.no_grad():
            vp = model(Xv).argmax(1)
        vacc = float((vp == torch.from_numpy(yval.astype(np.int64)).to(device))
                     .float().mean())
        if vacc > best:
            best, bad = vacc, 0
            best_state = {k: v.detach().cpu().clone()
                          for k, v in model.state_dict().items()}
        else:
            bad += 1
            if bad >= 25:
                break
    model.load_state_dict(best_state)
    model.eval()
    with torch.no_grad():
        logits = model(Xte_t)
    return logits.cpu().numpy()


def preds_from_logits(logits_ens):
    return np.argmax(np.mean(logits_ens, axis=0), axis=1)


# ------------------------------------------------------------ main cv -------
def cross_validate(X_exp, y_exp, X_sim, y_sim, tw, use_aug, model_name,
                   n_seeds, device, verbose=True, n_unlabeled_sim=False):
    skf = StratifiedKFold(5, shuffle=True, random_state=config.CV_SEED)
    folds_rec, all_pred, all_true = [], [], []
    all_logits = []
    for fold, (tr_idx, te_idx) in enumerate(skf.split(X_exp, y_exp)):
        val_idx = tr_idx[::7][:max(1, len(tr_idx) // 6)]
        tr_idx = np.setdiff1d(tr_idx, val_idx, assume_unique=True)
        rng = np.random.default_rng(config.AUG_SEED + fold * 1000)
        parts = [X_sim, y_sim, X_exp[tr_idx], y_exp[tr_idx]]
        if use_aug:
            Xae, yae = make_augmented(X_exp[tr_idx], tw, config.AUG_N_EXP, rng)
            yae = y_exp[tr_idx][yae]
            Xas, yas = make_augmented(X_sim, tw, config.AUG_N_SIM, rng)
            yas = y_sim[yas]
            parts += [Xae, yae, Xas, yas]
        Xtr = np.concatenate(parts[0::2], 0).astype(np.float32)
        ytr = np.concatenate(parts[1::2], 0).astype(np.int64)
        Xval, yval = X_exp[val_idx], y_exp[val_idx]
        Xte, yte = X_exp[te_idx], y_exp[te_idx]

        if verbose:
            print(f"  fold {fold}: train {len(Xtr)} (exp {len(tr_idx)} "
                  f"sim {len(X_sim)} aug "
                  f"{config.AUG_N_EXP + config.AUG_N_SIM if use_aug else 0}), "
                  f"val {len(val_idx)}, test {len(te_idx)}", flush=True)
        logits_ens = []
        for s in range(n_seeds):
            L = train_one(Xtr, ytr, Xval, yval, Xte, yte, model_name,
                          config.EPOCHS_MAX, device, seed=config.SEED + s)
            logits_ens.append(L)
        logits_ens = np.stack(logits_ens)          # (seeds, n_test, 7)
        pred = preds_from_logits(logits_ens)
        acc = float((pred == yte).mean())
        f1mi = f1_score(yte, pred, average="micro")
        f1ma = f1_score(yte, pred, average="macro")
        cm = confusion_matrix(yte, pred, labels=np.arange(config.NUM_CLASSES))
        folds_rec.append(dict(fold=fold, accuracy=acc, f1_micro=f1mi,
                              f1_macro=f1ma, test_idx=te_idx.tolist(),
                              pred=pred.tolist(), true=yte.tolist()))
        all_pred += pred.tolist(); all_true += yte.tolist()
        all_logits.append(logits_ens)
        if verbose:
            print(f"    -> test acc {acc:.4f} f1_macro {f1ma:.4f}", flush=True)
    accs = np.array([f["accuracy"] for f in folds_rec])
    f1mi = np.array([f["f1_micro"] for f in folds_rec])
    f1ma = np.array([f["f1_macro"] for f in folds_rec])
    agg = dict(
        accuracy_mean=float(accs.mean()),
        accuracy_std=float(accs.std(ddof=1)),
        f1_micro_mean=float(f1mi.mean()),
        f1_micro_std=float(f1mi.std(ddof=1)),
        f1_macro_mean=float(f1ma.mean()),
        f1_macro_std=float(f1ma.std(ddof=1)),
        overall_accuracy=float(np.mean(np.array(all_true) == np.array(all_pred))),
        overall_cm=confusion_matrix(all_true, all_pred,
                                    labels=np.arange(config.NUM_CLASSES)),
        per_fold_acc=[f["accuracy"] for f in folds_rec],
    )
    return agg, folds_rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--aug", action="store_true")
    ap.add_argument("--noaug", dest="aug", action="store_false")
    ap.set_defaults(aug=True)
    ap.add_argument("--model", default="mlp")
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--coarse", default=None)
    ap.add_argument("--tag", default=None)
    ap.add_argument("--device", default="auto")
    args = ap.parse_args()
    if args.device == "auto":
        args.device = "cuda" if torch.cuda.is_available() else "cpu"

    d = load_data()
    Xe, ye, Xs, ys, tw = d["X_exp"], d["y_exp"], d["X_theo"], d["y_theo"], d["tw"]
    if args.coarse:
        f = int(args.coarse)
        from train_eval import coarsen
        Xe, tw = coarsen(Xe, f, tw)
        Xs, _ = coarsen(Xs, f)
    tag = args.tag or (f"{args.model}_{'aug' if args.aug else 'noaug'}"
                       + (f"_coarse{args.coarse}" if args.coarse else ""))
    t0 = time.time()
    agg, folds = cross_validate(Xe, ye, Xs, ys, tw, args.aug, args.model,
                                args.seeds, args.device)
    out = dict(tag=tag, model=args.model, use_aug=args.aug, n_seeds=args.seeds,
               coarse=args.coarse, agg=agg, folds=folds,
               runtime_s=time.time() - t0)
    agg_out = dict(agg, overall_cm=agg["overall_cm"].tolist())
    out["agg"] = agg_out
    with open(os.path.join(config.RESULTS_DIR, f"{tag}.json"), "w") as fp:
        json.dump(out, fp, indent=2, default=float)
    np.save(os.path.join(config.RESULTS_DIR, f"{tag}.npz"), out,
            allow_pickle=True)
    print(f"TAG {tag}: acc {agg['accuracy_mean']:.4f} +/- "
          f"{agg['accuracy_std']:.4f}  f1_macro {agg['f1_macro_mean']:.4f}  "
          f"[{','.join(f'{a:.3f}' for a in agg['per_fold_acc'])}] "
          f"({time.time()-t0:.0f}s)")
    print(json.dumps(out["agg"], indent=2, default=float))


if __name__ == "__main__":
    main()