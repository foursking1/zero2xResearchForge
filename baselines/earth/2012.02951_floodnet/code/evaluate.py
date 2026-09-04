"""Final evaluation of the selected model and ablation evidence.

Runs on the frozen evaluation split (never touched during model selection),
computes overall accuracy and per-question-type accuracy, then runs:

  * random-image ablation (fixed seed): pair each eval question with a random
    different image feature -> expected large drop if the model uses images;
  * language-prior baseline: best-fusion model trained on the same hyperparams
    but with image features zeroed -> measures how much of the accuracy is
    achievable from language alone;
  * majority-per-template prior on eval.

Writes results/evidence_table.csv and results/metrics.json.
"""
import json
import os

import numpy as np
import torch

import config
import models

DEVICE = torch.device("cpu")


def load_data():
    cfg = json.load(open(os.path.join(config.RESULTS_DIR, "split.json")))
    d18 = np.load(os.path.join(config.WORKSPACE, "features_r18.npz"))
    dvit = np.load(os.path.join(config.WORKSPACE, "features_vit.npz"))
    r18 = {"feats": np.array(d18["feats"]), "spatial": np.array(d18["spatial"]),
           "ids": np.array(d18["ids"])}
    vit = {"feats": np.array(dvit["feats"]), "ids": np.array(dvit["ids"])}
    maps = {}
    for kind, d in (("r18", r18), ("vit", vit)):
        ids = [str(i) for i in d["ids"]]
        keys = [i.split(".")[0] for i in ids]
        maps[kind] = {k: n for n, k in enumerate(keys)}
    rows = {}
    for split, qas in cfg["split_qa"].items():
        split_rows = []
        for v in qas:
            n_r = maps["r18"][v["Image_ID"].split(".")[0]]
            n_v = maps["vit"][v["Image_ID"].split(".")[0]]
            split_rows.append(dict(
                iid=v["Image_ID"], q=v["Question"], t=v["Question_Type"],
                ans=str(v["Ground_Truth"]),
                fr=torch.from_numpy(r18["feats"][n_r]),
                spa=torch.from_numpy(r18["spatial"][n_r]),
                fv=torch.from_numpy(vit["feats"][n_v])))
        rows[split] = split_rows
    return cfg, rows, maps, r18, vit


def build_model(train_summary, r18, vit, cfg):
    qa_all = json.load(open(config.VQA_TRAIN_JSON))
    vocab_ans = sorted({str(v["Ground_Truth"]) for v in qa_all.values()})
    ans2idx = {a: i for i, a in enumerate(vocab_ans)}
    type_answers = {}
    for v in qa_all.values():
        type_answers.setdefault(v["Question_Type"], set()).add(str(v["Ground_Truth"]))
    masks = {t: torch.tensor([ans2idx[a] for a in sorted(s)], dtype=torch.long)
             for t, s in type_answers.items()}
    vocab = models.build_vocab([v["Question"] for v in qa_all.values()])

    best_name = max(train_summary, key=lambda k: train_summary[k]["dev_acc"])
    meta = train_summary[best_name]
    ckpt = torch.load(os.path.join(config.WORKSPACE, meta["model"]), map_location="cpu")
    return (best_name, ckpt["arch"], ckpt["featset"], ckpt["img_dim"], ckpt["epoch"],
            ckpt["best_dev_acc"]), vocab, ans2idx, masks


@torch.no_grad()
def predict(net, rows, featset, shuffle_seed=None, zero_images=False):
    """Return list of predicted answer indices for rows.

    shuffle_seed -> pair each question with a random other image's features
    (BOTH global and spatial features swapped consistently) to test how much
    the model relies on the image. zero_images -> replace all image features
    (global + spatial) with zeros (pure-language baseline).
    """
    n = len(rows)
    if zero_images:
        # no visual information whatsoever
        pass
    elif shuffle_seed is not None:
        rng = np.random.RandomState(shuffle_seed)
        perm = rng.permutation(n)
        while (perm == np.arange(n)).all():
            perm = rng.permutation(n)
        rows = [rows[perm[i]] for i in range(n)]

    def build(r):
        img = torch.cat([r["fr"], r["fv"]], dim=0) if featset == "r18vit" else (
            r["fv"] if featset == "vit" else r["fr"])
        spa = r["spa"]
        if zero_images:
            img = torch.zeros_like(img)
            spa = torch.zeros_like(spa)
        return img, spa

    preds = []
    bs = 256
    for i in range(0, n, bs):
        b = rows[i:i + bs]
        pairs = [build(r) for r in b]
        imgfeat = torch.stack([p[0] for p in pairs])
        spa = torch.stack([p[1] for p in pairs])
        toks = models.pad_sequences([models.encode(r["q"], net.vocab) for r in b])
        qtypes = [r["t"] for r in b]
        logits = net(imgfeat, spa, toks, qtypes)
        preds.extend(logits.argmax(1).tolist())
    return preds


def acc_by(rows, preds):
    exact = [1 if rows[i]["ans"] == preds[i] else 0 for i in range(len(rows))]
    types = sorted({r["t"] for r in rows})
    per_type = {}
    for t in types:
        idx = [i for i, r in enumerate(rows) if r["t"] == t]
        per_type[t] = sum(exact[i] for i in idx) / max(len(idx), 1)
    return sum(exact) / max(len(exact), 1), per_type, exact


def train_prior_model(cfg, rows, vocab, ans2idx, masks, featset, arch, img_dim,
                      zero_images=False, epochs=60):
    """Train for a language-prior baseline (image features replaced by zeros)."""
    net = models.JointNet(vocab, len(ans2idx), img_dim, arch=arch,
                          answer_masks=masks).to(DEVICE)
    tr_rows = rows["train"];
    dv_rows = rows["dev"]
    # deterministic order
    tr_ids = [i for i in range(len(tr_rows))]
    rng = np.random.RandomState(123)
    rng.shuffle(tr_ids)
    opt = torch.optim.Adam(net.parameters(), lr=3e-4, weight_decay=1e-5)
    lossf = torch.nn.CrossEntropyLoss()

    def feats(row):
        zed = torch.zeros(img_dim)
        if zero_images:
            img = zed
            spa = torch.zeros_like(row["spa"])
        else:
            if featset == "r18vit":
                img = torch.cat([row["fr"], row["fv"]], dim=0)
            else:
                img = row["fv"] if featset == "vit" else row["fr"]
            spa = row["spa"]
        return img, spa

    best_dv, best_state = 0.0, None
    bs = 128
    for ep in range(epochs):
        net.train()
        for i in range(0, len(tr_ids), bs):
            bidx = tr_ids[i:i + bs]
            b = [tr_rows[j] for j in bidx]
            img = torch.stack([feats(r)[0] for r in b])
            spa = torch.stack([feats(r)[1] for r in b])
            toks = models.pad_sequences([models.encode(r["q"], vocab) for r in b])
            qtype = [r["t"] for r in b]
            ans = torch.tensor([ans2idx[r["ans"]] for r in b])
            logits = net(img, spa, toks, qtype)
            loss = lossf(logits, ans)
            opt.zero_grad(); loss.backward(); opt.step()
        net.eval()
        with torch.no_grad():
            b = dv_rows
            img = torch.stack([feats(r)[0] for r in b])
            spa = torch.stack([feats(r)[1] for r in b])
            toks = models.pad_sequences([models.encode(r["q"], vocab) for r in b])
            qtype = [r["t"] for r in b]
            ans = torch.tensor([ans2idx[r["ans"]] for r in b])
            logits = net(img, spa, toks, qtype)
            acc = (logits.argmax(1) == ans).float().mean().item()
        if acc > best_dv:
            best_dv = acc
            best_state = {k: v.clone() for k, v in net.state_dict().items()}
    net.load_state_dict(best_state)
    return net, best_dv


def main():
    cfg, rows, maps, r18, vit = load_data()
    train_summary = json.load(open(os.path.join(config.RESULTS_DIR, "train_summary.json")))
    (best_name, arch, featset, img_dim, best_ep, best_dev), vocab, ans2idx, masks = \
        build_model(train_summary, r18, vit, cfg)

    net = models.JointNet(vocab, len(ans2idx), img_dim, arch=arch, answer_masks=masks)
    ckpt = torch.load(os.path.join(config.WORKSPACE, train_summary[best_name]["model"]),
                      map_location="cpu")
    net.load_state_dict(ckpt["state"])
    net.eval()

    inv = {i: a for a, i in ans2idx.items()}

    # ---- per-split predictions ------------------------------------------
    results = {}
    for split in ("train", "dev", "eval"):
        preds = predict(net, rows[split], featset)
        pred_str = [inv[p] for p in preds]
        results[split] = acc_by(rows[split], pred_str)
    oa_eval = results["eval"][0]

    # ---- random-image ablation (eval) ------------------------------------
    preds_sh = predict(net, rows["eval"], featset, shuffle_seed=config.SEED)
    pred_str_sh = [inv[p] for p in preds_sh]
    oa_rand = acc_by(rows["eval"], pred_str_sh)[0]

    # ---- language-prior baseline (zeroed image features) -----------------
    prior_net, prior_dev = train_prior_model(cfg, rows, vocab, ans2idx, masks,
                                             featset, arch, img_dim, zero_images=True)
    prior_net.eval()
    preds_prior = predict(prior_net, rows["eval"], featset, zero_images=True)
    oa_prior = acc_by(rows["eval"], [inv[p] for p in preds_prior])[0]

    # ---- majority-per-template prior -------------------------------------
    from collections import defaultdict, Counter
    prior_tpl = defaultdict(list)
    for r in rows["train"]:
        prior_tpl[r["q"]].append(r["ans"])
    maj = {q: Counter(a).most_common(1)[0][0] for q, a in prior_tpl.items()}
    oa_maj = sum(1 for r in rows["eval"]
                 if maj.get(r["q"], None) == r["ans"]) / max(len(rows["eval"]), 1)

    # ---- evidence table ---------------------------------------------------
    import csv
    rows_out = []
    for split in ("train", "dev", "eval"):
        pred_str = [inv[p] for p in predict(net, rows[split], featset)]
        for r, p in zip(rows[split], pred_str):
            rows_out.append(dict(split=split, question_type=r["t"], image_id=r["iid"],
                                 question=r["q"], answer=r["ans"], prediction=p,
                                 correct=int(p == r["ans"])))
    with open(os.path.join(config.RESULTS_DIR, "evidence_table.csv"), "w",
              newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["split", "question_type", "image_id",
                                          "question", "answer", "prediction", "correct"])
        w.writeheader()
        w.writerows(rows_out)
    print("wrote evidence_table.csv", len(rows_out), "rows")

    # ---- metrics json ------------------------------------------------------
    by_type_eval = results["eval"][1]
    anchor = 0.72
    metrics = {
        "task": "2012.02951_floodnet",
        "anchor_overall_accuracy_paper": anchor,
        "overall_accuracy": round(oa_eval, 4),
        "relative_diff_vs_anchor": round(abs(oa_eval - anchor) / anchor, 4),
        "split": "agent image-level 85/15 eval split (official Valid/Test answers unpublished)",
        "question_split": {"train": cfg["meta"]["train"]["n_qa"],
                           "dev": cfg["meta"]["dev"]["n_qa"],
                           "eval": cfg["meta"]["eval"]["n_qa"]},
        "image_split": cfg["meta"]["image_split"],
        "train_size": cfg["meta"]["train"]["n_qa"],
        "seed": config.SEED,
        "accuracy_by_type": {k: round(v, 4) for k, v in by_type_eval.items()},
        "accuracy_split": {k: (round(v[0], 4)) for k, v in results.items()},
        "random_image_ablation_accuracy": round(oa_rand, 4),
        "language_prior_accuracy_zeroed_image": round(oa_prior, 4),
        "majority_per_template_prior_accuracy": round(oa_maj, 4),
        "best_config": best_name,
        "best_dev_acc": round(best_dev, 4),
        "best_epoch": best_ep,
        "architecture": arch,
        "pretrained_features": featset,
    }
    with open(os.path.join(config.RESULTS_DIR, "metrics.json"), "w") as f:
        json.dump(metrics, f, indent=2)
    print(json.dumps(metrics, indent=2))

    # ---- by-type summary csv ----------------------------------------------
    with open(os.path.join(config.RESULTS_DIR, "by_type_summary.csv"), "w",
              newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["split", "question_type", "accuracy", "n_qas"])
        for split in ("eval", "dev", "train"):
            n_by_type = defaultdict(int)
            for r in rows[split]:
                n_by_type[r["t"]] += 1
            if split == "eval":
                acc_map = by_type_eval
            else:
                _, _, exacts = results[split]
                acc_map = {}
                for t in n_by_type:
                    idx = [i for i, r in enumerate(rows[split]) if r["t"] == t]
                    acc_map[t] = sum(exacts[i] for i in idx) / len(idx)
            for t, n in sorted(n_by_type.items()):
                w.writerow([split, t, round(acc_map[t], 4), n])

    print("done.")


if __name__ == "__main__":
    torch.manual_seed(config.SEED)
    np.random.seed(config.SEED)
    main()