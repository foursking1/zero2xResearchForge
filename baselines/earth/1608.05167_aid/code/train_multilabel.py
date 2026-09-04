"""Multi-label 17-class training on the AID_MultiLabel frozen parquet.

Splits: fixed-seed 60/20/20. Model: IMAGENET-pretrained ResNet18, fine-tuned.
Loss: BCEWithLogitsLoss. Metrics: mAP, macro-F1, subset accuracy, per-class
binary stats.
"""
import argparse
import json
import os
import sys
import time

import numpy as np
import torch
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    f1_score,
    precision_recall_fscore_support,
)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from aid_common import (  # noqa: E402
    CLASS_NAMES_17,
    N_CLASSES_17,
    SEED,
    save_metrics,
)
from aid_pipeline import (  # noqa: E402
    ParquetMultilabelDataset,
    load_multilabel,
    make_model_multilabel,
    set_seed,
    split_isotropic,
)


def train_epoch(model, loader, opt, criterion, device):
    model.train()
    tot, n = 0.0, 0
    for x, y in loader:
        x, y = x.to(device), y.to(device)
        opt.zero_grad()
        out = model(x)
        loss = criterion(out, y)
        loss.backward()
        opt.step()
        tot += loss.item() * x.size(0)
        n += x.size(0)
    return tot / n


@torch.no_grad()
def evaluate(model, loader, device):
    model.eval()
    preds, ys = [], []
    for x, y in loader:
        x = x.to(device)
        out = torch.sigmoid(model(x)).cpu().numpy()
        preds.append(out)
        ys.append(y.numpy())
    return np.concatenate(preds, 0), np.concatenate(ys, 0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=int, default=30)
    ap.add_argument("--lr", type=float, default=1e-4)
    ap.add_argument("--batch-size", type=int, default=32)
    ap.add_argument("--size", type=int, default=224)
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--outdir", default=os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "results"))
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    ap.add_argument("--parquet", default=None,
                    help="explicit frozen parquet path")
    args = ap.parse_args()

    set_seed(args.seed)
    device = torch.device(args.device)
    print("device:", device)

    import aid_common
    images, labels = load_multilabel(
        args.parquet or aid_common.FROZEN_PARQUET, verify=True
    )
    print("dataset:", images.shape, labels.shape)
    split = split_isotropic(images, labels, seed=args.seed)
    print({k: len(v) for k, v in split.items()})

    tr = torch.utils.data.DataLoader(
        ParquetMultilabelDataset(images, labels, split["train"], "train", args.size),
        batch_size=args.batch_size, shuffle=True, num_workers=2,
    )
    va = torch.utils.data.DataLoader(
        ParquetMultilabelDataset(images, labels, split["val"], "val", args.size),
        batch_size=args.batch_size, shuffle=False, num_workers=2,
    )
    te = torch.utils.data.DataLoader(
        ParquetMultilabelDataset(images, labels, split["test"], "test", args.size),
        batch_size=args.batch_size, shuffle=False, num_workers=2,
    )

    model = make_model_multilabel("resnet18", N_CLASSES_17).to(device)
    pos = np.clip(labels[split["train"]].sum(0), 1, None)
    neg = len(split["train"]) - labels[split["train"]].sum(0)
    pos_w = torch.as_tensor(neg / pos, dtype=torch.float32).to(device)
    criterion = torch.nn.BCEWithLogitsLoss(pos_weight=pos_w)
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=args.epochs)

    best_ap, best_state = -1.0, None
    ckpt_path = os.path.join(args.outdir, "best_multilabel.pt")
    hist = []
    for ep in range(args.epochs):
        t0 = time.time()
        loss = train_epoch(model, tr, opt, criterion, device)
        vpred, vy = evaluate(model, va, device)
        per_ap = [
            average_precision_score(vy[:, c], vpred[:, c])
            for c in range(N_CLASSES_17)
        ]
        mAP_v = float(np.mean(per_ap))
        sched.step()
        hist.append({"epoch": ep, "loss": loss, "val_mAP": mAP_v})
        print(f"ep {ep:03d} loss {loss:.4f} val mAP {mAP_v:.4f} "
              f"({time.time()-t0:.1f}s)")
        if mAP_v > best_ap:
            best_ap = mAP_v
            best_state = {k: v.clone() for k, v in model.state_dict().items()}
            torch.save({"model": best_state, "val_mAP": mAP_v, "epoch": ep},
                       ckpt_path)
            print(f"  saved best multi-label ckpt (val mAP {mAP_v:.4f})")

    if best_state is None:
        best_state = {k: v.clone() for k, v in model.state_dict().items()}
    model.load_state_dict(best_state)
    tpred, ty = evaluate(model, te, device)

    per_ap = [
        average_precision_score(ty[:, c], tpred[:, c])
        for c in range(N_CLASSES_17)
    ]
    mAP = float(np.mean(per_ap))
    yhat = (tpred >= 0.5).astype(int)
    macro_f1 = float(f1_score(ty, yhat, average="macro", zero_division=0))
    subset_acc = float(accuracy_score(ty, yhat))
    micro_prec, micro_rec, micro_f1, _ = precision_recall_fscore_support(
        ty, yhat, average="micro", zero_division=0
    )
    P, R, F, _ = precision_recall_fscore_support(
        ty, yhat, average=None, zero_division=0
    )
    tn = ((1 - ty) * (1 - yhat)).sum(0)
    fp = ((1 - ty) * yhat).sum(0)
    fn = (ty * (1 - yhat)).sum(0)
    tp = (ty * yhat).sum(0)

    print("\n=== TEST ===")
    print(f"mAP {mAP:.4f} macro-F1 {macro_f1:.4f} subset acc {subset_acc:.4f} "
          f"micro-F1 {micro_f1:.4f}")

    rows = []
    for c in range(N_CLASSES_17):
        rows.append({
            "class": CLASS_NAMES_17[c],
            "num_true": int(ty[:, c].sum()),
            "tp": int(tp[c]), "fp": int(fp[c]),
            "fn": int(fn[c]), "tn": int(tn[c]),
            "precision": float(P[c]), "recall": float(R[c]),
            "f1": float(F[c]),
            "ap": float(per_ap[c]),
        })
    rows.append({
        "class": "ALL",
        "num_true": int(ty.sum()),
        "tp": int(tp.sum()), "fp": int(fp.sum()),
        "fn": int(fn.sum()), "tn": int(tn.sum()),
        "precision": float(micro_prec), "recall": float(micro_rec),
        "f1": float(micro_f1),
        "ap": mAP,
    })
    os.makedirs(args.outdir, exist_ok=True)
    ev_path = os.path.join(args.outdir, "evidence_table.csv")
    import pandas as pd
    pd.DataFrame(rows).to_csv(ev_path, index=False)
    print("wrote", ev_path)

    # Per-class AP and threshold plots saved to evidence/ via JSON
    metrics = {
        "mAP": round(mAP, 4),
        "macro_f1": round(macro_f1, 4),
        "subset_accuracy": round(subset_acc, 4),
        "micro_f1": round(float(micro_f1), 4),
        "per_class_ap": {CLASS_NAMES_17[c]: round(per_ap[c], 4)
                          for c in range(N_CLASSES_17)},
        "per_class_count": {CLASS_NAMES_17[c]: int(labels[:, c].sum())
                            for c in range(N_CLASSES_17)},
        "seed": args.seed,
        "split_sizes": {k: int(len(v)) for k, v in split.items()},
        "backbone": "resnet18_pretrained_finetuned",
        "input_size": args.size,
        "epochs": args.epochs,
        "test_threshold": 0.5,
        "history": hist,
    }
    save_metrics(metrics, os.path.join(args.outdir, "metrics_multilabel.json"))

    # Save test predictions for later analysis/plots
    np.savez(
        os.path.join(args.outdir, "multilabel_test_preds.npz"),
        pred=tpred, true=ty,
    )


if __name__ == "__main__":
    main()