"""
Task 3: 2001.10591_stability_ml_predictions
Verify the paper's key claim: "formation-energy prediction accuracy != stability
prediction accuracy" for compositional models.

Pipeline:
  1. Data statistics: row counts and target distributions for Ef/Ed train/val/test.
  2. Frozen reference recomputation:
     - Delta_Hd MAE for the 6 provided models (Ed_allMP_*.json stats.Ed.reg.abs.mean),
       plus a test-set recomputation by matching JSON predictions to CritExam__Ed_test.csv.
     - Classification metrics for the 5 provided classifiers (Ed_classifier_*.json
       stats.Ed.cl scores).
  3. Train our own ElFrac (element-fraction) model on Ef (regression), report
     MAE/RMSE/R2 on the held-out test set.
  4. Train our own stability model on the same features (Delta_Hd <= 0 binary),
     report accuracy/F1/FPR on the test set.
  5. Contrast table: low Ef MAE vs poor stability-classification metrics.

All metrics are computed from the frozen data; the paper's numbers are only used
for comparison.

Usage:
    python analyze_stability.py [data_dir] [out_dir]
"""
import json
import os
import re
import sys

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.metrics import accuracy_score, f1_score, mean_absolute_error, r2_score, roc_auc_score
from sklearn.metrics import confusion_matrix, precision_recall_fscore_support, roc_curve
import lightgbm as lgb

# Fixed random seed
SEED = 42

# Frozen data location
DEFAULT_DATA = r"F:/dataset/materials/2001.10591_stability_ml_predictions"

# Paper anchor values for comparison
PAPER_DHD_MAE = {  # eV/atom (full 85,014)
    "ElFrac": 0.101, "Meredig": 0.095, "Magpie": 0.092,
    "AutoMat": 0.084, "ElemNet": 0.075, "Roost": 0.069,
}
PAPER_CLS = {  # acc / f1 / fpr (Table S2 口径)
    "ElFrac": {"acc": 0.723, "f1": 0.631, "fpr": 0.191},
    "Meredig": {"acc": 0.746, "f1": 0.666, "fpr": 0.180},
    "Magpie": {"acc": 0.759, "f1": 0.683, "fpr": 0.170},
    "AutoMat": {"acc": 0.792, "f1": 0.732, "fpr": 0.153},
    "ElemNet": {"acc": 0.744, "f1": 0.683, "fpr": 0.219},
}

# Periodic table element order (118)
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
ELEM_IDX = {e: i for i, e in enumerate(ELEMENTS)}


def parse_formula(f):
    """Parse a chemical formula like 'Cd5Fe2O28P8' -> dict element:count."""
    counts = {}
    for m in re.finditer(r"([A-Z][a-z]?)(\d*\.?\d*)", f):
        el, n = m.group(1), m.group(2)
        if not el:
            continue
        counts[el] = counts.get(el, 0) + (float(n) if n else 1.0)
    return counts


def formula_features(formulas):
    """Element-fraction feature matrix (n x 118)."""
    X = np.zeros((len(formulas), len(ELEMENTS)))
    for i, f in enumerate(formulas):
        c = parse_formula(f)
        total = sum(c.values())
        if total <= 0:
            continue
        for el, n in c.items():
            if el in ELEM_IDX:
                X[i, ELEM_IDX[el]] = n / total
    return X


def read_csv(path):
    df = pd.read_csv(path)
    return df["formula"].tolist(), df["target"].to_numpy()


def main():
    data_dir = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_DATA
    here = os.path.dirname(os.path.abspath(__file__))
    out_dir = sys.argv[2] if len(sys.argv) > 2 else os.path.join(here, "..", "results")
    out_dir = os.path.abspath(out_dir)
    os.makedirs(out_dir, exist_ok=True)

    np.random.seed(SEED)

    results = {}

    # ---------------- 1. Data statistics ----------------
    print("=== 1. Data statistics ===")
    stat = {}
    for prop in ["Ef", "Ed"]:
        for split in ["train", "val", "test"]:
            f, y = read_csv(os.path.join(data_dir, f"CritExam__{prop}_{split}.csv"))
            stat[f"{prop}_{split}"] = {
                "n": len(f),
                "target_mean": float(y.mean()),
                "target_std": float(y.std()),
                "target_min": float(y.min()),
                "target_max": float(y.max()),
            }
            print(f"{prop}_{split}: n={len(f)} mean={y.mean():.4f} std={y.std():.4f}")
    results["data_statistics"] = stat

    # ---------------- 2. Frozen reference recomputation ----------------
    print("\n=== 2. Frozen reference models ===")
    dhd_mae = {}
    dhd_mae_test = {}
    cls_metrics = {}
    models6 = ["ElFrac", "Meredig", "Magpie", "AutoMat", "ElemNet", "Roost"]
    test_formulas, test_ed = read_csv(os.path.join(data_dir, "CritExam__Ed_test.csv"))

    for m in models6:
        with open(os.path.join(data_dir, f"Ed_allMP_{m}_ml_results.json")) as fp:
            d = json.load(fp)
        mae_full = d["stats"]["Ed"]["reg"]["abs"]["mean"]
        dhd_mae[m] = mae_full
        # test-set recomputation (for B2 check)
        pred_map = dict(zip(d["data"]["formulas"], d["data"]["Ed"]))
        preds = np.array([pred_map.get(f, np.nan) for f in test_formulas])
        mask = ~np.isnan(preds)
        mae_te = float(mean_absolute_error(test_ed[mask], preds[mask]))
        dhd_mae_test[m] = mae_te
        rmse_full = d["stats"]["Ed"]["reg"]["rmse"]
        r2_full = d["stats"]["Ed"]["reg"]["r2"]
        print(f"{m:<10s} full-set dHd MAE={mae_full:.4f} test-set MAE={mae_te:.4f} "
              f"RMSE={rmse_full:.4f} R2={r2_full:.4f} (n_test={int(mask.sum())})")
        # classifier metrics from Ed_allMP files (also present)
        cl = d["stats"]["Ed"].get("cl", {}).get("0", {})
        if cl and "scores" in cl:
            cls_metrics[m + "_allMP"] = cl["scores"]
    results["dhd_mae_full"] = dhd_mae
    results["dhd_mae_test"] = dhd_mae_test

    # classifier files (Table S2 口径)
    cls5 = ["ElFrac", "Meredig", "Magpie", "AutoMat", "ElemNet"]
    for m in cls5:
        with open(os.path.join(data_dir, f"Ed_classifier_{m}_ml_results.json")) as fp:
            d = json.load(fp)
        s = d["stats"]["Ed"]["cl"]["0"]["scores"]
        cls_metrics[m] = s
        print(f"classifier {m:<10s} acc={s['accuracy']:.3f} f1={s['f1']:.3f} "
              f"precision={s['precision']:.3f} recall={s['recall']:.3f} fpr={s['fpr']:.3f}")
    results["classifier_metrics"] = cls_metrics

    # ---------------- 3. Own ElFrac Ef regression ----------------
    print("\n=== 3. Own ElFrac Ef regression ===")
    tr_f, tr_ef = read_csv(os.path.join(data_dir, "CritExam__Ef_train.csv"))
    va_f, va_ef = read_csv(os.path.join(data_dir, "CritExam__Ef_val.csv"))
    te_f, te_ef = read_csv(os.path.join(data_dir, "CritExam__Ef_test.csv"))
    X_tr = formula_features(tr_f)
    X_va = formula_features(va_f)
    X_te = formula_features(te_f)

    # Ridge baseline
    ridge = Ridge(alpha=1.0)
    ridge.fit(X_tr, tr_ef)
    pred_va = ridge.predict(X_va)
    pred_te = ridge.predict(X_te)
    ridge_metrics = {
        "MAE": float(mean_absolute_error(te_ef, pred_te)),
        "RMSE": float(np.sqrt(np.mean((te_ef - pred_te) ** 2))),
        "R2": float(r2_score(te_ef, pred_te)),
        "val_MAE": float(mean_absolute_error(va_ef, pred_va)),
    }
    print("Ridge Ef test MAE=%.4f RMSE=%.4f R2=%.4f" %
          (ridge_metrics["MAE"], ridge_metrics["RMSE"], ridge_metrics["R2"]))

    # LightGBM regressor (nonlinear)
    lgb_reg = lgb.LGBMRegressor(
        n_estimators=500, learning_rate=0.05, num_leaves=63,
        random_state=SEED, n_jobs=2, verbose=-1)
    lgb_reg.fit(X_tr, tr_ef, eval_set=[(X_va, va_ef)],
                callbacks=[lgb.early_stopping(50, verbose=False)])
    pred_te_lgb = lgb_reg.predict(X_te)
    lgb_metrics = {
        "MAE": float(mean_absolute_error(te_ef, pred_te_lgb)),
        "RMSE": float(np.sqrt(np.mean((te_ef - pred_te_lgb) ** 2))),
        "R2": float(r2_score(te_ef, pred_te_lgb)),
        "best_iter": int(lgb_reg.best_iteration_),
    }
    print("LightGBM Ef test MAE=%.4f RMSE=%.4f R2=%.4f (iter=%d)" %
          (lgb_metrics["MAE"], lgb_metrics["RMSE"], lgb_metrics["R2"], lgb_reg.best_iteration_))
    results["elfrac_ef_regression"] = {"ridge": ridge_metrics, "lgbm": lgb_metrics}

    # ---------------- 4. Own stability prediction ----------------
    print("\n=== 4. Own stability classification (same features) ===")
    tr_f_ed, tr_ed = read_csv(os.path.join(data_dir, "CritExam__Ed_train.csv"))
    va_f_ed, va_ed = read_csv(os.path.join(data_dir, "CritExam__Ed_val.csv"))
    te_f_ed, te_ed = read_csv(os.path.join(data_dir, "CritExam__Ed_test.csv"))
    X_tr_ed = formula_features(tr_f_ed)
    X_va_ed = formula_features(va_f_ed)
    X_te_ed = formula_features(te_f_ed)
    y_tr = (tr_ed <= 0).astype(int)
    y_va = (va_ed <= 0).astype(int)
    y_te = (te_ed <= 0).astype(int)

    lgb_clf = lgb.LGBMClassifier(
        n_estimators=500, learning_rate=0.05, num_leaves=63,
        random_state=SEED, n_jobs=2, verbose=-1)
    lgb_clf.fit(X_tr_ed, y_tr, eval_set=[(X_va_ed, y_va)],
                callbacks=[lgb.early_stopping(50, verbose=False)])
    pred_cls = lgb_clf.predict(X_te_ed)
    pred_prob = lgb_clf.predict_proba(X_te_ed)[:, 1]

    tn, fp, fn, tp = confusion_matrix(y_te, pred_cls).ravel()
    fpr = fp / (fp + tn) if (fp + tn) > 0 else float("nan")
    acc = accuracy_score(y_te, pred_cls)
    f1 = f1_score(y_te, pred_cls)
    prec, rec, _, _ = precision_recall_fscore_support(y_te, pred_cls, average="binary")
    auc = roc_auc_score(y_te, pred_prob)
    own_cls = {
        "accuracy": float(acc), "f1": float(f1), "fpr": float(fpr),
        "precision": float(prec), "recall": float(rec), "auc": float(auc),
        "tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp),
    }
    print(f"Own stability classifier: acc={acc:.3f} f1={f1:.3f} fpr={fpr:.3f} "
          f"precision={prec:.3f} recall={rec:.3f} AUC={auc:.3f}")
    results["own_stability_classifier"] = own_cls

    # stability rate in test
    stab_rate_test = float((y_te == 1).mean() * 100)
    results["test_stability_rate_pct"] = stab_rate_test
    print(f"Test stability rate (Ed<=0): {stab_rate_test:.1f}%")

    # ---------------- 5. Contrast table ----------------
    print("\n=== 5. Contrast ===")
    contrast = {
        "ef_test_mae_eV_atom": lgb_metrics["MAE"],
        "ef_test_rmse_eV_atom": lgb_metrics["RMSE"],
        "stability_acc": acc,
        "stability_f1": f1,
        "stability_fpr": fpr,
    }
    # Check claim conditions
    claim_check = {
        "ef_mae_low_le_0.2": bool(lgb_metrics["MAE"] <= 0.2),
        "acc_below_80": bool(acc < 0.80),
        "f1_below_0.75": bool(f1 < 0.75),
        "fpr_above_0.15": bool(fpr > 0.15),
        "any_stability_metric_bad": bool((acc < 0.80) or (f1 < 0.75) or (fpr > 0.15)),
    }
    results["contrast"] = contrast
    results["claim_check"] = claim_check
    print(claim_check)
    conclusion = "supported" if claim_check["ef_mae_low_le_0.2"] and claim_check["any_stability_metric_bad"] else (
        "partially_supported" if claim_check["any_stability_metric_bad"] else "inconclusive")
    results["conclusion"] = conclusion

    # ---------------- Save ----------------
    with open(os.path.join(out_dir, "metrics.json"), "w") as f:
        json.dump(results, f, indent=2)
    print("\nWrote", os.path.join(out_dir, "metrics.json"))

    import csv
    rows = []
    for m in models6:
        rows.append({"dataset": "Ed_allMP", "method": m, "split": "allMP",
                     "metric": "dHd_MAE_eV_atom", "value": round(dhd_mae[m], 4)})
        rows.append({"dataset": "Ed_allMP", "method": m, "split": "test",
                     "metric": "dHd_MAE_eV_atom", "value": round(dhd_mae_test[m], 4)})
    for m, s in cls_metrics.items():
        if m.endswith("_allMP"):
            continue
        rows.append({"dataset": "Ed_classifier", "method": m, "split": "allMP",
                     "metric": "accuracy", "value": round(s["accuracy"], 4)})
        rows.append({"dataset": "Ed_classifier", "method": m, "split": "allMP",
                     "metric": "f1", "value": round(s["f1"], 4)})
        rows.append({"dataset": "Ed_classifier", "method": m, "split": "allMP",
                     "metric": "fpr", "value": round(s["fpr"], 4)})
    # own model
    rows.append({"dataset": "CritExam_Ef", "method": "ElFrac-LightGBM", "split": "test",
                 "metric": "MAE_eV_atom", "value": round(lgb_metrics["MAE"], 4)})
    rows.append({"dataset": "CritExam_Ef", "method": "ElFrac-LightGBM", "split": "test",
                 "metric": "RMSE_eV_atom", "value": round(lgb_metrics["RMSE"], 4)})
    rows.append({"dataset": "CritExam_Ed", "method": "ElFrac-LightGBM-clf", "split": "test",
                 "metric": "accuracy", "value": round(acc, 4)})
    rows.append({"dataset": "CritExam_Ed", "method": "ElFrac-LightGBM-clf", "split": "test",
                 "metric": "f1", "value": round(f1, 4)})
    rows.append({"dataset": "CritExam_Ed", "method": "ElFrac-LightGBM-clf", "split": "test",
                 "metric": "fpr", "value": round(fpr, 4)})
    with open(os.path.join(out_dir, "evidence_table.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["dataset", "method", "split", "metric", "value"])
        w.writeheader()
        w.writerows(rows)
    print("Wrote", os.path.join(out_dir, "evidence_table.csv"))


if __name__ == "__main__":
    main()
