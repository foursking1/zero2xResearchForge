"""Analyze the frozen full-scale reproduction results (200-epoch runs in F:/dataset workspace).

Computes per-config best/final accuracy, saved ratio, and compares against paper Table 2
values extracted from the paper PDF.
"""
import json, os, glob, numpy as np, pandas as pd

ROOT = r"F:/dataset/2604.04681v1/results"

def summarize(res):
    va = res["result"]["valid_acc"]
    ta = res["result"]["train_acc"]
    return {
        "best_acc": max(va),
        "best_epoch": int(np.argmax(va)),
        "final_acc": va[-1],
        "mean_last10": float(np.mean(va[-10:])),
        "mean_all": float(np.mean(va)),
        "saved_ratio": res["prune"]["saved_ratio"],
        "pruned_num": res["prune"]["pruned_num"],
        "n_epochs": len(va),
        "hyper": res["hyperparameter"],
    }

def main():
    rows = []
    # baseline
    base_path = os.path.join(ROOT, "baseline_cifar10", "res.json")
    if os.path.exists(base_path):
        r = summarize(json.load(open(base_path)))
        r["config"] = "cifar10_full"
        r["prune_type"] = "full"
        r["data"] = "cifar10"
        rows.append(r)
    # table2 runs
    for d in glob.glob(os.path.join(ROOT, "table2", "*", "res.json")):
        r = summarize(json.load(open(d)))
        # config name e.g. cifar10_bls_inf_30
        cfg = os.path.basename(os.path.dirname(d))
        r["config"] = cfg
        hp = r["hyper"]
        r["data"] = hp.get("data", cfg.split("_")[0])
        r["prune_type"] = hp.get("prune_type", "?")
        r["prune_ratio_param"] = hp.get("prune_ratio")
        rows.append(r)

    df = pd.DataFrame(rows)
    df = df.sort_values("config")
    print("=== Frozen full-scale (200-epoch) results ===")
    cols = ["config", "data", "prune_type", "prune_ratio_param", "best_acc", "final_acc",
            "mean_last10", "saved_ratio", "n_epochs"]
    print(df[cols].to_string(index=False))

    out = os.path.join("results", "frozen_table2_summary.csv")
    os.makedirs("results", exist_ok=True)
    df.to_csv(out, index=False)
    print("\nsaved:", out)

    # Compare BLS vs paper Table2 values (from paper PDF)
    paper = {
        "cifar10_full": 95.6,
        "cifar10_infobatch_30": 95.6, "cifar10_infobatch_50": 95.1, "cifar10_infobatch_70": 94.7,
        "cifar10_seta_30": 95.7, "cifar10_seta_50": 95.3, "cifar10_seta_70": 95.0,
        "cifar10_bls_inf_30": 95.6, "cifar10_bls_inf_50": 95.1, "cifar10_bls_inf_70": 94.5,
        "cifar10_bls_seta_30": 95.6, "cifar10_bls_seta_50": 95.3, "cifar10_bls_seta_70": 95.0,
        "cifar100_full": 78.2,
        "cifar100_infobatch_30": 78.2, "cifar100_infobatch_50": 78.1, "cifar100_infobatch_70": 76.5,
        "cifar100_seta_30": 78.4, "cifar100_seta_50": 78.0, "cifar100_seta_70": 76.7,
        "cifar100_bls_inf_30": 78.4, "cifar100_bls_inf_50": 77.7, "cifar100_bls_inf_70": None,
        "cifar100_bls_seta_30": 78.5, "cifar100_bls_seta_50": 78.1, "cifar100_bls_seta_70": 76.7,
    }
    print("\n=== BLS repro vs paper Table 2 (paper cited) ===")
    for _, row in df.iterrows():
        cfg = row["config"]
        # map cfg -> paper key
        if "bls_inf" in cfg:
            key = f'{row["data"]}_bls_inf_{cfg.split("_")[-1]}'
        elif "bls_seta" in cfg:
            key = f'{row["data"]}_bls_seta_{cfg.split("_")[-1]}'
        elif "full" in cfg:
            key = f'{row["data"]}_full'
        else:
            continue
        pv = paper.get(key)
        if pv is None:
            continue
        delta = row["best_acc"] - pv
        print(f'{cfg:24s} best={row["best_acc"]:.2f}  paper={pv:.2f}  delta={delta:+.2f}  saved_ratio={row["saved_ratio"]:.3f}')

if __name__ == "__main__":
    main()
