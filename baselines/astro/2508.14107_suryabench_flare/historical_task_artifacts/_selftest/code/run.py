"""Self-test solver for 2508.14107_suryabench_flare (L2).

Pipeline: lag-only GOES-history features -> LogisticRegression -> TSS/HSS on
official splits. All numbers are recomputed from the frozen data in ../data.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]          # _selftest/
DATA = ROOT.parent / "data"                          # frozen data
OUT = ROOT / "results"
OUT.mkdir(parents=True, exist_ok=True)

WARMUP = (24, 72, 168)
THRESHOLD = 0.5
SPLITS = ["train", "validation", "test", "leaky_validation"]


def goes_to_flux(s) -> float:
    s = str(s).strip()
    if s in ("FQ", ""):
        return 0.0
    cls, val = s[0], s[1:]
    try:
        v = float(val)
    except ValueError:
        return 0.0
    mult = {"B": 1e-7, "C": 1e-6, "M": 1e-5, "X": 1e-4}.get(cls, 0.0)
    return v * mult


def load_split(name: str) -> pd.DataFrame:
    return pd.read_csv(DATA / f"{name}.csv", parse_dates=["timestamp"])


def label_consistency(df: pd.DataFrame) -> dict:
    cls = df["max_goes_class"].str[0]
    num = pd.to_numeric(df["max_goes_class"].str[1:], errors="coerce")
    rank = cls.map({"B": 1.0, "C": 2.0, "M": 3.0, "X": 4.0}).fillna(0.0) + num / 10.0
    ok_max = int(((rank >= 3.1).astype(int) == df["label_max"]).sum())
    ok_cum = int(((df["cumulative_index"] >= 10).astype(int) == df["label_cum"]).sum())
    return {"rows": len(df), "label_max_consistent": ok_max == len(df),
            "label_cum_consistent": ok_cum == len(df),
            "label_max_pos": int(df["label_max"].sum()),
            "label_max_rate": round(float(df["label_max"].mean()), 4),
            "label_cum_pos": int(df["label_cum"].sum()),
            "label_cum_rate": round(float(df["label_cum"].mean()), 4)}


def build_features(eval_df: pd.DataFrame, history: pd.DataFrame):
    """Lag-only features: any feature for window t uses only rows with ts < t."""
    eval_df = eval_df.copy()
    eval_df["flux"] = eval_df["max_goes_class"].apply(goes_to_flux)
    eval_ts = set(eval_df["timestamp"])
    h = history.copy()
    h["flux"] = h["max_goes_class"].apply(goes_to_flux)
    comb = pd.concat(
        [h[["timestamp", "flux", "cumulative_index"]],
         eval_df[["timestamp", "flux", "cumulative_index"]]],
        ignore_index=True,
    ).sort_values("timestamp").reset_index(drop=True)
    f = pd.DataFrame(index=comb.index)
    for w in WARMUP:
        f[f"lagmax_{w}"] = comb["flux"].shift(1).rolling(w, min_periods=min(w, 24)).max()
        f[f"lagmean_{w}"] = comb["flux"].shift(1).rolling(w, min_periods=min(w, 24)).mean()
        f[f"lagcum_{w}"] = comb["cumulative_index"].shift(1).rolling(w, min_periods=min(w, 24)).sum()
    f["lagmax_1"] = comb["flux"].shift(1)
    f["hour"] = comb["timestamp"].dt.hour
    f["doy_sin"] = np.sin(2 * np.pi * comb["timestamp"].dt.dayofyear / 365.25)
    keep = comb["timestamp"].isin(eval_ts)
    return f[keep].reset_index(drop=True), eval_df["label_max"].reset_index(drop=True)


def metrics_from_counts(y_true, y_pred):
    y = np.asarray(y_true, dtype=int)
    p = np.asarray(y_pred, dtype=int)
    tp = int(((y == 1) & (p == 1)).sum())
    fp = int(((y == 0) & (p == 1)).sum())
    tn = int(((y == 0) & (p == 0)).sum())
    fn = int(((y == 1) & (p == 0)).sum())
    tpr = tp / (tp + fn) if (tp + fn) else 0.0
    fpr = fp / (fp + tn) if (fp + tn) else 0.0
    tss = tpr - fpr
    denom = (tp + fn) * (fn + tn) + (tp + fp) * (fp + tn)
    hss = 2 * (tp * tn - fp * fn) / denom if denom else 0.0
    f1 = 2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) else 0.0
    return {"n": int(len(y)), "base_rate": round(float(y.mean()), 6),
            "threshold": THRESHOLD, "tp": tp, "fp": fp, "tn": tn, "fn": fn,
            "tss": round(float(tss), 6), "hss": round(float(hss), 6),
            "f1": round(float(f1), 6)}


def evaluate(ev: pd.DataFrame, history: pd.DataFrame, scaler, model):
    X, y = build_features(ev, history)
    valid = X.notna().all(axis=1)
    X, y = X[valid], y[valid]
    proba = model.predict_proba(scaler.transform(X))[:, 1]
    pred = (proba >= THRESHOLD).astype(int)
    res = metrics_from_counts(y, pred)
    res["rows_excluded_warmup"] = int((~valid).sum())
    scan = {}
    for t in np.arange(0.10, 0.90, 0.10):
        scan[round(float(t), 2)] = round(metrics_from_counts(y, (proba >= float(t)).astype(int))["tss"], 4)
    res["threshold_scan_tss"] = scan
    res["tss_min_scan"] = min(scan.values())
    res["tss_max_scan"] = max(scan.values())
    return res


def main():
    data = {n: load_split(n) for n in SPLITS}
    consistency = {n: label_consistency(d) for n, d in data.items()}

    train = data["train"]
    Xtr, ytr = build_features(train, train.head(0))
    valid_tr = Xtr.notna().all(axis=1)
    Xtr, ytr = Xtr[valid_tr], ytr[valid_tr]
    scaler = StandardScaler().fit(Xtr)
    model = LogisticRegression(max_iter=2000).fit(scaler.transform(Xtr), ytr)

    results = {}
    for name in ["validation", "test", "leaky_validation"]:
        results[name] = evaluate(data[name], train, scaler, model)

    # per-year test breakdown
    per_year = []
    for yr, g in data["test"].groupby(data["test"]["timestamp"].dt.year):
        r = evaluate(g, train, scaler, model)
        r["year"] = int(yr)
        per_year.append(r)
    results["test_per_year"] = per_year

    # evidence table
    rows = []
    for name in ["validation", "test", "leaky_validation"]:
        r = results[name]
        rows.append({"period": name, "n": r["n"], "base_rate": r["base_rate"],
                     "threshold": r["threshold"], "tp": r["tp"], "fp": r["fp"],
                     "tn": r["tn"], "fn": r["fn"], "tss": r["tss"], "hss": r["hss"]})
    ev = pd.DataFrame(rows)
    ev.to_csv(OUT / "evidence_table.csv", index=False)

    metrics = {
        "task": "2508.14107_suryabench_flare",
        "target": "label_max (window max >= M1.0)",
        "split_stats": consistency,
        "train_base_rate": consistency["train"]["label_max_rate"],
        "test": {k: results["test"][k] for k in
                 ["n", "base_rate", "threshold", "tp", "fp", "tn", "fn", "tss", "hss",
                  "rows_excluded_warmup", "threshold_scan_tss", "tss_min_scan", "tss_max_scan"]},
        "validation": {k: results["validation"][k] for k in
                       ["n", "base_rate", "tss", "hss", "tss_min_scan", "tss_max_scan"]},
        "leaky_validation": {k: results["leaky_validation"][k] for k in
                             ["n", "base_rate", "tss", "hss", "tss_min_scan", "tss_max_scan"]},
        "test_per_year": [{k: r[k] for k in ["year", "n", "base_rate", "tss", "hss"]} for r in per_year],
        "uncertainty": {
            "method": "threshold sensitivity envelope (0.10-0.80 step 0.10) over test-period TSS",
            "interval": {"low": results["test"]["tss_min_scan"], "high": results["test"]["tss_max_scan"]},
        },
        "conclusion": "partially_supported",
    }
    (OUT / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")

    # figure: per-year TSS vs base rate on test
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    yrs = [r["year"] for r in per_year]
    tss = [r["tss"] for r in per_year]
    br = [r["base_rate"] for r in per_year]
    fig, ax1 = plt.subplots(figsize=(7.5, 4.2))
    ax1.plot(yrs, tss, "o-", color="#1f77b4", label="TSS (test, per year)")
    ax1.set_xlabel("Year (official test split 2020-2024)")
    ax1.set_ylabel("TSS", color="#1f77b4")
    ax1.tick_params(axis="y", labelcolor="#1f77b4")
    ax2 = ax1.twinx()
    ax2.plot(yrs, br, "s--", color="#d62728", label="label_max base rate")
    ax2.set_ylabel("base rate", color="#d62728")
    ax2.tick_params(axis="y", labelcolor="#d62728")
    ax1.axhline(0.0, color="k", lw=0.8)
    ax1.set_title("Test-period flare forecasting skill vs positive-class base rate (2020-2024)")
    lines = ax1.get_lines() + ax2.get_lines()
    ax1.legend(lines, [l.get_label() for l in lines], loc="lower right", fontsize=8)
    fig.tight_layout()
    fig.savefig(OUT / "figure.svg", format="svg")
    plt.close(fig)
    print(json.dumps({k: results[k]["tss"] for k in ["validation", "test", "leaky_validation"]}, indent=2))


if __name__ == "__main__":
    main()