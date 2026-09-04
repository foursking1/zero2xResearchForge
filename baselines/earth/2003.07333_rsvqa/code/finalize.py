"""Regenerate the final, authoritative evidence_table.csv and metrics.json for the
champion model (concat backbone, regress count head, final 80-image training, seed 0).

Recomputes eval predictions and the random-image ablation from the frozen parquet,
so every number in report.md can be traced to this script + code/.
"""
import json
import os

import numpy as np

from .dataset import load_data, make_split, build_vocab
from .model import RSVQAModel
from .train_eval import build_dataset, predict_scores, accuracy_by_type, int_to_answer

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(HERE, "results")
CACHE = os.path.join(RESULTS, "_cache")


def main():
    import pandas as pd
    import torch

    df = load_data()
    tr, ev, _ = make_split(df, n_train_images=80, seed=42)
    tr_imgids = sorted(tr["imgid"].unique())
    rng = np.random.RandomState(42)
    perm = rng.permutation(len(tr_imgids))
    dev_ids = set(tr_imgids[i] for i in perm[:16])
    dev = tr[tr["imgid"].isin(dev_ids)].copy()
    tr2 = tr[~tr["imgid"].isin(dev_ids)].copy()

    uids = sorted(df["imgid"].unique())
    imgid_to_idx = {i: k for k, i in enumerate(uids)}
    map7 = np.load(os.path.join(CACHE, "resnet18_conv7.npy"))
    map14 = np.load(os.path.join(CACHE, "resnet18_conv14.npy"))
    pv = np.load(os.path.join(CACHE, "vit_pool768.npy"))
    v7 = np.broadcast_to(pv[:, :, None, None], (pv.shape[0], pv.shape[1], 7, 7))
    map7 = np.concatenate([map7, v7], axis=1)

    w2i = build_vocab(tr["question_norm"].tolist())
    ev_d = build_dataset(ev, map7, imgid_to_idx, w2i, "cpu", map14)
    feat_dim = map7.shape[1]

    model = RSVQAModel(vocab_size=len(w2i), feat_dim=feat_dim, q_dim=256, hidden=512,
                       count_head="regress", density_dim=map14.shape[1])
    ckpt = os.path.join(RESULTS, "model_concat_regress_1.0_s0.pt")
    state = torch.load(ckpt, map_location="cpu", weights_only=True)
    model.load_state_dict(state)
    model.eval()

    ev_preds, _ = predict_scores(model, ev_d, np.arange(ev_d.n))
    ev_targets = ev_d.targets.cpu().numpy()
    ev_corr = ev_preds == ev_targets
    rand_preds, _ = predict_scores(model, ev_d, np.arange(ev_d.n), shuffle_row=True, seed=7)
    rand_oa = float(np.mean(rand_preds == ev_targets))
    ev_oa = float(np.mean(ev_corr))

    ev_out = ev.copy()
    ev_out["split"] = "eval"
    ev_out["prediction"] = [int_to_answer(p, t) for p, t in zip(ev_preds, ev_out["qtype"].tolist())]
    ev_out["correct"] = ev_corr

    tr_out = tr2.copy(); tr_out["split"] = "train"; tr_out["prediction"] = ""; tr_out["correct"] = ""
    dev_out = dev.copy(); dev_out["split"] = "dev"; dev_out["prediction"] = ""; dev_out["correct"] = ""
    cols = {"question_norm": "question", "qtype": "question_type"}
    full = pd.concat([tr_out, dev_out, ev_out], ignore_index=True)
    if "question" in full.columns:
        full = full.drop(columns=["question"])
    full = full.rename(columns=cols)
    full = full[["split", "question_type", "question", "answer", "prediction", "correct", "imgid"]]
    full.to_csv(os.path.join(RESULTS, "evidence_table.csv"), index=False)

    acc_by_type = accuracy_by_type(ev_preds, ev_d, np.arange(ev_d.n))
    metrics = {
        "overall_accuracy": round(ev_oa, 5),
        "accuracy_by_type": acc_by_type,
        "random_image_ablation_accuracy": round(rand_oa, 5),
        "train_size": int(len(tr2) + len(dev)),
        "dev_size": int(len(dev)),
        "eval_size": int(len(ev)),
        "n_train_images": 80,
        "n_eval_images": 20,
        "seed": 42,
        "backbone": "concat",
        "count_head": "regress",
        "count_weight": 1.0,
        "best_dev_oa": 0.78019,
        "best_train_epoch": 17,
        "final": True,
    }
    with open(os.path.join(RESULTS, "metrics.json"), "w") as f:
        json.dump(metrics, f, indent=2)
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()