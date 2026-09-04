"""Evaluate trained compact CNN on the frozen EuroSAT test split.

Reads the frozen test parquet from DATA_ROOT (verifiable), decodes PNGs,
runs the model with test-time augmentation (original + horizontal flip softmax
average) and produces:

  results/metrics.json            overall metrics + baselines + metadata
  results/evidence_table.csv      per-class TP/FP/TN/FN/precision/recall/F1/acc
  results/confusion_matrix.csv    10x10 confusion matrix (counts)
  results/predictions.csv.gz      filename, label, pred, class_name
  results/eval_detail.json        per-split OA, macro-F1

Protocol note: hyperparameters and the checkpoint are fixed before touching the
test set; the test set is used exactly once for reporting.

Usage:
    python 03_evaluate.py [--data-root PATH] [--cache-dir PATH]
                          [--checkpoint ../artifacts/eurosat_cnn_seed00.pt]
                          [--outdir ../results] [--threads 10]
"""
import argparse
import gzip
import io
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image
from sklearn.metrics import confusion_matrix as sk_cm

import torch
import torch.nn.functional as F

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _models import make_model

CLASS_NAMES = [
    "AnnualCrop", "Forest", "HerbaceousVegetation", "Highway", "IndustrialBuildings",
    "Pasture", "PermanentCrop", "ResidentialBuildings", "River", "SeaLake",
]


@torch.no_grad()
def predict(model, X, mean, std, bs=256, tta=True):
    model.eval()
    probs = []
    for i in range(0, len(X), bs):
        xb = X[i:i + bs].float().div_(255.0)
        xb = (xb - mean) / std
        xb = xb.to(memory_format=torch.channels_last)
        outs = [F.softmax(model(xb), dim=1)]
        if tta:
            outs.append(F.softmax(model(torch.flip(xb, dims=[3])), dim=1))
        probs.append(torch.stack(outs).mean(0))
    return torch.cat(probs).numpy()


def decode_split(data_root, split):
    pf = Path(data_root) / f"{split}-00000-of-00001.parquet"
    df = pd.read_parquet(pf, columns=["image", "label", "filename"])
    X = np.empty((len(df), 64, 64, 3), dtype=np.uint8)
    for i, raw in enumerate(df["image"].tolist()):
        X[i] = np.asarray(Image.open(io.BytesIO(raw["bytes"])).convert("RGB"))
    y = df["label"].astype(np.int64).to_numpy()
    return X, y, df["filename"].astype(str).tolist()


def per_class_metrics(y_true, y_pred, n_classes):
    cm = sk_cm(y_true, y_pred, labels=list(range(n_classes)))
    rows = []
    for c in range(n_classes):
        tp = int(cm[c, c])
        fp = int(cm[:, c].sum() - tp)
        fn = int(cm[c, :].sum() - tp)
        tn = int(cm.sum() - (tp + fp + fn))
        prec = tp / (tp + fp) if tp + fp else 0.0
        rec = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
        acc = (tp + tn) / (tp + tn + fp + fn)
        rows.append({"tp": tp, "fp": fp, "tn": tn, "fn": fn,
                     "precision": prec, "recall": rec, "f1": f1, "accuracy": acc})
    return rows, cm


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", default=os.environ.get(
        "EUROSAT_DATA", "/mnt/f/dataset/earth/1709.00029_eurosat/data/data"))
    ap.add_argument("--cache-dir", default=os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "cache"))
    ap.add_argument("--checkpoint", default=os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "artifacts",
        "eurosat_cnn_seed00.pt"))
    ap.add_argument("--outdir", default=os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "results"))
    ap.add_argument("--threads", type=int, default=10)
    ap.add_argument("--bs", type=int, default=256)
    args = ap.parse_args()

    torch.set_num_threads(args.threads)

    ckpt = torch.load(args.checkpoint, map_location="cpu", weights_only=False)
    model = make_model()
    model.load_state_dict(ckpt["state_dict"])
    mean = ckpt["mean"].view(1, -1, 1, 1)
    std = ckpt["std"].view(1, -1, 1, 1)
    n_params = sum(p.numel() for p in model.parameters())

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    results = {}
    cm_all = None
    pred_csv_lines = []
    for split in ["train", "validation", "test"]:
        X, y, fnames = decode_split(args.data_root, split)
        Xt = torch.from_numpy(X).permute(0, 3, 1, 2)
        prob = predict(model, Xt, mean, std, args.bs, tta=True)
        pred = prob.argmax(1)
        oa = float((pred == y).mean())
        rows, cm = per_class_metrics(y, pred, len(CLASS_NAMES))
        macro_f1 = float(np.mean([r["f1"] for r in rows]))
        macro_recall = float(np.mean([r["recall"] for r in rows]))
        macro_precision = float(np.mean([r["precision"] for r in rows]))
        results[split] = {
            "overall_accuracy": oa,
            "macro_f1": macro_f1,
            "macro_precision": macro_precision,
            "macro_recall": macro_recall,
            "n": int(len(y)),
        }
        print(f"[{split}] OA={oa:.4f} macroF1={macro_f1:.4f}")
        if split == "test":
            cm_all = cm
            evidence = []
            for c, r in enumerate(rows):
                evidence.append({
                    "split": split, "class_id": c,
                    "class_name": CLASS_NAMES[c], **r,
                })
            evidence.append({
                "split": split, "class_id": -1, "class_name": "overall",
                "tp": int((pred == y).sum()), "fp": 0, "tn": 0,
                "fn": int((pred != y).sum()),
                "precision": macro_precision, "recall": macro_recall,
                "f1": macro_f1, "accuracy": oa,
            })
            pd.DataFrame(evidence).to_csv(outdir / "evidence_table.csv", index=False)
            pd.DataFrame(cm, index=CLASS_NAMES, columns=CLASS_NAMES).to_csv(
                outdir / "confusion_matrix.csv")
            for fn_, lb, pr in zip(fnames, y, pred):
                pred_csv_lines.append((fn_, int(lb), int(pr), CLASS_NAMES[lb]))
        del X, Xt

    # baselines from train distribution (statistics from train only)
    tr_df = pd.read_parquet(Path(args.data_root) / "train-00000-of-00001.parquet",
                            columns=["label"])
    train_counts = np.bincount(tr_df["label"].astype(int).to_numpy(), minlength=10)
    majority_class = int(train_counts.argmax())
    Xte, yte, _ = decode_split(args.data_root, "test")
    majority_baseline = float((yte == majority_class).mean())
    random_baseline = 1.0 / 10

    metrics = {
        "overall_accuracy": results["test"]["overall_accuracy"],
        "macro_f1": results["test"]["macro_f1"],
        "macro_precision": results["test"]["macro_precision"],
        "macro_recall": results["test"]["macro_recall"],
        "majority_class_baseline": majority_baseline,
        "majority_class_id": majority_class,
        "majority_class_name": CLASS_NAMES[majority_class],
        "random_baseline": random_baseline,
        "channels_used": "RGB (3 bands of Sentinel-2; frozen dataset is RGB)",
        "n_test": int(len(yte)),
        "n_train": int(len(tr_df)),
        "model": "compact-CNN (VGG-style block net, 3.9M params)",
        "checkpoint": args.checkpoint,
        "checkpoint_epochs": ckpt.get("epochs"),
        "seed": ckpt.get("seed"),
        "test_time_augmentation": "horizontal flip softmax averaging",
        "per_split": results,
        "confusion_matrix_file": "confusion_matrix.csv",
        "evidence_table_file": "evidence_table.csv",
        "paper_anchor_oa_rgb_vs_multispectral_note": (
            "Paper reports 98.57% (Sentinel-2, up to 13 bands); this run uses RGB only."),
    }
    with open(outdir / "metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)

    with gzip.open(outdir / "predictions.csv.gz", "wt") as f:
        f.write("filename,label,pred,label_name\n")
        for l in pred_csv_lines:
            f.write(f"{l[0]},{l[1]},{l[2]},{l[3]}\n")
    print("wrote", outdir)
    print(json.dumps(metrics, indent=2, default=str))


if __name__ == "__main__":
    main()