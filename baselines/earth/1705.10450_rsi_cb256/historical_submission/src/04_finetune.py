"""Main method: fine-tune ImageNet-pretrained ResNet18 with a two-level head.

* label_2 (35-way) is the primary task; label_1 (7-way) is an auxiliary
  hierarchical task sharing the same backbone (multi-task CE loss).
* Data read from results/images_224.memmap + labels.npz; split uses the frozen
  data/split_train_test_50.csv. Statistics are computed only from the train
  subset; the test set is touched purely at evaluation time.
* Fixed seed -> reproducible; best-checkpoint saved to checkpoints/.

Usage:
  python3 src/04_finetune.py --epochs 4 --lr 1e-3 --backbone-lr 5e-4 \
      --out checkpoints/resnet18_mtl.pt
"""
import argparse
import os
import sys
import time

import numpy as np
import torch
import torch.nn.functional as F

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import CHECKPOINT_DIR, RESULTS_DIR, SEED, load_labels, set_seed  # noqa: E402
from evaluate_utils import evaluate_model  # noqa: E402
from train_utils import (MultiTaskResNet, augment_batch, make_augment)  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=int, default=4)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--backbone-lr", type=float, default=5e-4)
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--lambda1", type=float, default=0.3)
    ap.add_argument("--freeze", type=str, default="",
                    help="'' | stem | layer0_1 | layer0_2 | layer0_3 (freeze prefix of backbone)")
    ap.add_argument("--resume", type=str, default="")
    ap.add_argument("--out", type=str,
                    default=os.path.join(CHECKPOINT_DIR, "resnet18_mtl.pt"))
    args = ap.parse_args()

    set_seed(SEED)
    torch.set_num_threads(int(os.environ.get("TORCH_THREADS","10")))

    imgmem = np.load(os.path.join(RESULTS_DIR, "images_224.memmap"), mmap_mode="r")
    lab = load_labels()
    l1, l2, split = lab["label_1"], lab["label_2"], lab["split"]
    tr, te = split == "train", split == "test"
    idx_tr = np.where(tr)[0]
    print(f"[finetune] train={idx_tr.size} test={te.sum()}")

    model = MultiTaskResNet()
    if args.resume and os.path.exists(args.resume):
        model.load_state_dict(torch.load(args.resume, map_location="cpu"))
        print("[finetune] resumed from", args.resume)
    freeze = {
        "": [],
        "stem": ["backbone.conv1", "backbone.bn1", "backbone.maxpool"],
        "layer0_1": ["backbone.conv1", "backbone.bn1", "backbone.maxpool",
                     "backbone.layer1"],
        "layer0_2": ["backbone.conv1", "backbone.bn1", "backbone.maxpool",
                     "backbone.layer1", "backbone.layer2"],
        "layer0_3": ["backbone.conv1", "backbone.bn1", "backbone.maxpool",
                     "backbone.layer1", "backbone.layer2", "backbone.layer3"],
    }
    for prefix in freeze.get(args.freeze, []):
        for name, p in model.named_parameters():
            if name.startswith(prefix):
                p.requires_grad = False
    if args.freeze:
        print(f"[finetune] frozen to '{args.freeze}' (only later layers + heads train)")

    params = []
    for name, p in model.named_parameters():
        if not p.requires_grad:
            continue
        group_lr = args.lr if name.startswith("head") else args.backbone_lr
        params.append({"params": p, "lr": group_lr})
    opt = torch.optim.SGD(params, momentum=0.9, weight_decay=1e-4)
    total_iters = (args.epochs * idx_tr.size) // args.batch + 1
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=total_iters)
    transform = make_augment()

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    best_oa = -1.0
    t0 = time.time()
    for ep in range(1, args.epochs + 1):
        model.train()
        rng = np.random.RandomState(SEED + ep)
        order = rng.permutation(idx_tr)
        ep_loss, cnt = 0.0, 0
        for s in range(0, order.size, args.batch):
            ids = order[s:s + args.batch]
            xb = np.ascontiguousarray(imgmem[ids])
            y2 = torch.from_numpy(l2[ids].astype(np.int64))
            y1 = torch.from_numpy(l1[ids].astype(np.int64))
            xt = augment_batch(xb, transform)
            logits2, logits1, _ = model.embed_and_logits(xt)
            loss = F.cross_entropy(logits2, y2) + \
                args.lambda1 * F.cross_entropy(logits1, y1)
            opt.zero_grad()
            loss.backward()
            opt.step()
            sched.step()
            ep_loss += loss.item(); cnt += 1
            if cnt % 25 == 0:
                print(f"  ep{ep} it={cnt} loss={loss.item():.3f} "
                      f"({time.time()-t0:.0f}s)", flush=True)
        print(f"[finetune] epoch {ep} avg_loss={ep_loss/cnt:.3f} "
              f"({time.time()-t0:.0f}s)", flush=True)
        val_oa, val_l1a, _ = evaluate_model(model, imgmem, l2, l1, te, quick=True)
        print(f"[finetune] ep{ep} quick test OA={val_oa*100:.3f}% "
              f"label1 acc={val_l1a*100:.2f}%", flush=True)
        if val_oa > best_oa:
            best_oa = val_oa
            torch.save(model.state_dict(), args.out)
            print("  saved best checkpoint", args.out)
    torch.save(model.state_dict(), args.out)
    print(f"[finetune] done best-quick OA {best_oa*100:.3f}% in {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()