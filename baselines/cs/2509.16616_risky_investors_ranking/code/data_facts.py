"""Judge-facing data-facts probe (B-dimension reproducibility).

Recomputes from the frozen CSVs (via common.py): row counts, top-1% label,
70/10/20 stratified splits ratios, and writes evidence/data_facts.json.
"""
from __future__ import annotations
import os, sys, json, hashlib, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import build_dataset, prepare_fold, ROOT, SEED

EVID = os.path.join(ROOT, "evidence")
os.makedirs(EVID, exist_ok=True)


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for buf in iter(lambda: f.read(1 << 20), b""):
            h.update(buf)
    return h.hexdigest()


def main():
    facts = {"seed": SEED, "prior": 0.01, "group_size": 100}
    for name, rel in (("creditcard", "creditcard/creditcard.csv"),
                      ("jobprofit", "jobprofit/job_profitability.csv")):
        ds = build_dataset(name)
        meta = ds["meta"]
        import pandas as pd
        n_csv_cols = int(pd.read_csv(os.path.join(os.path.dirname(ROOT), "data", rel),
                                     nrows=0).shape[1])
        facts[name] = {
            "csv": rel,
            "sha256": sha(os.path.join(os.path.dirname(ROOT), "data", rel)),
            "rows": meta["n_rows"], "cols": n_csv_cols,
            "pos": meta["pos"],
            "neg": meta["neg"], "pos_ratio": round(meta["pos_ratio"], 5),
        }
        facts[name].update({k: v for k, v in meta.items() if k not in ("pos", "neg", "pos_ratio", "n_rows", "n_feats")})
        facts[name]["folds"] = {}
        for fold in (1, 2, 3):
            d = prepare_fold(name, fold)
            facts[name]["folds"][f"fold{fold}"] = {
                "train": int(len(d["y_train"])), "train_pos_ratio": round(float(d["y_train"].mean()), 5),
                "val": int(len(d["y_val"])), "val_pos_ratio": round(float(d["y_val"].mean()), 5),
                "test": int(len(d["y_test"])), "test_pos_ratio": round(float(d["y_test"].mean()), 5),
                "n_groups": int(len(d["groups"])), "group_size": int(d["groups"].shape[1]),
            }
    out = os.path.join(EVID, "data_facts.json")
    json.dump(facts, open(out, "w"), indent=2, default=float)
    print(json.dumps(facts, indent=2, default=float))


if __name__ == "__main__":
    main()