"""Train VQA models on the frozen split; select the best on the dev set.

Configs compared (all frozen ImageNet features, CPU):
  1. r18-concat   ResNet-18 global + LSTM -> concat MLP
  2. r18-mfb      ResNet-18 spatial + LSTM -> MFB with co-attention
  3. r18vit-concat ResNet-18 + ViT-B/16 globals -> concat MLP
  4. r18vit-mfb   ResNet-18 spatial + both globals -> MFB with co-attention
  5. vit-concat   ViT-B/16 global -> concat MLP

Model selection is done exclusively on the dev split; the evaluation split is
never used here (anti-leak).
"""
import json
import os
import sys

import numpy as np
import torch
import torch.nn as nn

import config
import models

DEVICE = torch.device("cpu")


def load_features():
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
    return maps, r18, vit


def build_qa_arrays(split_qas, maps, r18, vit):
    """Return lists of (id, img_feats, question_tokens, qtype, answer_idx)."""
    rows = []
    for v in split_qas:
        iid = v["Image_ID"].split(".")[0]
        n_r = maps["r18"][iid]
        n_v = maps["vit"][iid]
        feat_r = torch.from_numpy(r18["feats"][n_r])
        spat_r = torch.from_numpy(r18["spatial"][n_r])
        feat_v = torch.from_numpy(vit["feats"][n_v])
        rows.append(dict(iid=iid, fr=feat_r, spa=spat_r, fv=feat_v,
                         q=v["Question"], t=v["Question_Type"],
                         ans=v["Ground_Truth"]))
    return rows


def split_rows(all_rows, split_qas):
    """Map rows (in split.json order) to train/dev/eval."""
    return all_rows


class QADataset(torch.utils.data.Dataset):
    def __init__(self, rows, vocab, ans2idx):
        self.rows = rows
        self.vocab = vocab
        self.ans2idx = ans2idx

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, i):
        r = self.rows[i]
        toks = models.encode(r["q"], self.vocab)
        return dict(fr=r["fr"], spa=r["spa"], fv=r["fv"], toks=toks,
                    qtype=r["t"], ans=self.ans2idx[r["ans"]])


def collate(batch):
    fr = torch.stack([b["fr"] for b in batch])
    fv = torch.stack([b["fv"] for b in batch])
    spa = torch.stack([b["spa"] for b in batch])
    toks = models.pad_sequences([b["toks"] for b in batch])
    qtype = [b["qtype"] for b in batch]
    ans = torch.tensor([b["ans"] for b in batch])
    return fr, fv, spa, toks, qtype, ans


def build_img(fr, fv, featset):
    if featset["r18_plus_vit"]:
        return torch.cat([fr, fv], dim=1)
    return fv if featset["which"] == "vit" else fr


def run_training(all_rows, vocab, ans2idx, idx_split, featset, arch,
                 n_answers, masks, out_dir, epochs=80, lr=3e-4, bs=128,
                 patience=15):
    tr_idx, dv_idx, _ = idx_split

    def make_loader(idxs):
        ds = QADataset([all_rows[i] for i in idxs], vocab, ans2idx)
        return torch.utils.data.DataLoader(ds, batch_size=bs, shuffle=True,
                                           collate_fn=collate,
                                           num_workers=0)

    train_ld = make_loader(tr_idx)
    dev_ld = make_loader(dv_idx)

    img_dim = featset["dim"]
    net = models.JointNet(vocab, n_answers, img_dim, arch=arch, answer_masks=masks)
    net.to(DEVICE)

    opt = torch.optim.Adam(net.parameters(), lr=lr, weight_decay=1e-5)
    lossf = nn.CrossEntropyLoss()
    best_dev, best_state, best_epoch = 0.0, None, 0
    hist = []
    for ep in range(1, epochs + 1):
        net.train()
        tot, ok = 0, 0
        for fr, fv, spa, toks, qtype, ans in train_ld:
            img = build_img(fr, fv, featset)
            logits = net(img, spa, toks, qtype)
            loss = lossf(logits, ans)
            opt.zero_grad()
            loss.backward()
            opt.step()
            ok += (logits.argmax(1) == ans).sum().item()
            tot += len(ans)

        net.eval()
        dv_ok, dv_tot = 0, 0
        with torch.no_grad():
            for fr, fv, spa, toks, qtype, ans in dev_ld:
                img = build_img(fr, fv, featset)
                logits = net(img, spa, toks, qtype)
                dv_ok += (logits.argmax(1) == ans).sum().item()
                dv_tot += len(ans)
        dv_acc = dv_ok / max(dv_tot, 1)
        hist.append((ep, dv_acc))
        if dv_acc > best_dev:
            best_dev, best_epoch = dv_acc, ep
            best_state = {k: v.clone() for k, v in net.state_dict().items()}
        if ep - best_epoch >= patience:
            break

    model_path = os.path.join(out_dir, f"model_{featset['name']}_{arch}.pt")
    torch.save({"state": best_state, "arch": arch, "featset": featset["name"],
                "best_dev_acc": best_dev, "epoch": best_epoch,
                "img_dim": img_dim}, model_path)
    return best_dev, best_epoch, model_path


def main():
    cfg = json.load(open(os.path.join(config.RESULTS_DIR, "split.json")))
    split_qas = cfg["split_qa"]
    maps, r18, vit = load_features()
    rows = build_qa_arrays(split_qas["all"], maps, r18, vit)

    # answer vocabulary + per-type masks from the full official annotation file
    qa_all = json.load(open(config.VQA_TRAIN_JSON))
    vocab_ans = sorted({str(v["Ground_Truth"]) for v in qa_all.values()})
    ans2idx = {a: i for i, a in enumerate(vocab_ans)}
    n_answers = len(vocab_ans)

    type_answers = {}
    for v in qa_all.values():
        type_answers.setdefault(v["Question_Type"], set()).add(str(v["Ground_Truth"]))
    masks = {t: torch.tensor([ans2idx[a] for a in sorted(s)], dtype=torch.long)
             for t, s in type_answers.items()}

    idx_split = (
        [i for i, v in enumerate(split_qas["all"]) if v["Image_ID"] in
         set(cfg["split_images"]["train"])],
        [i for i, v in enumerate(split_qas["all"]) if v["Image_ID"] in
         set(cfg["split_images"]["dev"])],
        [i for i, v in enumerate(split_qas["all"]) if v["Image_ID"] in
         set(cfg["split_images"]["eval"])],
    )

    vocab = models.build_vocab([v["Question"] for v in split_qas["all"]])

    featsets = {
        "r18-concat": dict(name="r18", which="r18", dim=512, r18_plus_vit=False),
        "r18-mfb": dict(name="r18", which="r18", dim=512, r18_plus_vit=False),
        "r18vit-concat": dict(name="r18vit", which="r18", dim=1280, r18_plus_vit=True),
        "r18vit-mfb": dict(name="r18vit", which="r18", dim=1280, r18_plus_vit=True),
        "vit-concat": dict(name="vit", which="vit", dim=768, r18_plus_vit=False),
    }
    arch_per = {"r18-concat": "concat", "r18-mfb": "mfb",
                "r18vit-concat": "concat", "r18vit-mfb": "mfb",
                "vit-concat": "concat"}

    results = {}
    for name, featset in featsets.items():
        print(f"\n=== training {name} ===")
        dev_acc, best_ep, path = run_training(
            rows, vocab, ans2idx, idx_split, featset, arch_per[name],
            n_answers, masks, config.WORKSPACE)
        results[name] = {"dev_acc": dev_acc, "model": os.path.basename(path),
                         "best_epoch": best_ep}
        print(f"  best dev acc {dev_acc:.4f} (epoch {best_ep})")

    with open(os.path.join(config.RESULTS_DIR, "train_summary.json"), "w") as f:
        json.dump({k: {"dev_acc": v["dev_acc"], "model": v["model"]}
                   for k, v in results.items()}, f, indent=2)
    best = max(results, key=lambda k: results[k]["dev_acc"])
    print("\nBEST:", best, results[best])


if __name__ == "__main__":
    torch.manual_seed(config.SEED)
    np.random.seed(config.SEED)
    main()