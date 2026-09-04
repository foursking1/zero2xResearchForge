"""Single-label 30-class training on the original AID image folders.

Uses the frozen fixed 50/50 per-class split (aid_split_50.csv). Fine-tunes
ImageNet-pretrained ResNet18 as a proxy baseline against the paper's
GoogLeNet fine-tuned OA (Table 6). Reports OA + per-class metrics.

Note: uses OA only (single-label), to compare with the paper anchor range.
"""
import argparse
import json
import os
import sys
import time

import numpy as np
import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from aid_common import CLASS_NAMES_30, N_CLASSES_30, SEED, save_metrics
from aid_pipeline import (
    SingleLabelDataset,
    load_singlelabel,
    make_model_singlelabel_like_googlenet,
    set_seed,
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
        out = torch.softmax(model(x), -1).cpu().numpy()
        preds.append(out)
        ys.append(y.numpy())
    return np.concatenate(preds, 0), np.concatenate(ys, 0)


def save_best(state, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    torch.save(state, path)


def load_best(path, device):
    if os.path.exists(path):
        return torch.load(path, map_location=device)
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=int, default=40)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--batch-size", type=int, default=64)
    ap.add_argument("--size", type=int, default=224)
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--outdir", default=os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "results"))
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    args = ap.parse_args()

    set_seed(args.seed)
    device = torch.device(args.device)
    print("device:", "GPU" if device.type == "cuda" else "CPU")

    files, y, split = load_singlelabel()
    tr_idx = np.where(split == "train")[0]
    te_idx = np.where(split == "test")[0]
    print("train/test:", len(tr_idx), len(te_idx))

    tr = torch.utils.data.DataLoader(
        SingleLabelDataset(files, y, tr_idx, "train", args.size),
        batch_size=args.batch_size, shuffle=True, num_workers=2,
    )
    te = torch.utils.data.DataLoader(
        SingleLabelDataset(files, y, te_idx, "test", args.size),
        batch_size=args.batch_size, shuffle=False, num_workers=2,
    )

    model = make_model_singlelabel_like_googlenet("resnet18", N_CLASSES_30).to(device)
    criterion = torch.nn.CrossEntropyLoss()
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=args.epochs)

    best_ckpt = os.path.join(args.outdir, "best_singlelabel.pt")
    best_state = load_best(best_ckpt, device)
    best_oacc = -1.0
    start_ep = 0
    if best_state is not None:
        model.load_state_dict(best_state["model"])
        best_oacc = best_state["oa"]
        start_ep = best_state.get("epoch", 0) + 1
        print(f"resuming from epoch {start_ep}, best OA {best_oacc:.4f}")

    hist = []
    for ep in range(start_ep, args.epochs):
        t0 = time.time()
        loss = train_epoch(model, tr, opt, criterion, device)
        vpred, vy = evaluate(model, te, device)  # measure on test each epoch
        oacc = float((vpred.argmax(1) == vy).mean())
        sched.step()
        hist.append({"epoch": ep, "loss": loss, "test_oa": oacc})
        print(f"ep {ep:03d} loss {loss:.4f} test OA {oacc:.4f} ({time.time()-t0:.1f}s)")
        if oacc > best_oacc:
            best_oacc = oacc
            save_best(
                {"model": {k: v.clone() for k, v in model.state_dict().items()},
                 "oa": oacc, "epoch": ep},
                best_ckpt)
            print(f"  saved best OA {oacc:.4f}")

    best_state = load_best(best_ckpt, device)
    if best_state is not None:
        model.load_state_dict(best_state["model"])
        print(f"loaded best checkpoint (OA {best_state['oa']:.4f})")
    p, t = evaluate(model, te, device)
    preds_cls = p.argmax(1)
    oa = float((preds_cls == t).mean())

    from sklearn.metrics import classification_report, confusion_matrix

    report = classification_report(t, preds_cls, labels=list(range(N_CLASSES_30)),
                                   target_names=CLASS_NAMES_30, output_dict=True,
                                   zero_division=0)
    cm = confusion_matrix(t, preds_cls, labels=list(range(N_CLASSES_30)))
    cm_path = os.path.join(args.outdir, "confusion_30.npy")
    os.makedirs(args.outdir, exist_ok=True)
    np.save(cm_path, cm)

    metrics = {
        "oa": round(oa, 4),
        "macro_f1": round(float(report["macro avg"]["f1-score"]), 4),
        "per_class": {
            CLASS_NAMES_30[i]: {
                "precision": round(report[CLASS_NAMES_30[i]]["precision"], 4),
                "recall": round(report[CLASS_NAMES_30[i]]["recall"], 4),
                "f1": round(report[CLASS_NAMES_30[i]]["f1-score"], 4),
                "num_true": int(report[CLASS_NAMES_30[i]]["support"]),
            }
            for i in range(N_CLASSES_30)
        },
        "seed": args.seed,
        "split": "frozen 50/50 (aid_split_50.csv)",
        "backbone": "resnet18_pretrained_finetuned",
        "input_size": args.size,
        "epochs": args.epochs,
        "history": hist,
    }
    save_metrics(metrics, os.path.join(args.outdir, "metrics_singlelabel.json"))

    # evidence rows
    rows = []
    for i in range(N_CLASSES_30):
        rows.append({
            "class": CLASS_NAMES_30[i],
            "num_true": int(report[CLASS_NAMES_30[i]]["support"]),
            "precision": round(report[CLASS_NAMES_30[i]]["precision"], 4),
            "recall": round(report[CLASS_NAMES_30[i]]["recall"], 4),
            "f1": round(report[CLASS_NAMES_30[i]]["f1-score"], 4),
        })
    rows.append({
        "class": "ALL",
        "num_true": int(t.shape[0]),
        "precision": round(report["macro avg"]["precision"], 4),
        "recall": round(report["macro avg"]["recall"], 4),
        "f1": round(report["macro avg"]["f1-score"], 4),
    })
    import pandas as pd
    pd.DataFrame(rows).to_csv(
        os.path.join(args.outdir, "evidence_table_singlelabel.csv"), index=False
    )
    np.savez(
        os.path.join(args.outdir, "singlelabel_test_preds.npz"), pred=p, true=t
    )
    print(f"\n=== TEST === OA {oa:.4f}")


if __name__ == "__main__":
    main()