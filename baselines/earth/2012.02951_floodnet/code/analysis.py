"""Deep analysis + figures for the report (uses the frozen split & features).

Produces results/per_template.csv, results/per_template_eval.csv and figures/
  * fig_accuracy_by_type.png      eval accuracy per question type vs paper anchor
  * fig_counting_scatter.png      true vs predicted count (counting templates)
  * fig_visual_vs_language.png    per-type accuracy: images vs zeroed-image prior
"""
import json
import os
from collections import Counter, defaultdict

import numpy as np
import torch

import config
import evaluate as E
import models

DEVICE = torch.device("cpu")


def main():
    cfg, rows, maps, r18, vit = E.load_data()
    train_summary = json.load(open(os.path.join(config.RESULTS_DIR, "train_summary.json")))
    (best_name, arch, featset, img_dim, best_ep, best_dev), vocab, ans2idx, masks = \
        E.build_model(train_summary, r18, vit, cfg)

    net = models.JointNet(vocab, len(ans2idx), img_dim, arch=arch, answer_masks=masks)
    ckpt = torch.load(os.path.join(config.WORKSPACE, train_summary[best_name]["model"]),
                      map_location="cpu")
    net.load_state_dict(ckpt["state"])
    net.eval()

    # re-train language prior exactly like evaluate.py
    prior_net, prior_dev = E.train_prior_model(cfg, rows, vocab, ans2idx, masks,
                                               featset, arch, img_dim, zero_images=True)
    prior_net.eval()

    inv = {i: a for a, i in ans2idx.items()}
    ev = rows["eval"]

    preds_img = [inv[p] for p in E.predict(net, ev, featset)]
    preds_rand = [inv[p] for p in E.predict(net, ev, featset, shuffle_seed=config.SEED)]
    preds_prior = [inv[p] for p in E.predict(prior_net, ev, featset, zero_images=True)]

    def exact(preds):
        return {i: preds[i] == ev[i]["ans"] for i in range(len(ev))}

    corr_img = exact(preds_img)
    corr_rand = exact(preds_rand)
    corr_prior = exact(preds_prior)

    # ---------------- per-template (eval) ---------------------------------
    import csv
    tpl = defaultdict(list)
    for i, r in enumerate(ev):
        tpl[(r["q"], r["t"])].append(i)
    with open(os.path.join(config.RESULTS_DIR, "per_template_eval.csv"), "w",
              newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["question", "question_type", "n", "accuracy_images",
                    "accuracy_random_image", "accuracy_zeroed_image",
                    "majority_prior_accuracy"])
        for (q, t), idx in sorted(tpl.items(), key=lambda kv: -len(kv[1])):
            prior = Counter(ev[i]["ans"] for i in idx).most_common(1)[0][0]
            w.writerow([q, t, len(idx),
                        round(sum(corr_img[i] for i in idx) / len(idx), 4),
                        round(sum(corr_rand[i] for i in idx) / len(idx), 4),
                        round(sum(corr_prior[i] for i in idx) / len(idx), 4),
                        round(sum(ev[i]["ans"] == prior for i in idx) / len(idx), 4)])

    # ---------------- counting analysis -----------------------------------
    counting_ev = [(i, ev[i]["ans"], int(preds_img[i])) for i in range(len(ev))
                   if ev[i]["t"] in ("Simple_Counting", "Complex_Counting")]
    c_true = np.array([int(a) for _, a, _ in counting_ev])
    c_pred = np.array([p for _, _, p in counting_ev])
    mae = np.abs(c_true - c_pred).mean()
    acc_exact = (c_true == c_pred).mean()
    acc_oneoff = (np.abs(c_true - c_pred) <= 1).mean()

    # ---------------- by-type: images vs language --------------------------
    types = sorted({r["t"] for r in ev})
    by_type = {}
    for t in types:
        idx = [i for i, r in enumerate(ev) if r["t"] == t]
        by_type[t] = {
            "accuracy_images": sum(corr_img[i] for i in idx) / len(idx),
            "accuracy_random_image": sum(corr_rand[i] for i in idx) / len(idx),
            "accuracy_zeroed_image": sum(corr_prior[i] for i in idx) / len(idx),
            "n": len(idx),
        }

    # ---------------- figures ----------------------------------------------
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    paper = {"Simple_Counting": 0.31, "Complex_Counting": 0.28,
             "Yes_No": 0.98, "Condition_Recognition": 0.96}
    names = {v: k for v, k in
             [("Simple_Counting", "Simple Counting"), ("Complex_Counting", "Complex Counting"),
              ("Yes_No", "Yes/No"), ("Condition_Recognition", "Condition Recognition")]}

    fig, ax = plt.subplots(figsize=(9, 4.6))
    x = np.arange(len(types))
    w = 0.36
    ax.bar(x - w / 2, [by_type[t]["accuracy_images"] for t in types], w,
           label="This work (eval, 85/15 split)")
    ax.bar(x + w / 2, [paper[t] for t in types], w,
           label="Paper Table 5 (MFB co-attn, validation)")
    ax.set_xticks(x)
    ax.set_xticklabels([names[t] for t in types], rotation=12)
    ax.set_ylabel("Accuracy")
    ax.set_ylim(0, 1.05)
    ax.axhline(0.72, ls="--", c="gray", lw=1)
    ax.text(3.3, 0.73, "anchor OA 0.72", fontsize=8, color="gray")
    ax.set_title("FloodNet VQA per-type accuracy vs paper anchor")
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(config.FIGURES_DIR, "fig_accuracy_by_type.png"), dpi=150)

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.4), sharey=True)
    for ax, t in zip(axes, ("Simple_Counting", "Complex_Counting")):
        idx = [(i, int(ev[i]["ans"]), int(preds_img[i])) for i in range(len(ev))
               if ev[i]["t"] == t]
        tt = np.array([a for _, a, _ in idx])
        pp = np.array([p for _, _, p in idx])
        ax.scatter(tt, pp, s=8, alpha=0.55)
        m = max(tt.max(), pp.max())
        ax.plot([0, m], [0, m], ls="--", c="gray")
        ax.set_xlabel("True count")
        ax.set_ylabel("Predicted count")
        ax.set_title(f"{names[t]}  (acc={np.mean(tt==pp):.3f})")
    fig.suptitle("Counting questions: true vs predicted (eval)")
    fig.tight_layout()
    fig.savefig(os.path.join(config.FIGURES_DIR, "fig_counting_scatter.png"), dpi=150)

    fig, ax = plt.subplots(figsize=(8.5, 4.4))
    x = np.arange(len(types))
    ax.bar(x - w, [by_type[t]["accuracy_images"] for t in types], w, label="with images")
    ax.bar(x, [by_type[t]["accuracy_random_image"] for t in types], w, label="random image")
    ax.bar(x + w, [by_type[t]["accuracy_zeroed_image"] for t in types], w, label="zeroed image (lang prior)")
    ax.set_xticks(x)
    ax.set_xticklabels([names[t] for t in types], rotation=12)
    ax.set_ylabel("Accuracy")
    ax.set_ylim(0, 1.05)
    ax.set_title("Language-bias diagnostics (eval split)")
    ax.legend(fontsize=9)
    fig.tight_layout()
    fig.savefig(os.path.join(config.FIGURES_DIR, "fig_visual_vs_language.png"), dpi=150)

    print("per-template table ->", os.path.join(config.RESULTS_DIR, "per_template_eval.csv"))
    print("counting mae", round(mae, 3), "exact", round(acc_exact, 4),
          "within1", round(acc_oneoff, 4))

    # save counting stats
    out = {
        "counting": {"mae": mae, "accuracy_exact": acc_exact, "accuracy_within_1": acc_oneoff},
        "per_type": {t: {k: round(v, 4) for k, v in d.items()} for t, d in by_type.items()},
    }
    json.dump(out, open(os.path.join(config.RESULTS_DIR, "analysis.json"), "w"), indent=2)


if __name__ == "__main__":
    torch.manual_seed(config.SEED)
    np.random.seed(config.SEED)
    main()