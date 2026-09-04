"""02_pretrain.py -- pre-train the candidate source models on a source organ.

Usage:
    python 02_pretrain.py --source liver --epochs 60     (direction 1; pool on Liver)
    python 02_pretrain.py --source spleen --epochs 40    (direction 2; pool on Spleen)
    python 02_pretrain.py --source liver --only scratch  (only re-init the scratch member)

Each pool member is a 2-D U-Net.  Members differ by capacity (base channels),
weight-init / optimisation seed, learning rate and/or training budget -- the
heterogeneous "pre-trained model pool" whose transferability the framework must
sort.  `--only` pretrains a single member id.  Weights (pretrained or, for the
scratch member, random init) are stored under work/checkpoints as
`<source>_<id>_pretrained.pt`.
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
from common import CKPT_DIR, SPLITS, case_ids
from dataset import make_loader
from models_unet import UNet
from train_utils import set_seed, build_model, fit, save_ckpt, load_ckpt, count_params
import torch.nn as nn

CFG = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "pool_config.json")))


def pretrain_member(source, member, epochs):
    tag = f"{source}_{member['id']}_pretrained"
    if member.get("pretrained", True):
        cases = SPLITS[source][0] + SPLITS[source][1]  # all cases of the source organ
        tr = make_loader(source, cases, batch_size=CFG["pretrain"]["batch_size"],
                         seed=member["seed"], max_slices=CFG["pretrain"]["max_slices_per_case"],
                         augment=True, size=CFG["pretrain"]["size"],
                         fg_only=CFG["pretrain"].get("fg_only", False))
        set_seed(member["seed"])
        model = build_model(member)
        opt = Adam(model.parameters(), lr=member["lr"])
        t0 = time.time()
        print(f"[pretrain] {tag}: ntrain={len(tr.dataset)} params={count_params(model)} lr={member['lr']}")
        d = fit(model, tr, opt, epochs=epochs)
        print(f"[pretrain] {tag}: final_traj_dice={d:.4f} wall={time.time()-t0:.1f}s")
        save_ckpt(model, tag, {"source": source, "member": member["id"],
                               "epochs": epochs, "lr": member["lr"], "seed": member["seed"]})
        return {"id": member["id"], "epochs": epochs, "final_step_dice": float(d)}
    else:  # random-init member; just persist the (freshly seeded) init as its "pretrained" weights
        set_seed(member["seed"])
        model = build_model(member)
        save_ckpt(model, tag, {"source": source, "member": member["id"],
                               "epochs": 0, "random_init": True})
        print(f"[pretrain] {tag}: random-init saved (no pretraining)")
        return {"id": member["id"], "epochs": 0, "random_init": True}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", choices=["liver", "spleen"], required=True)
    ap.add_argument("--epochs", type=int, default=None)
    ap.add_argument("--only", default=None)
    ap.add_argument("--output", default=None)
    a = ap.parse_args()

    if a.epochs:
        for m in CFG["pool"]:
            if m.get("pretrained", True):
                m["pretrain_epochs"] = a.epochs
        json.dump(CFG, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "pool_config.json"), "w"), indent=2)

    members = CFG["pool"] if not a.only else [m for m in CFG["pool"] if m["id"] == a.only]
    assert members, a.only
    summary = []
    for m in members:
        res = pretrain_member(a.source, m, m.get("pretrain_epochs", 0))
        res["source"] = a.source
        summary.append(res)
    out = a.output or os.path.join(os.path.dirname(os.path.abspath(__file__)), "work", f"pretrain_{a.source}.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump(summary, open(out, "w"), indent=2)
    print("[pretrain] summary ->", out, json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()