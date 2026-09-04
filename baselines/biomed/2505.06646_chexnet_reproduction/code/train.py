# -*- coding: utf-8 -*-
"""Train / fine-tune ImageNet-pretrained DenseNet-121 (CheXNet architecture)
for 14-class multi-label classification on the frozen NIH ChestX-ray14 subset.

Usage:
    python train.py --model repro    --epochs 14 [--device cuda|cpu]
    python train.py --model enhanced --epochs 18

For each model it:
  * trains with BCE (repro) or Focal Loss (enhanced),
  * validates on a 162-image split carved from the training shard (seed 42),
  * keeps the checkpoint with the best validation mean ROC-AUC,
  * writes checkpoint + test/val probabilities + thresholds to checkpoints/.

No test-shard leak: the frozen test shard is used for evaluation only.
"""
import argparse
import json
import math
import os
import sys
import time

import numpy as np
import torch
import torch.nn as nn

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common  # noqa: E402

LABELS = common.LABELS
N_CLASS = common.N_CLASS


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", choices=["repro", "enhanced"], required=True)
    ap.add_argument("--epochs", type=int, default=14)
    ap.add_argument("--batch-size", type=int, default=32)
    ap.add_argument("--lr", type=float, default=1e-4)
    ap.add_argument("--weight-decay", type=float, default=1e-4)
    ap.add_argument("--label-smoothing", type=float, default=0.0)
    ap.add_argument("--ema", type=float, default=0.0,
                    help="exponential moving average of weights (e.g. 0.999)")
    ap.add_argument("--aug", choices=["light", "strong"], default="light")
    ap.add_argument("--seed", type=int, default=common.SEED)
    ap.add_argument("--focal-alpha", type=float, default=0.25)
    ap.add_argument("--tag", default=None,
                    help="optional sub-folder under code/checkpoints to keep "
                         "multiple runs; outputs land in checkpoints/<tag>/")
    ap.add_argument("--device", default=None,
                    help="cuda or cpu (default: auto)")
    ap.add_argument("--data-dir", default=None,
                    help="directory with nih_*-00000.parquet (default: auto)")
    ap.add_argument("--out", default=None,
                    help="output base directory (default: agent_solution/)")
    ap.add_argument("--fp16", action="store_true",
                    help="use mixed precision (CUDA only)")
    return ap.parse_args()


def make_loader(rows, targets, train_tf, eval_tf, batch_size, shuffle, kind):
    tf = train_tf if (kind in ("repro", "enhanced") and shuffle) else eval_tf
    n = len(rows)

    class DS(torch.utils.data.Dataset):
        def __len__(self):
            return n

        def __getitem__(self, i):
            img = tf(common.decode(rows.iloc[i]))
            return img, torch.from_numpy(targets[i])

    return torch.utils.data.DataLoader(DS(), batch_size=batch_size, shuffle=shuffle,
                                       num_workers=2, pin_memory=True)


def train_one(model, loader, loss_f, opt, sched, device, fp16):
    model.train()
    total, n = 0.0, 0
    scaler = torch.amp.GradScaler("cuda", enabled=fp16)
    for x, y in loader:
        x, y = x.to(device), y.to(device)
        opt.zero_grad(set_to_none=True)
        with torch.amp.autocast("cuda", enabled=fp16):
            loss = loss_f(model(x), y)
        scaler.scale(loss).backward()
        scaler.step(opt)
        scaler.update()
        total += loss.item() * x.size(0)
        n += x.size(0)
    if sched is not None:
        sched.step()
    return total / n


@torch.no_grad()
def predict(model, loader, device, fp16, tta=False):
    """Predict probabilities. With tta=True, average the image and its
    horizontal flip (test-time augmentation - no test labels used)."""
    model.eval()
    probs, tgts = [], []
    for x, y in loader:
        x = x.to(device)
        with torch.amp.autocast("cuda", enabled=fp16):
            logits = model(x)
            if tta:
                logits = (logits + model(x.flip(-1)).detach()) * 0.5
        probs.append(torch.sigmoid(logits.float()).cpu().numpy())
        tgts.append(y.numpy())
    return np.vstack(probs), np.vstack(tgts)


def mean_val_auc(y_val, p_val):
    aucs = common.per_class_auc(y_val, p_val)
    return float(np.nanmean(aucs)), aucs


def tune_thresholds(y_val, p_val):
    """Per-class thresholds maximizing F1 on the val split (enhanced arm).

    A grid over (0.05, 0.95) is scanned for every class; classes carrying no
    val positives are left at the default 0.5.
    """
    thr = np.ones(N_CLASS) * 0.5
    grid = np.arange(0.05, 0.96, 0.05)
    from sklearn.metrics import f1_score
    for c in range(N_CLASS):
        if y_val[:, c].sum() == 0:
            continue
        best_f1, best_t = -1.0, 0.5
        for t in grid:
            f1 = f1_score(y_val[:, c], (p_val[:, c] >= t).astype(int), zero_division=0)
            if f1 > best_f1:
                best_f1, best_t = f1, float(t)
        thr[c] = best_t
    return thr


def main():
    args = parse_args()
    common_extra = {}
    if args.data_dir:
        common_extra["PB_DATA_DIR"] = args.data_dir
        os.environ["PB_DATA_DIR"] = args.data_dir
    torch.manual_seed(args.seed)
    np.random.seed(args.seed)

    device = (args.device or
              ("cuda" if torch.cuda.is_available() else "cpu"))
    fp16 = args.fp16 and device == "cuda"

    out = args.out or os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    ckpt_dir = os.path.join(out, "code", "checkpoints", args.tag or "")
    os.makedirs(ckpt_dir, exist_ok=True)

    tag_suffix = f"_{args.tag}" if args.tag else ""
    log_path = os.path.join(out, "evidence",
                            f"train_log_{args.model}{tag_suffix}.txt")
    lf = open(log_path, "w", encoding="utf-8")

    def log(msg):
        print(msg)
        lf.write(msg + "\n")
        lf.flush()

    log(f"== train.py --model {args.model}  device={device}  fp16={fp16} ==")
    log(f"seed={args.seed}  epochs={args.epochs}  bs={args.batch_size}  "
        f"lr={args.lr}  wd={args.weight_decay}")

    # ---------------- data ----------------
    data_dir = common.find_data_dir()
    log(f"data dir: {data_dir}")
    train, test = common.load_data_split(data_dir)
    Y_train = common.labels_to_multihot(train["labels"])
    Y_test = common.labels_to_multihot(test["labels"])
    tr_idx, val_idx = common.train_val_split(train)
    train_rows, val_rows = train.iloc[tr_idx], train.iloc[val_idx]
    Y_tr, Y_val = Y_train[tr_idx], Y_train[val_idx]

    log(f"train rows: {len(train_rows)}  val rows: {len(val_rows)}  "
        f"test rows: {len(test)}")
    log("val per-class positives (1=Atelectasis..14=Hernia): "
        f"{Y_val.sum(axis=0).astype(int).tolist()}")
    log("test per-class positives: "
        f"{Y_test.sum(axis=0).astype(int).tolist()}")

    train_tf, eval_tf = common.build_transforms(args.model, strong=(args.aug == "strong"))
    tr_loader = make_loader(train_rows, Y_tr, train_tf, eval_tf, args.batch_size, True, args.model)
    val_loader = make_loader(val_rows, Y_val, train_tf, eval_tf, args.batch_size, False, "eval")
    te_loader = make_loader(test, Y_test, train_tf, eval_tf, args.batch_size, False, "eval")

    # ---------------- model ----------------
    model = common.build_model()
    model = model.to(device)
    n_params = sum(p.numel() for p in model.parameters())
    log(f"DenseNet-121 params: {n_params/1e6:.2f}M")

    loss_f = (lambda lg, t: common.bce_loss(lg, t)) if args.model == "repro" \
        else (lambda lg, t: common.focal_loss(lg, t, alpha=args.focal_alpha))

    label_smoothing = args.label_smoothing
    if label_smoothing > 0.0:
        def smooth_loss(logits, targets):
            sm = targets * (1.0 - 2.0 * label_smoothing) + label_smoothing
            return (common.bce_loss if args.model == "repro"
                    else lambda lg, t: common.focal_loss(lg, t, alpha=args.focal_alpha))(logits, sm)

        loss_f = smooth_loss
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=args.epochs)

    val_probs = []   # snapshot val probabilities in the same tail window
    best_auc, best_state, best_ep = -1.0, None, -1
    ema_state = None  # exponential moving average of the online weights
    ema_decay = args.ema
    test_probs = []   # snapshot test probabilities per epoch (trace, for ensembling)
    t0 = time.time()
    for ep in range(args.epochs):
        tloss = train_one(model, tr_loader, loss_f, opt, sched, device, fp16)
        if ema_decay > 0.0:
            with torch.no_grad():
                if ema_state is None:
                    ema_state = {k: v.detach().cpu().float().clone() for k, v in model.state_dict().items()}
                else:
                    for k, v in model.state_dict().items():
                        ema_state[k].mul_(ema_decay).add_(v.detach().cpu().float(), alpha=1 - ema_decay)
        p_val, _ = predict(model, val_loader, device, fp16, tta=True)
        m_auc, aucs = mean_val_auc(Y_val, p_val)
        lr_now = opt.param_groups[0]["lr"]
        log(f"epoch {ep+1:02d}/{args.epochs}  loss={tloss:.4f}  "
            f"val mean AUC={m_auc:.4f}  lr={lr_now:.2e}")
        if m_auc > best_auc:
            best_auc, best_ep = m_auc, ep + 1
            cand = ema_state if ema_state is not None else model.state_dict()
            best_state = {k: v.detach().cpu().clone() for k, v in cand.items()}
        if ep >= args.epochs // 2:  # trace only the second half (still under sine-wave->0 lr)
            p_te, _ = predict(model, te_loader, device, fp16, tta=True)
            test_probs.append(p_te)
            p_vl, _ = predict(model, val_loader, device, fp16, tta=True)
            val_probs.append(p_vl)
    log(f"epochs done in {time.time()-t0:.0f}s; best val mean AUC={best_auc:.4f} @ep{best_ep}")

    # ---------------- final predictions ----------------
    model.load_state_dict(best_state)
    model.to(device)
    p_val, _ = predict(model, val_loader, device, fp16, tta=True)
    p_test, _ = predict(model, te_loader, device, fp16, tta=True)

    # snapshot ensemble: average the trailing checkpoints (fixed recipe, no
    # test-driven selection); stochastic-approximation style variance reduction.
    k_ens = max(2, args.epochs // 4)
    ens = np.mean(np.stack(test_probs[-k_ens:]), axis=0) if len(test_probs) >= k_ens \
        else p_test if not test_probs else np.mean(np.stack(test_probs), axis=0)

    if args.model == "enhanced":
        ens_val = np.mean(np.stack(val_probs[-k_ens:]), axis=0) if len(val_probs) >= k_ens \
            else p_val
        thr = tune_thresholds(Y_val, ens_val)
    else:
        thr = np.ones(N_CLASS) * 0.5
    log(f"thresholds: {np.round(thr, 2).tolist()}")

    # ---------------- save ----------------
    torch.save(best_state, os.path.join(ckpt_dir, f"{args.model}_best.pt"))
    np.savez_compressed(
        os.path.join(ckpt_dir, f"{args.model}_pred.npz"),
        p_val=p_val, p_test=p_test, p_test_ens=ens,
        p_val_ens=ens_val if args.model == "enhanced" else p_val,
        y_val=Y_val, y_test=Y_test,
        thresholds=thr,
        best_auc=float(best_auc),
    )
    json.dump({"threshold": thr.tolist(), "best_val_auc": best_auc,
               "train_n_used": int(len(train_rows)), "val_n": int(len(val_rows)),
               "epochs": int(args.epochs), "seed": int(args.seed)},
              open(os.path.join(ckpt_dir, f"{args.model}_meta.json"), "w"),
              indent=2)
    log(f"saved checkpoints/{args.model}_best.pt, _pred.npz, _meta.json "
        f"(ensemble over last {k_ens} traced snapshots)")

    # ---------------- quick test metrics ----------------
    yt = Y_test
    eng_auc = float(np.nanmean(common.per_class_auc(yt, ens)))
    eng_f1 = float(np.mean(common.per_class_f1(yt, (ens >= thr).astype(float))))
    log(f"[{args.model}] test mean AUC (snapshot-ensemble)={eng_auc:.4f}  "
        f"test mean F1={eng_f1:.4f}")
    lf.close()
    # free GPU memory for the sibling processes
    if device == "cuda":
        del model
        torch.cuda.empty_cache()


if __name__ == "__main__":
    main()