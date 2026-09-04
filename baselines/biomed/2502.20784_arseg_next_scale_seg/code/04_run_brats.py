#!/usr/bin/env python3
"""Train & evaluate BraTS-2021-mini 2D axial multi-class segmentation:
baseline single-scale U-Net vs AR-Seg-style multi-scale next-scale U-Net (+consensus)."""
from __future__ import annotations
import os, sys, json, time, argparse
import numpy as np
import torch
import torch.nn.functional as F

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import UNetBaseline, ArSegUNet, DEVICE, SEED
from trainer import make_loader, train_multiclass_epoch, eval_multiclass

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CACHE = os.path.join(ROOT, "results", "cache", "brats")
OUT = os.path.join(ROOT, "results", "brats")
os.makedirs(OUT, exist_ok=True)

torch.manual_seed(SEED)
np.random.seed(SEED)


def load_cache():
    x_tr = np.load(os.path.join(CACHE, "x_train.npy")); y_tr = np.load(os.path.join(CACHE, "y_train.npy"))
    x_va = np.load(os.path.join(CACHE, "x_val.npy"));   y_va = np.load(os.path.join(CACHE, "y_val.npy"))
    x_te = np.load(os.path.join(CACHE, "x_test.npy"));  y_te = np.load(os.path.join(CACHE, "y_test.npy"))
    return (x_tr, y_tr), (x_va, y_va), (x_te, y_te)


def train_one(model, name, tr, va, te, device, epochs=25, batch_size=64, lr=3e-4, ar=True, class_weights=None):
    load_tr = make_loader(tr[0], tr[1], batch_size, True)
    optim = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(optim, T_max=epochs)
    n_classes = 4
    best = -1
    best_state = None
    t0 = time.time()
    hist = []
    for ep in range(1, epochs + 1):
        loss = train_multiclass_epoch(model, load_tr, optim, device, arstyle=ar,
                                      n_classes=n_classes, coarse_weight=0.3)
        va_pooled, _ = eval_multiclass(model, va[0], va[1], device, arstyle=ar)
        vd = np.mean([va_pooled[k] for k in ("et", "tc", "wt")])
        sched.step()
        hist.append({"epoch": ep, "loss": loss, "val_mean_region_dice": float(vd)})
        if vd > best:
            best = vd
            best_state = {k: v.clone() for k, v in model.state_dict().items()}
        if ep % 5 == 0 or ep == epochs:
            print(f"[{name}] ep {ep:2d}/{epochs} loss {loss:.4f} val_meanDice {vd:.4f} ({time.time()-t0:.0f}s)")
    model.load_state_dict(best_state)
    torch.save(best_state, os.path.join(OUT, f"{name}_best.pt"))
    model.eval()

    res = {}
    for tag, ns in [("single", 1), ("consensus_k8", 8)]:
        pooled, per_slice = eval_multiclass(model, te[0], te[1], device, arstyle=ar, n_samples=ns, K=8)
        res[tag] = {"dice_et": pooled["et"], "dice_tc": pooled["tc"], "dice_wt": pooled["wt"],
                    "mean_region_dice": float(np.mean([pooled[k] for k in ("et", "tc", "wt")])),
                    "n_slices": len(te[0])}
        print(f"[{name}] test {tag:15s} ET {pooled['et']:.4f} TC {pooled['tc']:.4f} WT {pooled['wt']:.4f} "
              f"mean {res[tag]['mean_region_dice']:.4f}")
        np.save(os.path.join(OUT, f"{name}_{tag}_sliceDice.npy"),
                np.array([per_slice["et"], per_slice["tc"], per_slice["wt"]]))

    out = {
        "model": name, "dataset": "BraTS2021_mini", "train_slices": len(tr[0]),
        "val_slices": len(va[0]), "test_slices": len(te[0]), "epochs": epochs,
        "best_val_mean_region_dice": float(best),
        "best_epoch": int(np.argmax([h["val_mean_region_dice"] for h in hist]) + 1),
        "train_time_s": round(time.time() - t0, 1), "test": res, "history": hist,
    }
    with open(os.path.join(OUT, f"{name}.json"), "w") as f:
        json.dump(out, f, indent=2, default=str)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=int, default=25)
    ap.add_argument("--batch", type=int, default=64)
    ap.add_argument("--device", default=DEVICE)
    args = ap.parse_args()
    print(f"[brats] device={args.device} torch_threads={torch.get_num_threads()}")
    (tr, va, te) = load_cache()
    print(f"[brats] train={len(tr[0])} val={len(va[0])} test={len(te[0])}")
    # class weights to counter ET/NEC rarity in multi-class CE (rough prior)
    counts = np.array([int((te[1] == 0).sum()), int((te[1] == 1).sum()),
                       int((te[1] == 2).sum()), int((te[1] == 3).sum())])
    cw = torch.tensor(float(counts.sum()) / (counts + 1e-6), dtype=torch.float32)

    m_base = UNetBaseline(in_ch=1, out_ch=4).to(args.device)
    m_ar = ArSegUNet(in_ch=1, out_ch=4).to(args.device)
    r_base = train_one(m_base, "unet_baseline", tr, va, te, args.device,
                       epochs=args.epochs, batch_size=args.batch, ar=False, class_weights=cw)
    r_ar = train_one(m_ar, "arseg_nextscale", tr, va, te, args.device,
                     epochs=args.epochs, batch_size=args.batch, ar=True, class_weights=cw)
    print("[brats] DONE baseline meanDice=%.4f | arseg meanDice=%.4f" %
          (r_base["test"]["single"]["mean_region_dice"], r_ar["test"]["single"]["mean_region_dice"]))


if __name__ == "__main__":
    main()