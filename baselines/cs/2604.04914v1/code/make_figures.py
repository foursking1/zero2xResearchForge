"""Generate the figure set for the Pensieve verification study.

Reads results/analysis_results.jsonl and writes PNGs into results/figures/:

  fig_c01_capacity_heatmap.png   MIP / CROWN per-query outcomes (models x queries)
  fig_c03_exec_time_boxplot.png  per-query execution time (log scale) by backend & model
  fig_c04_stacked_bars.png       safe/unsafe/unknown aggregates per property & model
  fig_margin_histogram.png       best-margin distribution from the heuristic search

Also prints the numbers used in solution.md (unknown counts, single-engine
decision fraction) so the values in the text are traceable.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
RESULTS = ROOT / "results"
FIGDIR = RESULTS / "figures"
FIGDIR.mkdir(parents=True, exist_ok=True)

MODELS = ["small", "mid", "big"]
PROPS = ["capacity_utilization", "rebuffering_avoidance", "robustness"]
BACKENDS = ["heuristic", "mip", "crown_bab"]


def load() -> list[dict]:
    rows = []
    for line in (RESULTS / "analysis_results.jsonl").read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def statuses_by_key(rows: list[dict]) -> dict[tuple, dict]:
    """(model, prop, query) -> {backend: status}."""
    out: dict[tuple, dict] = {}
    for r in rows:
        key = (r["model"], r["prop"], r["query"])
        out.setdefault(key, {})[r["backend"]] = r.get("status", "error")
    return out


def combined(outcomes: dict[str, str]) -> str:
    """Union of engines: unsafe wins, else safe, else unknown."""
    if any(v == "unsafe" for v in outcomes.values()):
        return "unsafe"
    if any(v == "safe" for v in outcomes.values()):
        return "safe"
    return "unknown"


def query_order(rows: list[dict], prop: str) -> list[str]:
    qs = sorted({r["query"] for r in rows if r["prop"] == prop})
    return qs


def main():
    rows = load()
    by_key = statuses_by_key(rows)
    print(f"loaded {len(rows)} backend runs, {len(by_key)} (model,prop,query) combos\n")

    cmap = {"safe": "#2e9e4f", "unsafe": "#c0392b", "unknown": "#bdbdbd", "error": "#000000"}
    order = {"safe": 0, "unsafe": 1, "unknown": 2}

    # ---------- C01: capacity utilization heatmap ----------
    prop = "capacity_utilization"
    qs = query_order(rows, prop)
    for backend, fname in [("mip", "fig_c01_capacity_heatmap_mip.png"),
                           ("crown_bab", "fig_c01_capacity_heatmap_crown.png")]:
        fig, ax = plt.subplots(figsize=(max(5, 1.4 * len(qs)), 2.6))
        grid = np.full((len(MODELS), len(qs)), np.nan)
        annot = np.full((len(MODELS), len(qs)), "", dtype=object)
        for i, m in enumerate(MODELS):
            for j, q in enumerate(qs):
                st = by_key.get((m, prop, q), {}).get(backend, "missing")
                if st in cmap:
                    grid[i, j] = order[st]
                    annot[i, j] = st[0].upper()
                else:
                    grid[i, j] = order["unknown"]
                    annot[i, j] = "?"
        ax.imshow(grid, cmap=matplotlib.colors.ListedColormap([cmap["safe"], cmap["unsafe"], cmap["unknown"]]),
                  vmin=0, vmax=2, aspect="auto")
        for i in range(len(MODELS)):
            for j in range(len(qs)):
                ax.text(j, i, annot[i, j], ha="center", va="center",
                        color="white" if grid[i, j] < 2 else "black", fontsize=11)
        ax.set_xticks(range(len(qs)))
        ax.set_xticklabels([q.replace("input100_eps01_", "").replace(".vnnlib", "") for q in qs],
                           rotation=30, ha="right", fontsize=7)
        ax.set_yticks(range(len(MODELS)))
        ax.set_yticklabels(MODELS)
        ax.set_title(f"Capacity Utilization — {backend} outcome per query")
        fig.tight_layout()
        fig.savefig(FIGDIR / fname, dpi=150)
        plt.close(fig)
        print(f"wrote {fname}")

    # ---------- C03: execution time boxplots (log scale) ----------
    times = {(m, b): [] for m in MODELS for b in ("mip", "crown_bab")}
    for r in rows:
        if r["backend"] in ("mip", "crown_bab") and r.get("time_s") is not None:
            times[(r["model"], r["backend"])].append(r["time_s"])
    fig, ax = plt.subplots(figsize=(6, 3.4))
    positions, labels, data, colors = [], [], [], []
    pos = 1.0
    for b in ("crown_bab", "mip"):
        for m in MODELS:
            d = times[(m, b)]
            positions.append(pos)
            labels.append(f"{m}\n{b.replace('crown_bab','CROWN').replace('mip','MIP')}")
            data.append(d)
            colors.append("#d96a5a" if b == "crown_bab" else "#5a86d9")
            pos += 1.0
        pos += 0.5
    bp = ax.boxplot(data, positions=positions, tick_labels=labels, patch_artist=True, widths=0.6,
                    showfliers=True, flierprops=dict(marker="o", ms=2.5, alpha=0.6))
    for patch, c in zip(bp["boxes"], colors):
        patch.set_facecolor(c)
        patch.set_alpha(0.55)
    ax.set_yscale("log")
    ax.set_ylabel("Query exec. time (s, log scale)")
    ax.set_ylim(top=max(ax.get_ylim()[1], 10 ** 2.4))
    ax.set_title("Per-query execution time by backend and model size")
    fig.tight_layout()
    fig.savefig(FIGDIR / "fig_c03_exec_time_boxplot.png", dpi=150)
    plt.close(fig)
    print("wrote fig_c03_exec_time_boxplot.png")

    # ---------- C04: stacked bars per property & model ----------
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.0), sharey=True)
    for ax, prop in zip(axes, PROPS):
        qs = query_order(rows, prop)
        counts = {m: {"safe": 0, "unsafe": 0, "unknown": 0} for m in MODELS}
        for m in MODELS:
            for q in qs:
                st = combined(by_key.get((m, prop, q), {}))
                counts[m][st] += 1
        y = np.arange(len(MODELS))
        left = np.zeros(len(MODELS))
        for st, col in [("safe", cmap["safe"]), ("unsafe", cmap["unsafe"]), ("unknown", cmap["unknown"])]:
            vals = np.array([counts[m][st] for m in MODELS])
            ax.barh(y, vals, left=left, color=col, label=st, edgecolor="white", linewidth=0.4)
            for yi, (v, lf) in enumerate(zip(vals, left)):
                if v > 0:
                    ax.text(lf + v / 2, yi, str(int(v)), ha="center", va="center", color="white", fontsize=8)
            left += vals
        ax.set_yticks(y)
        ax.set_yticklabels(MODELS)
        ax.set_xticks(np.arange(0, 13))
        ax.set_title(prop.replace("_", "\n"), fontsize=9)
    axes[0].legend(fontsize=7, loc="lower right", ncol=1)
    axes[0].set_xlabel("num. queries (aggregated)")
    fig.suptitle("Pensieve query outcomes (union of heuristic + MIP + CROWN-BaB)")
    fig.tight_layout()
    fig.savefig(FIGDIR / "fig_c04_stacked_bars.png", dpi=150)
    plt.close(fig)
    print("wrote fig_c04_stacked_bars.png")

    # ---------- margin histogram from heuristic ----------
    margins = []
    for r in rows:
        if r["backend"] == "heuristic" and r.get("best_margin") is not None:
            margins.append(r["best_margin"])
    if margins:
        fig, ax = plt.subplots(figsize=(5.5, 3.0))
        ax.hist(margins, bins=30, color="#5a86d9", alpha=0.8)
        ax.axvline(0.0, color="#c0392b", lw=1.2)
        ax.set_xlabel("best heuristic margin  (<=0 => violation found)")
        ax.set_ylabel("queries")
        ax.set_title(f"Best margins over {len(margins)} (model, query) pairs")
        fig.tight_layout()
        fig.savefig(FIGDIR / "fig_margin_histogram.png", dpi=150)
        plt.close(fig)
        print("wrote fig_margin_histogram.png")

    # ---------- text metrics ----------
    print("\n===== metrics for solution.md =====")
    for m in MODELS:
        res = {k: 0 for k in ("safe", "unsafe", "unknown")}
        engine_decided = {"mip": 0, "crown_bab": 0, "both": 0, "neither": 0}
        total = 0
        for prop in PROPS:
            for q in query_order(rows, prop):
                out = by_key.get((m, prop, q), {})
                st = combined(out)
                res[st] += 1
                total += 1
                mip_st = out.get("mip", "unknown")
                cb_st = out.get("crown_bab", "unknown")
                mi = mip_st in ("safe", "unsafe")
                cb = cb_st in ("safe", "unsafe")
                if mi and cb:
                    engine_decided["both"] += 1
                elif mi:
                    engine_decided["mip"] += 1
                elif cb:
                    engine_decided["crown_bab"] += 1
                else:
                    engine_decided["neither"] += 1
        resolved = res["safe"] + res["unsafe"]
        single = engine_decided["mip"] + engine_decided["crown_bab"]
        print(f"model={m}: total={total} safe={res['safe']} unsafe={res['unsafe']} "
              f"unknown={res['unknown']} resolved={resolved} "
              f"resolved_by_only_one_engine={single} "
              f"(mip-only={engine_decided['mip']}, crown-only={engine_decided['crown_bab']}, "
              f"both={engine_decided['both']}, neither={engine_decided['neither']})")
        if resolved:
            print(f"          -> single-engine fraction of resolved: {single/resolved:.1%}")
    print("\n===== per-backend unknown counts (for C08-style comparison) =====")
    for m in MODELS:
        for b in BACKENDS:
            n = sum(1 for r in rows if r["model"] == m and r["backend"] == b and r.get("status") == "unknown")
            nsafe = sum(1 for r in rows if r["model"] == m and r["backend"] == b and r.get("status") == "safe")
            nun = sum(1 for r in rows if r["model"] == m and r["backend"] == b and r.get("status") == "unsafe")
            print(f"  {m:>5} {b:<10} safe={nsafe} unsafe={nun} unknown={n}")


if __name__ == "__main__":
    main()
