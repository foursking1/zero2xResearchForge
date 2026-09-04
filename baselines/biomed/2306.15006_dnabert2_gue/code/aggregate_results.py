"""Aggregate all experiment outputs into evidence_table.csv / metrics.json / claim.md content.

Sources:
  - results/data_stats.json        (computed by data_utils on the frozen gz files)
  - results/baseline_kmer.json     (k-mer LR/RF baselines)
  - results/finetune/*_full_metrics.json   (DNABERT-2 + LoRA fine-tune)
  - results/prmtprobe/*_probe_metrics.json (DNABERT-2 frozen-feature logistic probe)
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from data_utils import DATASETS, TASK_METRIC  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "results"


def load_json(p):
    return json.loads(Path(p).read_text())


def main():
    # ---------- 1. sample statistics ----------
    stats = load_json(RES / "data_stats.json")

    # ---------- 2. method metrics ----------
    baseline_lr = load_json(RES / "baseline_kmer.json")  # {k4_{ds}_lr: {f1, mcc, acc}}
    baseline_rf = load_json(RES / "baseline_rf.json") if (RES / "baseline_rf.json").exists() else {}
    finetune = {}
    for ds in DATASETS:
        p = RES / "finetune" / f"{ds}_full_metrics.json"
        if p.exists():
            finetune[ds] = load_json(p)
    probe = {}
    for ds in DATASETS:
        p = RES / "prmtprobe" / f"{ds}_probe_metrics.json"
        if p.exists():
            probe[ds] = load_json(p)

    # ---------- 3. evidence table ----------
    rows = []

    def add(ds, method, metrics, primary):
        for met in ("f1", "mcc", "acc"):
            rows.append({"dataset": ds, "method": method, "metric": met, "value": metrics[met]})

    for ds in DATASETS:
        prim = TASK_METRIC[ds]
        add(ds, "kmer4_lr", baseline_lr[f"k4_{ds}_lr"], prim)
        if baseline_rf:
            add(ds, "kmer4_rf", baseline_rf[f"k4_{ds}_rf"], prim)
        if ds in finetune:
            add(ds, finetune[ds]["method"], finetune[ds]["test"], prim)
        if ds in probe:
            add(ds, "dnabert2_feat_lr", probe[ds]["test"], prim)

    with open(RES / "evidence_table.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["dataset", "method", "metric", "value"])
        w.writeheader()
        w.writerows(rows)

    # ---------- 4. comparisons / verdict ----------
    comp = {ds: {} for ds in DATASETS}
    wins, losses = 0, 0
    for ds in DATASETS:
        prim = TASK_METRIC[ds]
        base_val = baseline_lr[f"k4_{ds}_lr"][prim]
        comp[ds]["baseline_kmer4_lr"] = base_val
        comp[ds]["baseline_kmer4_rf"] = baseline_rf.get(f"k4_{ds}_rf", {}).get(prim)
        f_lora = finetune[ds]["test"][prim] if ds in finetune and finetune[ds]["test"].get(prim) is not None else None
        comp[ds]["dnabert2_lora"] = f_lora
        comp[ds]["dnabert2_lora_minus_baseline"] = round(f_lora - base_val, 4) if f_lora is not None else None
        if f_lora is not None:
            if f_lora >= base_val:
                wins += 1
            else:
                losses += 1

    # paper anchors (reference only - never copied as our measurements)
    anchors = {
        "gue_mean_dnabert2": 66.80,
        "gue_mean_dnabert2_ft_extra": 67.77,
        "gue_mean_nucleotide_transformer": 66.93,
        "dnabert3mer_task_means": {"EMP": 49.54, "TF_M": 57.73, "PD": 84.63, "CPD": 72.96},
    }

    prom_f1 = comp["prom_300_all"].get("dnabert2_lora")
    core_f1 = comp["prom_core_all"].get("dnabert2_lora")
    mag_ok = prom_f1 is not None and prom_f1 >= 0.80
    wins_ok = wins >= len(DATASETS) - 1  # majority (>=3 of 4)

    if wins == len(DATASETS) and mag_ok:
        verdict = "supported"
        verdict_note = "foundation model >= k-mer baseline on all 4 frozen tasks and promoter F1 in paper magnitude"
    elif wins_ok and mag_ok:
        verdict = "supported"
        verdict_note = "foundation model >= k-mer baseline on majority and promoter F1 in paper magnitude"
    elif wins_ok or mag_ok:
        verdict = "partially_supported"
        verdict_note = f"wins={wins}/4 tasks, promoter-F1-magnitude={'yes' if mag_ok else 'no'}"
    elif wins == 0 and not mag_ok:
        verdict = "contradicted"
        verdict_note = "foundation model did not beat k-mer baseline on any task and magnitude off"
    else:
        verdict = "inconclusive"
        verdict_note = "mixed/indeterminate evidence on the frozen subset"

    out = {
        "task_id": "2306.15006_dnabert2_gue",
        "sample_statistics": stats,
        "methods": {
            "baseline": "k-mer(4-mer) frequency + logistic regression / random forest",
            "foundation": "DNABERT-2-117M BPE transformer + LoRA fine-tune (primary); frozen-feature logistic probe (supplementary)",
        },
        "per_task_comparison": comp,
        "wins_vs_baseline": {"n": wins, "total": len(DATASETS), "losses": losses},
        "magnitude_check": {"prom_300_all_f1": prom_f1, "promoter_f1_ge_80": mag_ok},
        "paper_anchors": anchors,
        "primary_metric_convention": TASK_METRIC,
        "verdict": verdict,
        "verdict_note": verdict_note,
        "evidence_table": str(RES / "evidence_table.csv"),
    }
    (RES / "metrics.json").write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()