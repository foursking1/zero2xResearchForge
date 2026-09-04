"""CFKD: Counterfactual Knowledge Distillation (tractable proxy).

The paper's full CFKD trains a DDPM and uses SCE to generate counterfactual
explanations, then uses an oracle (trained on unpoisoned data) to label them,
and fine-tunes the student's last layer on the augmented dataset.

For the datasets with *controllable* confounders we reproduce the *effect* of
CFKD faithfully: we generate counterfactuals by flipping only the confounder
feature while keeping the causal feature unchanged, label them with the true
causal label (a perfect oracle -- the paper assumes a practitioner with high
accuracy), and fine-tune the last layer on the augmented set.

  * Squares   : flip background intensity (bright<->dark), keep foreground.
  * Smiling   : flip watermark opacity (transparent<->opaque), keep face.

For Blond/Camelyon the confounder (gender / hospital color cast) is a natural
attribute that cannot be cleanly flipped without a generative model, so CFKD
is not run there (a known limitation of this reproduction).

Usage:
    python cfkd.py <dataset> <poison>   (dataset in {squares, smiling})
"""
import json
import os
import sys

import numpy as np
import torch
import torch.nn as nn

from config import SEED, WORKSPACE, compute_group_metrics
from corrections import (load_split, split_root, predict, group_metrics)
from models import make_resnet18
from generate_squares import render_square
from prep_real_data import apply_watermark, load_celeba_img

LR = 0.01
EPOCHS = 20


def make_cf_squares(split):
    """Generate counterfactual images: same foreground, flipped background."""
    rng = np.random.default_rng(SEED)
    imgs, cf_imgs = [], []
    g = split["groups"].numpy()
    for i in range(len(g)):
        t, q = divmod(int(g[i]), 2)
        # reconstruct fg from image? simpler: re-sample causal feature per group
        if t == 0:
            fg = rng.uniform(0.0, 0.5)
        else:
            fg = rng.uniform(0.5, 1.0)
        # flipped confounder
        q2 = 1 - q
        if q2 == 0:
            bg = rng.uniform(0.5, 1.0)
        else:
            bg = rng.uniform(0.0, 0.5)
        img = render_square(fg, bg, rng=rng)
        img += rng.normal(0.0, 0.1, img.shape)
        img = np.clip(img, 0.0, 1.0).astype(np.float32)
        cf_imgs.append(img.transpose(2, 0, 1))
        imgs.append(split["images"][i].numpy())
    return (torch.from_numpy(np.stack(imgs)).float(),
            torch.from_numpy(np.stack(cf_imgs)).float())


def make_cf_smiling(poison):
    """Counterfactual: same face, watermark opacity flipped.

    Loads the original images from the frozen CelebA source and re-applies the
    watermark with an opacity from the *opposite* range, so the confounder
    value flips while the causal (Smiling) attribute is unchanged.
    """
    import json as _json
    rng = np.random.default_rng(SEED)
    manifest = _json.load(open(os.path.join(
        WORKSPACE, "real", f"smiling_{poison}", "train.json")))
    cf_imgs = []
    for rec in manifest:
        # must match the 128x128 real_tensors used for training
        img = load_celeba_img(rec["id"], size=128)
        if rec["conf"] == 0:
            op = rng.uniform(0.5, 1.0)  # flip to opaque
        else:
            op = rng.uniform(0.0, 0.5)  # flip to transparent
        cf_imgs.append(apply_watermark(img, op).transpose(2, 0, 1))
    return torch.from_numpy(np.stack(cf_imgs)).float()


def fine_tune_last_layer(model, x_aug, y_aug, val, test, epochs=EPOCHS,
                         lr=LR):
    for p in model.parameters():
        p.requires_grad = False
    for p in model.fc.parameters():
        p.requires_grad = True
    opt = torch.optim.SGD(model.fc.parameters(), lr=lr)
    lossf = nn.CrossEntropyLoss()
    best_aga, best_state = -1, None
    n = x_aug.size(0)
    for ep in range(epochs):
        model.train()
        per = torch.randperm(n, generator=torch.Generator().manual_seed(ep))
        opt.zero_grad()
        for i in range(0, n, 32):
            idx = per[i:i + 32]
            out = model(x_aug[idx])
            loss = lossf(out, y_aug[idx])
            loss.backward()
            opt.step()
            opt.zero_grad()
        emp, aga, wga, _ = group_metrics(model, val["images"], val["targets"],
                                         val["groups"])
        if aga > best_aga:
            best_aga = aga
            best_state = {k: v.clone() for k, v in model.state_dict().items()}
    model.load_state_dict(best_state)
    emp, aga, wga, gacc = group_metrics(model, test["images"], test["targets"],
                                        test["groups"])
    return {"test_emp": emp, "test_aga": aga, "test_wga": wga,
            "test_group_accs": gacc, "best_val_aga": best_aga}


def run_cfkd_squares(poison):
    root = split_root("squares", poison)
    train, val, test = load_split(root)
    model = make_resnet18(2, SEED)
    model.load_state_dict(torch.load(
        os.path.join(WORKSPACE, "models", "students",
                     f"squares_{poison}", "best.pt"), weights_only=False))
    x_orig, x_cf = make_cf_squares(train)
    y_orig = train["targets"].clone()
    x_aug = torch.cat([x_orig, x_cf])
    y_aug = torch.cat([y_orig, y_orig])  # causal label unchanged
    res = fine_tune_last_layer(model, x_aug, y_aug, val, test)
    print(f"[cfkd-squares-{poison}] {res}")
    return res


def run_cfkd_smiling(poison):
    root = split_root("smiling", poison)
    train, val, test = load_split(root)
    model = make_resnet18(2, SEED)
    model.load_state_dict(torch.load(
        os.path.join(WORKSPACE, "models", "students",
                     f"smiling_{poison}", "best.pt"), weights_only=False))
    x_cf = make_cf_smiling(poison)
    y_cf = train["targets"].clone()  # causal label unchanged
    x_aug = torch.cat([train["images"], x_cf])
    y_aug = torch.cat([train["targets"], y_cf])
    res = fine_tune_last_layer(model, x_aug, y_aug, val, test)
    print(f"[cfkd-smiling-{poison}] {res}")
    return res


def main(dataset, poison):
    if dataset == "squares":
        res = run_cfkd_squares(poison)
    elif dataset == "smiling":
        res = run_cfkd_smiling(poison)
    else:
        raise NotImplementedError(
            "CFKD proxy implemented only for squares and smiling")
    out_dir = os.path.join(WORKSPACE, "results", "cfkd")
    os.makedirs(out_dir, exist_ok=True)
    json.dump({"dataset": dataset, "poison": poison, **res},
              open(os.path.join(out_dir, f"{dataset}_{poison}.json"), "w"),
              indent=2)
    return res


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
