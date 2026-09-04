"""Q1: ligand / target leakage statistics for the time-based split vs an
equally sized random split (seed=0).

Ligand identity  = canonical RDKit SMILES (proxy for the paper's 'Ligand ID')
Target identity  = exact protein sequence (proxy for the paper's 'UniProt ID',
                   since the frozen CSV does not ship UniProt IDs)

Output: agent_solution/results/leakage_stats.csv
"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common  # noqa: E402

OUT = os.path.join(common.ROOT, "agent_solution", "results")


def pair_leakage(train_set, other, kind):
    """Count rows of `other` (set B) whose identity appears in `train_set`."""
    col = "_lig" if kind == "ligand" else "seq"
    train_pool = set(train_set[col].dropna().tolist())
    total = len(other)
    hit = other[col].map(lambda v: (v is not None) and (v in train_pool))
    n_hit = int(hit.sum())
    n_known = int(other[col].notna().sum())
    ratio = n_hit / total if total else 0.0
    ratio_known = n_hit / n_known if n_known else 0.0
    return n_hit, total, ratio, n_known, ratio_known


def compute_block(df, tag, rows):
    """Compute train/test, train/val, val/test leakage dicts for a dataframe."""
    tr = df[df["split"] == "train"]
    va = df[df["split"] == "val"]
    te = df[df["split"] == "test"]
    stats = {"tag": tag, "n_train": len(tr), "n_val": len(va), "n_test": len(te)}
    pairs = {
        "train->test": (tr, te),
        "train->val": (tr, va),
        "val->test": (va, te),
    }
    for name, (a, b) in pairs.items():
        for kind, label in [("ligand", "lig"), ("target", "seq")]:
            n_hit, tot, ratio, n_known, ratio_known = pair_leakage(a, b, kind)
            stats[f"{name}_{label}_hit"] = n_hit
            stats[f"{name}_{label}_ratio"] = ratio
            stats[f"{name}_{label}_ratio_known"] = ratio_known
            stats[f"{name}_{label}_known"] = n_known
    # combined: ligand-OR-target leak into train for each test complex
    tr_lig = set(tr["_lig"].dropna().tolist())
    tr_seq = set(tr["seq"].dropna().tolist())

    def comb(b):
        hit = b.apply(lambda r: (pd.notna(r["_lig"]) and r["_lig"] in tr_lig)
                                 or (r["seq"] in tr_seq), axis=1)
        return int(hit.sum()), len(b), hit.mean()

    for nm, b in [("test", te), ("val", va)]:
        nh, tot, ratio = comb(b)
        stats[f"train->{nm}_lig_or_seq_hit"] = nh
        stats[f"train->{nm}_lig_or_seq_ratio"] = ratio
    return stats


def main():
    common.verify_checksums()
    df = common.load_lp_data()
    df = common.add_ligand_ids(df)

    # ligand / target leakage under the time-based (official) split
    time_stats = compute_block(df, "time", df)

    # ligand / target leakage under an equally sized random split (seed 0)
    df_rand = common.add_random_split(df, seed=common.SEED)
    rand_stats = compute_block(df_rand, "random", df_rand)

    stats = pd.DataFrame([time_stats, rand_stats])

    # also global identity counts
    ident = {
        "tag": "identity",
        "n_unique_ligand_canonical": int(df["_lig"].nunique()),
        "n_unique_ligand_raw_rows": int(df["smiles"].astype(str).nunique()),
        "n_unique_target_seq": int(df["seq"].nunique()),
        "n_missing_smiles": int(df["smiles"].isna().sum()),
        "n_unparseable_smiles": int(df["_lig"].isna().sum() - df["smiles"].isna().sum()),
    }
    stats = pd.concat([stats, pd.DataFrame([ident])], ignore_index=True)

    os.makedirs(OUT, exist_ok=True)
    stats.to_csv(os.path.join(OUT, "leakage_stats.csv"), index=False)

    pd.set_option("display.width", 220)
    pd.set_option("display.max_columns", 60)
    print(stats.T.to_string())
    print("\nSaved:", os.path.join(OUT, "leakage_stats.csv"))


if __name__ == "__main__":
    main()