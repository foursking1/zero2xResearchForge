"""05_analyze.py -- evaluation of the TE estimates against true fine-tuned Dice.

Outputs (results/):
  evidence_table.csv  : source_model, te_method, te_score, ft_dice, rank
  te_rankings.csv     : per-direction rankings for every TE method
  metrics.json        : per-method Pearson, weighted Kendall tau-b, top-1 hit,
                        paper-anchor comparison and conclusion label.
  figures (evidence/): scatter of TE score vs. fine-tuned Dice.
"""
import os
import sys
import json
import math
import argparse
import numpy as np
import scipy.stats as st

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import RESULTS_DIR, EVIDENCE_DIR, save_json

METHODS = ["ccfv", "logme", "leep", "gbc"]
METHOD_LABEL = {"ccfv": "CC-FV", "logme": "LogME", "leep": "LEEP", "gbc": "GBC"}

PAPER_ANCHOR = {
    "ccfv": {"pearson": 0.7003, "tau": 0.4986, "src": "arXiv:2307.11958 Table 1 (5-task mean)"},
    "logme": {"pearson": 0.2082, "tau": 0.0218, "src": "arXiv:2307.11958 Table 1"},
    "gbc": {"pearson": 0.3317, "tau": 0.4111, "src": "arXiv:2307.11958 Table 1"},
}


def weighted_kendall_tau_b(x, y, w=None):
    """Vigna (2015) weighted Kendall tau-b."""
    x = np.asarray(x, float); y = np.asarray(y, float)
    n = len(x)
    if w is None:
        w = np.ones(n)
    num = 0.0; denx = 0.0; deny = 0.0
    for i in range(n):
        for j in range(i + 1, n):
            wij = w[i] * w[j]
            sx = np.sign(x[i] - x[j]); sy = np.sign(y[i] - y[j])
            num += wij * sx * sy
            denx += wij * (sx != 0)
            deny += wij * (sy != 0)
    den = math.sqrt(denx * deny)
    return num / den if den > 0 else float("nan")


def pearson(x, y):
    x = np.asarray(x, float); y = np.asarray(y, float)
    if np.std(x) == 0 or np.std(y) == 0:
        return float("nan")
    return float(st.pearsonr(x, y)[0])


def spearman(x, y):
    return float(st.spearmanr(x, y)[0]) if (np.std(x) > 0 and np.std(y) > 0) else float("nan")


def load_direction(source, target, finetune_file):
    with open(os.path.join(RESULTS_DIR, finetune_file)) as f:
        ft = json.load(f)
    ft = {r["source_model"]: r["ft_dice"] for r in ft}
    return ft


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--directions", default="liver2spleen")
    ap.add_argument("--runs", default="primary", help="label for this ground-truth run")
    ap.add_argument("--ft-suffix", default="", help="suffix for finetune json (e.g. '_full')")
    a = ap.parse_args()
    dirs = [d for d in a.directions.split(",") if d]

    agg = {}
    all_rows = []
    per_dir = {}

    for d in dirs:
        source, target = d.split("2")
        te_file = os.path.join(RESULTS_DIR, f"te_{d}.json")
        ft_file = os.path.join(RESULTS_DIR, f"finetune_{d}{a.ft_suffix}.json")
        if not (os.path.exists(te_file) and os.path.exists(ft_file)):
            print(f"[skip] missing {d} ({ft_file})")
            continue
        te = json.load(open(te_file))
        ft = load_direction(source, target, ft_file)
        models = [r["source_model"] for r in te]
        ft_dice = np.array([ft[m] if m in ft else float("nan") for m in models])
        print(f"[dir {d}] {len(models)} models, ft_dice:", np.round(ft_dice, 3).tolist())
        stats = {}
        for m in METHODS:
            scores = np.array([r[m] for r in te])
            pear = pearson(scores, ft_dice)
            tau = weighted_kendall_tau_b(scores, ft_dice)
            # top-1 hit
            try:
                hit = int(np.argmax(scores) == np.argmax(ft_dice))
            except Exception:
                hit = -1
            stats[m] = {"pearson": pear, "w_kendall_tau": tau, "top1_hit": hit,
                        "best_model": models[int(np.argmax(scores))],
                        "best_dice_model": models[int(np.argmax(ft_dice))]}
            # evidence table rows (rank 1 = best TE score)
            n = len(scores)
            ranks = n - np.argsort(np.argsort(scores))  # 1=best
            for i, r in enumerate(te):
                all_rows.append({"direction": d, "source_model": r["source_model"],
                                 "te_method": METHOD_LABEL[m], "te_score": float(r[m]),
                                 "ft_dice": float(ft_dice[i]) if not math.isnan(ft_dice[i]) else None,
                                 "rank": int(ranks[i])})
            print(f"    {m}: pearson={pear:.4f} tau={tau:.4f} top1_hit={hit}")
        per_dir[d] = {"models": models, "ft_dice": ft_dice.tolist(),
                      "te": {m: [r[m] for r in te] for m in METHODS}, "stats": stats}

    # ---- aggregate across directions -------------------------------------
    summary = {}
    for m in METHODS:
        pears = [per_dir[d]["stats"][m]["pearson"] for d in per_dir if per_dir[d]["stats"][m]["pearson"] == per_dir[d]["stats"][m]["pearson"]]
        taus = [per_dir[d]["stats"][m]["w_kendall_tau"] for d in per_dir if not math.isnan(per_dir[d]["stats"][m]["w_kendall_tau"])]
        hits = [per_dir[d]["stats"][m]["top1_hit"] for d in per_dir]
        summary[m] = {
            "per_direction": {d: {"pearson": per_dir[d]["stats"][m]["pearson"],
                                  "w_kendall_tau": per_dir[d]["stats"][m]["w_kendall_tau"],
                                  "top1_hit": per_dir[d]["stats"][m]["top1_hit"]} for d in per_dir},
            "mean_pearson": float(np.mean(pears)) if pears else None,
            "mean_w_kendall_tau": float(np.mean(taus)) if taus else None,
            "top1_hits": hits,
            "all_top1_hit": all(h >= 0 for h in hits) and all(h == 1 for h in hits) if hits else None,
            "pearson_pooled": (float(pearson(
                np.concatenate([np.array(per_dir[d]["te"][m]) for d in per_dir]),
                np.concatenate([np.array(per_dir[d]["ft_dice"]) for d in per_dir])))
                if len(per_dir) == 1 else None),
            "paper_anchor": PAPER_ANCHOR.get(m, {}),
        }

    # ---- conclusion ---------------------------------------------------------
    ccfv = summary["ccfv"]
    ccfv_pear = ccfv["mean_pearson"]; ccfv_tau = ccfv["mean_w_kendall_tau"]
    best_pear = max((summary[m]["mean_pearson"] for m in ("logme", "leep", "gbc")
                     if summary[m]["mean_pearson"] is not None), default=float("-inf"))
    beats = ccfv_pear is not None and ccfv_pear > best_pear + 1e-6
    anchor_pass = ccfv_pear is not None and (ccfv_pear >= 0.5 or (ccfv_tau is not None and ccfv_tau >= 0.3))
    weak_pass = ccfv_pear is not None and (ccfv_pear >= 0.3 or (ccfv_tau is not None and ccfv_tau >= 0.2))
    hits = [per_dir[d]["stats"]["ccfv"]["top1_hit"] for d in per_dir]
    all_hit = bool(hits) and all(h == 1 for h in hits) if all(h >= 0 for h in hits) else False
    conclusion = (
        "supported" if (anchor_pass and beats and all_hit)
        else "partially_supported" if (anchor_pass or (weak_pass and beats))
        else "contradicted" if ccfv_pear is not None
        else "inconclusive"
    )

    metrics = {
        "gt_run": a.runs,
        "evaluation": {
            "note": "frozen 2-organ subset; target task = Spleen (Liver source pool). "
                    "rank correlation between TE score and fine-tuned test Dice over the source-model pool",
            "correlation_base": "Pearson r, weighted Kendall tau-b (Vigna 2015), uniform pair weights",
            "directions": list(per_dir.keys()),
            "pool_size_per_direction": len(per_dir[next(iter(per_dir))]["models"]) if per_dir else 0,
        },
        "methods": summary,
        "paper_anchor_ccfv": PAPER_ANCHOR["ccfv"],
        "conclusion": conclusion,
        "generated_by": "05_analyze.py",
    }
    save_json(metrics, os.path.join(RESULTS_DIR, f"metrics{a.ft_suffix or ''}.json"))
    if not a.ft_suffix:
        # primary run doubles as the canonical metrics.json
        save_json(metrics, os.path.join(RESULTS_DIR, "metrics.json"))

    # ---- evidence table ------------------------------------------------------
    import csv
    ev_path = os.path.join(RESULTS_DIR, f"evidence_table{a.ft_suffix or ''}.csv"
                           if a.ft_suffix else os.path.join(RESULTS_DIR, "evidence_table.csv"))
    if not a.ft_suffix:
        # primary run writes the canonical evidence_table.csv (probe ground truth)
        with open(ev_path, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["direction", "source_model", "te_method", "te_score", "ft_dice", "rank"])
            for r in all_rows:
                w.writerow([r["direction"], r["source_model"], r["te_method"],
                            f"{r['te_score']:.6f}", f"{r['ft_dice']}" if r["ft_dice"] is not None else "",
                            r["rank"]])

    save_json(per_dir, os.path.join(RESULTS_DIR, "rankings.json"))
    print("\n=== summary ===")
    print(json.dumps(summary, indent=2))
    print("CONCLUSION:", conclusion)
    write_figures(per_dir, directions=list(per_dir.keys()))


def write_figures(per_dir, directions):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    for d in directions:
        fig, axes = plt.subplots(1, len(METHODS), figsize=(4.2 * len(METHODS), 4.2))
        if len(METHODS) == 1:
            axes = [axes]
        ft = np.array(per_dir[d]["ft_dice"])
        for ax, m in zip(axes, METHODS):
            s = np.array(per_dir[d]["te"][m])
            ax.scatter(s, ft, alpha=0.8, s=60)
            if np.std(s) > 0 and np.std(ft) > 0:
                b, a = np.polyfit(s, ft, 1)
                xs = np.linspace(s.min(), s.max(), 20)
                ax.plot(xs, a + b * xs, "r--", lw=1)
            ax.set_xlabel(METHOD_LABEL[m])
            ax.set_ylabel("fine-tuned Dice")
            ax.set_title(f"{d} | r={pearson(s, ft):.3f}")
        fig.tight_layout()
        fig.savefig(os.path.join(EVIDENCE_DIR, f"te_vs_dice_{d}.png"), dpi=120)
        plt.close(fig)
    print("figures saved to", EVIDENCE_DIR)


if __name__ == "__main__":
    main()