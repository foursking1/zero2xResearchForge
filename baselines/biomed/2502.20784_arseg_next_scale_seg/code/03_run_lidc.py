#!/usr/bin/env python3
"""Train & evaluate LIDC binary nodule-region segmentation:
baseline single-scale U-Net vs AR-Seg-style multi-scale next-scale U-Net (+consensus)."""
from __future__ import annotations
import os, sys, json, time, argparse
import numpy as np
import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import UNetBaseline, ArSegUNet, DEVICE, SEED
from trainer import make_loader, train_binary_epoch, eval_binary, soft_dice, hard_dice, _iou

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CACHE = os.path.join(ROOT, "results", "cache", "lidc")
OUT = os.path.join(ROOT, "results", "lidc")
os.makedirs(OUT, exist_ok=True)

torch.manual_seed(SEED)
np.random.seed(SEED)


def load_cache():
    x_tr = np.load(os.path.join(CACHE, "x_train.npy")); y_tr = np.load(os.path.join(CACHE, "y_train.npy"))
    x_va = np.load(os.path.join(CACHE, "x_val.npy"));   y_va = np.load(os.path.join(CACHE, "y_val.npy"))
    x_te = np.load(os.path.join(CACHE, "x_test.npy"));  y_te = np.load(os.path.join(CACHE, "y_test.npy"))
    return (x_tr, y_tr), (x_va, y_va), (x_te, y_te)


def train_one(model, name, tr, va, te, device, epochs=30, batch_size=256, lr=3e-4, ans=None,
              aux_weight=0.3):
    load_tr = make_loader(tr[0], tr[1], batch_size, True)
    optim = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(optim, T_max=epochs)
    best = -1
    best_state = None
    t0 = time.time()
    hist = []
    for ep in range(1, epochs + 1):
        loss = train_binary_epoch(model, load_tr, optim, device,
                                  arstyle=(ans is not None), coarse_weight=aux_weight)
        vsd, _, _, _, _, _ = eval_binary(model, va[0], va[1], device, arstyle=(ans is not None))
        sched.step()
        hist.append({"epoch": ep, "loss": loss, "val_soft_dice": vsd})
        if vsd > best:
            best = vsd
            best_state = {k: v.clone() for k, v in model.state_dict().items()}
        if ep % 5 == 0 or ep == epochs:
            print(f"[{name}] ep {ep:2d}/{epochs} loss {loss:.4f} val_softdice {vsd:.4f} ({time.time()-t0:.0f}s)")
    model.load_state_dict(best_state)
    torch.save(best_state, os.path.join(OUT, f"{name}_best.pt"))
    model.eval()

    n_te = len(te[0])
    res = {}
    for tag, ns in [("single", 1), ("consensus_k8", 8)]:
        sd, hd, iou, sd_list, hd_list, iou_list = eval_binary(
            model, te[0], te[1], device, arstyle=(ans is not None), n_samples=ns)
        res[tag] = {"soft_dice": float(sd), "hard_dice": float(hd), "iou": float(iou),
                    "n": n_te}
        np.savez(os.path.join(OUT, f"{name}_{tag}.npz"),
                 soft_dice=np.asarray(sd_list), hard_dice=np.asarray(hd_list), iou=np.asarray(iou_list))
        print(f"[{name}] test {tag:15s} soft_dice {sd:.4f} hard_dice {hd:.4f} iou {iou:.4f} (n={n_te})")

    out = {
        "model": name, "dataset": "LIDC", "train_patches": len(tr[0]),
        "val_patches": len(va[0]), "test_patches": n_te, "epochs": epochs,
        "best_val_soft_dice": best, "best_epoch": int(np.argmax([h["val_soft_dice"] for h in hist]) + 1),
        "train_time_s": round(time.time() - t0, 1),
        "test": res, "history": hist,
    }
    with open(os.path.join(OUT, f"{name}.json"), "w") as f:
        json.dump(out, f, indent=2, default=str)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=int, default=30)
    ap.add_argument("--batch", type=int, default=256)
    ap.add_argument("--device", default=DEVICE)
    ap.add_argument("--run", default="all", choices=["all", "baseline", "arseg", "arseg_nosup"])
    ap.add_argument("--aux_weight", type=float, default=0.3, help="multi-scale aux loss weight (0 => no multiscale-sup ablation)")
    args = ap.parse_args()
    print(f"[lidc] device={args.device} torch_threads={torch.get_num_threads()} run={args.run}")
    (tr, va, te) = load_cache()
    print(f"[lidc] train={len(tr[0])} val={len(va[0])} test={len(te[0])}")

    runs = []
    if args.run in ("all", "baseline"):
        m_base = UNetBaseline(in_ch=1, out_ch=1).to(args.device)
        runs.append(train_one(m_base, "unet_baseline", tr, va, te, args.device,
                              epochs=args.epochs, batch_size=args.batch, ans=None))
    if args.run in ("all", "arseg"):
        m_ar = ArSegUNet(in_ch=1, out_ch=1).to(args.device)
        runs.append(train_one(m_ar, "arseg_nextscale", tr, va, te, args.device,
                              epochs=args.epochs, batch_size=args.batch, ans="arseg",
                              aux_weight=args.aux_weight))
    if args.run in ("arseg_nosup",):
        m_ar = ArSegUNet(in_ch=1, out_ch=1).to(args.device)
        runs.append(train_one(m_ar, "arseg_noscale_sup", tr, va, te, args.device,
                              epochs=args.epochs, batch_size=args.batch, ans="arseg",
                              aux_weight=0.0))
    for r in runs:
        print("[lidc] DONE %s test soft_dice=%.4f" % (r["model"], r["test"]["single"]["soft_dice"]))


if __name__ == "__main__":
    main()