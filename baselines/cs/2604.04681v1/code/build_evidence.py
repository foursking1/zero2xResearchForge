"""Build the final evidence table and metrics JSON for task 2604.04681v1 (BLS).

Evidence sources (all read in place, nothing copied):
  - FROZEN full-scale 200-epoch runs:  F:/dataset/2604.04681v1/results/table2/<cfg>/res.json
                                        F:/dataset/2604.04681v1/results/baseline_cifar10/res.json
  - OWN small-scale CPU runs (10 epochs, n_train=2000, 3 seeds):
                                        agent_solution/code/results/cpu/*.json
  - PSD analysis:                       F:/dataset/2604.04681v1/results/figure2_psd/psd_summary_info.json
  - Paper cited values:                 parsed from the paper Table 2 (see PAPER_TABLE2 below) and
                                        F:/dataset/2604.04681v1/paper_values.json

Outputs (relative to script dir):
  - ../results/evidence_table.csv
  - ../results/metrics.json
"""
import json, os, glob, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
RESULTS_DIR = os.path.join(ROOT, "results")
FROZEN_ROOT = r"F:/dataset/2604.04681v1"
FROZEN_T2 = os.path.join(FROZEN_ROOT, "results", "table2")
FROZEN_BASE = os.path.join(FROZEN_ROOT, "results", "baseline_cifar10", "res.json")
FROZEN_PSD = os.path.join(FROZEN_ROOT, "results", "figure2_psd", "psd_summary_info.json")
CPU_DIR = os.path.join(HERE, "results", "cpu")

# ----------------------------------------------------------------------------
# Paper-cited values (Table 2, ResNet18, Accuracy %). Source: paper text Table 2.
# NOTE: "\\" marks a ratio the paper calls unattainable for that method.
# ----------------------------------------------------------------------------
PAPER_TABLE2 = {
    "cifar10": {
        "full": 95.6,
        "InfoBatch": {0.3: 95.6, 0.5: 95.1, 0.7: 94.7},
        "SeTa": {0.3: 95.7, 0.5: 95.3, 0.7: 95.0},
        "BLS_InfoBatch": {0.3: 95.6, 0.5: 95.1, 0.7: 94.5},
        "BLS_SeTa": {0.3: 95.6, 0.5: 95.3, 0.7: 95.0},
    },
    "cifar100": {
        "full": 78.2,
        "InfoBatch": {0.3: 78.2, 0.5: 78.1, 0.7: 76.5},
        "SeTa": {0.3: 78.4, 0.5: 78.0, 0.7: 76.7},
        "BLS_InfoBatch": {0.3: 78.4, 0.5: 77.7, 0.7: None},  # paper: "\\" (unattainable)
        "BLS_SeTa": {0.3: 78.5, 0.5: 78.1, 0.7: 76.7},
    },
}

# ----------------------------------------------------------------------------
# Load frozen full-scale results
# ----------------------------------------------------------------------------
def load_frozen_table2():
    """Return {name: {data, prune_type, ratio, best, final, saved, epochs}}"""
    out = {}
    for d in sorted(os.listdir(FROZEN_T2)):
        rpath = os.path.join(FROZEN_T2, d, "res.json")
        if not os.path.exists(rpath):
            continue
        j = json.load(open(rpath))
        res = j.get("result", {})
        prune = j.get("prune", {})
        hyper = j.get("hyperparameter", {})
        va = res.get("valid_acc", [])
        data = hyper.get("data")
        pt = hyper.get("prune_type")
        ratio = hyper.get("prune_ratio")
        out[d] = {
            "data": data, "prune_type": pt, "ratio": ratio,
            "best": max(va) if va else None, "final": va[-1] if va else None,
            "saved_ratio": prune.get("saved_ratio"),
            "epochs": hyper.get("epoch"),
            "dataset_size": hyper.get("dataset_size"),
            "valid_acc": va,
        }
    return out

def load_frozen_baseline():
    j = json.load(open(FROZEN_BASE))
    res = j.get("result", {})
    return {
        "data": "cifar10", "prune_type": "full", "best": res.get("best_acc"),
        "final": res.get("final_acc"), "valid_acc": res.get("valid_acc", []),
    }

# ----------------------------------------------------------------------------
# Load own CPU runs
# ----------------------------------------------------------------------------
def load_cpu_runs():
    runs = []
    for f in glob.glob(os.path.join(CPU_DIR, "*.json")):
        if "stale" in os.path.basename(f):
            continue
        r = json.load(open(f))
        if "valid_acc" not in r:
            continue
        runs.append(r)
    return runs

def aggregate_cpu(runs):
    groups = {}
    for r in runs:
        key = (r["data"], r["prune_type"], r.get("ratio"), r["model"])
        groups.setdefault(key, []).append(r)
    rows = {}
    for key, rs in groups.items():
        best = np.array([r["best_acc"] for r in rs])
        saved = np.array([r["saved_ratio"] for r in rs])
        rows[key] = {
            "data": key[0], "prune_type": key[1], "ratio": key[2], "model": key[3],
            "n_seeds": len(rs),
            "best_mean": float(best.mean()),
            "best_std": float(best.std(ddof=1)) if len(best) > 1 else 0.0,
            "saved_mean": float(saved.mean()),
            "epochs": rs[0]["epochs"], "n_train": rs[0]["n_train"],
        }
    return rows

# ----------------------------------------------------------------------------
# Evidence rows
# ----------------------------------------------------------------------------
EVIDENCE_COLS = ["claim_id", "rule", "metric", "value", "unit", "criterion", "source", "judgement"]

rows = []

def add(claim, rule, metric, value, unit, criterion, source, judgement=""):
    rows.append({
        "claim_id": claim, "rule": rule, "metric": metric, "value": value,
        "unit": unit, "criterion": criterion, "source": source, "judgement": judgement,
    })

def fmt(x, nd=2):
    if x is None:
        return ""
    if isinstance(x, float):
        return f"{x:.{nd}f}"
    return str(x)

# ---------------- C02 (TASK.md): CIFAR10/100 ResNet18 @ 30/50/70% ----------------
frozen = load_frozen_table2()
base = load_frozen_baseline()
print("Loaded frozen table2 configs:", len(frozen))

# 1) BLS vs Full baseline (frozen full-scale)
full_c10 = base["best"]
for pt in ["BLS_InfoBatch", "BLS_SeTa"]:
    for r in [0.3, 0.5, 0.7]:
        cfg = next((c for c in frozen.values()
                    if c["data"] == "cifar10" and c["prune_type"] == pt and c["ratio"] == r), None)
        if cfg is None:
            continue
        d = cfg["best"] - full_c10
        judge = "indistinguishable" if abs(d) <= 1.0 else "different"
        add("C02", "R04", f"cifar10_{pt}@{int(r*100)}%_acc", fmt(cfg["best"]),
            "acc%", f"200ep full50k ResNet18 (frozen); full baseline {full_c10:.2f}",
            "frozen_fullscale", judge)
        add("C02", "R04", f"cifar10_{pt}@{int(r*100)}%_delta_vs_full", fmt(d, 2),
            "pp", "frozen BLS best minus frozen full best", "frozen_fullscale", judge)
        add("C02", "R04", f"cifar10_{pt}@{int(r*100)}%_saved_ratio", fmt(cfg["saved_ratio"], 4),
            "ratio", "actual fraction of data skipped (frozen)", "frozen_fullscale", "")

# CIFAR100: no frozen full baseline -> compare to paper-cited full 78.2
for pt in ["BLS_InfoBatch", "BLS_SeTa"]:
    for r in [0.3, 0.5, 0.7]:
        cfg = next((c for c in frozen.values()
                    if c["data"] == "cifar100" and c["prune_type"] == pt and c["ratio"] == r), None)
        if cfg is None:
            continue
        pfull = PAPER_TABLE2["cifar100"]["full"]
        d = cfg["best"] - pfull
        judge = "indistinguishable" if abs(d) <= 1.0 else "better"
        add("C02", "R05/R06", f"cifar100_{pt}@{int(r*100)}%_acc", fmt(cfg["best"]),
            "acc%", "200ep full50k ResNet18 (frozen); paper full 78.2 (cited)",
            "frozen_fullscale", judge)
        add("C02", "R05/R06", f"cifar100_{pt}@{int(r*100)}%_delta_vs_full", fmt(d, 2),
            "pp", "frozen BLS best minus paper full (cited)", "frozen_fullscale", judge)
        add("C02", "R05/R06", f"cifar100_{pt}@{int(r*100)}%_saved_ratio", fmt(cfg["saved_ratio"], 4),
            "ratio", "actual fraction of data skipped (frozen)", "frozen_fullscale", "")

# 2) BLS vs InfoBatch/SeTa (frozen BLS vs paper-cited original methods)
for data in ["cifar10", "cifar100"]:
    for pt, orig in [("BLS_InfoBatch", "InfoBatch"), ("BLS_SeTa", "SeTa")]:
        for r in [0.3, 0.5, 0.7]:
            cfg = next((c for c in frozen.values()
                        if c["data"] == data and c["prune_type"] == pt and c["ratio"] == r), None)
            if cfg is None:
                continue
            pval = PAPER_TABLE2[data][orig][r]
            if pval is None:
                add("C02", "R04/R05/R06", f"{data}_{pt}@{int(r*100)}%_delta_vs_{orig}", "n/a",
                    "pp", "paper marks ratio unattainable for original method", "paper_cited", "inconclusive")
                continue
            d = cfg["best"] - pval
            judge = "indistinguishable" if abs(d) <= 1.0 else ("better" if d > 0 else "worse")
            add("C02", "R04/R05/R06", f"{data}_{pt}@{int(r*100)}%_delta_vs_{orig}", fmt(d, 2),
                "pp", f"frozen BLS best vs paper {orig} (cited), same pruning target",
                "frozen_vs_paper", judge)

# 3) Own CPU small-scale paired comparison (C02 robustness)
cpu = aggregate_cpu(load_cpu_runs())
for pt, orig in [("BLS_InfoBatch", "InfoBatch"), ("BLS_SeTa", "SeTa")]:
    for r in [0.3]:
        key_b = (("cifar10", pt, r, "resnet18"))
        key_o = (("cifar10", orig, r, "resnet18"))
        if key_b in cpu and key_o in cpu:
            d = cpu[key_b]["best_mean"] - cpu[key_o]["best_mean"]
            add("C02", "R04", f"cpu_cifar10_{pt}@{int(r*100)}%_delta_vs_{orig}_mean", fmt(d, 2),
                "pp", f"own CPU run (10ep, n_train=2000, {cpu[key_b]['n_seeds']} seeds), mean BLS minus mean {orig}",
                "own_cpu_run", "directional")
            add("C02", "R04", f"cpu_cifar10_{pt}@{int(r*100)}%_acc_mean", fmt(cpu[key_b]["best_mean"]),
                "acc%", f"own CPU run, {cpu[key_b]['n_seeds']} seeds, std {cpu[key_b]['best_std']:.2f}",
                "own_cpu_run", "directional")
# full vs BLS on CPU
for pt in ["BLS_InfoBatch", "BLS_SeTa"]:
    key_b = ("cifar10", pt, 0.3, "resnet18")
    key_f = ("cifar10", "full", 0.3, "resnet18")
    if key_b in cpu and key_f in cpu:
        d = cpu[key_b]["best_mean"] - cpu[key_f]["best_mean"]
        add("C02", "R04", f"cpu_cifar10_{pt}@30%_delta_vs_full_mean", fmt(d, 2),
            "pp", f"own CPU run, mean BLS minus mean full ({cpu[key_f]['best_mean']:.2f})",
            "own_cpu_run", "directional")

# ---------------- C01 (TASK.md): large-scale (ToCa/MJ+ST/SS1M) ----------------
# Data not available in the frozen workspace (code_audit confirms). Paper-cited only.
pv = json.load(open(os.path.join(FROZEN_ROOT, "paper_values.json")))["table_values"]
t1 = pv["table1"]
add("C01", "R01", "ToCa_COCO_CIDEr_BLS_InfoBatch", t1["ToCa_COCO_CIDEr_BLS_InfoBatch"], "CIDEr",
    "paper Table 1 (cited); no ToCa data in frozen workspace", "paper_cited", "inconclusive")
add("C01", "R01", "ToCa_COCO_CIDEr_BLS_SeTa", t1["ToCa_COCO_CIDEr_BLS_SeTa"], "CIDEr",
    "paper Table 1 (cited)", "paper_cited", "inconclusive")
add("C01", "R02", "MJ+ST_IIIT5k_BLS_InfoBatch", t1["MJ+ST_IIIT5k_ABINet_BLS_InfoBatch"], "acc%",
    "paper Table 1 (cited); no MJ+ST data in frozen workspace", "paper_cited", "inconclusive")
add("C01", "R03", "SS1M_COCO_CIDEr_BLS_SeTa", "n/a", "CIDEr",
    "paper anchor 45.6 (cited); no SS1M data in frozen workspace", "paper_cited", "inconclusive")

# ---------------- C03 (TASK.md): cross-architecture ----------------
t3 = pv["table3"]
for arch in ["ResNet18", "ResNet50", "EfficientNet", "ViT", "Swin", "Vim"]:
    add("C03", "R07/R08/R09", f"ImageNet_{arch}_BLS", t3[f"{arch}_BLS"], "acc%",
        "paper Table 3 (cited); no ImageNet data in frozen workspace", "paper_cited", "inconclusive")
# CIFAR100 ResNet50 probe (own CPU run, small scale)
for pt in ["BLS_InfoBatch", "BLS_SeTa"]:
    key_b = ("cifar100", pt, 0.3, "resnet50")
    key_f = ("cifar100", "full", 0.3, "resnet50")
    if key_b in cpu and key_f in cpu:
        d = cpu[key_b]["best_mean"] - cpu[key_f]["best_mean"]
        add("C03", "-", f"cpu_cifar100_{pt}@30%_ResNet50_delta_vs_full", fmt(d, 2),
            "pp", "own CPU run (10ep, n_train=2000, 1 seed) — directional only",
            "own_cpu_run", "directional")

# ---------------- C04 (TASK.md): diverse tasks ----------------
t4 = pv["table4"]
add("C04", "R10", "COCO_ViECap_CIDEr_BLS_SeTa", t4["COCO_ViECap_CIDEr_BLS_SeTa"], "CIDEr",
    "paper Table 4 (cited); no COCO captioning data in frozen workspace", "paper_cited", "inconclusive")
add("C04", "R11", "MSR_VTT_B4_BLS", t4["MSR_VTT_B4_BLS"], "B4",
    "paper Table 4 (cited); no MSR-VTT data in frozen workspace", "paper_cited", "inconclusive")
add("C04", "R12", "WHU_MVS_lt3_acc_BLS", "n/a", "acc%",
    "paper mentions multi-view stereo; no WHU-MVS data in frozen workspace", "paper_cited", "inconclusive")

# ---------------- S01 baseline reproduction (claim_spec C06) ----------------
d_base = base["best"] - PAPER_TABLE2["cifar10"]["full"]
add("S01", "R06", "cifar10_full_best_acc", fmt(base["best"]), "acc%",
    f"200ep full50k ResNet18 (frozen); paper 95.6 (cited), delta {d_base:+.2f}pp",
    "frozen_fullscale", "supported" if abs(d_base) <= 1.0 else "deviates")

# ---------------- S02 BLS implementation (claim_spec C07) ----------------
add("S02", "-", "BLS_EMA_update_present", "verified", "bool",
    "BLS/BLS/__init__.py lines 407-410: scores[idx] = alpha*scores[idx] + (1-alpha)*batch_loss (batch-conditional EMA)",
    "code_inspection", "supported")

# ---------------- S03 PSD frequency separation (claim_spec C08 / anchor R21) ----------------
psd = json.load(open(FROZEN_PSD))
add("S03", "R21", "signal_psd_ratio", fmt(psd["signal_ratio"], 4), "ratio",
    "frozen PSD analysis (n_batches=%d)" % psd["n_batches"], "frozen_fullscale", "")
add("S03", "R21", "noise_psd_ratio", fmt(psd["noise_ratio"], 4), "ratio",
    "frozen PSD analysis", "frozen_fullscale", "")
add("S03", "R21", "noise_psd_gt_signal_at_high_freq", "False", "bool",
    "frozen PSD summary r22_pass (paper claims noise>signal at high freq; reproduction does not confirm)",
    "frozen_fullscale", "contradicted")

# ---------------- S04 overhead (claim_spec C11 / anchor R29-R30) ----------------
t10 = pv["table10"]
add("S04", "R29/R30", "BLS_scoring_time_s", t10["BLS_scoring_time_s"], "s",
    "paper Table 10 (cited); no timing data in frozen workspace", "paper_cited", "inconclusive")
add("S04", "R29/R30", "InfoBatch_scoring_time_s", t10["InfoBatch_scoring_time_s"], "s",
    "paper Table 10 (cited)", "paper_cited", "inconclusive")

# ----------------------------------------------------------------------------
# Write outputs
# ----------------------------------------------------------------------------
df = pd.DataFrame(rows, columns=EVIDENCE_COLS)
os.makedirs(RESULTS_DIR, exist_ok=True)
out_csv = os.path.join(RESULTS_DIR, "evidence_table.csv")
df.to_csv(out_csv, index=False)
print("Wrote", out_csv, "rows:", len(df))

# metrics.json — machine-readable, keys consistent with evidence metric column
metrics = {}
for r in rows:
    metrics[r["metric"]] = {
        "value": r["value"], "unit": r["unit"], "criterion": r["criterion"],
        "source": r["source"], "judgement": r["judgement"],
    }
metrics["_meta"] = {
    "paper_id": "2604.04681v1",
    "generated_by": "build_evidence.py",
    "sources": {
        "frozen_fullscale": "F:/dataset/2604.04681v1/results/table2/*/res.json + baseline_cifar10/res.json (200ep, full 50k dataset, official BLS repo)",
        "own_cpu_run": "agent_solution/code/results/cpu/*.json (10ep, n_train=2000, ResNet18/50, own CPU runs)",
        "paper_cited": "values cited from paper tables (paper_values.json / paper text) — NOT reproduced",
        "code_inspection": "BLS/BLS/__init__.py",
    },
}
out_json = os.path.join(RESULTS_DIR, "metrics.json")
with open(out_json, "w") as f:
    json.dump(metrics, f, indent=1, ensure_ascii=False)
print("Wrote", out_json)
