"""Assemble the claim evidence tables and figures from the per-model metrics CSVs.

  python make_evidence.py
Outputs under results/:
  evidence_table.csv      rows = (model, lead_time) with overall MAE/RMSE + per-station MAE
  claim_analysis.md       supported/... judgements with growth/差值 derived automatically
  figures/mae_vs_horizon.png, figures/per_station_28d.png
"""
from __future__ import annotations

import glob
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common  # noqa: E402

RESULTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
FIGS = os.path.join(RESULTS, "figures")
os.makedirs(FIGS, exist_ok=True)

LEADS = [7, 14, 21, 28]
CLASS = {
    "DLinear": "linear", "NLinear": "linear",
    "NBEATS": "mlp", "MLPResidual": "mlp", "TSMixer": "mlp",
    "PatchTST": "transformer",
    "Chronos_c100": "zeroshot", "Chronos_c512": "zeroshot",
    "persistence": "baseline", "mean_last7": "baseline", "mean_last30": "baseline",
}

def classify(model: str) -> str:
    if model.startswith("MLPResidual"):
        return "mlp"
    if model in CLASS:
        return CLASS[model]
    return "other"


def collect() -> tuple[pd.DataFrame, pd.DataFrame]:
    frame_rows, agg_rows = [], []
    for f in sorted(glob.glob(os.path.join(RESULTS, "metrics_*.csv"))):
        m = pd.read_csv(f)
        model = m["model"].iloc[0]
        frame_rows.append(m)
        for lead in LEADS:
            sub = m[m["lead"] == lead]
            if sub.empty:
                continue
            row = {"model": model, "lead_time": lead,
                   "overall_mae": float(sub.groupby("station")["mae"].mean().mean()),
                   "overall_rmse": float(sub.groupby("station")["rmse"].mean().mean()),
                   "class": classify(model)}
            for st in common.TARGETS:
                v = sub[sub["station"] == st]["mae"].mean()
                if len(sub[sub["station"] == st]) > 0:
                    row[f"mae_{st}"] = float(v)
            agg_rows.append(row)
    frame = pd.concat(frame_rows, ignore_index=True)
    agg = pd.DataFrame(agg_rows)
    return frame, agg


def growth(agg: pd.DataFrame, model: str) -> float | None:
    s = agg[agg["model"] == model].set_index("lead_time")
    if 7 in s.index and 28 in s.index:
        return (s.loc[28, "overall_mae"] - s.loc[7, "overall_mae"]) / s.loc[7, "overall_mae"]
    return None


def main() -> None:
    frame, agg = collect()
    # keep order: task-specific models first, then chronos, then baselines
    model_set = set(agg["model"])
    order = [] 
    for m in sorted(model_set, key=lambda x: (classify(x) not in ("linear", "mlp", "transformer"),
                                              x.startswith(("Chronos",)),
                                              x.startswith(("persistence", "mean_")))):
        if m in order:
            continue
        order.append(m)
    # re-order: linear, then mlp, then transformer, then zeroshot, then baseline
    cat = {"linear": 0, "mlp": 1, "transformer": 2, "zeroshot": 3, "baseline": 4}
    order = sorted(model_set, key=lambda m: (cat[classify(m)], m))
    agg["order"] = agg["model"].map({m: i for i, m in enumerate(order)})
    agg = agg.sort_values(["order", "lead_time"]).drop(columns="order").reset_index(drop=True)
    agg.to_csv(os.path.join(RESULTS, "evidence_table.csv"), index=False)
    frame.to_csv(os.path.join(RESULTS, "evidence_station_lead.csv"), index=False)

    # ---- Figures ---------------------------------------------------------
    cls_color = {"linear": "#d62728", "mlp": "#1f77b4", "transformer": "#ff7f0e",
                 "zeroshot": "#2ca02c", "baseline": "#999999"}
    order = [m for m in order if m in CLASS or m.startswith("MLPResidual")]
    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    for model in order:
        sub = agg[agg["model"] == model]
        if sub.empty or model.startswith("MLPResidual_mc") and not model.endswith("0.1"):
            continue
        sub = sub.set_index("lead_time").reindex(LEADS)
        ax.plot(LEADS, sub["overall_mae"], marker="o", label=model,
                color=cls_color.get(classify(model), "#444"), linewidth=1.8)
    ax.set_xlabel("lead time (days)")
    ax.set_ylabel("Overall MAE")
    ax.set_title("Everglades water-level: Overall MAE vs forecast horizon")
    ax.legend(fontsize=8, ncol=2)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(FIGS, "mae_vs_horizon.png"), dpi=160)
    plt.close(fig)

    # station difficulty at 28d
    s28 = agg[agg["lead_time"] == 28]
    fig, ax = plt.subplots(figsize=(9, 4))
    stations = common.TARGETS
    x = np.arange(len(stations))
    width = 0.14
    plotted = [m for m in order if m in set(s28["model"]) and not (m.startswith("MLPResidual_mc") and not m.endswith("0.1"))]
    for i, model in enumerate(plotted):
        vals = [s28[s28["model"] == model][f"mae_{st}"].iloc[0] if f"mae_{st}" in s28.columns else np.nan
                for st in stations]
        ax.bar(x + (i - 2.5) * width, vals, width, label=model)
    ax.set_xticks(x, stations)
    ax.set_ylabel("MAE at 28 days")
    ax.legend(fontsize=7, ncol=2)
    ax.set_title("Per-station MAE at 28-day horizon (colour = model)")
    fig.tight_layout()
    fig.savefig(os.path.join(FIGS, "per_station_28d.png"), dpi=160)
    plt.close(fig)

    # ---- Claim analysis --------------------------------------------------
    best_mlp = agg.assign(g=lambda d: d.groupby("model")["overall_mae"].transform("first"))
    m28 = agg[agg["lead_time"] == 28].set_index("model")["overall_mae"]
    lin_models = [m for m in order if classify(m) == "linear" and m in m28.index]
    mlp_models = [m for m in order if classify(m) in ("mlp",) and m in m28.index]

    def fmt(x: float) -> str: return f"{x:.3f}"

    growths = {m: growth(agg, m) for m in order}
    lin_growth = [growths[m] for m in lin_models if growths[m] is not None]
    mlp_best = min(m28[m] for m in mlp_models) if mlp_models else None
    chrono = [m for m in order if classify(m) == "zeroshot"]
    chrono_best = min(m28[m] for m in chrono) if chrono else None

    lines = []
    lines.append("# Claim analysis (auto-generated from evidence_table.csv)\n")
    lines.append(f"Overall MAE @ 7 d : " + ", ".join(f"{m}={fmt(m28[m]) if False else fmt(agg[(agg.model==m)&(agg.lead_time==7)]['overall_mae'].iloc[0])}" for m in order if m in agg[agg.lead_time==7].model.unique()) + "\n")
    lines.append(f"Overall MAE @ 28 d: " + ", ".join(f"{m}={fmt(m28[m])}" for m in order if m in m28.index) + "\n")
    lines.append(f"\n7->28 d relative growth: " + ", ".join(f"{m}=+{(g*100):.0f}%" for m, g in growths.items() if g is not None) + "\n")
    lines.append(f"\n(a) MLP<linear @28d: {('supported' if mlp_best is not None and all(mlp_best < m28[m] for m in lin_models) else 'not-supported')} "
                 f"(best MLP {fmt(mlp_best)} vs NLinear {fmt(m28['NLinear'])} / DLinear {fmt(m28['DLinear'])})\n")
    lines.append(f"(b) linear growth>=50%: {('supported' if all(g >= 0.5 for g in lin_growth) else 'partial')} "
                 f"(DLinear +{lin_growth[0]*100:.0f}%, NLinear +{lin_growth[1]*100:.0f}%)\n")
    lines.append(f"(c) chronos best: {'supported' if chrono_best is not None and mlp_best is not None and mlp_best - chrono_best >= 0.05 else 'contradicted'} "
                 f"(Chronos_best {fmt(chrono_best)} vs best MLP {fmt(mlp_best)})\n")
    open(os.path.join(RESULTS, "claim_analysis.md"), "w").write("\n".join(lines))
    print("\n".join(lines))
    print(f"\nSaved evidence_table.csv, figures, claim_analysis.md")


if __name__ == "__main__":
    main()