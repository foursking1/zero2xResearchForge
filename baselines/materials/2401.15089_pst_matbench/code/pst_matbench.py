"""
Task 5: 2401.15089_pst_matbench - PDD-encoding material property regression.

Simplified reproduction of the PST paper's core claim: PDD isometry invariants
(k-nearest-neighbour distance distribution) + composition -> accurate MatBench
property prediction. Uses PDD(k=15) distance histograms + element-fraction
composition features, trained with LightGBM on the frozen 5-fold MatBench splits.

Runs 3 properties (band gap mp_gap, formation energy mp_e_form, shear modulus
log_gvrh), 5-fold CV, reports test MAE (mean+std), plus a band-gap ablation
(composition-only / PDD-only / both).

Features for each (dataset, fold, split) are computed ONCE and reused by the
ablation. Large training sets are subsampled (fixed seed) to max_train per fold.

Usage:
    python pst_matbench.py [data_root] [out_dir] [max_train] [workers]
"""
import os
import sys
import csv
import json
import time
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd
from pymatgen.core import Structure, Lattice
import amd
import lightgbm as lgb

SEED = 42
PROPERTIES = ["mp_gap", "mp_e_form", "log_gvrh"]
PAPER_TARGETS = {"mp_gap": 0.210, "mp_e_form": 0.032, "log_gvrh": 0.074}
DEFAULT_ROOT = r"F:/dataset/materials/2401.15089_pst_matbench"
HERE = os.path.dirname(os.path.abspath(__file__))

ELEMENTS = [
    "H", "He", "Li", "Be", "B", "C", "N", "O", "F", "Ne", "Na", "Mg", "Al", "Si", "P",
    "S", "Cl", "Ar", "K", "Ca", "Sc", "Ti", "V", "Cr", "Mn", "Fe", "Co", "Ni", "Cu",
    "Zn", "Ga", "Ge", "As", "Se", "Br", "Kr", "Rb", "Sr", "Y", "Zr", "Nb", "Mo", "Tc",
    "Ru", "Rh", "Pd", "Ag", "Cd", "In", "Sn", "Sb", "Te", "I", "Xe", "Cs", "Ba", "La",
    "Ce", "Pr", "Nd", "Pm", "Sm", "Eu", "Gd", "Tb", "Dy", "Ho", "Er", "Tm", "Yb", "Lu",
    "Hf", "Ta", "W", "Re", "Os", "Ir", "Pt", "Au", "Hg", "Tl", "Pb", "Bi", "Po", "At",
    "Rn", "Fr", "Ra", "Ac", "Th", "Pa", "U", "Np", "Pu", "Am", "Cm", "Bk", "Cf", "Es",
    "Fm", "Md", "No", "Lr", "Rf", "Db", "Sg", "Bh", "Hs", "Mt", "Ds", "Rg", "Cn", "Nh",
    "Fl", "Mc", "Lv", "Ts", "Og",
]
N_BINS = 55
BIN_MIN, BIN_MAX = 1.5, 7.0
BIN_EDGES = np.linspace(BIN_MIN, BIN_MAX, N_BINS + 1)

_fcache = {}  # (dataset, fold, split, max_rows) -> (hist, comp, y, orig_idx)


def get_cell(cell_field):
    return np.array(cell_field[0].tolist(), dtype=float)


def pdd_histogram(row, k=15):
    pos = np.array(row["positions"].tolist(), dtype=float)
    anums = np.array(row["atomic_numbers"].tolist(), dtype=int)
    cell = get_cell(row["cell"])
    struct = Structure(Lattice(cell), anums, pos, coords_are_cartesian=True)
    pset = amd.periodicset_from_pymatgen_structure(struct)
    pdd = amd.PDD(pset, k=k)  # ndarray (n_motifs, k+1): col0 weights, cols1..k distances
    pdd = np.asarray(pdd, dtype=float)
    dists = pdd[:, 1:]
    weights = pdd[:, 0]
    w = weights / weights.sum()
    finite = np.isfinite(dists)
    flat_d = dists[finite]
    flat_w = np.repeat(w, dists.shape[1])[finite.ravel()]
    hist, _ = np.histogram(flat_d, bins=BIN_EDGES, weights=flat_w)
    return hist


def composition_features(anums):
    anums = np.asarray(anums, dtype=int)
    x = np.zeros(118)
    for z in anums:
        if 1 <= z <= 118:
            x[z - 1] += 1
    s = x.sum()
    return x / s if s > 0 else x


def feature_worker(batch):
    out = []
    for row in batch:
        hist = pdd_histogram(row)
        comp = composition_features(row["atomic_numbers"])
        out.append((hist, comp))
    return out


def load_data(root, dataset, fold, split):
    path = os.path.join(root, f"matbench_{dataset}_fold{fold}_{split}.parquet")
    return pd.read_parquet(path)


def get_features(root, dataset, fold, split, max_rows, workers):
    key = (dataset, fold, split, max_rows)
    if key in _fcache:
        return _fcache[key]
    df = load_data(root, dataset, fold, split)
    if max_rows and len(df) > max_rows:
        df = df.sample(max_rows, random_state=SEED)
    rows = df[["positions", "atomic_numbers", "cell"]].to_dict("records")
    n_workers = min(workers, max(1, len(rows)))
    # Contiguous chunks (NOT round-robin): ProcessPoolExecutor.map returns results in
    # the same order as the input batches, so contiguous slices preserve row order and
    # keep features aligned with y / orig_idx.
    n = len(rows)
    k = n_workers
    chunk = (n + k - 1) // k
    batches = [rows[i * chunk:(i + 1) * chunk] for i in range(k)]
    feats = []
    with ProcessPoolExecutor(max_workers=n_workers) as ex:
        for res in ex.map(feature_worker, batches):
            feats.extend(res)
    # defensive: ensure the number of feature rows matches df length
    assert len(feats) == n, f"feature count {len(feats)} != rows {n}"
    hist = np.array([f[0] for f in feats])
    comp = np.array([f[1] for f in feats])
    y = df["y"].to_numpy()
    idx = df["orig_idx"].to_numpy()
    _fcache[key] = (hist, comp, y, idx)
    return _fcache[key]


def train_eval(X_tr, y_tr, X_va, y_va, X_te, y_te, n_est=800):
    m = lgb.LGBMRegressor(n_estimators=n_est, learning_rate=0.05, num_leaves=63,
                          random_state=SEED, n_jobs=2, verbose=-1)
    m.fit(X_tr, y_tr, eval_set=[(X_va, y_va)],
          callbacks=[lgb.early_stopping(100, verbose=False)])
    pred = m.predict(X_te)
    mae = float(np.mean(np.abs(pred - y_te)))
    return mae, pred


def run_property(root, dataset, max_train, workers, out_rows, pred_records):
    fold_mae = []
    all_pred, all_y, all_idx = [], [], []
    for fold in range(5):
        t0 = time.time()
        tr_h, tr_c, tr_y, _ = get_features(root, dataset, fold, "train", max_train, workers)
        va_h, va_c, va_y, _ = get_features(root, dataset, fold, "val", None, workers)
        te_h, te_c, te_y, te_idx = get_features(root, dataset, fold, "test", None, workers)
        X_tr = np.hstack([tr_h, tr_c]); X_va = np.hstack([va_h, va_c]); X_te = np.hstack([te_h, te_c])
        mae, pred = train_eval(X_tr, tr_y, X_va, va_y, X_te, te_y)
        fold_mae.append(mae)
        all_pred.extend(pred.tolist()); all_y.extend(te_y.tolist()); all_idx.extend(te_idx.tolist())
        out_rows.append({"dataset": dataset, "fold": fold, "model": "PDD+ElFrac-LGBM",
                         "metric": "MAE", "value": round(mae, 4)})
        print(f"  [{dataset}] fold{fold} MAE={mae:.4f}  ({time.time()-t0:.0f}s)", flush=True)
    mean_mae = float(np.mean(fold_mae)); std_mae = float(np.std(fold_mae))
    out_rows.append({"dataset": dataset, "fold": "mean", "model": "PDD+ElFrac-LGBM",
                     "metric": "MAE", "value": round(mean_mae, 4)})
    pred_records[dataset] = {"fold_mae": fold_mae, "mean": mean_mae, "std": std_mae,
                             "test_idx": all_idx, "pred": all_pred, "y": all_y,
                             "paper_mae": PAPER_TARGETS.get(dataset)}
    print(f"  [{dataset}] MEAN MAE={mean_mae:.4f} +- {std_mae:.4f}", flush=True)


def run_ablation(root, max_train, workers, out_rows):
    """Band-gap ablation reusing cached features from the main mp_gap run."""
    dataset = "mp_gap"
    results = {}
    for name, use_hist, use_comp in [("Comp-only", False, True),
                                     ("PDD-only", True, False),
                                     ("PST-ish", True, True)]:
        fold_mae = []
        for fold in range(5):
            tr_h, tr_c, tr_y, _ = get_features(root, dataset, fold, "train", max_train, workers)
            va_h, va_c, va_y, _ = get_features(root, dataset, fold, "val", None, workers)
            te_h, te_c, te_y, _ = get_features(root, dataset, fold, "test", None, workers)
            if use_hist and use_comp:
                X_tr = np.hstack([tr_h, tr_c]); X_va = np.hstack([va_h, va_c]); X_te = np.hstack([te_h, te_c])
            elif use_hist:
                X_tr, X_va, X_te = tr_h, va_h, te_h
            else:
                X_tr, X_va, X_te = tr_c, va_c, te_c
            mae, _ = train_eval(X_tr, tr_y, X_va, va_y, X_te, te_y, n_est=500)
            fold_mae.append(mae)
        results[name] = float(np.mean(fold_mae))
        out_rows.append({"dataset": dataset, "fold": "mean", "model": name,
                         "metric": "MAE", "value": round(results[name], 4)})
        print(f"  [ablation] {name}: MAE={results[name]:.4f}", flush=True)
    return results


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_ROOT
    out_dir = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "results")
    max_train = int(sys.argv[3]) if len(sys.argv) > 3 else 30000
    workers = int(sys.argv[4]) if len(sys.argv) > 4 else 8
    os.makedirs(out_dir, exist_ok=True)

    out_rows = []
    pred_records = {}

    stats = {}
    for dataset in PROPERTIES:
        stats[dataset] = {split: len(load_data(root, dataset, 0, split))
                          for split in ["train", "val", "test"]}
    print("DATA STATS:", json.dumps(stats), flush=True)

    for dataset in PROPERTIES:
        print("Running", dataset, flush=True)
        run_property(root, dataset, max_train, workers, out_rows, pred_records)

    print("Running band-gap ablation", flush=True)
    ablation = run_ablation(root, max_train, workers, out_rows)

    with open(os.path.join(out_dir, "evidence_table.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["dataset", "fold", "model", "metric", "value"])
        w.writeheader()
        w.writerows(out_rows)

    for dataset, rec in pred_records.items():
        with open(os.path.join(out_dir, f"pred_{dataset}.csv"), "w", newline="") as f:
            wr = csv.writer(f)
            wr.writerow(["test_idx", "y", "pred"])
            for ix, y, p in zip(rec["test_idx"], rec["y"], rec["pred"]):
                wr.writerow([ix, y, p])

    # Conclusion label (four-tier) based on ablation direction + magnitude vs paper.
    ab = ablation
    direction_ok = bool(ab["PDD-only"] > ab["Comp-only"] >= ab["PST-ish"])
    mag_ratios = {k: (pred_records[k]["mean"] / PAPER_TARGETS[k]) for k in PROPERTIES}
    if direction_ok and all(1.0 <= mag_ratios[k] < 5.0 for k in PROPERTIES):
        conclusion = "partially_supported"
    elif direction_ok:
        conclusion = "partially_supported"
    else:
        conclusion = "inconclusive"
    metrics = {
        "task": "2401.15089_pst_matbench",
        "method": "PDD(k=15) distance histogram + ElFrac composition + LightGBM",
        "seed": SEED,
        "max_train": max_train,
        "workers": workers,
        "data_root": root,
        "data_stats_fold0": stats,
        "results": {k: {kk: vv for kk, vv in v.items()
                        if kk not in ("test_idx", "pred", "y")}
                    for k, v in pred_records.items()},
        "ablation_bandgap": ablation,
        "paper_targets": PAPER_TARGETS,
        "conclusion": conclusion,
        "evidence_rows": out_rows,
    }
    with open(os.path.join(out_dir, "metrics.json"), "w") as f:
        json.dump(metrics, f, indent=2)

    print("\n=== SUMMARY ===")
    for dataset in PROPERTIES:
        r = pred_records[dataset]
        print(f"{dataset}: MAE={r['mean']:.4f} +- {r['std']:.4f} (paper {PAPER_TARGETS.get(dataset)})")
    print("ablation:", ablation)


if __name__ == "__main__":
    main()
