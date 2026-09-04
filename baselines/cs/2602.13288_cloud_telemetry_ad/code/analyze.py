"""Post-hoc analysis: claim verdicts, paper Table III comparison, figures.

Reads results/evidence_table.csv and results/series_raw.csv (produced by
run_series.py) and writes:

  results/claim_summary.json          - claim verdict data
  results/subgroup_scores_table.csv   - subgroup x model matrix
  results/fig_subgroup_heatmap.png    - heatmap of NAB scores
  results/fig_attribution_bars.png    - best-model attribution per subgroup
  results/fig_per_series_grus.png     - example per-series GRU detection
"""

from __future__ import annotations

import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "..", "results")

MODELS = ["GRU", "TCN", "Transformer", "TSMixer", "IsolationForest"]

# Paper Table III anchor values (for the "direction/magnitude" comparison only)
PAPER_MS = {
    "application-crash-rate-1": {"GRU": 31.76, "TSMixer": 31.68, "Transformer": 29.34, "TCN": 23.13, "IsolationForest": 11.25},
    "application-crash-rate-2": {"GRU": 35.70, "TSMixer": 29.64, "Transformer": 32.01, "TCN": 33.20, "IsolationForest": 0.00},
    "consumer-purchase-rate": {"GRU": 48.24, "TSMixer": 62.93, "Transformer": 44.16, "TCN": 48.12, "IsolationForest": 0.00},
    "ecommerce-api-incoming-rps": {"GRU": 36.83, "TSMixer": 19.07, "Transformer": 45.71, "TCN": 6.95, "IsolationForest": 9.93},
    "mongodb-machine-rps": {"GRU": 18.01, "TSMixer": 0.00, "Transformer": 0.00, "TCN": 0.00, "IsolationForest": 0.00},
    "data-ingress-rate": {m: 0.00 for m in MODELS},
    "middle-tier-api-dependency-latency": {m: 0.00 for m in MODELS},
    "mongodb-application-rps": {m: 0.00 for m in MODELS},
    "service-unavailable": {m: 0.00 for m in MODELS},
}
PAPER_NAB = {
    "artificialWithAnomaly": {"GRU": 11.06, "TSMixer": 0.00, "Transformer": 0.00, "TCN": 0.00, "IsolationForest": 0.00},
    "realAdExchange": {"GRU": 0.00, "TSMixer": 0.00, "Transformer": 5.52, "TCN": 2.77, "IsolationForest": 0.00},
    "realAWSCloudwatch": {"GRU": 5.82, "TSMixer": 9.83, "Transformer": 0.00, "TCN": 16.44, "IsolationForest": 0.00},
    "realKnownCause": {"GRU": 0.00, "TSMixer": 2.30, "Transformer": 0.00, "TCN": 0.00, "IsolationForest": 0.00},
    "realTraffic": {"GRU": 20.26, "TSMixer": 18.27, "Transformer": 3.85, "TCN": 0.00, "IsolationForest": 0.00},
    "realTweets": {"GRU": 0.00, "TSMixer": 0.00, "Transformer": 6.11, "TCN": 0.00, "IsolationForest": 0.00},
    "artificialNoAnomaly": {m: 0.00 for m in MODELS},
}

MS_CLAIM_SUBGROUPS = ["application-crash-rate-1", "application-crash-rate-2",
                      "consumer-purchase-rate", "ecommerce-api-incoming-rps",
                      "mongodb-machine-rps"]
NAB_CLAIM_SUBGROUPS = ["artificialWithAnomaly", "realAdExchange",
                       "realAWSCloudwatch", "realKnownCause", "realTraffic",
                       "realTweets"]


def load():
    ev = pd.read_csv(os.path.join(RES, "evidence_table.csv"))
    raw = pd.read_csv(os.path.join(RES, "series_raw.csv"))
    return ev, raw


def matrix(ev, dataset):
    pv = ev[ev["dataset"] == dataset].pivot(index="subgroup", columns="model",
                                            values="nab_score")
    pv = pv.reindex(columns=[m for m in MODELS if m in pv.columns])
    return pv


def claim_a(ev):
    pv = matrix(ev, "microsoft")
    rec = {}
    for sg in MS_CLAIM_SUBGROUPS:
        row = {m: float(pv.loc[sg, m]) for m in MODELS}
        rec[sg] = row
    pos = {}
    for m in MODELS:
        pos[m] = all(rec[sg][m] > 0 for sg in MS_CLAIM_SUBGROUPS)
    gru_all_pos = pos["GRU"]
    others_all_pos = [m for m in MODELS if m != "GRU" and pos[m]]
    return {"per_subgroup": rec, "model_all_positive": pos,
            "gru_all_positive": gru_all_pos, "others_all_positive": others_all_pos}


def claim_b(ev):
    pv = matrix(ev, "nab")
    best = {}
    for sg in NAB_CLAIM_SUBGROUPS:
        row = {m: float(pv.loc[sg, m]) for m in MODELS}
        top = max(row, key=row.get)
        best[sg] = {"best_model": top, "best_score": row[top],
                    "all": row, "n_pos": sum(1 for v in row.values() if v > 0)}
    n_arch = len({v["best_model"] for v in best.values()})
    return {"best": best, "n_distinct_architectures": n_arch}


def fmt_verdict(claim):
    return (f"claim(a): GRU all-positive={claim['gru_all_positive']}, "
            f"other all-positive models={claim['others_all_positive'] or 'none'}")


def make_figures(ev, raw, outdir):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(17, 6))
    for ax, ds, title in ((axes[0], "microsoft", "Microsoft Cloud Monitoring"),
                          (axes[1], "nab", "NAB")):
        pv = matrix(ev, ds)
        cols = list(pv.columns)
        data = pv.values.astype(float)
        im = ax.imshow(data, cmap="RdYlGn", vmin=-40, vmax=80)
        ax.set_xticks(range(len(cols))); ax.set_xticklabels(cols, rotation=30)
        ax.set_yticks(range(len(pv.index))); ax.set_yticklabels(pv.index)
        for i in range(data.shape[0]):
            for j in range(data.shape[1]):
                ax.text(j, i, f"{data[i, j]:.0f}", ha="center", va="center",
                        fontsize=8, color="black" if abs(data[i, j]) < 40 else "white")
        ax.set_title(title)
        fig.colorbar(im, ax=ax, shrink=0.8, label="normalized NAB score")
    fig.tight_layout()
    fig.savefig(os.path.join(outdir, "fig_subgroup_heatmap.png"), dpi=140)
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(16, 5))
    for ax, ds, subs, part in ((axes[0], "microsoft", MS_CLAIM_SUBGROUPS, "a"),
                               (axes[1], "nab", NAB_CLAIM_SUBGROUPS, "b")):
        pv = matrix(ev, ds)
        x = np.arange(len(subs))
        for k, m in enumerate(MODELS):
            ax.bar(x - 0.36 + k * 0.18, [pv.loc[sg, m] for sg in subs],
                   0.17, label=m)
        ax.axhline(0, color="k", lw=0.8)
        ax.set_xticks(x); ax.set_xticklabels(subs, rotation=20, ha="right")
        ax.set_title(f"claim ({part}): subgroup scores by model")
        ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(outdir, "fig_subgroup_bars.png"), dpi=140)
    plt.close(fig)


def main():
    ev, raw = load()
    ca = claim_a(ev)
    cb = claim_b(ev)

    summary = {
        "claim_a": ca,
        "claim_a_verdict": ("supported" if (ca["gru_all_positive"] and not ca["others_all_positive"])
                            else "partially_supported"),
        "claim_b": cb,
        "claim_b_verdict": ("supported" if cb["n_distinct_architectures"] >= 3 else "not_supported"),
        "n_series_failed": int(raw["ok"].value_counts().get(False, 0)),
        "raw_matrix_microsoft": matrix(ev, "microsoft").round(3).to_dict(),
        "raw_matrix_nab": matrix(ev, "nab").round(3).to_dict(),
    }
    with open(os.path.join(RES, "claim_summary.json"), "w") as fh:
        json.dump(summary, fh, indent=2, default=float)

    pv_ms = matrix(ev, "microsoft"); pv_nab = matrix(ev, "nab")
    mtab = pd.DataFrame({f"{ds}:{sg}": {m: pv.loc[sg, m] for m in pv.columns}
                         for ds, pv in [("microsoft", pv_ms), ("nab", pv_nab)]
                         for sg in pv.index}).round(3).T
    mtab.to_csv(os.path.join(RES, "subgroup_scores_table.csv"))
    make_figures(ev, raw, RES)

    print("==== claim (a) : Microsoft 5 anomaly subgroups (GRU unique all-positive?) ====")
    for sg, row in ca["per_subgroup"].items():
        print(f"  {sg:30s} " + "  ".join(f"{m}={row[m]:7.2f}" for m in MODELS))
    print("  all-positive models:", [m for m, v in ca["model_all_positive"].items() if v])
    print(f"  => claim(a) verdict: {summary['claim_a_verdict']}")

    print("\n==== claim (b) : NAB 6 anomaly subgroups (best-model attribution) ====")
    for sg, v in cb["best"].items():
        print(f"  {sg:22s} best={v['best_model']:12s} {v['best_score']:7.2f}  "
              + " ".join(f"{m}={x:6.2f}" for m, x in v["all"].items()))
    print(f"  distinct best architectures: {cb['n_distinct_architectures']}")
    print(f"  => claim(b) verdict: {summary['claim_b_verdict']}")

    print(f"\nfigures + tables written to {RES}")


if __name__ == "__main__":
    main()