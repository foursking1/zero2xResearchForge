"""Control experiment: a small CNN trained FROM SCRATCH (no ImageNet init).

This serves as a lower-bound / context control for the claim: without external
pretraining a compact CNN needs large compute and reaches lower accuracy, which
puts the paper's from-scratch VGG-16 result in perspective. Quick to run on CPU.
"""
import argparse
import os
import sys
import time

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (CHECKPOINT_DIR, N_L1, N_L2, RESULTS_DIR, SEED, load_labels,  # noqa: E402
                    normalize, set_seed)
from torchvision import transforms  # noqa: E402
from train_utils import make_augment  # noqa: E402


class SmallCNN(nn.Module):
    def __init__(self):
        super().__init__()
        self.stem = nn.Sequential(
            nn.Conv2d(3, 32, 3, padding=1), nn.BatchNorm2d(32), nn.ReLU(),
            nn.Conv2d(32, 32, 3, padding=1), nn.BatchNorm2d(32), nn.ReLU(),
            nn.MaxPool2d(2),  # 112
            nn.Conv2d(32, 64, 3, padding=1), nn.BatchNorm2d(64), nn.ReLU(),
            nn.Conv2d(64, 64, 3, padding=1), nn.BatchNorm2d(64), nn.ReLU(),
            nn.MaxPool2d(2),  # 56
            nn.Conv2d(64, 128, 3, padding=1), nn.BatchNorm2d(128), nn.ReLU(),
            nn.Conv2d(128, 128, 3, padding=1), nn.BatchNorm2d(128), nn.ReLU(),
            nn.MaxPool2d(2),  # 28
            nn.Conv2d(128, 256, 3, padding=1), nn.BatchNorm2d(256), nn.ReLU(),
            nn.Conv2d(256, 256, 3, padding=1), nn.BatchNorm2d(256), nn.ReLU(),
            nn.MaxPool2d(2),  # 14
            nn.Conv2d(256, 512, 3, padding=1), nn.BatchNorm2d(512), nn.ReLU(),
            nn.MaxPool2d(2),  # 7
            nn.AdaptiveAvgPool2d(1),
        )
        self.fc2 = nn.Linear(512, N_L2)
        self.fc1 = nn.Linear(512, N_L1)

    def embed_and_logits(self, x):
        f = torch.flatten(self.stem(x), 1)
        return self.fc2(f), self.fc1(f), f


def augment_resized(x_uint8, transform, res):
    """Per-sample PIL transform then resize to `res` (same normalization as eval)."""
    out = torch.empty(x_uint8.shape[0], 3, res, res)
    for i in range(x_uint8.shape[0]):
        pil = transforms.ToPILImage()(x_uint8[i])
        pil = transform(pil).resize((res, res))
        arr = normalize(np.asarray(pil))
        out[i] = torch.tensor(arr.transpose(2, 0, 1))
        pil.close()
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=int, default=10)
    ap.add_argument("--lr", type=float, default=0.05)
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--res", type=int, default=224,
                    help="training input resolution (smaller = faster)")
    ap.add_argument("--out", type=str,
                    default=os.path.join(CHECKPOINT_DIR, "smallcnn_fromscratch.pt"))
    args = ap.parse_args()

    set_seed(SEED)
    torch.set_num_threads(int(os.environ.get("TORCH_THREADS","10")))
    imgmem = np.load(os.path.join(RESULTS_DIR, "images_224.memmap"), mmap_mode="r")
    lab = load_labels()
    l1, l2, split = lab["label_1"], lab["label_2"], lab["split"]
    tr, te = split == "train", split == "test"
    idx_tr = np.where(tr)[0]

    model = SmallCNN()
    opt = torch.optim.SGD(model.parameters(), lr=args.lr, momentum=0.9,
                          weight_decay=5e-4)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(
        opt, T_max=((args.epochs * idx_tr.size) // args.batch) + 1)
    transform = make_augment()
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    t0 = time.time()
    best = -1
    for ep in range(1, args.epochs + 1):
        model.train()
        rng = np.random.RandomState(SEED + 100 + ep)
        order = rng.permutation(idx_tr)
        tot = 0.0; cnt = 0
        for s in range(0, order.size, args.batch):
            ids = order[s:s + args.batch]
            xb = np.ascontiguousarray(imgmem[ids])
            y2 = torch.from_numpy(l2[ids].astype(np.int64))
            y1 = torch.from_numpy(l1[ids].astype(np.int64))
            xt = augment_resized(xb, transform, args.res)
            logits2, logits1, _ = model.embed_and_logits(xt)
            loss = F.cross_entropy(logits2, y2) + 0.3 * F.cross_entropy(logits1, y1)
            opt.zero_grad(); loss.backward(); opt.step(); sched.step()
            tot += loss.item(); cnt += 1
            if cnt % 50 == 0:
                print(f"  ep{ep} it={cnt} loss={loss.item():.3f} "
                      f"({time.time()-t0:.0f}s)", flush=True)
        print(f"[scratch] ep{ep} loss={tot/cnt:.3f} ({time.time()-t0:.0f}s)", flush=True)
        # quick eval
        te_idx = np.where(te)[0]
        pred2, pred1 = [], []
        model.eval()
        with torch.no_grad():
            for s in range(0, te_idx.size, args.batch):
                ids = te_idx[s:s + args.batch]
                xb = np.ascontiguousarray(imgmem[ids])
                xt = augment_resized(xb, torch.nn.Identity(), args.res)
                lg2, lg1, _ = model.embed_and_logits(xt)
                pred2.append(lg2.argmax(1).numpy()); pred1.append(lg1.argmax(1).numpy())
        p2 = np.concatenate(pred2); p1 = np.concatenate(pred1)
        oa = float((p2 == l2[te]).mean())
        l1a = float((p1 == l1[te]).mean())
        print(f"[scratch] ep{ep} test OA={oa*100:.3f}% label1={l1a*100:.2f}%", flush=True)
        if oa > best:
            best = oa; torch.save(model.state_dict(), args.out)
    print(f"[scratch] done best OA {best*100:.3f}% in {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()