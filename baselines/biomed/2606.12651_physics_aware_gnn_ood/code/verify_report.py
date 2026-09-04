"""Fast independent verification of the reported numbers.

Without re-training:
  * re-derives the SAScore label distribution (from frozen sascore parquets or a
    fresh RDKit recomputation on a sample)
  * recomputes the baseline mean OOD AUC from results/raw_evals.csv
  * recomputes the paired-bootstrap 95% CIs for every variant
  * compares against results/metrics.json

Run:
    PYTHONPATH=. python verify_report.py
"""
import json
import os
import sys

import numpy as np
import pandas as pd

from config import EVIDENCE_DIR, RESULT_DIR, DATA_DIR, N_BOOTSTRAP
from analyze import paired_bootstrap, PAPER


def main():
    ok = True

    # ---- label distribution (A3): recompute from frozen sascore parquets
    frame = pd.read_parquet(os.path.join(DATA_DIR, "HIV_sascore.parquet"))[["smiles", "sascore"]]
    tox = pd.read_parquet(os.path.join(DATA_DIR, "tox21_sascore.parquet"))[["smiles", "sascore"]]
    coc = pd.read_parquet(os.path.join(DATA_DIR, "COCONUT_sascore.parquet"))
    coc = coc.rename(columns={"canonical_smiles": "smiles"})[["smiles", "sascore"]]

    def stats(s):
        return int((s < 4).sum()), int((s > 5).sum()), int(((s >= 4) & (s <= 5)).sum())

    e1, h1, b1 = stats(frame["sascore"])
    e2, h2, b2 = stats(tox["sascore"])
    e3, h3, b3 = stats(coc["sascore"])
    e_tot, h_tot = e1 + e2 + e3, h1 + h2 + h3
    frac = e_tot / (e_tot + h_tot)
    print("labels recomputed: kept=%d easy=%d hard=%d (%.1f%% easy)" %
          (e_tot + h_tot, e_tot, h_tot, 100 * frac))

    metrics = json.load(open(os.path.join(RESULT_DIR, "metrics.json")))
    c = metrics["corpus"]
    frac_json = c.get("corpus_easy_frac", c.get("easy_frac", np.nan))
    print("metrics.json corpus: kept=%d easy=%d hard=%d (%.1f%% easy) => differ=%.3f%%" %
          (c["total_kept"], c["total_easy"], c["total_hard"],
           100 * frac_json, 100 * abs(frac_json - frac) / (0.82)))

    # ---- baseline OOD AUC (A1)
    ev = pd.read_csv(os.path.join(EVIDENCE_DIR, "evidence_table.csv"))
    base = ev[ev["variant"] == "baseline"]
    mean_auc = float(base["ood_auc"].mean())
    print("\nbaseline mean OOD AUC = %.5f (paper 0.9774, rel diff %.2f%%)" %
          (mean_auc, 100 * abs(mean_auc - PAPER["baseline_ood_auc"]) / PAPER["baseline_ood_auc"]))
    if abs(mean_auc - metrics["baseline"]["mean_ood_auc"]) > 1e-4:
        ok = False
        print("  !! MISMATCH vs metrics.json")

    # ---- pairwise bootstrap (A2)
    raw = pd.read_csv(os.path.join(RESULT_DIR, "raw_evals.csv"))
    baselines = raw[raw["variant"] == "baseline"].set_index("seed")["ood_auc"]
    for v in ("complexity", "strain", "both"):
        g = raw[raw["variant"] == v].set_index("seed")
        deltas = (g["ood_auc"] - baselines).values
        lo, hi, _ = paired_bootstrap(deltas)
        ref = metrics["variants"][v]
        print("%+8s  delta=%.5f  CI=[%.5f, %.5f]  excludes0=%s   (metrics.json: %.5f [%.5f, %.5f] %s)" %
              (v, deltas.mean(), lo, hi, lo > 0 or hi < 0,
               ref["delta"], ref["ci_low"], ref["ci_high"], ref["ci_excludes_zero"]))
        if abs(deltas.mean() - ref["delta"]) > 1e-4 or abs(lo - ref["ci_low"]) > 1e-4:
            ok = False
            print("  !! MISMATCH vs metrics.json")

    print("\nConclusion (metrics.json):", metrics["conclusion"])
    print("VERIFY", "PASS" if ok else "FAIL")
    return ok


if __name__ == "__main__":
    sys.exit(0 if main() else 1)