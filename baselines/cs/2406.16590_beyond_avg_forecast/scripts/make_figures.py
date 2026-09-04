"""Publication-style figures from the multi-view SMAPE results."""
import json
import os
import pickle

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(BASE, "results")
FIG = os.path.join(RES, "figures")
os.makedirs(FIG, exist_ok=True)

METHOD_COLORS = {
    "NHITS": "#d62728", "Theta": "#1f77b4", "ETS": "#ff7f0e", "SES": "#2ca02c",
    "SNaive": "#7f7f7f", "RWD": "#9467bd", "ARIMA": "#8c564b",
}
METHOD_ORDER = ["NHITS", "Theta", "ETS", "SES", "SNaive", "RWD", "ARIMA"]


def load_df():
    return pd.read_csv(os.path.join(RES, "evidence_table.csv")), \
        pd.read_csv(os.path.join(RES, "winloss_table.csv"))


def barplot(df, rows, ylabel, title, fname):
    fig, ax = plt.subplots(figsize=(9, 4.2))
    x = np.arange(len(rows))
    methods = [r["method"] for r in rows]
    values = [r["smape"] for r in rows]
    colors = [METHOD_COLORS.get(m, "#333") for m in methods]
    bars = ax.bar(x, values, color=colors, alpha=0.85)
    ax.set_xticks(x)
    ax.set_xticklabels(methods, rotation=25)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    for xi, v in zip(x, values):
        ax.text(xi, v + max(values) * 0.01, f"{v:.2f}", ha="center", fontsize=8)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, fname), dpi=150)
    plt.close(fig)


def fig_overall(df):
    rows = (df[(df["view"] == "overall") & (df["dataset"] == "All")]
            .sort_values("smape").to_dict("records"))
    barplot(df, rows, "Overall SMAPE (%)", "Overall SMAPE (M3 + Tourism, 4,140 series)",
            "fig1_overall.png")


def fig_horizon(df):
    h = df[df["view"] == "horizon"]
    piv = h.pivot_table(index="condition", columns="method", values="smape")
    piv = piv[[c for c in METHOD_ORDER if c in piv.columns]]
    fig, ax = plt.subplots(figsize=(9, 4.5))
    piv.T.plot(kind="bar", ax=ax)
    ax.set_ylabel("SMAPE (%)"); ax.set_title("SMAPE by horizon step (first vs last)")
    ax.grid(axis="y", alpha=0.3); ax.legend(title="step")
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "fig2_horizon.png"), dpi=150)
    plt.close(fig)


def fig_frequency(df):
    f = df[df["view"] == "frequency"]
    piv = f.pivot_table(index="condition", columns="method", values="smape")
    piv = piv[[c for c in METHOD_ORDER if c in piv.columns]]
    fig, ax = plt.subplots(figsize=(9, 4.5))
    piv.T.plot(kind="bar", ax=ax)
    ax.set_ylabel("SMAPE (%)"); ax.set_title("SMAPE by sampling frequency")
    ax.grid(axis="y", alpha=0.3); ax.legend(title="frequency"); ax.set_xticklabels(ax.get_xticklabels(), rotation=25)
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "fig3_frequency.png"), dpi=150)
    plt.close(fig)


def fig_conditions(df):
    c = df[df["view"].isin(["difficult", "anomaly", "expected_shortfall"])]
    piv = c.pivot_table(index=["view", "condition"], columns="method", values="smape")
    piv = piv.reindex(["difficult", "anomaly", "expected_shortfall"])
    piv = piv[[ch for ch in METHOD_ORDER if ch in piv.columns]]
    fig, axs = plt.subplots(1, 3, figsize=(15, 4.2))
    labels = {"difficult": "Difficult series\n(SNaive SMAPE > 95% q)",
              "anomaly": "Anomaly points\n(outside SNaive 99% PI)",
              "expected_shortfall": "Expected shortfall\n(worst-5% of anomaly errors)"}
    for ax, view in zip(axs, ["difficult", "anomaly", "expected_shortfall"]):
        row = piv.loc[view]
        x = np.arange(len(row)); 
        ax.bar(x, row.values, color=[METHOD_COLORS.get(m, "#333") for m in row.index], alpha=0.85)
        ax.set_xticks(x); ax.set_xticklabels(row.index, rotation=30, fontsize=7)
        ax.set_title(labels[view], fontsize=9)
        for xi, v in zip(x, row.values):
            ax.text(xi, v + 0.5, f"{v:.1f}", ha="center", fontsize=7)
        ax.grid(axis="y", alpha=0.3)
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "fig4_conditions.png"), dpi=150)
    plt.close(fig)


def fig_winloss(df):
    wl = df[df["view"] == "winloss"].dropna(subset=["win_rate"])
    fig, ax = plt.subplots(figsize=(10, 5))
    for m in ["NHITS", "Theta", "ETS", "SES", "ARIMA", "RWD"]:
        sub = wl[wl["method"] == m]
        for opp, row in sub.iterrows():
            ax.scatter(row["win_rate"], m, marker="o", s=90,
                       color=METHOD_COLORS.get(m), edgecolor="k", linewidth=0.5)
    ax.axvline(0.5, ls="--", color="gray")
    ax.axvspan(0.3, 0.7, color="gray", alpha=0.15, label="30%-70% band")
    ax.set_xlabel("win rate vs opponent (per-series SMAPE)")
    ax.set_ylabel("method")
    ax.set_xlim(0, 1)
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "fig5_winloss.png"), dpi=150)
    plt.close(fig)


def fig_theta_scatter():
    """Per-series SMAPE scatter NHITS vs Theta (the '50%-ish' win/loss picture)."""
    with open(os.path.join(RES, "per_series_smape.pkl"), "rb") as fh:
        data = pickle.load(fh)
    ps = data["per_series"]
    a, b = np.asarray(ps["NHITS"]), np.asarray(ps["Theta"])
    valid = np.isfinite(a) & np.isfinite(b)
    a, b = a[valid], b[valid]
    cap = 60.0
    a, b = np.clip(a, 0, cap), np.clip(b, 0, cap)
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.plot([0, cap], [0, cap], "--", color="gray", lw=1)
    ax.scatter(b, a, s=4, alpha=0.35, rasterized=True)
    ax.set_xlabel("Theta mean SMAPE"); ax.set_ylabel("NHITS mean SMAPE")
    ax.set_title(f"Per-series SMAPE: NHITS vs Theta (n={a.size})")
    ax.set_xlim(0, cap); ax.set_ylim(0, cap)
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "fig6_theta_scatter.png"), dpi=150)
    plt.close(fig)


def main():
    df, wl = load_df()
    fig_overall(df)
    fig_horizon(df)
    fig_frequency(df)
    fig_conditions(df)
    fig_winloss(wl)
    fig_theta_scatter()
    print("figures written to", FIG)


if __name__ == "__main__":
    main()