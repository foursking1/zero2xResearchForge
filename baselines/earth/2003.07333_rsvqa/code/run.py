"""Main experiment driver.

Loads the frozen RSVQA parquet, builds the image-level 80/20 split (seed 42),
caches frozen CNN/ViT features, trains the CNN-LSTM VQA model, and evaluates on
the held-out 20-image eval split including the random-image ablation.

Supports experiments:
  --backbone resnet18 | vit      (frozen visual encoder)
  --count-head regress | density (count prediction strategy)
  --count-weight W               (extra weight on the count loss)
  --final                        (re-train on all 80 train images, then eval)

Usage:
  python -m code.run --device cpu --backbone resnet18 --count-head regress --epochs 60
"""
import argparse
import json
import os

import numpy as np

from .dataset import load_data, make_split, build_vocab, decode_image
from .features import extract_resnet18_features, extract_resnet18_conv, extract_vit_features
from .model import RSVQAModel
from .train_eval import (build_dataset, predict, accuracy, accuracy_by_type,
                         predict_scores, train_model, int_to_answer)

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(HERE, "results")
CACHE = os.path.join(RESULTS, "_cache")
for p in (RESULTS, CACHE):
    os.makedirs(p, exist_ok=True)

QTYPE_NAMES = ["presence", "comparison", "rural_urban", "count"]


def feature(name, extractor):
    p = os.path.join(CACHE, f"{name}.npy")
    if os.path.exists(p):
        print(f"[cache] {name}")
        return np.load(p)
    print(f"[extract] {name}")
    feats = extractor()
    np.save(p, feats)
    return feats


def get_images(df):
    uids = sorted(df["imgid"].unique())
    im_by_id = {r["imgid"]: decode_image(r["image"]) for _, r in df.iterrows()}
    return uids, [im_by_id[i] for i in uids]


def main(args):
    import torch
    import pandas as pd

    device = "cpu" if args.device == "cpu" else "cuda"
    torch.manual_seed(args.seed)
    np.random.seed(args.seed)
    torch.set_num_threads(args.threads)
    try:
        torch.use_deterministic_algorithms(True, warn_only=True)
    except TypeError:
        torch.use_deterministic_algorithms(True)

    df = load_data()
    tr, ev, _ = make_split(df, n_train_images=80, seed=42)

    tr_imgids = sorted(tr["imgid"].unique())
    rng = np.random.RandomState(42)
    perm = rng.permutation(len(tr_imgids))
    dev_ids = set(tr_imgids[i] for i in perm[:16])
    tr2 = tr[~tr["imgid"].isin(dev_ids)].copy()
    dev = tr[tr["imgid"].isin(dev_ids)].copy()

    uids, ims = get_images(df)
    imgid_to_idx = {i: k for k, i in enumerate(uids)}
    feats = load_features(args.backbone, ims, device)
    map7, map14 = feats
    print(f"features map7 {map7.shape} map14 {None if map14 is None else map14.shape}")

    w2i = build_vocab(tr["question_norm"].tolist())
    print(f"vocab size {len(w2i)}")

    if args.count_only:
        train_pool = (tr2 if not args.final else tr)
        train_pool = train_pool[train_pool["qtype"] == "count"]
        dev = dev[dev["qtype"] == "count"]
        print(f"[count-only] train {len(train_pool)} count rows")
    else:
        train_pool = tr2 if not args.final else tr
    print(f"train {len(train_pool)} rows/{train_pool['imgid'].nunique()} imgs | "
          f"dev {len(dev)} rows/{dev['imgid'].nunique()} imgs | "
          f"eval {len(ev)} rows/{ev['imgid'].nunique()} imgs (untouched until final eval)")

    tr_d = build_dataset(train_pool, map7, imgid_to_idx, w2i, device, map14)
    dev_d = build_dataset(dev, map7, imgid_to_idx, w2i, device, map14)
    ev_d = build_dataset(ev, map7, imgid_to_idx, w2i, device, map14)

    feat_dim = map7.shape[1]
    density_dim = map14.shape[1] if map14 is not None else feat_dim
    model = RSVQAModel(vocab_size=len(w2i), feat_dim=feat_dim, q_dim=256, hidden=512,
                       count_head=args.count_head, density_dim=density_dim,
                       count_weight=args.count_weight, n_bins=args.n_bins)
    model = model.to(device)
    opt = torch.optim.Adam(model.parameters(), lr=1e-3, weight_decay=1e-5)
    if args.final:
        # when training on all 80 images there is no dev set for early stopping;
        # use the dev-budget learned in the non-final run
        epochs = args.epochs
    best_dev, best_ep = train_model(model, tr_d, dev_d, opt, epochs=args.epochs,
                                    bs=128, device=device, seed=args.seed, patience=10,
                                    count_weight=args.count_weight, only_count=args.count_only)
    print(f"[select] best dev OA {best_dev:.4f} at epoch {best_ep}")

    dev_preds, _ = predict(model, dev_d, np.arange(dev_d.n))
    print("[dev by-type]", json.dumps(accuracy_by_type(dev_preds, dev_d, np.arange(dev_d.n)), indent=1))

    torch.save(model.state_dict(), os.path.join(RESULTS, f"model_{args.tag}.pt"))

    # ---- final evaluation -------------------------------------------------
    ev_preds, ev_scores = predict_scores(model, ev_d, np.arange(ev_d.n))
    ev_targets = ev_d.targets.cpu().numpy()
    ev_corr = ev_preds == ev_targets
    ev_oa = float(ev_corr.mean())
    rand_preds, _ = predict_scores(model, ev_d, np.arange(ev_d.n), shuffle_row=True, seed=7)
    rand_oa = float(np.mean(rand_preds == ev_targets))

    if args.save_scores:
        import pickle
        with open(os.path.join(RESULTS, f"eval_scores_{args.tag}.pkl"), "wb") as f:
            pickle.dump({"scores": ev_scores, "qtypes": ev_d.qtypes.cpu().numpy(),
                         "targets": ev_targets}, f)

    e = ev.copy()
    e["split"] = "eval"
    o = pd.concat([tr2[["question_norm", "answer", "qtype", "imgid"]].assign(split="train"),
                   dev[["question_norm", "answer", "qtype", "imgid"]].assign(split="dev"),
                   e[["question_norm", "answer", "qtype", "imgid"]].assign(split="eval")],
                  ignore_index=True)
    o["prediction"] = ""
    o["correct"] = ""
    is_eval = o["split"] == "eval"
    o.loc[is_eval, "prediction"] = [int_to_answer(p, t) for p, t in
                                    zip(ev_preds, ev["qtype"].tolist())]
    o.loc[is_eval, "correct"] = ev_corr.astype(bool).astype(str)
    o = o.rename(columns={"question_norm": "question", "qtype": "question_type"})
    if "question.1" in o.columns:
        o = o.drop(columns=["question.1"])
    o = o[["split", "question_type", "question", "answer", "prediction", "correct", "imgid"]]
    o.to_csv(os.path.join(RESULTS, "evidence_table.csv"), index=False)

    acc_by_type = accuracy_by_type(ev_preds, ev_d, np.arange(ev_d.n))
    metrics = {
        "overall_accuracy": round(ev_oa, 5),
        "accuracy_by_type": acc_by_type,
        "random_image_ablation_accuracy": round(rand_oa, 5),
        "train_size": int(len(train_pool)),
        "dev_size": int(len(dev)),
        "eval_size": int(len(ev)),
        "n_train_images": int(train_pool["imgid"].nunique()),
        "n_eval_images": int(ev["imgid"].nunique()),
        "seed": 42,
        "backbone": args.backbone,
        "count_head": args.count_head,
        "count_weight": args.count_weight,
        "best_dev_oa": round(float(best_dev), 5),
        "best_train_epoch": int(best_ep),
        "final": bool(args.final),
    }
    with open(os.path.join(RESULTS, "metrics.json"), "w") as f:
        json.dump(metrics, f, indent=2)
    print("[eval] OA", round(ev_oa, 5), "| by-type", json.dumps(acc_by_type))
    print("[eval] random-image ablation OA", round(rand_oa, 5))
    return metrics


def load_features(backbone, ims, device):
    if backbone == "vit":
        pool = feature("vit_pool768", lambda: extract_vit_features(ims, device=device))
        v7 = pool[:, :, None, None]
        map7 = np.broadcast_to(v7, (v7.shape[0], v7.shape[1], 7, 7))
        return map7, None
    if backbone == "resnet18":
        map7 = feature("resnet18_conv7", lambda: extract_resnet18_features(ims, device=device, pool=False))
        map14 = feature("resnet18_conv14", lambda: extract_resnet18_conv(ims, device=device, stage=3))
        return map7, map14
    if backbone == "concat":
        r7 = feature("resnet18_conv7", lambda: extract_resnet18_features(ims, device=device, pool=False))
        pv = feature("vit_pool768", lambda: extract_vit_features(ims, device=device))
        # broadcast ViT global token to every spatial location and concatenate channels
        v7 = pv[:, :, None, None]
        v7 = np.broadcast_to(v7, (v7.shape[0], v7.shape[1], r7.shape[2], r7.shape[3]))
        map7 = np.concatenate([r7, v7], axis=1)
        map14 = feature("resnet18_conv14", lambda: extract_resnet18_conv(ims, device=device, stage=3))
        return map7, map14
    raise ValueError(backbone)


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--backbone", default="resnet18", choices=["resnet18", "vit", "concat"])
    ap.add_argument("--count-head", default="regress", choices=["regress", "density", "hybrid"])
    ap.add_argument("--count-weight", type=float, default=1.0)
    ap.add_argument("--n-bins", type=int, default=41)
    ap.add_argument("--epochs", type=int, default=60)
    ap.add_argument("--final", action="store_true")
    ap.add_argument("--save-scores", action="store_true")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--count-only", action="store_true")
    ap.add_argument("--threads", type=int, default=8)
    return ap.parse_args()


if __name__ == "__main__":
    args = parse_args()
    co = "_countonly" if args.count_only else ""
    args.tag = f"{args.backbone}_{args.count_head}_{args.count_weight}{co}_s{args.seed}"
    main(args)