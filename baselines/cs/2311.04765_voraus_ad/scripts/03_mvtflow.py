"""03_mvtflow.py — main dense normalizing-flow model (MVT-Flow style).

Re-implementation of the voraus-AD paper's primary method family:
an action-conditioned RealNVP normalizing flow operating on the per-timestep
130-dim (z-scored with training-set statistics) feature vector.

Config matches the paper Sec. V-B1 intent (4 affine coupling blocks, Adam):
lr 8e-4, up to 70 epochs; batch size enlarged for CPU/GPU throughput.

Anomaly score of a sample = mean over its observed timesteps of
- log p(x_t | action) under the trained flow.

No GPU required (CPU fallback); device is auto-selected.
Usage:
    python 03_mvtflow.py --epochs 70 --batch-size 8192 --seed 42 --out-name mvtflow
"""
import argparse
import json
import os
import time

import numpy as np
import torch

import common
import mvtflow_module as MF
from mvtflow_module import CondRealNVP, D, device, evaluate, train_epoch


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=int, default=70)
    ap.add_argument("--batch-size", type=int, default=8192)
    ap.add_argument("--n-blocks", type=int, default=4)
    ap.add_argument("--hidden", type=int, default=256)
    ap.add_argument("--ctx-dim", type=int, default=32)
    ap.add_argument("--lr", type=float, default=8e-4)
    ap.add_argument("--eval-every", type=int, default=5)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out-name", type=str, default="mvtflow")
    ap.add_argument("--threads", type=int, default=4,
                    help="torch CPU threads (ignored on CUDA)")
    ap.add_argument("--subsample", type=float, default=1.0,
                    help="fraction of training timesteps used per epoch")
    args = ap.parse_args()

    torch.manual_seed(args.seed)
    np.random.seed(args.seed)
    if device.type == "cpu":
        torch.set_num_threads(args.threads)

    d = common.load_cache()
    Xn, lengths = d["Xn"], d["lengths"]
    setting, anomaly, category, action = d["setting"], d["anomaly"].astype(bool), d["category"], d["action"]
    train_mask, test_mask = common.get_train_test_masks(setting)
    train_idx = np.where(train_mask)[0]

    model = CondRealNVP(d=D, n_blocks=args.n_blocks, ctx_dim=args.ctx_dim,
                        hidden=args.hidden).to(device)
    opt = torch.optim.Adam(model.parameters(), lr=args.lr)

    print(f"[pool] building timestep pool ...", flush=True)
    t0 = time.time()
    Xp, Ap = MF.build_timestep_pool(Xn, lengths, action, train_idx)
    n_train_steps = Xp.shape[0]
    print(f"[train] {n_train_steps} timesteps, {len(train_idx)} samples, "
          f"params={sum(p.numel() for p in model.parameters())} "
          f"(pool built in {time.time() - t0:.0f}s)", flush=True)

    t0 = time.time()
    first = train_epoch(model, opt, Xp, Ap, args, 0)
    print(f"[bench] epoch0 time {time.time() - t0:.1f}s (loss {first:.3f})", flush=True)

    best_mean = -1
    best_state = None

    for ep in range(1, args.epochs):
        t0 = time.time()
        tr_loss = train_epoch(model, opt, Xp, Ap, args, ep)
        dt = time.time() - t0
        msg = f"epoch {ep:3d}/{args.epochs} loss {tr_loss:.3f} ({dt:.0f}s"
        if ep % args.eval_every == 0 or ep == args.epochs - 1:
            score, mean_auc, aucs = evaluate(model, Xn, lengths, action, test_mask, anomaly, category)
            msg += f", mean_auc {mean_auc:.4f}"
            if mean_auc > best_mean:
                best_mean = mean_auc
                best_state = {k: v.clone() for k, v in model.state_dict().items()}
                np.save(os.path.join(common.BASE, "results", f"{args.out_name}_scores_best.npy"), score)
        msg += ")"
        print(msg, flush=True)

    if best_state is not None:
        model.load_state_dict(best_state)
    score, mean_auc, aucs = evaluate(model, Xn, lengths, action, test_mask, anomaly, category)
    print(f"\n[final] mean AUROC = {mean_auc:.4f} (best seen across epochs: {best_mean:.4f})")

    torch.save(model.state_dict(), os.path.join(common.BASE, "results", f"{args.out_name}.pt"))
    np.save(os.path.join(common.BASE, "results", f"{args.out_name}_scores.npy"), score)

    import pandas as pd
    rows = []
    for cat in range(12):
        pos = np.where(test_mask & anomaly & (category == cat))[0]
        rows.append({
            "category_id": cat, "category_name": common.CATEGORY_NAMES[cat],
            "n_anomaly": int(len(pos)), "auroc_main": round(aucs[cat], 4)})
    pd.DataFrame(rows).to_csv(os.path.join(common.BASE, "results", f"{args.out_name}_table.csv"), index=False)

    meta = {"args": vars(args), "mean_auc": float(mean_auc), "best_seen_mean_auc": float(best_mean),
            "per_category": {int(k): float(v) for k, v in aucs.items()}}
    with open(os.path.join(common.BASE, "results", f"{args.out_name}_meta.json"), "w") as f:
        json.dump(meta, f, indent=2)
    print("saved results/", args.out_name, "meanauc", round(mean_auc, 4))


if __name__ == "__main__":
    main()