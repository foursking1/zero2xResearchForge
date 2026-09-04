"""Additional analysis: confusion pairs + channel-sensitivity diagnostic.

Confusion analysis is computed from the frozen test split predictions.
The channel-sensitivity study is a diagnostic at inference time only (it does
NOT retrain the model): we re-feed the test images with a greyscale-replicated
input and with individual channels zeroed/substituted to measure how much RGB
color information the classifier relies on. This is reported as a diagnostic,
not as an alternative training protocol.

Usage:
    python 04_analyze.py [--data-root PATH] [--checkpoint ../artifacts/eurosat_cnn_seed00.pt]
                         [--outdir ../results] [--threads 10]
"""
import argparse
import json
import io
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image

import torch
import torch.nn.functional as F

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _models import make_model, CLASS_NAMES

ROOT = Path(__file__).resolve().parents[1]


def load_test(data_root):
    df = pd.read_parquet(Path(data_root) / "test-00000-of-00001.parquet",
                         columns=["image", "label", "filename"])
    X = np.empty((len(df), 64, 64, 3), dtype=np.uint8)
    for i, raw in enumerate(df["image"].tolist()):
        X[i] = np.asarray(Image.open(io.BytesIO(raw["bytes"])).convert("RGB"))
    y = df["label"].astype(np.int64).to_numpy()
    return X, y


@torch.no_grad()
def softmax_probs(model, Xt, mean, std, bs=256):
    model.eval()
    outs = []
    for i in range(0, len(Xt), bs):
        xb = Xt[i:i + bs].float().div_(255.0)
        xb = (xb - mean) / std
        xb = xb.to(memory_format=torch.channels_last)
        o = F.softmax(model(xb), dim=1) + F.softmax(model(torch.flip(xb, dims=[3])), dim=1)
        outs.append(o)
    return torch.cat(outs).cpu().numpy()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", default=os.environ.get(
        "EUROSAT_DATA", "/mnt/f/dataset/earth/1709.00029_eurosat/data/data"))
    ap.add_argument("--checkpoint", default=str(ROOT / "artifacts" / "eurosat_cnn_seed00.pt"))
    ap.add_argument("--outdir", default=str(ROOT / "results"))
    ap.add_argument("--threads", type=int, default=10)
    args = ap.parse_args()
    torch.set_num_threads(args.threads)

    ckpt = torch.load(args.checkpoint, map_location="cpu", weights_only=False)
    model = make_model()
    model.load_state_dict(ckpt["state_dict"])
    mean = ckpt["mean"].unsqueeze(0).unsqueeze(-1).unsqueeze(-1)
    std = ckpt["std"].unsqueeze(0).unsqueeze(-1).unsqueeze(-1)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    X, y = load_test(args.data_root)
    Xt = torch.from_numpy(X).permute(0, 3, 1, 2)
    pred = softmax_probs(model, Xt, mean, std).argmax(1)

    cm = np.zeros((10, 10), dtype=int)
    for t, p in zip(y, pred):
        cm[t, p] += 1
    np.fill_diagonal(cm, 0)

    pairs = []
    for t in range(10):
        for p in range(10):
            if p != t and cm[t, p] > 0:
                pairs.append((int(cm[t, p]), CLASS_NAMES[t], CLASS_NAMES[p]))
    pairs.sort(reverse=True)
    confusion_pairs = [{"count": int(c), "true": t, "pred": p}
                       for c, t, p in pairs]

    per_class_correct = [(int((pred == y)[y == c].sum()), CLASS_NAMES[c])
                         for c in range(10)]
    per_class_correct.sort(key=lambda x: x[0])

    # channel sensitivity diagnostics (inference-time only)
    diag = {}
    Xf = Xt.float().div_(255.0)
    for name, variant in [
        ("grayscale_replicated", lambda x: x.mean(dim=1, keepdim=True).expand(-1, 3, -1, -1)),
        ("zero_blue", lambda x: x * torch.tensor([1.0, 1.0, 0.0]).view(1, 3, 1, 1)),
        ("zero_green", lambda x: x * torch.tensor([1.0, 0.0, 1.0]).view(1, 3, 1, 1)),
        ("zero_red", lambda x: x * torch.tensor([0.0, 1.0, 1.0]).view(1, 3, 1, 1)),
        ("channel_shuffle_bg", lambda x: x[:, [1, 2, 0], :, :]),
    ]:
        xx = (variant(Xf) - mean) / std
        pr = softmax_probs(model, xx.to(memory_format=torch.channels_last), mean, std).argmax(1)
        diag[name] = float((pr == y).mean())

    report = {
        "top_confusion_pairs": confusion_pairs[:10],
        "per_class_correct_counts": per_class_correct,
        "inference_channel_diagnostic": diag,
        "note": ("Channel ablation is inference-time only; it measures classifier "
                 "sensitivity to spectral information, not a retrained model."),
    }
    with open(outdir / "analysis.json", "w") as f:
        json.dump(report, f, indent=2)
    print(json.dumps(report, indent=2, default=str))


if __name__ == "__main__":
    main()