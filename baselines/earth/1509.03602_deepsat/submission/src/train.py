#!/usr/bin/env python3
"""Train + evaluate a CNN on the SAT-6 frozen data (arXiv:1509.03602).

Pipeline (all numbers derive from the frozen official SAT-6 Test split):
  1. reads the cached .npz produced by prepare_data.py which embeds the
     fixed-seed 70/15/15 stratified split;
  2. trains a small CNN on the train subset (CPU),
     selecting hyper-parameters / best epoch by the VAL subset only;
  3. evaluates ONCE on the held-out test subset and writes:
       - submission/results/metrics.json
       - submission/results/evidence_table.csv  (per-class + overall)
       - submission/results/confusion_matrix.csv/.npy
       - submission/figure/confusion_matrix.png

Usage:
    python train.py [--cache ../data_cache] [--epochs 30] [--batch-size 512]
        [--seed 42] [--device cpu] [--out ../..]
"""
import argparse
import json
import os
import time

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from common import CLASS_NAMES, N_CLASSES, decode_images, load_dataframe, resolve_data_path


def make_model():
    return nn.Sequential(
        nn.Conv2d(3, 32, 3, padding=1), nn.BatchNorm2d(32), nn.ReLU(inplace=True),
        nn.Conv2d(32, 32, 3, padding=1), nn.BatchNorm2d(32), nn.ReLU(inplace=True),
        nn.MaxPool2d(2),
        nn.Conv2d(32, 64, 3, padding=1), nn.BatchNorm2d(64), nn.ReLU(inplace=True),
        nn.Conv2d(64, 64, 3, padding=1), nn.BatchNorm2d(64), nn.ReLU(inplace=True),
        nn.MaxPool2d(2),
        nn.Conv2d(64, 128, 3, padding=1), nn.BatchNorm2d(128), nn.ReLU(inplace=True),
        nn.Conv2d(128, 128, 3, padding=1), nn.BatchNorm2d(128), nn.ReLU(inplace=True),
        nn.MaxPool2d(2),
        nn.Flatten(),
        nn.Dropout(0.35),
        nn.Linear(1152, 256), nn.ReLU(inplace=True),
        nn.Dropout(0.35),
        nn.Linear(256, N_CLASSES),
    )


class Sat6Dataset(torch.utils.data.Dataset):
    def __init__(self, images, labels, mean, std, train=False):
        x = images.astype(np.float32) / 255.0
        x = (x - mean.reshape(1, 1, 1, 3)) / std.reshape(1, 1, 1, 3)
        self.x = torch.from_numpy(x).permute(0, 3, 1, 2)
        self.y = torch.from_numpy(labels.astype(np.int64))
        self.train = train

    def __len__(self):
        return len(self.y)

    def __getitem__(self, i):
        x, y = self.x[i], self.y[i]
        if self.train:
            # land-cover labels are flip-invariant -> safe geometric augmentation
            if torch.rand(1).item() < 0.5:
                x = torch.flip(x, dims=[2])
            if torch.rand(1).item() < 0.5:
                x = torch.flip(x, dims=[1])
        return x, y


@torch.no_grad()
def evaluate(model, loader, device):
    model.eval()
    preds, gts = [], []
    for x, y in loader:
        x = x.to(device, non_blocking=True)
        preds.append(model(x).argmax(1).cpu())
        gts.append(y)
    preds = torch.cat(preds).numpy()
    gts = torch.cat(gts).numpy()
    return preds, gts


def metrics(preds, gts):
    """Per-class and overall metrics. All computed from raw confusion counts."""
    n = len(CLASS_NAMES)
    tp = np.zeros(n, dtype=np.int64)
    fp = np.zeros(n, dtype=np.int64)
    fn = np.zeros(n, dtype=np.int64)
    tn = np.zeros(n, dtype=np.int64)
    for c in range(n):
        tp[c] = int(((preds == c) & (gts == c)).sum())
        fp[c] = int(((preds == c) & (gts != c)).sum())
        fn[c] = int(((preds != c) & (gts == c)).sum())
        tn[c] = int(((preds != c) & (gts != c)).sum())
    cm = np.zeros((n, n), dtype=np.int64)
    for p, g in zip(preds, gts):
        cm[g, p] += 1
    accuracy = tp.sum() / len(gts) if len(gts) else 0.0
    precision = np.divide(tp, tp + fp, out=np.zeros(n, dtype=float), where=(tp + fp) > 0)
    recall = np.divide(tp, tp + fn, out=np.zeros(n, dtype=float), where=(tp + fn) > 0)
    f1 = np.divide(2 * precision * recall, precision + recall,
                   out=np.zeros(n, dtype=float), where=(precision + recall) > 0)
    per_class_acc = np.array([(tp[c] + tn[c]) / len(gts) for c in range(n)])
    macro_f1 = float(f1.mean())
    return {
        "tp": tp, "fp": fp, "tn": tn, "fn": fn, "cm": cm,
        "precision": precision, "recall": recall, "f1": f1,
        "per_class_accuracy": per_class_acc,
        "accuracy": float(accuracy), "macro_f1": macro_f1,
    }


def pick_device(choice):
    """auto -> GPU only when enough VRAM is free (shared-box safety)."""
    if choice.startswith("cuda"):
        return torch.device(choice.split("cuda")[1] or "cuda")
    if choice == "cpu":
        return torch.device("cpu")
    if torch.cuda.is_available():
        free = torch.cuda.mem_get_info()[0] / 1024**2
        if free >= 2500:  # conservative: enough VRAM free for a small model
            return torch.device("cuda:0")
        print(f"[device] GPU present but only {free:.0f}MB free (<2500MB); using CPU")
    return torch.device("cpu")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=None, help="path to frozen sat6 parquet")
    ap.add_argument("--cache", default=None, help="data_cache dir written by prepare_data.py")
    ap.add_argument("--epochs", type=int, default=30)
    ap.add_argument("--batch-size", type=int, default=512)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--wd", type=float, default=1e-4)
    ap.add_argument("--patience", type=int, default=7,
                    help="early-stop epochs without val improvement")
    ap.add_argument("--device", default="auto",
                    help="auto|cpu|cuda[:n]. auto uses cuda only if >=2.5GB VRAM free")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", default=None, help="submission/ root that holds results/ and figure/")
    ap.add_argument("--toy", action="store_true", help="run 2 epochs on a slice for smoke tests")
    args = ap.parse_args()

    src_dir = os.path.dirname(os.path.abspath(__file__))
    cache_dir = args.cache or os.path.join(src_dir, "..", "data_cache")
    npz = np.load(os.path.join(cache_dir, "sat6_split.npz"), allow_pickle=True)
    mean, std = npz["mean"], npz["std"]
    train_idx, val_idx, test_idx = npz["train_idx"], npz["val_idx"], npz["test_idx"]
    with open(os.path.join(cache_dir, "split_stats.json")) as f:
        split_stats = json.load(f)

    data_path = resolve_data_path(args.data)
    print(f"[train] decoding pixels from frozen parquet: {data_path}")
    t_load = time.time()
    df = load_dataframe(data_path)
    labels = df["label"].to_numpy(np.int64)
    images = decode_images(df)
    print(f"[train] {len(df)} images decoded in {time.time()-t_load:.0f}s")

    if args.toy:  # smoke test only
        train_idx = train_idx[:2000]
        val_idx = val_idx[:500]
        epochs = 2
    else:
        epochs = args.epochs

    device = pick_device(args.device)
    torch.set_num_threads(min(20, os.cpu_count() or 1))
    torch.manual_seed(args.seed)
    np.random.seed(args.seed)
    torch.backends.cudnn.deterministic = True
    g = torch.Generator()
    g.manual_seed(args.seed)

    train_ds = Sat6Dataset(images[train_idx], labels[train_idx], mean, std, train=True)
    val_ds = Sat6Dataset(images[val_idx], labels[val_idx], mean, std, train=False)
    test_ds = Sat6Dataset(images[test_idx], labels[test_idx], mean, std, train=False)

    loader = lambda ds, shuf: torch.utils.data.DataLoader(
        ds, batch_size=args.batch_size, shuffle=shuf, num_workers=0)

    train_loader = loader(train_ds, True)
    val_loader = loader(val_ds, False)
    test_loader = loader(test_ds, False)

    model = make_model().to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=args.wd)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=epochs)
    crit = nn.CrossEntropyLoss()

    n_params = sum(p.numel() for p in model.parameters())
    print(f"[train] {n_params/1e6:.3f}M params, device={device}")
    print(f"[train] train={len(train_ds)} val={len(val_ds)} test={len(test_ds)}")

    best_val_acc, best_state, history, no_improve = 0.0, None, [], 0
    t_start = time.time()
    for ep in range(epochs):
        model.train()
        tot, correct, loss_sum = 0, 0, 0.0
        for x, y in train_loader:
            x, y = x.to(device), y.to(device)
            opt.zero_grad()
            out = model(x)
            loss = crit(out, y)
            loss.backward()
            opt.step()
            loss_sum += loss.item() * y.size(0)
            correct += (out.argmax(1) == y).sum().item()
            tot += y.size(0)
        sched.step()
        tr_acc = correct / tot
        vp, vg = evaluate(model, val_loader, device)
        va = float((vp == vg).mean())
        if va > best_val_acc:
            best_val_acc = va
            best_state = {k: v.clone() for k, v in model.state_dict().items()}
            no_improve = 0
        else:
            no_improve += 1
        history.append({"epoch": ep + 1, "train_acc": tr_acc,
                        "val_acc": va, "loss": loss_sum / tot})
        if (ep + 1) % 5 == 0 or ep == 0:
            print(f"[train] ep {ep+1:2d}/{epochs} train_acc={tr_acc:.4f} "
                  f"val_acc={va:.4f} lr={sched.get_last_lr()[0]:.2e} "
                  f"({time.time()-t_start:.0f}s)", flush=True)
        if no_improve >= args.patience and ep >= 10:
            print(f"[train] early stop at ep {ep+1} (no val improvement "
                  f"for {args.patience} epochs)")
            break

    print(f"[train] best val acc = {best_val_acc:.4f}")
    model.load_state_dict(best_state)

    # final evaluation on the held-out TEST subset (once)
    preds, gts = evaluate(model, test_loader, device)
    tvp, tvg = evaluate(model, val_loader, device)
    m = metrics(preds, gts)
    mv = metrics(tvp, tvg)

    overall_acc = m["accuracy"]
    majority_frac = float(np.bincount(gts).max() / len(gts))

    print(f"[test] overall accuracy = {overall_acc:.4f}  macro-F1 = {m['macro_f1']:.4f}")
    print(f"[test] majority-class baseline = {majority_frac:.4f}")

    out_root = os.path.abspath(args.out or os.path.join(src_dir, ".."))
    results_dir = os.path.join(out_root, "results")
    fig_dir = os.path.join(out_root, "figure")
    os.makedirs(results_dir, exist_ok=True)
    os.makedirs(fig_dir, exist_ok=True)

    ckpt = {
        "model_state": best_state,
        "mean": mean, "std": std,
        "seed": args.seed,
        "val_acc_best": best_val_acc,
        "split_info": {"train": int(len(train_idx)), "val": int(len(val_idx)),
                       "test": int(len(test_idx))},
    }
    torch.save(ckpt, os.path.join(out_root, "model_sat6.pt"))

    # ---- evidence table (per-class + overall), test split ----
    rows = []
    for c in range(N_CLASSES):
        rows.append({
            "split": "test", "class_id": c, "class_name": CLASS_NAMES[c],
            "tp": int(m["tp"][c]), "fp": int(m["fp"][c]),
            "tn": int(m["tn"][c]), "fn": int(m["fn"][c]),
            "precision": round(float(m["precision"][c]), 6),
            "recall": round(float(m["recall"][c]), 6),
            "f1": round(float(m["f1"][c]), 6),
            "accuracy": round(float(m["per_class_accuracy"][c]), 6),
        })
    rows.append({
        "split": "test", "class_id": -1, "class_name": "overall",
        "tp": int(m["tp"].sum()), "fp": int(m["fp"].sum()),
        "tn": int(m["tn"].sum()), "fn": int(m["fn"].sum()),
        "precision": round(float(np.nanmean(m["precision"])), 6),
        "recall": round(float(np.nanmean(m["recall"])), 6),
        "f1": round(m["macro_f1"], 6),
        "accuracy": round(overall_acc, 6),
    })
    import csv
    with open(os.path.join(results_dir, "evidence_table.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    np.save(os.path.join(results_dir, "confusion_matrix.npy"), m["cm"])
    np.savetxt(os.path.join(results_dir, "confusion_matrix.csv"), m["cm"],
               delimiter=",", fmt="%d", header=",".join(CLASS_NAMES))

    metrics_json = {
        "task": "1509.03602_deepsat",
        "paper_anchor_oa": 0.939,
        "overall_accuracy": round(overall_acc, 6),
        "macro_f1": round(m["macro_f1"], 6),
        "val_accuracy_best": round(best_val_acc, 6),
        "majority_class_baseline": round(majority_frac, 6),
        "train_size": int(len(train_idx)),
        "val_size": int(len(val_idx)),
        "test_size": int(len(test_idx)),
        "seed": args.seed,
        "epochs": epochs,
        "batch_size": args.batch_size,
        "lr": args.lr,
        "weight_decay": args.wd,
        "device": str(device),
        "n_params": int(n_params),
        "train_accuracy_final": round(history[-1]["train_acc"], 6),
        "test_confusion_matrix": m["cm"].tolist(),
        "history": history,
    }
    with open(os.path.join(results_dir, "metrics.json"), "w") as f:
        json.dump(metrics_json, f, indent=2)

    # ---- confusion matrix figure ----
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib.colors import LogNorm
        fig, ax = plt.subplots(figsize=(7, 6))
        cm = m["cm"]
        im = ax.imshow(cm, norm=LogNorm(vmin=1, vmax=cm.max()), cmap="Blues")
        ax.set_xticks(range(N_CLASSES), CLASS_NAMES, rotation=45, ha="right")
        ax.set_yticks(range(N_CLASSES), CLASS_NAMES)
        for i in range(N_CLASSES):
            for j in range(N_CLASSES):
                ax.text(j, i, int(cm[i, j]), ha="center", va="center",
                        color="white" if cm[i, j] > cm.max() / 2 else "black",
                        fontsize=8)
        ax.set_xlabel("Predicted")
        ax.set_ylabel("True")
        ax.set_title(f"SAT-6 test subset confusion matrix (OA={overall_acc * 100:.2f}%)")
        fig.colorbar(im, ax=ax)
        fig.tight_layout()
        fig.savefig(os.path.join(fig_dir, "confusion_matrix.png"), dpi=200)
        print(f"[test] figure saved to {fig_dir}/confusion_matrix.png")
    except Exception as e:  # plotting is non-critical
        print(f"[test] figure skipped: {e}")

    print(f"[test] results written under {out_root}/results")


if __name__ == "__main__":
    main()