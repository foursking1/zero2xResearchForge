"""Aggregate experiment results into a summary + evidence table.

Usage: python3 aggregate.py results_dir out_dir
Reads raw_results.csv (all configs). Computes per-architecture best WAPE,
builds evidence_table.csv with required columns, and a per-series comparison
of the best sequence model vs best MLP.
"""
import glob
import json
import os
import sys

import numpy as np
import pandas as pd

ANCHORS = {
    "gru": 15.182,
    "lstm": 15.282,
    "cnn": 15.612,
    "tcn": 15.587,
    "mlp": 21.114,
    "ernn": 15.621,
    "esn": 17.184,
}


def main(results_dir, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    raw = pd.read_csv(os.path.join(results_dir, "raw_results.csv"))
    print(f"loaded {len(raw)} runs")

    # best config per (model, past_history)
    best = (
        raw.sort_values("wape")
        .groupby(["model", "past_history"])
        .first()
        .reset_index()
    )
    best.to_csv(os.path.join(out_dir, "best_per_arch_ph.csv"), index=False)

    # best per model (any ph)
    best_model = best.sort_values("wape").groupby("model").first().reset_index()
    best_model.to_csv(os.path.join(out_dir, "best_per_arch.csv"), index=False)
    print(best_model[["model", "past_history", "normalization", "wape", "wape_std", "n_train_windows"]].to_string(index=False))
    print()

    seq_models = [m for m in best_model["model"].tolist() if m != "mlp"]
    mlp_row = best_model[best_model["model"] == "mlp"]
    if mlp_row.empty:
        print("WARNING: no MLP run found")
        return
    mlp_wape = float(mlp_row["wape"].iloc[0])
    best_seq = best_model[best_model["model"].isin(seq_models)].sort_values("wape").iloc[0]
    print(f"BEST SEQ: {best_seq['model']} wape={best_seq['wape']:.4f} (ph={best_seq['past_history']})")
    print(f"MLP      : wape={mlp_wape:.4f} (ph={mlp_row['past_history'].iloc[0]})")
    print(f"gap MLP - best_seq = {mlp_wape - best_seq['wape']:.4f} pp")

    # evidence table
    rows = []
    for _, r in best.iterrows():
        gap = np.nan
        if r["model"] != "mlp":
            gap = mlp_wape - float(r["wape"])
        rows.append(
            dict(
                model=r["model"],
                past_history=int(r["past_history"]),
                normalization=r["normalization"],
                n_series=int(r["n_series"]),
                wape=round(float(r["wape"]), 4),
                wape_std=round(float(r["wape_std"]), 4),
                wape_median=round(float(r["wape_median"]), 4),
                mae_mean=round(float(r["mae_mean"]), 2),
                target_mean_mean=round(float(r["target_mean_mean"]), 2),
                wape_gap_mlp=round(gap, 4),
                anchor=ANCHORS.get(r["model"], np.nan),
                rel_to_anchor=round((float(r["wape"]) - ANCHORS[r["model"]]) / ANCHORS[r["model"]] * 100, 2)
                if r["model"] in ANCHORS
                else np.nan,
                n_train_windows=int(r["n_train_windows"]),
                run_name=r["run_name"],
            )
        )
    ev = pd.DataFrame(rows)
    ev = ev.sort_values(["past_history", "wape"])
    ev.to_csv(os.path.join(out_dir, "evidence_table.csv"), index=False)
    print("\n--- evidence_table (per past_history best) ---")
    print(ev[["model", "past_history", "normalization", "n_series", "wape", "wape_gap_mlp", "rel_to_anchor"]].to_string(index=False))

    # per-series comparison of best seq vs best mlp
    per_series_dir = os.path.join(results_dir, "per_series")
    seq_row = best_seq
    seq_ps = pd.read_csv(
        os.path.join(per_series_dir, f"{seq_row['run_name']}.csv")
    ).rename(columns={"wape": "wape_seq", "mae": "mae_seq", "target_mean": "target_mean_seq"})
    mlp_ps = pd.read_csv(
        os.path.join(per_series_dir, f"{mlp_row['run_name'].iloc[0]}.csv")
    ).rename(columns={"wape": "wape_mlp", "mae": "mae_mlp", "target_mean": "target_mean_mlp"})
    cmp = seq_ps.merge(mlp_ps, on="series_id", how="inner")
    cmp["seq_better"] = cmp["wape_seq"] < cmp["wape_mlp"]
    cmp.to_csv(os.path.join(out_dir, "per_series_seq_vs_mlp.csv"), index=False)
    frac = cmp["seq_better"].mean() * 100
    print(f"\nper-series: best seq ({seq_row['model']}) beats MLP model on {frac:.1f}% of {len(cmp)} series")

    # wilcoxon / paired stats
    try:
        from scipy.stats import wilcoxon

        w, p = wilcoxon(cmp["wape_seq"], cmp["wape_mlp"]) if False else (np.nan, np.nan)
        stat, p = wilcoxon(cmp["wape_mlp"] - cmp["wape_seq"])
        print(f"wilcoxon (mlp - seq) signed-rank: stat={stat:.1f} p={p:.4g}")
        with open(os.path.join(out_dir, "stats.txt"), "w") as f:
            f.write(f"seq_better_frac={frac:.2f}\nwilcoxon_p={p:.4g}\nmean_diff(mlp-seq)={np.nanmean(cmp['wape_mlp']-cmp['wape_seq']):.4f}\n")
    except ImportError:
        print("scipy not available; skipped wilcoxon")
    return ev


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])