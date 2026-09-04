# -*- coding: utf-8 -*-
"""Run the SEP ensemble experiment (arXiv:2303.08092).

Trains CoNN / Committee / RH v1 / RH v2 on the frozen SEPTEBBS data with
`n_splits` random stratified 70/30 splits, reports per-split confusion
matrices and TSS / HSS / precision / recall / accuracy / ROC AUC, and writes
results/{metrics,evidence_table,critical_checks,uncertainty}.json plus a
figure.

Usage:  python run_sep.py [--n_splits 10] [--epochs 500] [--seed 20260817]
"""
import os
import sys
import json
import csv
import time
import argparse
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sep_data
import sep_models
import sep_metrics

OUTDIR = os.path.normpath(os.path.join(HERE, "..", "results"))
FIGDIR = os.path.normpath(os.path.join(HERE, "..", "figures"))


CHECKPOINT = os.path.normpath(os.path.join(HERE, "..", "results", "partial_sep.json"))


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--n_splits", type=int, default=10)
    p.add_argument("--epochs", type=int, default=500)
    p.add_argument("--lr", type=float, default=1e-3)
    p.add_argument("--seed", type=int, default=20260817)
    p.add_argument("--methods", type=str, default="CoNN,Committee,RH_v1,RH_v2")
    p.add_argument("--quick", action="store_true", help="use fewer epochs (debug)")
    p.add_argument("--resume", action="store_true",
                   help="resume from partial_sep.json checkpoint if present")
    return p.parse_args()


def main():
    args = parse_args()
    rng = np.random.default_rng(args.seed)
    methods = args.methods.split(",")

    X, y, w, summary = sep_data.load_clean()
    print(f"[data] clean rows {summary['clean_rows']}, SEP {summary['clean_sep']}")

    from sklearn.model_selection import StratifiedShuffleSplit

    n_splits = args.n_splits
    epochs = 200 if args.quick else args.epochs

    # results container: method -> list of per-split metric dicts
    results = {m: [] for m in methods}
    split_meta = []
    t_total_start = time.time()

    start_split = 0
    if args.resume and os.path.exists(CHECKPOINT):
        with open(CHECKPOINT) as f:
            cp = json.load(f)
        # restore completed per-split metrics (ignore methods not requested)
        for m in methods:
            results[m] = list(cp["results"].get(m, []))
        split_meta = list(cp.get("split_meta", []))
        start_split = int(cp.get("split_idx", 0))
        # advance the split-seed rng past the completed splits (10 draws each)
        for _ in range(10 * start_split):
            rng.integers(0, 2**31 - 1)
        print(f"[resume] restored {start_split} completed splits "
              f"({len(results[methods[0]])} per method)")

    sss = StratifiedShuffleSplit(n_splits=n_splits, test_size=0.3, random_state=args.seed)
    split_idx = 0
    for tr_idx, te_idx in sss.split(X, y):
        if split_idx < start_split:
            split_idx += 1
            continue
        Xtr, ytr = X[tr_idx], y[tr_idx]
        Xte, yte = X[te_idx], y[te_idx]
        seeds = [rng.integers(0, 2**31 - 1) for _ in range(10)]
        split_meta.append({
            "split": split_idx,
            "n_train": int(len(tr_idx)),
            "n_test": int(len(te_idx)),
            "n_sep_test": int(yte.sum()),
        })
        print(f"[split {split_idx}] train {len(tr_idx)} test {len(te_idx)} "
              f"SEP_test {yte.sum()}")
        for m in methods:
            t0 = time.time()
            res = sep_models.run_method(m, Xtr, ytr, Xte, w, seeds,
                                        epochs=epochs, lr=args.lr)
            # operating threshold: Youden-J on TRAIN probabilities (paper's
            # operating point is ~FPR 4%, not raw prob 0.5)
            thr, _ = sep_metrics.best_threshold(ytr, res["p_train"])
            met = sep_metrics.compute_all(yte, res["p"], m, threshold=thr)
            met["threshold"] = thr
            met["time_s"] = res["time_s"]
            met["total_time_s"] = time.time() - t0
            met["n_selected"] = res["n_selected"]
            met["epochs_used"] = res["epochs_used"]
            met["lr_used"] = res["lr_used"]
            results[m].append(met)
            print(f"    {m:9s} TSS={met['TSS']:.4f} HSS={met['HSS']:.4f} "
                  f"AUC={met['AUC']:.4f} tp={met['tp']} fn={met['fn']} "
                  f"fp={met['fp']} tn={met['tn']} thr={thr:.3f} [{met['time_s']:.1f}s]")
        # checkpoint after each split so an interrupted run can resume
        os.makedirs(os.path.dirname(CHECKPOINT), exist_ok=True)
        tmp = os.path.join(os.path.dirname(CHECKPOINT), "partial_sep.tmp.json")
        with open(tmp, "w") as f:
            json.dump({"results": results, "split_meta": split_meta,
                       "split_idx": split_idx + 1}, f, default=float)
        os.replace(tmp, CHECKPOINT)
        split_idx += 1

    # ---- summary stats ----
    stat_names = ["TSS", "HSS", "precision", "recall", "accuracy", "AUC",
                  "tp", "fn", "fp", "tn"]
    summary_stats = {}
    for m in methods:
        arr = {s: np.array([r[s] for r in results[m]], dtype=float) for s in stat_names}
        msum = {}
        for s in stat_names:
            a = arr[s]
            msum[s] = {
                "mean": float(a.mean()),
                "std": float(a.std()),
                "median": float(np.median(a)),
                "mad": float(np.median(np.abs(a - np.median(a)))),
            }
        msum["time_s_mean"] = float(np.mean([r["time_s"] for r in results[m]]))
        msum["n_selected"] = results[m][0]["n_selected"]
        msum["epochs_used"] = results[m][0]["epochs_used"]
        summary_stats[m] = msum
        print(f"\n=== {m} ===")
        for s in ["TSS", "HSS", "precision", "recall", "accuracy", "AUC"]:
            print(f"  {s:10s} mean±std {msum[s]['mean']:.4f}±{msum[s]['std']:.4f}  "
                  f"med±MAD {msum[s]['median']:.4f}±{msum[s]['mad']:.4f}")
        print(f"  confusion med±MAD: TP {msum['tp']['median']:.1f}±{msum['tp']['mad']:.1f} "
              f"FN {msum['fn']['median']:.1f}±{msum['fn']['mad']:.1f} "
              f"FP {msum['fp']['median']:.1f}±{msum['fp']['mad']:.1f} "
              f"TN {msum['tn']['median']:.1f}±{msum['tn']['mad']:.1f}")

    # ---- critical checks ----
    checks = {
        "claim_RHv2_TSS_ge_CoNN": {
            "RHv2_med_TSS": summary_stats["RH_v2"]["TSS"]["median"],
            "CoNN_med_TSS": summary_stats["CoNN"]["TSS"]["median"],
            "passed": bool(summary_stats["RH_v2"]["TSS"]["median"]
                           >= summary_stats["CoNN"]["TSS"]["median"]),
        },
        "claim_ensemble_dispersion_lower": {
            "CoNN_TSS_std": summary_stats["CoNN"]["TSS"]["std"],
            "CoNN_TSS_mad": summary_stats["CoNN"]["TSS"]["mad"],
            "ensembles": {m: {"TSS_std": summary_stats[m]["TSS"]["std"],
                              "TSS_mad": summary_stats[m]["TSS"]["mad"]}
                          for m in methods if m != "CoNN"},
            "passed": bool(all(summary_stats[m]["TSS"]["mad"]
                               < summary_stats["CoNN"]["TSS"]["mad"]
                               for m in methods if m != "CoNN")),
        },
        "claim_RHv2_HSS_ge_CoNN": {
            "RHv2_med_HSS": summary_stats["RH_v2"]["HSS"]["median"],
            "CoNN_med_HSS": summary_stats["CoNN"]["HSS"]["median"],
            "passed": bool(summary_stats["RH_v2"]["HSS"]["median"]
                           >= summary_stats["CoNN"]["HSS"]["median"]),
        },
        "claim_RHv2_ge_Committee_and_RHv1": {
            "RHv2_med_TSS": summary_stats["RH_v2"]["TSS"]["median"],
            "Committee_med_TSS": summary_stats["Committee"]["TSS"]["median"],
            "RHv1_med_TSS": summary_stats["RH_v1"]["TSS"]["median"],
            "RHv2_med_HSS": summary_stats["RH_v2"]["HSS"]["median"],
            "Committee_med_HSS": summary_stats["Committee"]["HSS"]["median"],
            "RHv1_med_HSS": summary_stats["RH_v1"]["HSS"]["median"],
            "passed": bool(summary_stats["RH_v2"]["TSS"]["median"]
                           >= summary_stats["Committee"]["TSS"]["median"]
                           and summary_stats["RH_v2"]["TSS"]["median"]
                           >= summary_stats["RH_v1"]["TSS"]["median"]),
        },
    }

    # ---- outputs ----
    os.makedirs(OUTDIR, exist_ok=True)
    os.makedirs(FIGDIR, exist_ok=True)

    paper_table2 = {
        "CoNN": {"TSS": 0.906, "HSS": 0.163},
        "Committee": {"TSS": 0.926, "HSS": 0.168},
        "RH_v1": {"TSS": 0.915, "HSS": 0.163},
        "RH_v2": {"TSS": 0.944, "HSS": 0.168},
    }
    vs_paper = {}
    for m in methods:
        vs_paper[m] = {
            "TSS_paper_med": paper_table2[m]["TSS"],
            "TSS_ours_med": summary_stats[m]["TSS"]["median"],
            "TSS_delta": float(summary_stats[m]["TSS"]["median"] - paper_table2[m]["TSS"]),
            "HSS_paper_med": paper_table2[m]["HSS"],
            "HSS_ours_med": summary_stats[m]["HSS"]["median"],
            "HSS_delta": float(summary_stats[m]["HSS"]["median"] - paper_table2[m]["HSS"]),
        }

    metrics = {
        "task": "2303.08092_solar_energetic_particle_ensemble",
        "device": "CPU",
        "n_splits": n_splits,
        "split_type": "stratified 70/30",
        "epochs_base": epochs,
        "lr_base": args.lr,
        "seed": args.seed,
        "data_summary": summary,
        "methods": summary_stats,
        "critical_checks": checks,
        "vs_paper_table2": vs_paper,
        "conclusion": ("supported" if checks["claim_RHv2_TSS_ge_CoNN"]["passed"]
                       and checks["claim_ensemble_dispersion_lower"]["passed"]
                       and checks["claim_RHv2_HSS_ge_CoNN"]["passed"]
                       else ("partially_supported"
                             if checks["claim_RHv2_TSS_ge_CoNN"]["passed"]
                             else "contradicted")),
        "total_time_s": time.time() - t_total_start,
    }
    with open(os.path.join(OUTDIR, "metrics.json"), "w") as f:
        json.dump(metrics, f, indent=2, default=float)

    # evidence table
    with open(os.path.join(OUTDIR, "evidence_table.csv"), "w", newline="") as f:
        wcsv = csv.writer(f)
        wcsv.writerow(["method", "split", "TSS", "HSS", "precision", "recall",
                       "accuracy", "AUC", "tp", "fn", "fp", "tn", "threshold",
                       "time_s"])
        for m in methods:
            for k, r in enumerate(results[m]):
                wcsv.writerow([m, k, f"{r['TSS']:.4f}", f"{r['HSS']:.4f}",
                               f"{r['precision']:.4f}", f"{r['recall']:.4f}",
                               f"{r['accuracy']:.4f}", f"{r['AUC']:.4f}",
                               r["tp"], r["fn"], r["fp"], r["tn"],
                               f"{r['threshold']:.4f}", f"{r['time_s']:.1f}"])

    with open(os.path.join(OUTDIR, "critical_checks.json"), "w") as f:
        json.dump(checks, f, indent=2, default=float)

    unc = {m: {s: summary_stats[m][s] for s in ["TSS", "HSS", "precision", "recall",
                                                "accuracy", "AUC"]}
           for m in methods}
    with open(os.path.join(OUTDIR, "uncertainty.json"), "w") as f:
        json.dump({"per_method": unc, "n_splits": n_splits,
                   "note": "std and MAD across independent random 70/30 splits"},
                  f, indent=2, default=float)

    # figure
    try:
        make_figure(results, methods, os.path.join(FIGDIR, "sep_metrics.svg"))
    except Exception as e:
        print("figure failed:", e)

    print("\nDONE. results in", OUTDIR)


def make_figure(results, methods, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(6, 4.5))
    labels = []
    for m in methods:
        tss = np.array([r["TSS"] for r in results[m]])
        hss = np.array([r["HSS"] for r in results[m]])
        ax.errorbar(tss.mean(), hss.mean(), xerr=tss.std(), yerr=hss.std(),
                    fmt="o", capsize=4, label=m)
        labels.append(m)
    ax.set_xlabel("TSS"); ax.set_ylabel("HSS")
    ax.set_title("SEP classifiers: TSS vs HSS (mean ± std over splits)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    main()
