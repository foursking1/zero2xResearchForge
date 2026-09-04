"""Post-hoc analysis & figures from the evidence table. Reads results/evidence_table.csv
and results/metrics.json, regenerates all tables/plots. Also computes baselines
(language-only template prior, global majority) on the fixed image-level eval split.

Usage: python3 analysis.py
"""
import hashlib
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RESULTS = os.path.join(ROOT, "results")
EVIDENCE = os.path.join(RESULTS, "evidence_table.csv")
DATA = "/mnt/f/dataset/earth/2003.07333_rsvqa/data/data/validation-00000-of-00001.parquet"

QTYPE_NAMES = ["presence", "comparison", "count", "rural_urban"]


def img_hash(im):
    return hashlib.md5(im["bytes"]).hexdigest()


def main():
    ev = pd.read_csv(EVIDENCE)
    metrics = json.load(open(os.path.join(RESULTS, "metrics.json")))
    if "question_type" not in ev.columns:
        ev = ev.rename(columns={"qtype": "question_type", "question_norm": "question"})

    e = ev[ev["split"] == "eval"].copy()
    e["correct"] = e["correct"].map(lambda x: str(x).lower() == "true")

    # ------- Tables ---------------------------------------------------------
    rows = []
    for t in QTYPE_NAMES:
        m = e["question_type"] == t
        rows.append({"type": t, "n": int(m.sum()),
                     "accuracy": round(float(e.loc[m, "correct"].mean()), 4)})
    overall = pd.DataFrame(rows)
    print(overall.to_string())

    # ------- Figures --------------------------------------------------------
    labels = overall["type"].tolist()
    vals = overall["accuracy"].tolist()
    n = overall["n"].tolist()
    fig, ax = plt.subplots(figsize=(7, 4))
    bars = ax.bar(range(len(vals)), vals, color=["#4472C4", "#ED7D31", "#70AD47", "#A5A5A5"])
    for i, (v, nn) in enumerate(zip(vals, n)):
        ax.text(i, v + 0.01, f"{v:.0%}\n(n={nn})", ha="center", fontsize=9)
    ax.set_ylim(0, 1.05)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels)
    ax.set_ylabel("Accuracy")
    ax.set_title(f"RSVQA LR subset (eval) accuracy by question type — OA={metrics['overall_accuracy']:.2%}")
    fig.tight_layout()
    fig.savefig(os.path.join(RESULTS, "accuracy_by_type.png"), dpi=150)
    plt.close(fig)

    # count error histogram (log-scale counts)
    ce = e[e["question_type"] == "count"].copy()
    ce["gt"] = ce["answer"].astype(int)
    ce["pred"] = ce["prediction"].astype(int)
    ce["err"] = ce["gt"] - ce["pred"]
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.hist(ce["err"], bins=40, color="#70AD47", edgecolor="white")
    ax.set_xlabel("prediction error (true - predicted)")
    ax.set_ylabel("count questions")
    ax.set_title("Count questions: distribution of prediction errors")
    fig.tight_layout()
    fig.savefig(os.path.join(RESULTS, "count_errors.png"), dpi=150)
    plt.close(fig)

    # ------- Baselines --------------------------------------------------------
    df = pd.read_parquet(DATA)
    df["imgid"] = df["image"].map(img_hash)
    rng = np.random.RandomState(42)
    ids = sorted(df["imgid"].unique())
    rng.shuffle(ids)
    eval_ids = set(ids[80:])
    tr = df[~df["imgid"].isin(eval_ids)].copy()
    evd = df[df["imgid"].isin(eval_ids)].copy()
    tr["qnorm"] = tr["question"].astype(str).str.strip()
    evd["qnorm"] = evd["question"].astype(str).str.strip()
    tr["anorm"] = tr["answer"].astype(str).str.strip()
    evd["anorm"] = evd["answer"].astype(str).str.strip()

    # global majority
    maj = tr["anorm"].value_counts().idxmax()
    base_global = round(float((evd["anorm"] == maj).mean()), 4)
    # per-question-template majority (language-only prior)
    tpl = tr.groupby("qnorm")["anorm"].agg(lambda s: s.value_counts().idxmax())
    pred_lang = evd["qnorm"].map(tpl)
    lang_prior = round(float((pred_lang == evd["anorm"]).mean()), 4)
    # image-only majority (always >50% baseline: predict majority over all answers of image)
    lang_by_type = {}
    def qtype(qs):
        qs = str(qs).strip().lower()
        if "rural or an urban" in qs: return "rural_urban"
        if "more " in qs or "less " in qs or " than " in qs or "equal to the number" in qs: return "comparison"
        if "how many" in qs or "what is the number" in qs or "what is the amount" in qs: return "count"
        return "presence"
    evd["t"] = evd["question"].map(qtype)
    for t in QTYPE_NAMES:
        m = evd["t"] == t
        lang_by_type[t] = round(float((pred_lang[m] == evd.loc[m, "anorm"]).mean()), 4) if m.any() else None

    baselines = {
        "global_majority": base_global,
        "language_prior_template": lang_prior,
        "language_prior_by_type": lang_by_type,
    }
    print(json.dumps(baselines, indent=2))
    with open(os.path.join(RESULTS, "baselines.json"), "w") as f:
        json.dump(baselines, f, indent=2)

    # ------- By-type predicted-vs-truth confusion (yes/no) -------------------
    for t in ("presence", "comparison"):
        m = e["question_type"] == t
        sub = e[m]
        cm = pd.crosstab(sub["answer"], sub["prediction"], dropna=False)
        print(f"\n{t} confusion:\n{cm.to_string()}")


if __name__ == "__main__":
    main()