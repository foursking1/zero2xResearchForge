"""Compute results/metrics.json from results/evidence_table.csv (single source of truth).

Also recomputed by train_seq_head.py after it appends position-aware head rows.
"""
import json
import os
import sys
import time

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import CSV_FILES, RESULTS_DIR  # noqa: E402


def main():
    table = pd.read_csv(os.path.join(RESULTS_DIR, "evidence_table.csv"))

    # best pretrained (esm2-*) and best hand-crafted (one-hot / aa-composition) per task
    def best(sub):
        return float(sub.loc[sub.spearman_rho.idxmax(), "spearman_rho"])

    metrics = {
        "evaluated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "paper_anchors": {
            "fluorescence": {"onehot": 0.14, "pretrain_transformer": 0.68,
                             "pretrain_lstm": 0.67, "unirep": 0.67},
            "stability": {"onehot": 0.19, "pretrain_transformer": 0.73,
                          "pretrain_lstm": 0.69, "pretrain_resnet": 0.73, "unirep": 0.73},
            "note": "Paper Table 2 values for discussion only; never counted as measured.",
        },
    }
    stats_path = os.path.join(RESULTS_DIR, "dataset_stats.json")
    if os.path.isfile(stats_path):
        metrics["dataset"] = json.load(open(stats_path))

    for task in CSV_FILES:
        sub = table[table.task == task]
        pret = sub[sub.representation.str.startswith("esm2-")]
        hand = sub[sub.representation.str.startswith(("one-hot", "aa-"))]
        bp, bo = best(pret), best(hand)
        metrics[task + "_best_pretrain_rho"] = round(bp, 6)
        metrics[task + "_best_pretrain_model"] = str(
            pret.loc[pret["spearman_rho"].idxmax(), "model"])
        metrics[task + "_best_onehot_rho"] = round(bo, 6)
        metrics[task + "_best_onehot_model"] = str(
            hand.loc[hand["spearman_rho"].idxmax(), "model"])
        metrics[task + "_delta_rho"] = round(bp - bo, 6)
        metrics[task + "_n_rows"] = int(table[table.task == task].shape[0])

    deltas = [metrics[t + "_delta_rho"] for t in CSV_FILES]
    if all(d > 0 for d in deltas):
        verdict = "supported"
    elif sum(d > 0 for d in deltas) == 1:
        verdict = "partially_supported"
    elif all(d <= 0 for d in deltas):
        verdict = "contradicted"
    else:
        verdict = "inconclusive"
    metrics["verdict"] = verdict
    metrics["verdict_definition"] = (
        "supported: pretrained representation beats one-hot on both tasks; "
        "partially_supported: on exactly one task; contradicted: on neither. "
        "All metrics computed on the test split of the frozen data.")
    with open(os.path.join(RESULTS_DIR, "metrics.json"), "w") as fh:
        json.dump(metrics, fh, indent=2, ensure_ascii=False)
    print("metrics.json written. verdict =", verdict, flush=True)
    return metrics


if __name__ == "__main__":
    main()