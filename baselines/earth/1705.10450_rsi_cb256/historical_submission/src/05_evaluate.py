"""Final evaluation; produces official deliverables for whatever model is chosen.

Models:
  --model resnet : the fine-tuned MultiTaskResNet (needs results/images_224.memmap)
  --model mlp    : MLP head on frozen ResNet18 features (results/features_*.npz)

Outputs (same for either):
  results/evidence_table.csv    per-class + overall metrics (test, label_2)
  results/metrics.json          overall_accuracy, macro_f1, label1_accuracy, ...
  results/predictions.npz       predicted/true ids + probabilities
  results/confusion_label2.csv  35x35 confusion matrix
  evidence/                     copies of the above + detached checkpoint

Usage: TORCH_THREADS=8 python3 src/05_evaluate.py --model resnet \
       --ckpt checkpoints/resnet18_mtl.pt
"""
import argparse
import json
import os
import shutil
import sys

import numpy as np
import pandas as pd
import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (CHECKPOINT_DIR, EVIDENCE_DIR, LABEL1_NAMES, LABEL2_NAMES,  # noqa: E402
                    N_L1, N_L2, RESULTS_DIR, SEED, load_labels, set_seed)
from sklearn.metrics import (accuracy_score, confusion_matrix,  # noqa: E402
                             f1_score)


def class_metrics(y_true, y_pred, n_classes):
    from sklearn.metrics import precision_recall_fscore_support
    ps, rs, fs, _ = precision_recall_fscore_support(
        y_true, y_pred, labels=list(range(n_classes)), zero_division=0)
    rows, conf = [], confusion_matrix(y_true, y_pred,
                                      labels=list(range(n_classes)))
    for c in range(n_classes):
        tp = int(conf[c, c]); fn = int(conf[c, :].sum()) - tp
        fp = int(conf[:, c].sum()) - tp; tn = int(conf.sum()) - tp - fp - fn
        rows.append({"split": "test", "class_level": 2,
                     "class_id": c, "class_name": LABEL2_NAMES[c],
                     "tp": tp, "fp": fp, "tn": tn, "fn": fn,
                     "precision": float(ps[c]), "recall": float(rs[c]),
                     "f1": float(fs[c]), "accuracy": float((tp + tn) / conf.sum())})
    return rows


def predict_resnet(model, imgmem, te, batch=64):
    from evaluate_utils import predict_test
    return predict_test(model, imgmem, None, None, te, batch)


def build_pred_resnet(ckpt, imgmem, te, batch=64):
    from train_utils import MultiTaskResNet
    model = MultiTaskResNet()
    model.load_state_dict(torch.load(ckpt, map_location="cpu"))
    model.eval()
    te_idx = np.where(te)[0]
    pred2, pred1, p2, p1 = [], [], [], []
    from common import normalize
    with torch.no_grad():
        for s in range(0, len(te_idx), batch):
            ids = te_idx[s:s + batch]
            xb = np.ascontiguousarray(imgmem[ids])
            xt = torch.tensor(normalize(xb).transpose(0, 3, 1, 2))
            lg2, lg1, _ = model.embed_and_logits(xt)
            pred2.append(lg2.argmax(1).numpy()); pred1.append(lg1.argmax(1).numpy())
            p2.append(lg2.softmax(-1).numpy()); p1.append(lg1.softmax(-1).numpy())
    return (np.concatenate(pred2), np.concatenate(pred1),
            np.concatenate(p2).astype(np.float32), np.concatenate(p1).astype(np.float32))


def build_pred_mlp(feat_te, model_path):
    from importlib import import_module
    from torch import no_grad
    HeadMLP = import_module("03b_mlp_probe").HeadMLP
    model = HeadMLP()
    model.load_state_dict(torch.load(model_path, map_location="cpu")["model"])
    model.eval()
    with no_grad():
        lg2, lg1, _ = model(torch.from_numpy(feat_te).float())
    p2 = lg2.softmax(-1).numpy().astype(np.float32)
    p1 = lg1.softmax(-1).numpy().astype(np.float32)
    return lg2.argmax(1).numpy(), lg1.argmax(1).numpy(), p2, p1


def write_outputs(pred2, pred1, p2, p1, true_l2, true_l1, model_desc,
                  split_sizes, oa_l2, mf1_l2, oa_l1):
    rows = class_metrics(true_l2, pred2, N_L2)
    ev = pd.DataFrame(rows + [{
        "split": "test", "class_level": 2, "class_id": -1,
        "class_name": "OVERALL", "tp": int((pred2 == true_l2).sum()),
        "fp": None, "tn": None, "fn": None, "precision": None,
        "recall": None, "f1": mf1_l2, "accuracy": oa_l2}])
    ev.to_csv(os.path.join(RESULTS_DIR, "evidence_table.csv"), index=False)

    metrics = {
        "overall_accuracy": round(oa_l2, 6),
        "label2_macro_f1": round(mf1_l2, 6),
        "label1_accuracy": round(oa_l1, 6),
        "n_classes_label2": int(N_L2), "n_classes_label1": int(N_L1),
        "model": model_desc, "resolution": 224, "seed": SEED,
        "split_sizes": {"train": split_sizes[0], "test": split_sizes[1]},
        "split_source": "frozen split_train_test_50.csv",
        "paper_anchor_oa": 95.13,
        "relative_gap_percent": round((oa_l2 * 100 - 95.13) / 95.13 * 100, 2),
    }
    with open(os.path.join(RESULTS_DIR, "metrics.json"), "w") as fp:
        json.dump(metrics, fp, indent=2, default=float)

    np.savez_compressed(os.path.join(RESULTS_DIR, "predictions.npz"),
                        pred2=pred2, pred1=pred1, true_l2=true_l2,
                        true_l1=true_l1, prob2=p2, prob1=p1)
    conf = confusion_matrix(true_l2, pred2, labels=list(range(N_L2)))
    pd.DataFrame(conf, index=LABEL2_NAMES, columns=LABEL2_NAMES).to_csv(
        os.path.join(RESULTS_DIR, "confusion_label2.csv"))
    for fn in ("evidence_table.csv", "metrics.json", "predictions.npz",
               "confusion_label2.csv"):
        shutil.copy(os.path.join(RESULTS_DIR, fn), EVIDENCE_DIR)
    print(f"[eval] MODEL={model_desc}")
    print(f"[eval] label_2 test OA = {oa_l2*100:.4f}%  (anchor 95.13%)")
    print(f"[eval] label_2 macro-F1 = {mf1_l2*100:.3f}%  label_1 acc = {oa_l1*100:.3f}%")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="resnet", choices=["resnet", "mlp"])
    ap.add_argument("--ckpt", default=os.path.join(CHECKPOINT_DIR, "resnet18_mtl.pt"))
    args = ap.parse_args()

    set_seed(SEED)
    torch.set_num_threads(int(os.environ.get("TORCH_THREADS", "10")))
    os.makedirs(EVIDENCE_DIR, exist_ok=True)
    lab = load_labels()
    l1, l2, split = lab["label_1"], lab["label_2"], lab["split"]
    te = split == "test"

    if args.model == "resnet":
        imgmem = np.load(os.path.join(RESULTS_DIR, "images_224.memmap"),
                         mmap_mode="r")
        if not os.path.exists(args.ckpt):
            print(f"[eval] MISSING {args.ckpt}")
            sys.exit(2)
        pred2, pred1, p2, p1 = build_pred_resnet(args.ckpt, imgmem, te)
        shutil.copy(args.ckpt, os.path.join(EVIDENCE_DIR, "checkpoint_detached.pt"))
        desc = "ResNet18 (ImageNet init) fine-tune + two-level heads"
    else:
        d = np.load(os.path.join(RESULTS_DIR, "features_resnet18_224.npz"))
        feat = d["feat"]
        mpt = os.path.join(RESULTS_DIR, "mlp_probe.pt")
        if not os.path.exists(mpt):
            print("[eval] run 03b_mlp_probe.py first"); sys.exit(2)
        pred2, pred1, p2, p1 = build_pred_mlp(feat[te], mpt)
        shutil.copy(mpt, os.path.join(EVIDENCE_DIR, "checkpoint_detached.pt"))
        desc = "Frozen ResNet18 features + MLP heads"

    oa_l2 = accuracy_score(l2[te], pred2)
    mf1_l2 = f1_score(l2[te], pred2, average="macro", labels=list(range(N_L2)),
                      zero_division=0)
    oa_l1 = accuracy_score(l1[te], pred1)
    write_outputs(pred2, pred1, p2, p1, l2[te], l1[te], desc,
                  (int((split == "train").sum()), int(te.sum())),
                  oa_l2, mf1_l2, oa_l1)
    print("[eval] evidence copied")


if __name__ == "__main__":
    main()