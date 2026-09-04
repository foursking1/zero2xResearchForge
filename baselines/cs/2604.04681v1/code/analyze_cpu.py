"""Analyze CPU experiment matrix for C02 (BLS vs InfoBatch/SeTa statistical comparison).

Reads results/cpu/*.json produced by run_all.py, aggregates across seeds,
computes paired BLS-vs-original accuracy differences and a tolerance-based
"statistically indistinguishable" check, and compares with the frozen
full-scale 200-epoch results and paper Table 2 values (cited).
"""
import json, os, glob, sys
import numpy as np, pandas as pd
from scipy import stats

RESDIR = "results/cpu"

# Paper Table 2 cited values (Accuracy %, ResNet18). † adjusted-epochs row.
PAPER_TABLE2 = {
    ("cifar10", "full", None): 95.6,
    ("cifar10", "InfoBatch", 0.3): 95.6, ("cifar10", "InfoBatch", 0.5): 95.1, ("cifar10", "InfoBatch", 0.7): 94.7,
    ("cifar10", "SeTa", 0.3): 95.7, ("cifar10", "SeTa", 0.5): 95.3, ("cifar10", "SeTa", 0.7): 95.0,
    ("cifar10", "BLS_InfoBatch", 0.3): 95.6, ("cifar10", "BLS_InfoBatch", 0.5): 95.1, ("cifar10", "BLS_InfoBatch", 0.7): 94.5,
    ("cifar10", "BLS_SeTa", 0.3): 95.6, ("cifar10", "BLS_SeTa", 0.5): 95.3, ("cifar10", "BLS_SeTa", 0.7): 95.0,
    ("cifar100", "full", None): 78.2,
    ("cifar100", "InfoBatch", 0.3): 78.2, ("cifar100", "InfoBatch", 0.5): 78.1, ("cifar100", "InfoBatch", 0.7): 76.5,
    ("cifar100", "SeTa", 0.3): 78.4, ("cifar100", "SeTa", 0.5): 78.0, ("cifar100", "SeTa", 0.7): 76.7,
    ("cifar100", "BLS_InfoBatch", 0.3): 78.4, ("cifar100", "BLS_InfoBatch", 0.5): 77.7,
    ("cifar100", "BLS_SeTa", 0.3): 78.5, ("cifar100", "BLS_SeTa", 0.5): 78.1, ("cifar100", "BLS_SeTa", 0.7): 76.7,
}

def load_runs(resdir=RESDIR):
    runs = []
    for f in glob.glob(os.path.join(resdir, "*.json")):
        if "stale" in os.path.basename(f):
            continue
        r = json.load(open(f))
        if "valid_acc" not in r:
            continue
        runs.append(r)
    return runs

def aggregate(runs):
    """Group by (data, prune_type, ratio, model); return list of summary dicts."""
    groups = {}
    for r in runs:
        key = (r["data"], r["prune_type"], r.get("ratio"), r["model"])
        groups.setdefault(key, []).append(r)
    rows = []
    for key, rs in groups.items():
        best = np.array([r["best_acc"] for r in rs])
        final = np.array([r["final_acc"] for r in rs])
        saved = np.array([r["saved_ratio"] for r in rs])
        rows.append({
            "data": key[0], "prune_type": key[1], "ratio": key[2], "model": key[3],
            "n_seeds": len(rs),
            "best_mean": best.mean(), "best_std": best.std(ddof=1) if len(best) > 1 else 0.0,
            "best_min": best.min(), "best_max": best.max(),
            "final_mean": final.mean(), "final_std": final.std(ddof=1) if len(final) > 1 else 0.0,
            "saved_mean": saved.mean(),
            "seeds": {r["seed"]: {"best": r["best_acc"], "final": r["final_acc"], "curve": r["valid_acc"]} for r in rs},
        })
    return pd.DataFrame(rows)

def paired_test(rows, data, ratio, model, a, b):
    """Paired BLS vs original using the same seeds."""
    ra = rows[(rows.data == data) & (rows.ratio == ratio) & (rows.model == model) & (rows.prune_type == a)]
    rb = rows[(rows.data == data) & (rows.ratio == ratio) & (rows.model == model) & (rows.prune_type == b)]
    if ra.empty or rb.empty:
        return None
    sa, sb = ra.iloc[0]["seeds"], rb.iloc[0]["seeds"]
    common = sorted(set(sa) & set(sb))
    if len(common) < 2:
        return None
    da = np.array([sa[s]["best"] for s in common])
    db = np.array([sb[s]["best"] for s in common])
    diff = db - da  # BLS - original
    dmean, dstd = diff.mean(), diff.std(ddof=1)
    t, p = stats.ttest_1samp(diff, 0.0)
    # tolerance-based check used by paper: within 0.5 pp on average, all within 1 pp
    pass_05 = abs(dmean) <= 0.5 and np.all(np.abs(diff) <= 1.0)
    # epoch-level pooled paired comparison (illustrative; not i.i.d.)
    ea = np.concatenate([np.array(sa[s]["curve"]) for s in common])
    eb = np.concatenate([np.array(sb[s]["curve"]) for s in common])
    _, p_epoch = stats.ttest_rel(eb, ea)
    return {
        "data": data, "ratio": ratio, "model": model,
        "orig": a, "bls": b, "n_seeds": len(common),
        "orig_best_mean": da.mean(), "bls_best_mean": db.mean(),
        "delta_mean": dmean, "delta_std": dstd,
        "delta_min": diff.min(), "delta_max": diff.max(),
        "p_seed": float(p), "p_epoch_pooled": float(p_epoch),
        "pass_tolerance_0.5pp": bool(pass_05),
    }

def main():
    runs = load_runs()
    if not runs:
        print("NO RUNS FOUND in", RESDIR)
        sys.exit(0)
    rows = aggregate(runs)
    print("=== CPU matrix summary (mean±std across seeds) ===")
    cols = ["data", "prune_type", "ratio", "model", "n_seeds",
            "best_mean", "best_std", "best_min", "best_max", "saved_mean"]
    df = rows.sort_values(["data", "model", "prune_type", "ratio"])
    print(df[cols].round(3).to_string(index=False))

    out = os.path.join("results", "cpu_matrix_summary.csv")
    os.makedirs("results", exist_ok=True)
    df.to_csv(out, index=False)

    # Paired C02 comparison: BLS_InfoBatch vs InfoBatch, BLS_SeTa vs SeTa
    print("\n=== C02 paired BLS vs original (same seeds, best acc, pp) ===")
    pairs = [("InfoBatch", "BLS_InfoBatch"), ("SeTa", "BLS_SeTa")]
    ptests = []
    for (data, ratio) in [("cifar10", 0.3), ("cifar100", 0.3), ("cifar10", 0.5)]:
        for model in ["resnet18", "resnet50"]:
            for a, b in pairs:
                pt = paired_test(rows, data, ratio, model, a, b)
                if pt:
                    ptests.append(pt)
    pdf = pd.DataFrame(ptests)
    if len(pdf):
        print(pdf.round(4).to_string(index=False))
        pdf.to_csv(os.path.join("results", "c02_paired_tests.csv"), index=False)

    # Compare vs full baseline (CPU runs) and vs frozen 200-epoch & paper
    print("\n=== BLS vs full baseline (CPU runs, same seed budget) ===")
    for (data, ratio) in [("cifar10", 0.3), ("cifar100", 0.3)]:
        full = rows[(rows.data == data) & (rows.prune_type == "full") & (rows.ratio == 0.3) & (rows.model == "resnet18")]
        if full.empty:
            continue
        fb = full.iloc[0]["best_mean"]
        for pt in ["BLS_InfoBatch", "BLS_SeTa"]:
            rr = rows[(rows.data == data) & (rows.prune_type == pt) & (rows.ratio == ratio) & (rows.model == "resnet18")]
            if rr.empty:
                continue
            print(f"{data} {pt}@{ratio} best={rr.iloc[0]['best_mean']:.2f}  full={fb:.2f}  delta={rr.iloc[0]['best_mean']-fb:+.2f}")

    # Compare frozen 200-epoch BLS vs paper Table2 (cited)
    frozen = json.load(open(r"F:/dataset/2604.04681v1/results/table2/combined.json"))
    print("\n=== Frozen 200-epoch BLS vs paper Table 2 (paper cited) ===")
    pt_map = {"bls_inf": "BLS_InfoBatch", "bls_seta": "BLS_SeTa"}
    for name, v in frozen["experiments"].items():
        # name format: <data>_bls_<which>_<ratio>, e.g. cifar10_bls_inf_30
        data, which = name.rsplit("_", 1)[0].split("_", 1)  # ('cifar10', 'bls_inf')
        ratio_s = int(name.rsplit("_", 1)[1])
        pt = pt_map[which]
        pv = PAPER_TABLE2.get((data, pt, ratio_s / 100.0))
        delta = v["best"] - pv if pv else float("nan")
        print(f"{name:26s} best={v['best']:.2f}  paper={pv if pv else 'n/a':<6}  delta={delta:+.2f}  saved={v['saved_ratio']:.3f}")

if __name__ == "__main__":
    main()
