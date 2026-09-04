"""03_finetune.py -- fine-tune every pool member on the *target* organ and score Dice.

Usage:
    python 03_finetune.py --target spleen --source liver --epochs 14
    python 03_finetune.py --target liver  --source spleen --epochs 20

Protocol (fixed, seeded):
  * pool weights: work/checkpoints/<source>_<id>_pretrained.pt   (from 02_pretrain)
  * fine-tune loader: target-organ *train* cases only  (Spleen train set for dir 1)
  * evaluation:      target-organ *test*  cases only, full foreground slices, Dice
  * the target train split is also the feature source for the TE estimators (04_te.py)
"""
import os
import sys
import json
import time
import argparse
import numpy as np
import torch
from torch.optim import Adam

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import CKPT_DIR, RESULTS_DIR, SPLITS
from dataset import make_loader
from models_unet import UNet
from train_utils import set_seed, build_model, fit, eval_dice, save_ckpt, load_ckpt, count_params

CFG = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "pool_config.json")))
torch.set_num_threads(16)


def full_eval_slices(model, organ, test_cases):
    """Evaluate on all foreground slices of each test case (no subsampling).
    Preprocessing mirrors the training cache path: fg-aware square crop -> 128."""
    import numpy as np
    from common import load_case, hu_normalize, fg_square_crop, to_uint8
    dices_all = []
    per_case = {}
    for c in test_cases:
        res = load_case(organ, f"{organ}_{c}")
        lab = res["lab"]
        fg = np.where(lab.reshape(-1, lab.shape[-1]).sum(axis=0) > 0)[0]
        img = hu_normalize(res["img"].copy())
        xs, ys = [], []
        for z in fg:
            i, l = fg_square_crop(img[:, :, z], lab[:, :, z])
            i = np.nan_to_num(np.asarray(i, np.float32))
            xs.append(to_uint8(np.clip(i, 0, 1)).astype(np.float32) / 255.0)
            ys.append((np.asarray(l) > 0).astype(np.float32))
        if not xs:
            per_case[c] = None
            continue
        xs = np.stack(xs)
        ys = np.stack(ys)
        ds = []
        model.eval()
        with torch.no_grad():
            for k in range(0, len(xs), 32):
                xb = torch.from_numpy(xs[k:k + 32, None])
                logits, _ = model(xb)
                p = (torch.sigmoid(logits) > 0.5).float().numpy()
                for pi, yi in zip(p[:, 0], ys[k:k + 32]):
                    inter = (pi * yi).sum()
                    un = pi.sum() + yi.sum()
                    ds.append(2 * inter / un if un > 0 else 1.0)
        dices_all += ds
        per_case[c] = float(np.mean(ds))
    return float(np.mean(dices_all)), per_case


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", choices=["spleen", "liver"], required=True)
    ap.add_argument("--source", choices=["liver", "spleen"], required=True)
    ap.add_argument("--epochs", type=int, default=14)
    ap.add_argument("--only", default=None)
    ap.add_argument("--max-slices-train", type=int, default=CFG["finetune"]["max_slices_per_case"])
    ap.add_argument("--cases", default=None,
                    help="'train;test' comma-list to override the target split (e.g. '1;0')")
    ap.add_argument("--freeze-encoder", action="store_true",
                    help="freeze encoder+bottleneck, train only decoder+head "
                         "(stable probe-style fine-tune for tiny targets)")
    ap.add_argument("--ft-out", default=None,
                    help="output json filename override (default results/finetune_<src>2<tgt>.json)")
    a = ap.parse_args()

    if a.cases:
        tr, te = a.cases.split(";")
        train_cases = [x for x in tr.split(",") if x]
        test_cases = [x for x in te.split(",") if x]
    else:
        train_cases, test_cases = SPLITS[a.target][0], SPLITS[a.target][1]
    members = CFG["pool"] if not a.only else [m for m in CFG["pool"] if m["id"] == a.only]

    rows = []
    for m in members:
        tag = f"{a.source}_{m['id']}"
        set_seed(m["seed"])
        model = build_model(m)
        ckpt = load_ckpt(f"{tag}_pretrained")
        model.load_state_dict(ckpt["state"])
        if m["pretrain_epochs"] == 0:
            print(f"[ft] {tag}: starting from RANDOM init")
        else:
            print(f"[ft] {tag}: initialised from {a.source}-pretrained weights")
        n_params_ft = None
        if a.freeze_encoder:
            for p in model.enc.parameters():
                p.requires_grad = False
            for p in model.downs.parameters():
                p.requires_grad = False
            for p in model.bot.parameters():
                p.requires_grad = False
            n_params_ft = sum(p.numel() for p in model.parameters() if p.requires_grad)
            print(f"[ft] {tag}: encoder frozen; trainable = {n_params_ft} params (decoder+head)")
        tr = make_loader(a.target, train_cases, batch_size=CFG["finetune"]["batch_size"],
                         seed=m["seed"], max_slices=a.max_slices_train, augment=True,
                         size=CFG["finetune"]["size"])
        opt = Adam(model.parameters(), lr=3e-4)
        n_train = len(tr.dataset)
        t0 = time.time()
        print(f"[ft] {tag}: n_train_slices={n_train} train_cases={train_cases} target={a.target} source={a.source}")
        d = fit(model, tr, opt, epochs=a.epochs)
        dice, std = eval_dice(model, make_loader(a.target, train_cases, batch_size=16, shuffle=False, seed=0, max_slices=a.max_slices_train, augment=False, size=CFG["finetune"]["size"]))
        full, per_case = full_eval_slices(model, a.target, test_cases)
        row = {"source_organ": a.source, "target_organ": a.target, "source_model": f"{tag}",
               "base": m["base"], "seed": m["seed"], "lr": m["lr"], "pretrain_epochs": m["pretrain_epochs"],
               "ft_epochs": a.epochs, "freeze_encoder": a.freeze_encoder,
               "train_dice": round(dice, 5), "ft_dice": round(full, 5),
               "ft_dice_std": round(std, 5), "per_case_dice": per_case,
               "wall_s": round(time.time() - t0, 1)}
        rows.append(row)
        print(f"[ft] {tag}: ft_dice(test)={full:.4f}  wall={time.time()-t0:.1f}s")
        save_ckpt(model, f"{tag}_finetuned", {"source": a.source, "target": a.target})

    path = os.path.join(RESULTS_DIR, a.ft_out or f"finetune_{a.source}2{a.target}.json")
    json.dump(rows, open(path, "w"), indent=2)
    print("saved", path)
    for r in rows:
        print("  ", r["source_model"], r["ft_dice"])


if __name__ == "__main__":
    main()