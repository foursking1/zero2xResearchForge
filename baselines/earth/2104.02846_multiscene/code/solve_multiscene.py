"""
MultiScene-Clean multi-label classification reproduction.
Frozen data: F:/dataset/earth/2104.02846_multiscene/
  - data/data/train-0000{0,1}-of-00002-*.parquet (14,000 images, 512x512x3, multi-label 36 classes)
  - multiscene_split_50.csv (fixed 50/50: 7,000 train / 7,000 test)

Paper anchor: ResNeXt-101 mAP 64.8% (MultiScene-Clean, Table II).
Method: ImageNet-pretrained ResNet50 frozen feature extractor + per-class L2-regularized
LogisticRegression (one-vs-rest) on the pooled features. Threshold = 0.5.
Metrics: mAP, mCF1, mEF1, OF1. Baselines: frequent-label prior.
"""
import argparse
import glob
import io
import json
import os
import time
from collections import Counter

import numpy as np
import pandas as pd
from PIL import Image
from sklearn.metrics import average_precision_score

os.environ.setdefault("OMP_NUM_THREADS", "8")

LABEL_NAMES = [
    "apron", "baseball field", "basketball field", "beach", "bridge", "cemetery",
    "commercial", "farmland", "woodland", "golf course", "greenhouse", "helipad",
    "lake or pond", "oil field", "orchard", "parking lot", "park", "pier", "port",
    "quarry", "railway", "residential", "river", "roundabout", "runway", "soccer",
    "solar panel", "sparse shrub", "stadium", "storage tank", "tennis court",
    "train station", "wastewater plant", "wind turbine", "works", "sea",
]
N_CLASSES = 36


def iter_bytes(df):
    for i in range(len(df)):
        yield df.iloc[i]["bytes"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="F:/dataset/earth/2104.02846_multiscene")
    ap.add_argument("--split", default="F:/dataset/earth/2104.02846_multiscene/multiscene_split_50.csv")
    ap.add_argument("--outdir", default=".")
    ap.add_argument("--seed", type=int, default=20260813)
    ap.add_argument("--model", default="resnet50")
    ap.add_argument("--img_size", type=int, default=256)
    ap.add_argument("--threshold", type=float, default=0.5)
    ap.add_argument("--batch_size", type=int, default=32)
    args = ap.parse_args()

    os.makedirs(args.outdir, exist_ok=True)

    split = pd.read_csv(args.split)
    print("split:", split["split"].value_counts().to_dict(), flush=True)

    files = sorted(glob.glob(os.path.join(args.data, "data", "data", "*.parquet")))
    rows = []
    for f in files:
        df = pd.read_parquet(f, columns=["label", "image"])
        shard = os.path.basename(f)
        for i in range(len(df)):
            r = df.iloc[i]
            rows.append({"shard_file": shard, "row_in_shard": i,
                         "labels": [int(x) for x in r["label"]],
                         "bytes": r["image"]["bytes"]})
    meta = pd.DataFrame(rows)
    print("meta rows", len(meta), flush=True)
    df = meta.merge(split, on=["shard_file", "row_in_shard"], how="inner")
    print("merged rows", len(df), flush=True)
    df_train = df[df["split"] == "train"].reset_index(drop=True)
    df_test = df[df["split"] == "test"].reset_index(drop=True)
    print("train", len(df_train), "test", len(df_test), flush=True)

    train_counts = Counter()
    for labs in df_train["labels"]:
        for x in labs:
            train_counts[x] += 1
    test_counts = Counter()
    for labs in df_test["labels"]:
        for x in labs:
            test_counts[x] += 1
    print("train label counts:", [train_counts.get(i, 0) for i in range(N_CLASSES)], flush=True)

    import feat_utils
    print("extracting features ...", flush=True)
    t0 = time.time()
    backbone, feat_dim = feat_utils.get_backbone(args.model, device="cpu")
    F_train = feat_utils.extract_features_stream(iter_bytes(df_train), backbone,
                                                 img_size=args.img_size, batch_size=args.batch_size,
                                                 cache_path=os.path.join(args.outdir, "feats_train.npy"),
                                                 n_total=len(df_train), feat_dim=feat_dim)
    F_test = feat_utils.extract_features_stream(iter_bytes(df_test), backbone,
                                                img_size=args.img_size, batch_size=args.batch_size,
                                                cache_path=os.path.join(args.outdir, "feats_test.npy"),
                                                n_total=len(df_test), feat_dim=feat_dim)
    print("features", F_train.shape, F_test.shape, "time", round(time.time()-t0,1), "s", flush=True)

    mu = F_train.mean(axis=0)
    sd = F_train.std(axis=0)
    sd[sd < 1e-8] = 1.0
    Xtr = (F_train - mu) / sd
    Xte = (F_test - mu) / sd

    Ytr = np.zeros((len(df_train), N_CLASSES), dtype=np.float64)
    Yte = np.zeros((len(df_test), N_CLASSES), dtype=np.float64)
    for i, labs in enumerate(df_train["labels"]):
        for x in labs:
            Ytr[i, x] = 1.0
    for i, labs in enumerate(df_test["labels"]):
        for x in labs:
            Yte[i, x] = 1.0

    from sklearn.linear_model import LogisticRegression

    # Per-class one-vs-rest LogisticRegression
    print("training per-class LR ...", flush=True)
    t0 = time.time()
    scores = np.zeros_like(Yte, dtype=np.float64)
    for c in range(N_CLASSES):
        if train_counts.get(c, 0) == 0:
            continue
        clf = LogisticRegression(C=0.1, max_iter=300, solver="lbfgs")
        clf.fit(Xtr, Ytr[:, c])
        scores[:, c] = clf.predict_proba(Xte)[:, 1]
    print("done", round(time.time()-t0,1), "s", flush=True)

    # Frequent-label baseline: predict prior probability = train frequency
    prior = np.zeros(N_CLASSES)
    for c in range(N_CLASSES):
        prior[c] = train_counts.get(c, 0) / max(len(df_train), 1)
    base_scores = np.tile(prior, (len(df_test), 1))
    base_ap = [average_precision_score(Yte[:, c], base_scores[:, c])
               for c in range(N_CLASSES) if Yte[:, c].sum() > 0]
    base_map = float(np.mean(base_ap)) if base_ap else 0.0

    def multilabel_metrics(scores, truth, threshold):
        pred = (scores >= threshold).astype(np.float32)
        per_class = {}
        ap_list = []
        for c in range(N_CLASSES):
            if truth[:, c].sum() > 0:
                ap = float(average_precision_score(truth[:, c], scores[:, c]))
            else:
                ap = 0.0
            ap_list.append(ap)
            tp = ((pred[:, c] == 1) & (truth[:, c] == 1)).sum()
            fp = ((pred[:, c] == 1) & (truth[:, c] == 0)).sum()
            fn = ((pred[:, c] == 0) & (truth[:, c] == 1)).sum()
            prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0
            per_class[c] = {"tp": int(tp), "fp": int(fp), "fn": int(fn),
                            "precision": float(prec), "recall": float(rec),
                            "f1": float(f1), "ap": ap}
        mAP = float(np.mean(ap_list))
        mCF1 = float(np.mean([per_class[c]["f1"] for c in range(N_CLASSES)]))
        ex_f1 = []
        for i in range(truth.shape[0]):
            tp_n = ((pred[i] == 1) & (truth[i] == 1)).sum()
            fp_n = ((pred[i] == 1) & (truth[i] == 0)).sum()
            fn_n = ((pred[i] == 0) & (truth[i] == 1)).sum()
            f1 = 2 * tp_n / (2 * tp_n + fp_n + fn_n) if (2 * tp_n + fp_n + fn_n) > 0 else 0.0
            ex_f1.append(f1)
        mEF1 = float(np.mean(ex_f1))
        ttp = int(sum(per_class[c]["tp"] for c in range(N_CLASSES)))
        ffp = int(sum(per_class[c]["fp"] for c in range(N_CLASSES)))
        ffn = int(sum(per_class[c]["fn"] for c in range(N_CLASSES)))
        OF1 = float(2 * ttp / (2 * ttp + ffp + ffn)) if (2 * ttp + ffp + ffn) > 0 else 0.0
        return mAP, mCF1, mEF1, OF1, per_class

    mAP, mCF1, mEF1, OF1, per_class = multilabel_metrics(scores, Yte, args.threshold)
    print("mAP=%.3f mCF1=%.3f mEF1=%.3f OF1=%.3f base_mAP=%.3f"
          % (mAP, mCF1, mEF1, OF1, base_map), flush=True)

    ev_rows = []
    for c in range(N_CLASSES):
        ev_rows.append({
            "label": c, "class_name": LABEL_NAMES[c],
            "n_train": int(train_counts.get(c, 0)), "n_test": int(test_counts.get(c, 0)),
            "n_correct": int(per_class[c]["tp"]),
            "precision": round(per_class[c]["precision"], 6),
            "recall": round(per_class[c]["recall"], 6),
            "f1": round(per_class[c]["f1"], 6),
            "ap": round(per_class[c]["ap"], 6),
        })
    ev_rows.append({"label": "ALL", "class_name": "overall",
                    "n_train": int(len(df_train)), "n_test": int(len(df_test)),
                    "n_correct": int(sum(per_class[c]["tp"] for c in range(N_CLASSES))),
                    "precision": round(mCF1, 6), "recall": round(mEF1, 6),
                    "f1": round(OF1, 6), "ap": round(mAP, 6)})
    ev = pd.DataFrame(ev_rows)
    ev.to_csv(os.path.join(args.outdir, "evidence_table.csv"), index=False)

    metrics = {
        "mAP": round(mAP, 6),
        "mCF1": round(mCF1, 6),
        "mEF1": round(mEF1, 6),
        "OF1": round(OF1, 6),
        "frequent_label_baseline_mAP": round(base_map, 6),
        "threshold": args.threshold,
        "seed": args.seed,
        "split": "frozen multiscene_split_50.csv (7000/7000)",
        "split_sizes": {"train": int(len(df_train)), "test": int(len(df_test))},
        "model": args.model,
        "img_size": args.img_size,
        "feature_dim": int(feat_dim),
        "classifier": "per-class LogisticRegression(C=0.1) on frozen ImageNet features",
        "paper_anchor_mAP": 0.648,
        "paper_anchor_source": "MultiScene-Clean Table II ResNeXt-101 mAP=64.8%",
        "device": "cpu",
        "per_class": {str(c): per_class[c] for c in range(N_CLASSES)},
    }
    with open(os.path.join(args.outdir, "metrics.json"), "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)
    print(json.dumps(metrics, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
