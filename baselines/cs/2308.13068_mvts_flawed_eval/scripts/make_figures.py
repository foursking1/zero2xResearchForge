"""Generate summary figures for the report into figures/."""
from __future__ import annotations

import json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
(ROOT / "figures").mkdir(parents=True, exist_ok=True)
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})

df = pd.read_csv(ROOT / "results" / "evidence_table.csv")
metrics = json.loads((ROOT / "results" / "metrics.json").read_text())

COLS = {"SWaT": "#23395B", "PSM": "#C0392B"}
METHOD_COLORS = {"PCA": "#2E86AB", "PCA-uniform": "#7FB2B5", "Mahalanobis": "#5D7E5E",
                 "GRU-AE": "#D98C4A", "GRU-AE-cholstd": "#E3B062", "Random": "#8C8C8C"}

def oracle(subset):
    return subset[subset["threshold"] == "oracle"].set_index("method")

# ---- Figure 1: pointwise F1 (oracle threshold) per dataset ----
fig, axes = plt.subplots(1, 2, figsize=(9, 4), sharey=True)
for ax, ds in zip(axes, ["SWaT", "PSM"]):
    o = oracle(df[df["dataset"] == ds])
    y = []
    labels = []
    for m in ["PCA", "PCA-uniform", "Mahalanobis", "GRU-AE", "GRU-AE-cholstd"]:
        if m in o.index:
            labels.append(m.replace("-cholstd", "\n(cholstd)"))
            y.append(o.loc[m, "f1_pointwise"])
    pos = np.arange(len(y))
    ax.bar(pos, y, color=[METHOD_COLORS[l.split("(")[0].strip()] for l in labels], width=0.62)
    rg = metrics["datasets"][ds]["random_guess"]["a1000"]
    ax.axhline(rg["pointwise_f1_mean"], ls="--", lw=1.2, color="#8C8C8C",
               label=f"random guess F1pw={rg['pointwise_f1_mean']:.4f}")
    ax.set_xticks(pos); ax.set_xticklabels(labels, fontsize=8)
    ax.set_title(f"{ds} — point-wise F1 (oracle threshold)")
    ax.set_ylim(0, 1); ax.legend(fontsize=8)
axes[0].set_ylabel("point-wise F1")
fig.tight_layout()
fig.savefig(ROOT / "figures" / "fig1_pointwise_f1_by_method.png", dpi=150)
plt.close(fig)

# ---- Figure 2: protocol inflation per method (oracle threshold) ----
fig, axes = plt.subplots(1, 2, figsize=(9, 4), sharey=True)
for ax, ds in zip(axes, ["SWaT", "PSM"]):
    o = oracle(df[df["dataset"] == ds])
    ms = [m for m in ["PCA", "PCA-uniform", "Mahalanobis", "GRU-AE", "GRU-AE-cholstd"] if m in o.index]
    x = np.arange(len(ms))
    pw = [o.loc[m, "f1_pointwise"] for m in ms]
    pa = [o.loc[m, "f1_point_adjust"] for m in ms]
    w = 0.36
    ax.bar(x - w/2, pw, w, label="point-wise", color="#2E86AB")
    ax.bar(x + w/2, pa, w, label="point-adjust", color="#D98C4A")
    rg = metrics["datasets"][ds]["random_guess"]["a1000"]
    ax.axhline(rg["point_adjust_f1_mean"], ls=":", lw=1.4, color="#C0392B",
               label=f"random guess F1pa={rg['point_adjust_f1_mean']:.4f}")
    ax.set_xticks(x); ax.set_xticklabels([m.replace("GRU-AE-cholstd", "GRU-AE*") for m in ms], fontsize=8)
    ax.set_title(f"{ds} — F1 under two protocols (oracle threshold)")
    ax.legend(fontsize=8)
axes[0].set_ylabel("F1"); axes[0].set_ylim(0, 1.02)
fig.tight_layout()
fig.savefig(ROOT / "figures" / "fig2_protocol_inflation.png", dpi=150)
plt.close(fig)

# ---- Figure 3: random-guess manipulation ----
fig, ax = plt.subplots(figsize=(6.5, 4))
for i, ds in enumerate(["SWaT", "PSM"]):
    rg = metrics["datasets"][ds]["random_guess"]["a1000"]
    o = oracle(df[df["dataset"] == ds])
    ax.plot(i, rg["pointwise_f1_mean"], "o", ms=9, color=COLS[ds], label=f"{ds} F1pw")
    ax.plot(i + 0.18, rg["point_adjust_f1_mean"], "^", ms=9, color=COLS[ds], label=f"{ds} F1pa")
    ax.errorbar(i, rg["pointwise_f1_mean"], yerr=rg["pointwise_f1_std"], fmt="none",
                color=COLS[ds], capsize=3)
    ax.errorbar(i + 0.18, rg["point_adjust_f1_mean"], yerr=rg["point_adjust_f1_std"],
                fmt="none", color=COLS[ds], capsize=3)
    ax.vlines([i, i + 0.18], 0, 1, alpha=0.08)
    # deep method pointwise F1 for reference
    gru = o.loc["GRU-AE", "f1_pointwise"]
    ax.axhline(gru, ls="--", lw=0.9, color=COLS[ds], alpha=0.5,
               label=f"{ds} GRU-AE point-wise F1={gru:.4f}")
ax.set_xticks([0, 0.18, 1, 1.18]); ax.set_xticklabels(["", "", "", ""])
ax.set_xticks([0.09, 1.09]); ax.set_xticklabels(["SWaT", "PSM"])
ax.set_ylabel("F1 (random guessing, α=1000, 50 repeats)")
ax.set_ylim(0, 1.05)
ax.set_title("No-learning random guessing under point-adjust vs point-wise")
ax.legend(fontsize=8, ncol=2)
fig.tight_layout()
fig.savefig(ROOT / "figures" / "fig3_random_guess_manipulation.png", dpi=150)
plt.close(fig)

# ---- Figure 4: score + label overview on SWaT (PCA) ----
d = np.load(ROOT / "results" / "predictions" / "SWaT_PCA.npz")
score, label = d["score_test"], d["label"]
o = oracle(df[df["dataset"] == "SWaT"]).loc["PCA", "threshold_value"]
fig, ax = plt.subplots(figsize=(12, 3.4))
t = np.arange(len(label))
ax.plot(t, score, lw=0.3, color="#2E86AB", label="PCA score (test)")
ax.axhline(o, ls="--", color="#C0392B", lw=1, label="oracle threshold")
true = label.astype(bool)
ax.fill_between(t, score.min(), score.max(), where=true, color="#C0392B", alpha=0.15, label="true anomaly")
ax.set_xlabel("time (test point index)"); ax.set_ylabel("score")
ax.set_title("SWaT — PCA reconstruction score, oracle threshold and true anomalies")
ax.legend(fontsize=8, ncol=3)
fig.tight_layout()
fig.savefig(ROOT / "figures" / "fig4_swat_pca_scores.png", dpi=150)
plt.close(fig)

print("figures written to", ROOT / "figures")