"""Compile final deliverables: results/evidence_table.csv and results/metrics.json.

Aggregates:
  1. Frozen full-scale 200-epoch BLS results vs paper Table 2 (cited)
  2. Frozen CIFAR10/100 full-batch baselines
  3. Frozen CIFAR100 cross-arch (ResNet18 vs ResNet50) BLS results
  4. Frozen PSD frequency-separation analysis
  5. My CPU direct-comparison matrix (BLS vs InfoBatch/SeTa, same seeds)
Outputs a flat metric list in evidence_table.csv and a machine-readable metrics.json.
"""
import json, os, glob
import numpy as np
import pandas as pd

RESDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results", "cpu")
FROZEN = r"F:/dataset/2604.04681v1/results"
BLS_RES = r"F:/dataset/2604.04681v1/code/BLS/results"

# Paper Table 2 cited (ResNet18 Accuracy %, from PDF) -- '论文引用'
PAPER_T2 = {
    ("cifar10", "full"): 95.6,
    ("cifar10", "InfoBatch", 0.3): 95.6, ("cifar10", "InfoBatch", 0.5): 95.1, ("cifar10", "InfoBatch", 0.7): 94.7,
    ("cifar10", "SeTa", 0.3): 95.7, ("cifar10", "SeTa", 0.5): 95.3, ("cifar10", "SeTa", 0.7): 95.0,
    ("cifar10", "BLS_InfoBatch", 0.3): 95.6, ("cifar10", "BLS_InfoBatch", 0.5): 95.1, ("cifar10", "BLS_InfoBatch", 0.7): 94.5,
    ("cifar10", "BLS_SeTa", 0.3): 95.6, ("cifar10", "BLS_SeTa", 0.5): 95.3, ("cifar10", "BLS_SeTa", 0.7): 95.0,
    ("cifar100", "full"): 78.2,
    ("cifar100", "InfoBatch", 0.3): 78.2, ("cifar100", "InfoBatch", 0.5): 78.1, ("cifar100", "InfoBatch", 0.7): 76.5,
    ("cifar100", "SeTa", 0.3): 78.4, ("cifar100", "SeTa", 0.5): 78.0, ("cifar100", "SeTa", 0.7): 76.7,
    ("cifar100", "BLS_InfoBatch", 0.3): 78.4, ("cifar100", "BLS_InfoBatch", 0.5): 77.7,
    ("cifar100", "BLS_SeTa", 0.3): 78.5, ("cifar100", "BLS_SeTa", 0.5): 78.1, ("cifar100", "BLS_SeTa", 0.7): 76.7,
}
# Paper Table 3 CIFAR100 cross-arch (Accuracy / Pruned %) -- '论文引用'
PAPER_T3_CIFAR100 = {
    ("R18", "full"): 78.2, ("R18", "BLS_InfoBatch"): 78.3, ("R18", "BLS_SeTa"): 78.4,
    ("R50", "full"): 80.6, ("R50", "BLS_InfoBatch"): 80.5, ("R50", "BLS_SeTa"): 80.7,
}

rows = []  # (metric, value, definition)
def add(name, value, definition):
    rows.append({"name": name, "value": value, "definition": definition})

def fmt(v, nd=3):
    return round(float(v), nd) if v is not None else None

# ---------------- 1. Frozen full-scale BLS vs paper Table 2 ----------------
frozen = json.load(open(os.path.join(FROZEN, "table2", "combined.json")))
pt_map = {"bls_inf": "BLS_InfoBatch", "bls_seta": "BLS_SeTa"}
for name, v in frozen["experiments"].items():
    data, which = name.rsplit("_", 1)[0].split("_", 1)
    ratio = int(name.rsplit("_", 1)[1]) / 100.0
    pt = pt_map[which]
    pv = PAPER_T2.get((data, pt, ratio))
    add(f"frozen_{name}_best_acc", fmt(v["best"]),
        f"冻结200epoch复现: CIFAR {data} {pt} @ {int(ratio*100)}% 最优准确率 (ResNet18)")
    if pv is not None:
        add(f"frozen_{name}_delta_vs_paper", fmt(v["best"] - pv),
            f"论文引用差值: 冻结复现 - 论文Table2 ({pt} {int(ratio*100)}%, 论文值{pv})")
    add(f"frozen_{name}_saved_ratio", fmt(v["saved_ratio"]),
        f"实际样本剪枝比例 (saved_ratio)")

# ---------------- 2. Frozen baselines ----------------
base10 = json.load(open(os.path.join(FROZEN, "baseline_cifar10", "res.json")))
va10 = base10["result"]["valid_acc"]
add("frozen_cifar10_full_best", fmt(max(va10)), "冻结200epoch CIFAR10 ResNet18 全量训练最优准确率")
add("frozen_cifar10_full_final", fmt(va10[-1]), "冻结200epoch CIFAR10 ResNet18 全量训练最终准确率")

# ---------------- 3. Frozen CIFAR100 cross-arch (R18 vs R50) ----------------
ab = json.load(open(os.path.join(BLS_RES, "table8_ablation", "table8_ablation.json")))
add("frozen_cifar100_r18_bls_infobatch_30", fmt(ab["resnet18_with_ema"]["best_accuracy"]),
    "冻结200epoch CIFAR100 ResNet18 BLS-InfoBatch@30% 最优准确率 (EMA)")
add("frozen_cifar100_r50_bls_infobatch_30", fmt(ab["resnet50_with_ema"]["best_accuracy"]),
    "冻结200epoch CIFAR100 ResNet50 BLS-InfoBatch@30% 最优准确率 (EMA)")
add("frozen_cifar100_r18_bls_infobatch_30_delta_vs_full", fmt(ab["resnet18_with_ema"]["best_accuracy"] - PAPER_T3_CIFAR100[("R18", "full")]),
    "论文引用差值: R18 BLS-InfoBatch@30 vs R18 Full(78.2)")
add("frozen_cifar100_r50_bls_infobatch_30_delta_vs_full", fmt(ab["resnet50_with_ema"]["best_accuracy"] - PAPER_T3_CIFAR100[("R50", "full")]),
    "论文引用差值: R50 BLS-InfoBatch@30 vs R50 Full(80.6)")

# ---------------- 4. Frozen PSD ----------------
psd = json.load(open(os.path.join(FROZEN, "figure2_psd", "psd_summary_info.json")))
add("psd_signal_ratio", fmt(psd["signal_ratio"]), "冻结PSD分析: 信号(signal)PSD占比")
add("psd_noise_ratio", fmt(psd["noise_ratio"]), "冻结PSD分析: 噪声(noise)PSD占比")
add("psd_r22_pass", bool(psd["r22_pass"]),
    "冻结PSD分析: 论文图2'噪声能量>信号能量'断言是否通过 (paper claims noise>signal, frozen shows signal>noise)")

# ---------------- 5. CPU direct comparison matrix ----------------
def load_runs():
    out = []
    for f in glob.glob(os.path.join(RESDIR, "*.json")):
        if "stale" in os.path.basename(f):
            continue
        r = json.load(open(f))
        if "valid_acc" in r:
            out.append(r)
    return out

runs = load_runs()
def group(runs):
    g = {}
    for r in runs:
        g.setdefault((r["data"], r["prune_type"], r.get("ratio"), r["model"]), []).append(r)
    return g

groups = group(runs)
def agg_mean(g, field="best_acc"):
    return float(np.mean([r[field] for r in g]))
def agg_std(g, field="best_acc"):
    return float(np.std([r[field] for r in g], ddof=1)) if len(g) > 1 else 0.0

for (data, pt, ratio, model), g in sorted(groups.items()):
    key = f"cpu_{data}_{pt}_{ratio}_{model}"
    add(f"{key}_best_mean", fmt(agg_mean(g)),
        f"CPU复现(10epoch/2000样本): best acc 均值 n={len(g)}")
    add(f"{key}_best_std", fmt(agg_std(g)),
        f"CPU复现(10epoch/2000样本): best acc 标准差 (种子间)")

def paired(rows_g, data, ratio, model, a, b):
    ga = groups.get((data, a, ratio, model))
    gb = groups.get((data, b, ratio, model))
    if not ga or not gb:
        return None
    seeds = {}
    for r in ga + gb:
        seeds.setdefault(r["seed"], {}).setdefault(a if r["prune_type"] == a else b, r["best_acc"])
    common = [s for s in seeds if a in seeds[s] and b in seeds[s]]
    if len(common) < 2:
        return None
    da = np.array([seeds[s][a] for s in common])
    db = np.array([seeds[s][b] for s in common])
    diff = db - da
    return {"data": data, "ratio": ratio, "model": model, "orig": a, "bls": b,
            "n_seeds": len(common), "orig_mean": float(da.mean()), "bls_mean": float(db.mean()),
            "delta_mean": float(diff.mean()), "delta_std": float(diff.std(ddof=1)),
            "delta_min": float(diff.min()), "delta_max": float(diff.max())}

pairs = [("InfoBatch", "BLS_InfoBatch"), ("SeTa", "BLS_SeTa")]
for (data, ratio, model) in [("cifar10", 0.3, "resnet18"), ("cifar10", 0.5, "resnet18"),
                             ("cifar100", 0.3, "resnet18")]:
    for a, b in pairs:
        p = paired(runs and groups, data, ratio, model, a, b)
        if p:
            add(f"cpu_{data}_{ratio}_{model}_{a}_vs_{b}_delta_mean", fmt(p["delta_mean"]),
                f"CPU直接对比(BLS-原始, 同种子配对): {b} - {a} 最优准确率平均差 (pp), n_seeds={p['n_seeds']}")
            add(f"cpu_{data}_{ratio}_{model}_{a}_vs_{b}_delta_std", fmt(p["delta_std"]),
                "同种子配对差值的种子间标准差 (pp)")

# ---------------- Write outputs ----------------
outdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results")
os.makedirs(outdir, exist_ok=True)
df = pd.DataFrame(rows)
df.to_csv(os.path.join(outdir, "evidence_table.csv"), index=False, encoding="utf-8-sig")

metrics = {r["name"]: (r["value"] if not isinstance(r["value"], np.bool_) else bool(r["value"]))
           for r in rows}
with open(os.path.join(outdir, "metrics.json"), "w", encoding="utf-8") as f:
    json.dump(metrics, f, indent=2, ensure_ascii=False)

print(f"evidence_table.csv: {len(rows)} metrics")
print(f"metrics.json: {len(metrics)} keys")
print(json.dumps(metrics, indent=1, ensure_ascii=False)[:1500])
