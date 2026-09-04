"""Aggregate per-fold results into evidence_table.csv + metrics.json + summary.

Sources:
  results/baselines_perfold.csv         (LGBM, XGB, RF, lambdaMART, with-prior)
  results/rankformer_{ds}_fold{f}.json  (Rankformer baseline, with-prior + without-prior)
  results/scores/pabce_{ds}_fold{f}_s{s}.npy  (PA-RiskRanker per-seed test scores)
For PA-RiskRanker the reported metric = 3-seed score ensemble (mean), aligning
with the paper's "3-fold average" reporting granularity.
"""
from __future__ import annotations
import os, json, glob, numpy as np, pandas as pd
from sklearn.metrics import roc_auc_score
from common import prepare_fold, topk_metrics, threshold_metrics, ROOT

RESULTS = os.path.join(ROOT, "results")
SCORES = os.path.join(RESULTS, "scores")
SEEDS = [10, 20, 30]


def load_baselines():
    p = os.path.join(RESULTS, "baselines_perfold.csv")
    return pd.read_csv(p) if os.path.exists(p) else pd.DataFrame()


def load_rankformer():
    rows = []
    for fp in sorted(glob.glob(os.path.join(RESULTS, "rankformer_*_fold*.json"))):
        if any(k in fp for k in ("_v", "_tuned", "v6", "v7")):
            continue
        r = json.load(open(fp))
        csv = os.path.basename(fp).replace(".json", ".csv")
        m = {"model": "rankformer",
           **{k: r[k] for k in ("f1", "financial_loss", "precision", "sensitivity", "specificity")},
             "auc": r["auc"], "threshold": r["threshold"], "dataset": r["dataset"], "fold": r["fold"],
             "setting": "with_prior"}
        rows.append(m)
    return pd.DataFrame(rows)


def pabce_ensemble_rows(dataset):
    d = prepare_fold(dataset, 1)
    y_test, i_test = d["y_test"], d["i_test"]
    rows = []
    for fold in (1, 2, 3):
        scs = []
        for s in SEEDS:
            fp = os.path.join(SCORES, f"pabce_{dataset}_fold{fold}_s{s}.npy")
            if not os.path.exists(fp):
                continue
            scs.append((s, np.load(fp)))
        if not scs:
            continue
        ens = np.mean([x[1] for x in scs], axis=0)
        d = prepare_fold(dataset, fold)
        wp = topk_metrics(d["y_test"], ens, d["i_test"])
        auc = float(roc_auc_score(d["y_test"], ens))
        row = {"dataset": dataset, "setting": "with_prior", "model": "PARiskRanker",
               "fold": f"ens({','.join(map(str, [s for s, _ in scs]))})",
               **{k: wp[k] for k in ("f1", "financial_loss", "precision", "sensitivity", "specificity")},
               "auc": auc, "threshold": np.nan, "n_seeds": len(scs)}
        rows.append(row)
    return rows, scs


def pa_without_prior_rows(dataset):
    """without-prior PA-RiskRanker: standard prior-free cut at probability 0.5
    (logit = 0) applied to the ensembled test scores."""
    rows = []
    for fold in (1, 2, 3):
        scs = []
        for s in SEEDS:
            fp = os.path.join(SCORES, f"pabce_{dataset}_fold{fold}_s{s}.npy")
            if os.path.exists(fp):
                scs.append(np.load(fp))
        if not scs:
            continue
        ens = np.mean(scs, axis=0)
        d = prepare_fold(dataset, fold)
        m = threshold_metrics(d["y_test"], ens, d["i_test"], 0.0)
        rows.append({"dataset": dataset, "setting": "without_prior", "model": "PARiskRanker",
                     "fold": "ens(10,20,30)", "f1": m["f1"],
                     "financial_loss": m["financial_loss"],
                     "auc": float(roc_auc_score(d["y_test"], ens)),
                     "precision": m["precision"], "sensitivity": m["sensitivity"],
                     "specificity": m["specificity"]})
    return rows


def main():
    parts = [load_baselines(), load_rankformer()]
    pa_rows = []
    for dataset in ("creditcard", "jobprofit"):
        rows, _ = pabce_ensemble_rows(dataset)
        pa_rows += rows
        pa_rows += pa_without_prior_rows(dataset)
    pa = pd.DataFrame(pa_rows) if pa_rows else pd.DataFrame()
    cols = ["dataset", "setting", "model", "fold", "f1", "financial_loss",
            "auc", "precision", "sensitivity", "specificity"]
    ev = pd.concat([p.reindex(columns=cols) for p in parts] + ([pa.reindex(columns=cols)] if len(pa) else []),
                   ignore_index=True)
    ev.to_csv(os.path.join(RESULTS, "evidence_table.csv"), index=False)

    def num(s):
        return pd.to_numeric(s, errors="coerce")
    g = ev.copy()
    g["f1"] = num(g["f1"]); g["financial_loss"] = num(g["financial_loss"])
    g["auc"] = num(g["auc"]); g["precision"] = num(g["precision"])
    g["sensitivity"] = num(g["sensitivity"]); g["specificity"] = num(g["specificity"])
    m = g.groupby(["dataset", "setting", "model"], sort=False).mean(numeric_only=True).reset_index()
    m = m.sort_values(["dataset", "setting", "model"])
    m.to_csv(os.path.join(RESULTS, "means_table.csv"), index=False)
    metrics = {}
    for _, r in m.iterrows():
        metrics[f"{r.dataset}__{r.setting}__{r.model}"] = {
            k: round(float(r[k]), 4) if k != "financial_loss" else round(float(r[k]), 2)
            for k in ("f1", "financial_loss", "auc", "precision", "sensitivity", "specificity")}
    json.dump(metrics, open(os.path.join(RESULTS, "metrics.json"), "w"), indent=2)

    lines = ["# Results — with-prior / without-prior (3-fold averages)", "",
             "| dataset | setting | model | F1 | FinLoss | AUC | P | S | Sp |",
             "|---|---|---|---|---|---|---|---|---|"]
    for _, r in m.iterrows():
        lines.append(f"| {r.dataset} | {r.setting} | {r.model} | {r.f1:.4f} | {r.financial_loss:,.1f} | "
                     f"{r.auc:.4f} | {r.precision:.4f} | {r.sensitivity:.4f} | {r.specificity:.4f} |")
    open(os.path.join(RESULTS, "summary.md"), "w").write("\n".join(lines))
    print("\n".join(lines))
    print("\nsaved evidence_table.csv / metrics.json / means_table.csv / summary.md")


if __name__ == "__main__":
    main()