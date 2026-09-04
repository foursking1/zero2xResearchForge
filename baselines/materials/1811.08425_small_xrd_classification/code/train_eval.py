"""Training and evaluation: 5-fold CV, augmentation ablation, coarsening.

Protocol (paper "Case 3"):
  - 5-fold CV over the 88 experimental spectra (shuffle + fixed seed).
  - Training set per fold = ALL 164 simulated spectra + 80% of experimental
    spectra; test set = the held-out 20% of experimental spectra.
  - Physics-informed augmentation (Eqs. 1-3) generates 2000 spectra from the
    simulated training set and 2000 from the experimental training set
    (**training fold only**, no leakage).
  - a-CNN trained with Adam (lr 1e-3), batch 128, BCE loss, early stopping.
  - Metrics: subset accuracy, F1 micro, F1 macro, confusion matrix.
"""

import time

import numpy as np
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import f1_score, confusion_matrix
import torch

import config
from data_loader import load_data
from augmentation import make_augmented
from model import build_model

torch.set_num_threads(min(20, __import__("os").cpu_count()))


def _to_torch(X, y, device="cpu"):
    return (torch.from_numpy(X.astype(np.float32)).to(device),
            torch.from_numpy(y.astype(np.int64)).to(device))


def _prepare_train_set(X_sim, y_sim, X_exp, y_exp, tw, use_aug, rng):
    """Build the per-fold training set (sim + exp [+ augmented])."""
    Xs, ys = [X_sim], [y_sim]
    if use_aug:
        X_aug_sim, y_aug_sim = make_augmented(X_sim, tw, config.AUG_N_SIM, rng,
                                              label=None)
        # label for augmented sim = the source sim spectrum's class
        y_aug_sim = y_sim[y_aug_sim]
        Xs.append(X_aug_sim); ys.append(y_aug_sim)
    Xs.append(X_exp); ys.append(y_exp)
    if use_aug:
        X_aug_exp, y_aug_exp = make_augmented(X_exp, tw, config.AUG_N_EXP, rng,
                                              label=None)
        y_aug_exp = y_exp[y_aug_exp]
        Xs.append(X_aug_exp); ys.append(y_aug_exp)
    X = np.concatenate(Xs, axis=0).astype(np.float32)
    y = np.concatenate(ys, axis=0).astype(np.int64)
    return X, y


def train_model(Xtr, ytr, Xval, yval, seed, verbose=False, device="cpu"):
    torch.manual_seed(seed)
    model = build_model().to(device)
    opt = torch.optim.Adam(model.parameters(), lr=config.LR)
    Xtr_t, ytr_t = _to_torch(Xtr, ytr, device)
    Xval_t, yval_t = _to_torch(Xval, yval, device)
    n = len(Xtr_t)
    best_acc, best_state, best_epoch, bad = -1, None, 0, 0
    t0 = time.time()
    for epoch in range(config.EPOCHS_MAX):
        model.train()
        perm = torch.randperm(n)
        for i in range(0, n, config.BATCH_SIZE):
            idx = perm[i:i + config.BATCH_SIZE]
            xb, yb = Xtr_t[idx], ytr_t[idx]
            opt.zero_grad()
            logits = model(xb)
            loss = model.loss(logits, yb)
            loss.backward()
            opt.step()
        # validation (on held-out experimental spectra only)
        model.eval()
        with torch.no_grad():
            logits = model(Xval_t)
            pred = logits.argmax(1).cpu().numpy()
        acc = float((pred == yval).mean())
        if acc > best_acc:
            best_acc, best_epoch, bad = acc, epoch, 0
            best_state = {k: v.detach().cpu().clone() for k, v in
                          model.state_dict().items()}
        else:
            bad += 1
            if bad >= config.EARLY_STOP_PATIENCE:
                break
    if verbose:
        print(f"    best val acc {best_acc:.3f} @ epoch {best_epoch} "
              f"({time.time()-t0:.1f}s)")
    model.load_state_dict(best_state)
    return model


def _evaluate(model, X, y, device="cpu"):
    model.eval()
    Xt, _ = _to_torch(X, y, device)
    with torch.no_grad():
        logits = model(Xt)
        pred = logits.argmax(1).cpu().numpy()
    acc = float((pred == y).mean())
    f1_micro = f1_score(y, pred, average="micro")
    f1_macro = f1_score(y, pred, average="macro")
    cm = confusion_matrix(y, pred, labels=np.arange(config.NUM_CLASSES))
    return acc, f1_micro, f1_macro, cm, pred


def cross_validate(X_exp, y_exp, X_sim, y_sim, tw, use_aug=True,
                   n_splits=5, seed=config.CV_SEED, device="cpu",
                   verbose=True):
    """Run 5-fold CV (Case 3). Returns per-fold and aggregated metrics."""
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=seed)
    folds = []
    all_pred, all_true = [], []
    for fold, (tr_idx, te_idx) in enumerate(skf.split(X_exp, y_exp)):
        # carve a validation set from the training experimental spectra
        val_idx = tr_idx[::7][:max(1, len(tr_idx) // 6)]
        tr_idx = np.setdiff1d(tr_idx, val_idx, assume_unique=True)
        rng = np.random.default_rng(config.AUG_SEED + fold * 1000)
        Xtr, ytr = _prepare_train_set(X_sim, y_sim, X_exp[tr_idx],
                                      y_exp[tr_idx], tw, use_aug, rng)
        Xval, yval = X_exp[val_idx], y_exp[val_idx]
        Xte, yte = X_exp[te_idx], y_exp[te_idx]
        if verbose:
            print(f"  fold {fold}: train {len(Xtr)} (exp {len(tr_idx)}, "
                  f"sim {len(X_sim)}, aug {2*config.AUG_N_SIM if use_aug else 0}), "
                  f"val {len(val_idx)}, test {len(te_idx)}")
        model = train_model(Xtr, ytr, Xval, yval,
                            seed=config.SEED + fold, verbose=verbose,
                            device=device)
        acc, f1_mi, f1_ma, cm, pred = _evaluate(model, Xte, yte, device=device)
        folds.append(dict(fold=fold, accuracy=acc, f1_micro=f1_mi,
                          f1_macro=f1_ma, cm=cm, test_idx=te_idx,
                          pred=pred, true=yte))
        all_pred.extend(pred.tolist()); all_true.extend(yte.tolist())
        if verbose:
            print(f"    -> test acc {acc:.4f}  f1_micro {f1_mi:.4f} "
                  f"f1_macro {f1_ma:.4f}")
    accs = np.array([f["accuracy"] for f in folds])
    f1mi = np.array([f["f1_micro"] for f in folds])
    f1ma = np.array([f["f1_macro"] for f in folds])
    agg = dict(
        accuracy_mean=float(accs.mean()), accuracy_std=float(accs.std(ddof=1)),
        f1_micro_mean=float(f1mi.mean()), f1_micro_std=float(f1mi.std(ddof=1)),
        f1_macro_mean=float(f1ma.mean()), f1_macro_std=float(f1ma.std(ddof=1)),
        overall_accuracy=float(np.mean(np.array(all_true) == np.array(all_pred))),
        overall_cm=confusion_matrix(all_true, all_pred,
                                    labels=np.arange(config.NUM_CLASSES)),
    )
    return agg, folds


def coarsen(X, step_factor, tw=None):
    """Coarsen the 2theta grid by averaging consecutive blocks.

    step_factor=4 -> 0.04*4 = 0.16 deg steps.
    """
    n = X.shape[1]
    n_out = n // step_factor
    Xc = X[:, :n_out * step_factor].reshape(X.shape[0], n_out, step_factor)
    Xc = Xc.mean(axis=2)
    if tw is not None:
        twc = tw[:n_out * step_factor].reshape(n_out, step_factor).mean(axis=1)
        return Xc, twc
    return Xc, None


def run_all(device="cpu"):
    d = load_data()
    X_exp, y_exp = d["X_exp"], d["y_exp"]
    X_sim, y_sim = d["X_theo"], d["y_theo"]
    tw = d["tw"]

    results = {}
    for use_aug in (True, False):
        print(f"=== 5-fold CV, augmentation={use_aug} ===")
        agg, folds = cross_validate(X_exp, y_exp, X_sim, y_sim, tw,
                                    use_aug=use_aug, device=device)
        results[("aug" if use_aug else "noaug")] = (agg, folds)
        np.save(config.RESULTS_DIR +
                f"/cv_{'aug' if use_aug else 'noaug'}.npy",
                dict(agg=agg,
                     per_fold=[dict(accuracy=f["accuracy"],
                                    f1_micro=f["f1_micro"],
                                    f1_macro=f["f1_macro"])
                               for f in folds]),
                allow_pickle=True)
        print(f"    agg: acc {agg['accuracy_mean']:.4f} +/- "
              f"{agg['accuracy_std']:.4f}, f1_micro "
              f"{agg['f1_micro_mean']:.4f}, f1_macro {agg['f1_macro_mean']:.4f}")

    # coarsening experiment
    print("=== Coarsening: 0.16 deg (step_factor=4) ===")
    for factor, label in ((2, "0.08"), (3, "0.12"), (4, "0.16"), (8, "0.32")):
        Xc, twc = coarsen(X_exp, factor, tw)
        Xsc, _ = coarsen(X_sim, factor)
        agg, folds = cross_validate(Xc, y_exp, Xsc, y_sim, twc, use_aug=True,
                                    device=device, verbose=False)
        results[("coarse", label)] = (agg, folds)
        print(f"    step {label} deg: acc {agg['accuracy_mean']:.4f} +/- "
              f"{agg['accuracy_std']:.4f}")
    return results


if __name__ == "__main__":
    device = "cuda" if config.__dict__.get("FORCE_GPU") else "cpu"
    results = run_all(device=device)
    print("done.")
