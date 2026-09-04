"""Shared data-prep / fold / group / metric code for PA-RiskRanker reproduction.

Protocol (documents the exact口径 used; mirrors arXiv:2509.16616 Appendix D):
----------------------------------------------------------------------------
Datasets (frozen raw CSVs, SHA-256 pinned in data/source_manifest.json):
  creditcard: data/creditcard/creditcard.csv   (284,807 rows x 31 cols)
  jobprofit : data/jobprofit/job_profitability.csv  (14,479 rows x 31 cols)

Labels
  creditcard: y = 1 iff Amount falls in the top 1% (sorted descending).
              `Amount` is then EXCLUDED from the prediction features (it
              directly encodes the label -> leakage), but it remains the
              financial-impact probe for the loss penalty.
  jobprofit : drop future-information columns (Job_Number, Jobs_Subtotal,
              Labor, Jobs_Total, Lead_Generated_From_Source, Pricebook_Price,
              Jobs_Gross_Margin); y = 1 iff Jobs_Gross_Margin (dollar profit)
              falls in the top 1%.  Jobs_Gross_Margin is the financial
              impact probe and equally excluded from features.

Splits
  3 independent 70/10/20 (train/val/test) stratified splits ("3-fold CV"
  following the paper's 3-run averaging), preserving ~1% / 99% class ratio
  in every split.  Frozen seeds: StratifiedShuffleSplit(random_state=2026)
  for the 70/20 split; per-fold seed for carving the 10% val out of train.

Ranking groups (paper Sec.3.2 adapted to tabular data)
  Each group = 1 high-risk anchor + group_size-1 normal samples sampled
  without replacement from the train split (group_size=100).  A group is
  the LETOR query: a ranking model must rank the anchor above its group
  peers.  Groups are only used at training time (lambdaMART / PA-RiskRanker /
  Rankformer); evaluation of a test fold ranks the full test set.

Evaluation (metrics all computed per fold then macro-averaged)
  with-prior : assume the risk prior = 1% of the eval population; declare
               the top round(0.01*n) score-ranked samples as risky.  This is
               the paper's `with prior` setting and the primary setting.
  F1 = 2*Precision*Sensitivity/(Precision+Sensitivity)
  Financial loss = sum over ALL misclassified samples (both FN and FP) of
               their impact probe: Amount (creditcard) / max(Jobs_Gross_Margin,0)
               (jobprofit; floored at 0 because it is a penalty).
  AUC computed on raw scores (threshold-free, identical in both settings).
"""
from __future__ import annotations
import os, json, hashlib, numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedShuffleSplit

SEED = 2026
FOLD_SEEDS = {1: 1, 2: 7, 3: 42}
GROUP_SIZE = 100            # paper-style ranking group size
PRIOR = 0.01                # "1% of traders are risky" prior

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # agent_solution/
CACHE = os.path.join(ROOT, "data_cache")
os.makedirs(CACHE, exist_ok=True)

JOBPROFIT_DROP = ["Job_Number", "Jobs_Subtotal", "Labor", "Jobs_Total",
                  "Lead_Generated_From_Source", "Pricebook_Price", "Jobs_Gross_Margin"]


# ---------------------------------------------------------------- data loading
def load_creditcard() -> pd.DataFrame:
    df = pd.read_csv(os.path.join(os.path.dirname(ROOT), "data", "creditcard", "creditcard.csv"))
    return df


def load_jobprofit() -> pd.DataFrame:
    df = pd.read_csv(os.path.join(os.path.dirname(ROOT), "data", "jobprofit", "job_profitability.csv"))
    return df


def build_dataset(name: str):
    """Return dict: X(orig), y(label), impact(probe for loss), feat_names, meta."""
    if name == "creditcard":
        df = load_creditcard()
        impact = df["Amount"].to_numpy(dtype=np.float64)
        threshold = df["Amount"].quantile(0.99)
        y = (df["Amount"] >= threshold).astype(np.int64).to_numpy()
        feats = [c for c in df.columns if c not in ("Class", "Amount")]
        X = df[feats].to_numpy(dtype=np.float64)
        meta = {"n_rows": len(df), "n_feats": len(feats), "neg": int((y == 0).sum()),
                "pos": int(y.sum()), "pos_ratio": float(y.mean()), "threshold_amount": float(threshold)}
    elif name == "jobprofit":
        df = load_jobprofit()
        cols = [c for c in df.columns if c not in JOBPROFIT_DROP]
        margin = df["Jobs_Gross_Margin"].to_numpy(dtype=np.float64)
        threshold = np.quantile(margin, 0.99)
        y = (margin >= threshold).astype(np.int64)
        impact = margin.copy()
        X = df[cols].to_numpy(dtype=np.float64)
        meta = {"n_rows": len(df), "n_feats": len(cols), "neg": int((y == 0).sum()),
                "pos": int(y.sum()), "pos_ratio": float(y.mean()),
                "threshold_margin": float(threshold), "dropped_cols": list(JOBPROFIT_DROP)}
    return {"X": X, "y": y, "impact": impact, "feats": feats if name == "creditcard" else cols, "meta": meta}


# ---------------------------------------------------------------- folds + groups
def make_splits(ds, fold: int):
    """Return dict with train/val/test index arrays for a fold (stratified 70/10/20)."""
    n = len(ds["y"])
    sss = StratifiedShuffleSplit(n_splits=3, test_size=0.2, random_state=SEED)  # folds 1..3 frozen
    g = list(sss.split(np.zeros(n), ds["y"]))
    tri_idx, te_idx = g[fold - 1]
    rng = np.random.RandomState(FOLD_SEEDS[fold])
    sssv = StratifiedShuffleSplit(n_splits=1, test_size=0.1, random_state=FOLD_SEEDS[fold])
    va_idx = next(sssv.split(np.zeros(len(tri_idx)), ds["y"][tri_idx]))[1]
    train = tri_idx
    val = tri_idx[va_idx]
    train = np.setdiff1d(tri_idx, val, assume_unique=False)
    return {"train": train, "val": val, "test": te_idx}


def build_groups(train_idx, y, group_size=GROUP_SIZE, seed=0):
    """Ranking groups (paper Sec.3.2): one positive anchor per group + negatives."""
    rng = np.random.RandomState(seed)
    pos = train_idx[y[train_idx] == 1]
    neg = train_idx[y[train_idx] == 0]
    n_anchor = len(pos)
    g = min(group_size - 1, len(neg))
    groups = []
    for a in pos:
        grp_idx = rng.choice(neg, size=g, replace=False)
        groups.append(np.concatenate([[a], grp_idx]))
    return groups


def prepare_fold(name: str, fold: int, rebuild: bool = False):
    """Cache + return dict with X(standardized train), arrays, groups."""
    cache_path = os.path.join(CACHE, f"{name}_fold{fold}.npz")
    grp_path = os.path.join(CACHE, f"{name}_fold{fold}_groups.npy")
    if os.path.exists(cache_path) and os.path.exists(grp_path) and not rebuild:
        z = np.load(cache_path, allow_pickle=True)
        d = {k: z[k] for k in z.files}
        d["groups"] = np.load(grp_path, allow_pickle=False)
        try:
            d["meta"] = json.load(open(cache_path.replace(".npz", "_meta.json")))
        except FileNotFoundError:
            d["meta"] = {}
        return d
    ds = build_dataset(name)
    splits = make_splits(ds, fold)
    mu, sd = ds["X"][splits["train"]].mean(0), ds["X"][splits["train"]].std(0) + 1e-9
    Xs = {k: (ds["X"][idx] - mu) / sd for k, idx in splits.items()}
    out = {
        "X_train": Xs["train"].astype(np.float32), "X_val": Xs["val"].astype(np.float32),
        "X_test": Xs["test"].astype(np.float32),
        "y_train": ds["y"][splits["train"]], "y_val": ds["y"][splits["val"]],
        "y_test": ds["y"][splits["test"]],
        "i_train": ds["impact"][splits["train"]], "i_val": ds["impact"][splits["val"]],
        "i_test": ds["impact"][splits["test"]],
        "feats": np.array(ds["feats"], dtype=object),
        "idx_train": splits["train"],
    }
    groups = build_groups(splits["train"], ds["y"], seed=FOLD_SEEDS[fold])
    out["groups"] = groups
    out["meta"] = ds["meta"]
    np.savez(cache_path, **{k: v for k, v in out.items() if k not in ("groups", "meta")})
    with open(cache_path.replace(".npz", "_meta.json"), "w") as f:
        json.dump(ds["meta"], f, default=str)
    np.save(grp_path, np.asarray(groups, dtype=np.int64), allow_pickle=False)
    return out


# ---------------------------------------------------------------- metrics
def topk_metrics(y_true, y_score, impact, prior=PRIOR):
    """with-prior evaluation. Returns dict of per-fold metrics."""
    n = len(y_true)
    k = int(round(prior * n))
    order = np.argsort(y_score, kind="mergesort")[::-1]
    pred = np.zeros(n, dtype=int)
    pred[order[:k]] = 1
    tp = int(np.sum((pred == 1) & (y_true == 1)))
    pos = int(y_true.sum())
    fn = pos - tp
    fp = k - tp
    tn = n - pos - fp
    precision = tp / k if k else 0.0
    sensitivity = tp / pos if pos else 0.0
    specificity = tn / (n - pos) if (n - pos) else 0.0
    f1 = 2 * precision * sensitivity / (precision + sensitivity) if (precision + sensitivity) else 0.0
    rix = (pred != y_true)
    loss = float(np.sum(np.maximum(impact[rix], 0.0)))   # print惩罚=误分类样本金额/利润 floor 0
    return {"f1": float(f1), "financial_loss": loss, "precision": precision,
            "sensitivity": float(sensitivity), "specificity": float(specificity),
            "tp": tp, "pos": pos, "k": k, "fp": fp, "fn": fn}


def threshold_metrics(y_true, y_score, impact, thr):
    pred = (y_score >= thr).astype(int)
    tp = int(np.sum((pred == 1) & (y_true == 1)))
    pos = int(y_true.sum())
    k = int(pred.sum())
    fn = pos - tp
    fp = k - tp
    tn = len(y_true) - pos - fp
    precision = tp / k if k else 0.0
    sensitivity = tp / pos if pos else 0.0
    specificity = tn / (len(y_true) - pos) if (len(y_true) - pos) else 0.0
    f1 = 2 * precision * sensitivity / (precision + sensitivity) if (precision + sensitivity) else 0.0
    rix = (pred != y_true)
    loss = float(np.sum(np.maximum(impact[rix], 0.0)))
    return {"f1": float(f1), "financial_loss": loss, "precision": precision,
            "sensitivity": sensitivity, "specificity": specificity,
            "tp": tp, "pos": pos, "k": k, "fp": fp, "fn": fn}


def pick_threshold(y_val, y_score_val, impact_val=None):
    """without-prior default threshold chosen on val (max F1); scale-agnostic."""
    candidates = np.unique(np.quantile(y_score_val, np.linspace(0, 1, 501)))
    best, best_f1 = candidates[len(candidates) // 2], -1.0
    for thr in candidates:
        m = threshold_metrics(y_val, y_score_val, np.ones(len(y_val)), thr)
        if m["f1"] > best_f1:
            best_f1, best = m["f1"], thr
    return float(best)


if __name__ == "__main__":
    for name in ("creditcard", "jobprofit"):
        ds = build_dataset(name)
        print(name, "rows=", ds["meta"]["n_rows"], "pos=", ds["meta"]["pos"],
              "pos_ratio=%.5f" % ds["meta"]["pos_ratio"])
        for fold in (1, 2, 3):
            p = prepare_fold(name, fold)
            tr = p["y_train"]
            print(f"  fold{fold} train={len(tr)}(pos={int(tr.sum())}) "
                  f"val={len(p['y_val'])}(pos={int(p['y_val'].sum())}) "
                  f"test={len(p['y_test'])}(pos={int(p['y_test'].sum())}) "
                  f"groups={len(p['groups'])}x{GROUP_SIZE}")