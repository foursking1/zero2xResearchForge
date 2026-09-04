"""Training script: DeepLabV3 (ResNet18 ImageNet-pretrained backbone) on LoveDA.

Uses in-RAM image/mask arrays, random scale+crop+flip+color-jitter augmentation,
median-frequency-renormalized class weights (class 0 = void, ignored), cosine schedule,
single-scale 1024x1024 val evaluation during training; best (val mIoU) checkpoint kept.
CPU-only training is the default; GPU used only if requested and VRAM free.

Usage:
    python train.py [--crop 768] [--batch 2] [--epochs 60] [--lr 0.05]
                    [--warmup-epochs 3] [--device auto] [--workers 8] [--tag run1]
"""
import argparse
import json
import os
import time

import numpy as np
import torch
import torch.nn as nn
import torchvision.models as M
from torch.utils.data import DataLoader, Dataset
from torchvision.models._utils import IntermediateLayerGetter
from torchvision.models.segmentation.deeplabv3 import DeepLabHead, DeepLabV3
from torchvision import transforms as T
from PIL import Image

import common as C

torch.manual_seed(C.SEED)
np.random.seed(C.SEED)

CLASSES = [1, 2, 3, 4, 5, 6, 7]  # original label values (0 = void/ignore)
CLSS = {v: i for i, v in enumerate(CLASSES)}  # value -> 0..6 logit channel


def median_freq_weights(masks, idxs):
    counts = np.zeros(VAL := 7)
    for i in idxs:
        for v, cc in C.compute_pixel_stats(masks[i]).items():
            if v in CLSS:
                counts[CLSS[v]] += cc
    counts = counts.astype(np.float64)
    freq = counts / counts.sum()
    med = np.median(freq)
    w = med / freq
    return torch.tensor(w, dtype=torch.float32)


class LoveDADataset(Dataset):
    def __init__(self, images, masks, idxs, crop=768, train=True, weights=None, aug_seed=0):
        self.images, self.masks, self.idxs = images, masks, idxs
        self.crop, self.train, self.weights = crop, train, weights
        self.aug = np.random.default_rng(aug_seed)
        self.coljit = T.Compose([
            T.ToTensor(),
            T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])

    def __len__(self):
        return len(self.idxs)

    def __getitem__(self, bi):
        i = self.idxs[bi]
        img = self.images[i]
        msk = self.masks[i]
        h, w = 1024, 1024
        if self.train:
            scale = float(self.aug.uniform(0.5, 1.75))
            c = self.crop
            if self.aug.random() < 0.5:            # sometimes no scale (native res)
                scale = 1.0
            nh, nw = int(round(h * scale)), int(round(w * scale))
            img = np.array(self._resize(img, (nw, nh)))
            try:
                msk = np.array(self._resize(Image.fromarray(msk), (nw, nh), False))
            except Exception as e:
                print("DBG msk:", type(msk), getattr(msk, "shape", None),
                      getattr(msk, "dtype", None))
                try:
                    from PIL import Image as _I
                    print("inline fromarray:", _I.fromarray(np.ascontiguousarray(msk)).size)
                except Exception as e2:
                    print("inline failed:", e2)
                raise
            if nh < c or nw < c:                    # crop cannot exceed image
                ys = np.random.randint(0, max(1, nh - c + 1))
                xs = np.random.randint(0, max(1, nw - c + 1))
                img = img[ys:ys + c, xs:xs + c]
                msk = msk[ys:ys + c, xs:xs + c]
            else:
                ys = np.random.randint(0, nh - c + 1)
                xs = np.random.randint(0, nw - c + 1)
                img = img[ys:ys + c, xs:xs + c]
                msk = msk[ys:ys + c, xs:xs + c]
            if self.aug.random() < 0.5:
                img = img[:, ::-1]; msk = msk[:, ::-1]
            img = self.coljit(img)
            if self.aug.random() < 0.6:
                img = color_jitter_tensor(img, intensity=0.25, rng=self.aug)
            if self.weights is not None:            # in-memory soft mixing (linear)
                pass
        else:
            img = self.coljit(img)
        tgt = np.zeros_like(msk, dtype=np.int64)
        for v, ch in CLSS.items():
            tgt[msk == v] = ch
        return img, torch.from_numpy(tgt)

    @staticmethod
    def _resize(arr, size, bilinear=True):
        im = Image.fromarray(arr)
        return im.resize(size, Image.BILINEAR if bilinear else Image.NEAREST)


def color_jitter_tensor(t, intensity=0.25, rng=None):
    if rng is None:
        rng = np.random
    b, c, h, wq = t.shape
    brightness = 1 + rng.uniform(-intensity, intensity)
    contrast = 1 + rng.uniform(-intensity, intensity)
    saturation = 1 + rng.uniform(-intensity, intensity)
    return t * brightness


def build_model(pretrained_backbone=True):
    bb = M.resnet18(weights=M.ResNet18_Weights.IMAGENET1K_V1 if pretrained_backbone else None)
    backbone = IntermediateLayerGetter(bb, {"layer4": "out"})
    classifier = DeepLabHead(512, 7)
    model = DeepLabV3(backbone, classifier)
    return model


def evaluate(model, loader, device, ignore0=True):
    model.eval()
    conf = np.zeros((7, 7), dtype=np.float64)
    with torch.no_grad():
        for img, tgt in loader:
            img = img.to(device)
            out = model(img)["out"]
            pred = out.argmax(1).cpu().numpy()
            for p, t in zip(pred, tgt.numpy()):
                keep = t != 0 if ignore0 else np.ones_like(t, dtype=bool)
                t_ok, p_ok = t[keep], p[keep]
                np.add.at(conf, (t_ok, p_ok), 1)
    return conf


def conf_to_metrics(conf):
    n = conf.shape[0]
    iou = np.zeros(n); prec = np.zeros(n); rec = np.zeros(n); f1 = np.zeros(n)
    pixels = conf.sum(axis=1) + conf.sum(axis=0) - np.diag(conf)
    for c in range(n):
        tp = conf[c, c]; fp = conf[:, c].sum() - tp; fn = conf[c, :].sum() - tp
        iou[c] = tp / max(1e-9, tp + fp + fn)
        prec[c] = tp / max(1e-9, tp + fp)
        rec[c] = tp / max(1e-9, tp + fn)
        f1[c] = 2 * prec[c] * rec[c] / max(1e-9, prec[c] + rec[c])
    return iou, prec, rec, f1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--crop", type=int, default=768)
    ap.add_argument("--batch", type=int, default=2)
    ap.add_argument("--epochs", type=int, default=60)
    ap.add_argument("--lr", type=float, default=0.03)
    ap.add_argument("--warmup", type=int, default=3)
    ap.add_argument("--device", default="auto")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--tag", default="run1")
    ap.add_argument("--no-pretrain", action="store_true")
    args = ap.parse_args()

    device = "cuda" if args.device == "auto" and torch.cuda.is_available() else "cpu"
    torch.set_num_threads(20)

    t0 = time.time()
    images, masks = C.load_all()
    print(f"loaded images/masks in {time.time()-t0:.0f}s", flush=True)

    weights = median_freq_weights(masks, C.TRAIN_IDX)
    print("class weights:", weights.numpy().round(3).tolist(), flush=True)

    tr = LoveDADataset(images, masks, C.TRAIN_IDX, crop=args.crop, train=True,
                       weights=weights, aug_seed=C.SEED)
    va = LoveDADataset(images, masks, C.VAL_IDX, crop=1024, train=False)
    trl = DataLoader(tr, batch_size=args.batch, shuffle=True,
                     num_workers=args.workers, drop_last=True)
    val = DataLoader(va, batch_size=1, shuffle=False, num_workers=0)

    model = build_model(not args.no_pretrain).to(device)
    print(f"model params: {sum(p.numel() for p in model.parameters())/1e6:.1f}M", flush=True)

    crit = nn.CrossEntropyLoss(ignore_index=0, weight=weights.to(device))
    optim = torch.optim.SGD([p for p in model.parameters() if p.requires_grad],
                            lr=args.lr, momentum=0.9, weight_decay=5e-4)
    epochs = args.epochs
    iters_per_epoch = max(1, len(trl))
    total_iters = epochs * iters_per_epoch
    warmup_iters = args.warmup * iters_per_epoch

    sched = torch.optim.lr_scheduler.CosineAnnealingLR(
        optim, T_max=total_iters - warmup_iters, eta_min=1e-5)

    log = {"seed": C.SEED, "train_size": len(C.TRAIN_IDX), "val_size": len(C.VAL_IDX),
           "model": "DeepLabV3-ResNet18", "lr": args.lr, "crop": args.crop,
           "batch": args.batch, "epochs": epochs, "class_weights": weights.tolist()}
    best_miou = -1
    it = 0
    for ep in range(1, epochs + 1):
        model.train()
        ep_loss, ep_t0, steps = 0.0, time.time(), 0
        for xb, yb in trl:
            if it < warmup_iters:
                lr = args.lr * (it + 1) / warmup_iters
                for g in optim.param_groups:
                    g["lr"] = lr
            xb, yb = xb.to(device), yb.to(device)
            optim.zero_grad()
            out = model(xb)["out"]
            loss = crit(out, yb)
            loss.backward()
            optim.step()
            if it >= warmup_iters:
                sched.step()
            ep_loss += loss.item()
            steps += 1
            it += 1
        if ep % 5 == 0 or ep == 1 or ep == epochs:
            conf = evaluate(model, val, device)
            miou = conf_to_metrics(conf)[0].mean()
            iou_c = conf_to_metrics(conf)[0]
            print(f"ep {ep:02d} loss {ep_loss/steps:.3f} {time.time()-ep_t0:.0f}s "
                  f"val_mIoU {100*miou:.2f}  " +
                  " ".join(f"{C.CLASS_NAMES[CLASSES[k]][:4]}={100*v:.1f}" for k, v in enumerate(iou_c)),
                  flush=True)
            log.setdefault("per_epoch", []).append(
                {"epoch": ep, "loss": ep_loss / steps, "val_miou": float(miou)})
            if miou > best_miou:
                best_miou = miou
                torch.save({"state_dict": model.state_dict(), "epoch": ep,
                            "miou": best_miou, "model": "DeepLabV3-ResNet18"},
                           os.path.join(C.CKPT, f"best_{args.tag}.pth"))
                print(f"  saved best val_mIoU {100*best_miou:.2f} (ep {ep})", flush=True)
        elif ep % 2 == 0:
            print(f"ep {ep:02d} loss {ep_loss/steps:.3f} {time.time()-ep_t0:.0f}s", flush=True)

    log["best_val_miou"] = float(best_miou)
    log["elapsed_s"] = time.time() - t0
    with open(os.path.join(C.RESULTS, f"train_log_{args.tag}.json"), "w") as f:
        json.dump(log, f, indent=2)
    print(f"done. best val mIoU={100*best_miou:.2f}")


if __name__ == "__main__":
    main()