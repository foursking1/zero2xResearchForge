#!/usr/bin/env python3
"""BraTS-2021-mini 2D binary Whole-Tumor segmentation (primary BraTS protocol here).

TASK.md direction 2 explicitly allows 'WT 二类' as a BraTS protocol.  Binary WT is more
reliable on a 10-case / single-modality mini subset than per-subregion 4-class (where ET/TC
generalisation is poor because tumour-subregion appearance is largely a *contrast-agent /
multi-modality* signal that the single frozen modality cannot provide).  We therefore
report binary WT Dice as the primary BraTS number (A1/A2 anchors), and keep the 4-class
results (04_run_brats.py) as an auxiliary, honestly-reported analysis.

Same AR-Seg style = multi-scale heads + next-scale conditioning (binary head), same
train/val/test protocol as 04_run_brats.py.
"""
from __future__ import annotations
import os, sys, json, time, argparse
import numpy as np
import torch
import torch.nn.functional as F

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import UNetBaseline, ArSegUNet, DEVICE, SEED
from trainer import make_loader, train_binary_epoch, soft_dice, hard_dice, _iou

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CACHE = os.path.join(ROOT, "results", "cache", "brats")
OUT = os.path.join(ROOT, "results", "brats")
os.makedirs(OUT, exist_ok=True)

torch.manual_seed(SEED)
np.random.seed(SEED)


def load_cache():
    def load(part):
        x = np.load(os.path.join(CACHE, f"x_{part}.npy"))
        y = np.load(os.path.join(CACHE, f"y_{part}.npy"))
        return x, (y > 0).astype(np.float32)
    return load("train"), load("val"), load("test")


def eval_wt(model, x, y, device, batch_size=128, n_samples=1, K=8, ar=False):
    model.eval()
    out = {"soft_dice": 0.0, "hard_dice": 0.0, "iou": 0.0, "n": 0}
    for i in range(0, len(x), batch_size):
        xi = torch.from_numpy(x[i:i + batch_size]).to(device).unsqueeze(1)
        yi = y[i:i + batch_size]
        if n_samples > 1:
            p = model.sample(xi, K=K)
        else:
            if ar:
                p = torch.sigmoid(model.forward_single(xi))
            else:
                p = torch.sigmoid(model(xi))
        p = p.detach().cpu().numpy()[:, 0]
        for a, b in zip(p, yi):
            out["soft_dice"] += soft_dice(a, b)
            out["hard_dice"] += hard_dice(a, b)
            out["iou"] += _iou(a, b)
        out["n"] += len(yi)
    for k in ("soft_dice", "hard_dice", "iou"):
        out[k] /= out["n"]
    return out


def eval_wt_patient_pooled(model, x, y, device, slice_owner, ar=False, n_samples=1):
    """Voxel-pooled WT Dice per test patient."""
    model.eval()
    per_pt = {}
    idx_by_pt = {}
    for i, own in enumerate(slice_owner):
        idx_by_pt.setdefault(own, []).append(i)
    for pt, idxs in sorted(idx_by_pt.items()):
        xs = x[np.array(idxs)]; ys = y[np.array(idxs)]
        preds = []
        with torch.no_grad():
            for i in range(0, len(xs), 128):
                xi = torch.from_numpy(xs[i:i + 128]).to(device).unsqueeze(1)
                if n_samples > 1:
                    p = model.sample(xi, K=n_samples)
                else:
                    p = torch.sigmoid(model.forward_single(xi)) if ar else torch.sigmoid(model(xi))
                preds.append(p.cpu().numpy())
        pred = np.concatenate(preds, 0)
        pr = pred.ravel().astype(np.float32)
        yr = ys.ravel().astype(np.float32)
        DICE = 2 * np.sum(pr * yr) / (np.sum(pr) + np.sum(yr) + 1e-6)
        pb = (pr > 0.5).astype(np.float32)
        HARD = 2 * np.sum(pb * yr) / (np.sum(pb) + np.sum(yr) + 1e-6)
        per_pt[int(pt)] = {"soft_dice": float(DICE), "hard_dice": float(HARD), "slices": len(idxs)}
    return per_pt


def train_one(model, name, tr, va, te, device, epochs, batch_size, lr, ar):
    load_tr = make_loader(tr[0], tr[1], batch_size, True)
    optim = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(optim, T_max=epochs)
    best = -1
    best_state = None
    t0 = time.time()
    hist = []
    for ep in range(1, epochs + 1):
        loss = train_binary_epoch(model, load_tr, optim, device, arstyle=ar)
        va_e = eval_wt(model, va[0], va[1], device, ar=ar)
        vsd = va_e["soft_dice"]
        sched.step()
        hist.append({"epoch": ep, "loss": loss, "val_soft_dice": vsd})
        if vsd > best:
            best = vsd
            best_state = {k: v.clone() for k, v in model.state_dict().items()}
        if ep % 5 == 0 or ep == epochs:
            print(f"[{name}] ep {ep:2d}/{epochs} loss {loss:.4f} val_softDice {vsd:.4f} ({time.time()-t0:.0f}s)")
    model.load_state_dict(best_state)
    torch.save(best_state, os.path.join(OUT, f"{name}_wt_best.pt"))
    model.eval()

    res = {}
    for tag, ns in (("single", 1), ("consensus_k8", 8)):
        e = eval_wt(model, te[0], te[1], device, n_samples=ns, ar=ar)
        res[tag] = {k: round(float(v), 4) for k, v in e.items()}
        print(f"[{name}] test {tag:15s} soft_dice {res[tag]['soft_dice']:.4f} "
              f"hard_dice {res[tag]['hard_dice']:.4f} iou {res[tag]['iou']:.4f}")

    with open(os.path.join(CACHE, "meta_test.txt")) as f:
        meta = [l.strip() for l in f]
    import re
    owner = np.array([int(re.match(r"case(\d+)", m).group(1)) for m in meta])
    per_pt = eval_wt_patient_pooled(model, te[0], te[1], device, owner, ar=ar)
    out = {
        "model": name, "dataset": "BraTS2021_mini_WT", "train_slices": len(tr[0]),
        "val_slices": len(va[0]), "test_slices": len(te[0]), "epochs": epochs,
        "best_val_soft_dice": best, "best_epoch": int(np.argmax([h["val_soft_dice"] for h in hist]) + 1),
        "train_time_s": round(time.time() - t0, 1), "test": res,
        "test_patient_pooled_soft_dice": per_pt, "history": hist,
    }
    with open(os.path.join(OUT, f"{name}_wt.json"), "w") as f:
        json.dump(out, f, indent=2, default=str)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=int, default=25)
    ap.add_argument("--batch", type=int, default=128)
    ap.add_argument("--device", default=DEVICE)
    args = ap.parse_args()
    (tr, va, te) = load_cache()
    print(f"[brats_wt] device={args.device} train={len(tr[0])} val={len(va[0])} test={len(te[0])}")
    m_base = UNetBaseline(in_ch=1, out_ch=1).to(args.device)
    m_ar = ArSegUNet(in_ch=1, out_ch=1).to(args.device)
    r_base = train_one(m_base, "unet_baseline", tr, va, te, args.device,
                       args.epochs, args.batch, 3e-4, ar=False)
    r_ar = train_one(m_ar, "arseg_nextscale", tr, va, te, args.device,
                     args.epochs, args.batch, 3e-4, ar=True)
    print("[brats_wt] DONE baseline WT sd=%.4f | arseg WT sd=%.4f" %
          (r_base["test"]["single"]["soft_dice"], r_ar["test"]["single"]["soft_dice"]))


if __name__ == "__main__":
    main()