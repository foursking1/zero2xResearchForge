"""Post-hoc analysis: data-facts verification, figures, claim summary.

    python scripts/analyze.py
"""
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from loader import build_bundle, prepare_split, load_anomaly_windows, build_context_edges

HOME = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARQUET = "/mnt/f/dataset/cs/2607.18127_cloudens/pivoted_data_all.parquet"
ANOMALY_CSV = "/mnt/f/dataset/cs/2607.18127_cloudens/data/labels/anomaly_windows.csv"
CACHE = os.path.join(HOME, "data")
RESULTS = os.path.join(HOME, "results")


def data_facts():
    bundle = build_bundle(PARQUET, ANOMALY_CSV, CACHE)
    split = prepare_split(bundle, slide_win=6, train_val_ratio=0.8, seed=42)
    gt_all = load_anomaly_windows(ANOMALY_CSV)
    atw = bundle.anomaly_windows_test
    im = atw[atw["anomaly_source"] == 2]
    it = atw[atw["anomaly_source"] == 1]
    tl = atw[atw["anomaly_source"] == 3]
    facts = {
        "parquet_rows": int(bundle.df.shape[0]),
        "feature_columns_5xx_count": int(bundle.df.shape[1]),
        "anomaly_windows_total": int(len(gt_all)),
        "anomaly_windows_test": int(len(atw)),
        "test_points": int(len(split["test_labels"])),
        "test_anomaly_points": int(split["test_labels"].sum()),
        "test_anomaly_pct": round(100 * split["test_labels"].mean(), 2),
        "test_windows_IT": int(len(it)), "test_windows_IM": int(len(im)),
        "test_windows_TestLog": int(len(tl)),
    }
    ei, ew = build_context_edges(bundle.cols)
    facts["context_undirected_edges"] = int(ei.shape[1] // 2)
    facts["context_edge_weights"] = sorted(np.unique(ew).round(2).tolist())
    # anomaly window id assignment (a7->0 ... a25->18)
    gt_map = {}
    numbers = atw["number"].tolist()
    for k, num in enumerate(numbers):
        gt_map[num] = k
    facts["test_window_id_mapping"] = gt_map
    with open(os.path.join(RESULTS, "data_facts.json"), "w") as f:
        json.dump(facts, f, indent=2)
    print(json.dumps(facts, indent=2))
    return facts


def make_figures(evidence_path=None):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    evidence_path = evidence_path or os.path.join(RESULTS, "evidence_table.csv")
    ev = pd.read_csv(evidence_path)
    grids = {}
    for mn in ("GRU", "ClouDens"):
        gf = os.path.join(RESULTS, f"grid_{mn}.csv")
        if os.path.exists(gf):
            grids[mn] = pd.read_csv(gf)

    plt.style.use("seaborn-v0_8-whitegrid")
    # ---- fig 1: canonical MD NAB comparison ----
    md = ev[(ev["scoring_strategy"] == "mahalanobis") & (ev["selection"] == "canonical")]
    x = np.arange(2)
    wdt = 0.35
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(x - wdt / 2, md["nab_standard"], wdt, label="NAB Standard", color="#3b72b0")
    ax.bar(x + wdt / 2, md["nab_lowfn"], wdt, label="NAB LowFN", color="#e08e45")
    ax.set_xticks(x, ["GRU", "ClouDens"])
    ax.set_ylabel("NAB score")
    ax.set_title("MD scoring, 5xx count subset (w=6), canonical threshold 99.8")
    ax.legend()
    for xi, (s, l) in zip(x, zip(md["nab_standard"], md["nab_lowfn"])):
        ax.text(xi - wdt / 2, s + 0.4, f"{s:.1f}", ha="center", fontsize=8)
        ax.text(xi + wdt / 2, l + 0.4, f"{l:.1f}", ha="center", fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(RESULTS, "fig1_nab_md_comparison.png"), dpi=150)
    plt.close(fig)

    # ---- fig 2: NAB(standard) vs MD percentile grid ----
    fig, ax = plt.subplots(figsize=(6, 4))
    for mn, c in (("GRU", "#444"), ("ClouDens", "#c33")):
        g = grids[mn]
        gm = g[g["strategy"] == "mahalanobis"]
        ax.plot(gm["threshold"], gm["nab_standard"], "-o", color=c, label=f"{mn}")
        ax.plot(gm["threshold"], gm["nab_lowfn"], "--o", color=c, label=f"{mn} LowFN")
    ax.set_xlabel("MD percentile threshold")
    ax.set_ylabel("NAB")
    ax.legend(fontsize=8)
    ax.set_title("NAB vs MD threshold (5xx count, w=6)")
    fig.tight_layout()
    fig.savefig(os.path.join(RESULTS, "fig2_nab_vs_threshold.png"), dpi=150)
    plt.close(fig)

    # ---- fig 3: detection vs ground-truth test windows (MD canonical) ----
    bundle = build_bundle(PARQUET, ANOMALY_CSV, CACHE)
    split = prepare_split(bundle, slide_win=6, train_val_ratio=0.8, seed=42)
    atw = bundle.anomaly_windows_test

    fig, axes = plt.subplots(2, 1, figsize=(13, 6), sharex=True)
    for mn, ax in (("GRU", axes[0]), ("ClouDens", axes[1])):
        recon = np.load(os.path.join(RESULTS, f"recon_errors_{mn}.npy"))
        sys.path.insert(0, os.path.join(HOME, "src"))
        from scoring import mahalanobis_scores
        ms = mahalanobis_scores(recon, topk=1)
        idx = split["test_index"]
        y = split["test_labels"]
        ax.plot(idx, (ms - ms.min()) / (ms.max() - ms.min()), lw=0.6, color="#777")
        for _, r in atw.iterrows():
            st, en = r["anomaly_window_start"], r["anomaly_window_end"]
            ax.axvspan(st, en, color="#8dd", alpha=0.25)
        ax.set_ylabel(f"{mn} MD score (scaled)")
        ax.set_title(f"{mn} -- canonical MD 99.8")
    axes[-1].set_xlabel("test time (2024-03-01 .. 2024-05-31)")
    fig.tight_layout()
    fig.savefig(os.path.join(RESULTS, "fig3_md_signal_test.png"), dpi=150)
    plt.close(fig)
    print("figures written to", RESULTS)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    if cmd in ("all", "facts"):
        data_facts()
    if cmd in ("all", "figs"):
        make_figures()