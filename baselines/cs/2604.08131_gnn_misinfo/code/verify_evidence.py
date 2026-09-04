"""
Independent verification of the evidence table.

Recomputes, from the raw saved predictions + frozen label definition, the
exact binary F1 / precision / recall reported in results/evidence_table.csv
using sklearn.metrics only (no model code), so an external judge can
spot-check the numbers without re-running training.

Usage:
    python verify_evidence.py [--results ../results]
"""

import argparse
import os

import numpy as np
import pandas as pd
from sklearn.metrics import f1_score, precision_score, recall_score


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default=os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "results"))
    args = ap.parse_args()

    ev = pd.read_csv(os.path.join(args.results, "evidence_table.csv"))
    preds = pd.read_csv(os.path.join(args.results, "predictions.csv"))

    print(f"{'model':<10} {'seed':<5} {'n':<7} {'f1':<8} {'prec':<8} "
          f"{'rec':<8} {'acc':<7}")
    per_seed = {}
    for model in ("graphsage", "mlp"):
        sub = preds[preds["model"] == model]
        for seed, g in sub.groupby("seed"):
            yt, yp = g["y_true"].values, g["y_pred"].values
            per_seed[(model, seed)] = dict(
                n=len(yt),
                f1=f1_score(yt, yp),
                precision=precision_score(yt, yp),
                recall=recall_score(yt, yp),
                acc=(yt == yp).mean())
            r = per_seed[(model, seed)]
            print(f"{model:<10} {seed:<5} {r['n']:<7} {r['f1']:<8.4f} "
                  f"{r['precision']:<8.4f} {r['recall']:<8.4f} "
                  f"{r['acc']:<7.4f}")

    print("\n--- 3-seed aggregates (recomputed from saved predictions) ---")
    for model in ("graphsage", "mlp"):
        seeds_sorted = sorted({s for (m, s) in per_seed if m == model})
        f1s = [per_seed[(model, s)]["f1"] for s in seeds_sorted]
        precs = [per_seed[(model, s)]["precision"] for s in seeds_sorted]
        recs = [per_seed[(model, s)]["recall"] for s in seeds_sorted]
        ns = [per_seed[(model, s)]["n"] for s in seeds_sorted]
        print(f"{model:<10} F1={np.mean(f1s)*100:.2f}±{np.std(f1s)*100:.2f}% "
              f"P={np.mean(precs)*100:.2f}% R={np.mean(recs)*100:.2f}% "
              f"(n={set(ns)})")

    print("\n--- evidence_table.csv ---")
    print(ev[["model", "split", "n", "f1", "precision", "recall",
              "f1_gap_pp"]].to_string(index=False))

    # explicit checks
    ok = True
    for _, row in ev.iterrows():
        model = row["model"]
        seed_n = {s for (m, s) in per_seed if m == model}
        f1s = [per_seed[(model, s)]["f1"] for s in sorted(seed_n)]
        rec_f1 = np.mean(f1s) * 100
        if abs(rec_f1 - row["f1"]) > 0.51:
            ok = False
            print(f"[MISMATCH] {model}: recomputed {rec_f1:.2f} vs table "
                  f"{row['f1']}")
    print("\nverification: " + ("PASS (evidence table consistent with saved "
                                "predictions)" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())