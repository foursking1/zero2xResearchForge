"""
Supplementary hull-reconstruction check for Task 3.

Faithful to the paper's protocol: train a compositional (ElFrac) model on
formation energies (Ef), then for each chemical system build the convex hull
of formation energies and compute the predicted decomposition energy
(Delta_Hd,pred = Ef_pred - hull_energy). Classify a compound as stable if
Delta_Hd,pred <= 0, and compare with the true stability labels.

Hull is built from the TRAINING-set compounds of each system (ground-truth DFT
Ef), so true and predicted Delta_Hd are relative to the SAME hull. Restricted
to binary and ternary systems for clean, fast low-dim hulls; capped to the
largest N systems to bound runtime.

Usage:
    python hull_check.py [data_dir] [out_dir]
"""
import json
import os
import re
import sys
from collections import defaultdict

import numpy as np
import pandas as pd
from scipy.spatial import ConvexHull
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix
import lightgbm as lgb

SEED = 42
DEFAULT_DATA = r"F:/dataset/materials/2001.10591_stability_ml_predictions"
MAX_SYSTEMS = 150

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
    counts = {}
    for m in re.finditer(r"([A-Z][a-z]?)(\d*\.?\d*)", f):
        el, n = m.group(1), m.group(2)
        if not el:
            continue
        counts[el] = counts.get(el, 0) + (float(n) if n else 1.0)
    return counts


def formula_features(formulas):
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


def composition_vector(f):
    c = parse_formula(f)
    total = sum(c.values())
    return {el: n / total for el, n in c.items()}


def lower_hull_binary(pts):
    """pts: (n,2) = [x, E]. Return function evaluating lower hull energy at x."""
    order = np.argsort(pts[:, 0])
    xs = pts[order, 0]
    ys = pts[order, 1]
    # monotone chain lower hull
    hull = []
    for i in range(len(xs)):
        while len(hull) >= 2 and cross(hull[-2], hull[-1], i, xs, ys) <= 0:
            hull.pop()
        hull.append(i)
    hull = np.array(hull)
    hx = xs[hull]
    hy = ys[hull]

    def eval_at(xq):
        if xq <= hx[0]:
            return hy[0]
        if xq >= hx[-1]:
            return hy[-1]
        idx = np.searchsorted(hx, xq) - 1
        idx = max(0, min(len(hx) - 2, idx))
        x0, x1 = hx[idx], hx[idx + 1]
        y0, y1 = hy[idx], hy[idx + 1]
        if x1 == x0:
            return y0
        return y0 + (y1 - y0) * (xq - x0) / (x1 - x0)

    return eval_at


def cross(i, j, k, xs, ys):
    return (xs[j] - xs[i]) * (ys[k] - ys[i]) - (ys[j] - ys[i]) * (xs[k] - xs[i])


def ternary_lower_hull(pts_xy, energies):
    """pts_xy: (n,2) compositions, energies: (n,) formation energies.
    Return function lower_hull_energy(x, y)."""
    pts = np.column_stack([pts_xy, energies])
    # add tiny jitter to avoid degenerate hull
    jitter = np.random.RandomState(SEED).normal(0, 1e-9, pts.shape)
    hull = ConvexHull(pts + jitter)
    eq = hull.equations  # (n_facets, 4): normal (nx,ny,nz), d
    facets = []
    for i, facet in enumerate(hull.simplices):
        n = eq[i][:3]
        if n[2] >= 0:
            continue  # lower facets: outward normal has negative energy component
        verts = pts[facet]  # (3,3)
        A = verts[:, :2]  # (3,2)
        e = verts[:, 2]
        # plane: E = a*x + b*y + c
        M = np.column_stack([A, np.ones(3)])
        try:
            coef = np.linalg.solve(M, e)
        except np.linalg.LinAlgError:
            continue
        # containment: query (x,y) inside triangle projection?
        t = np.array([[1.0, 0.0], [0.0, 1.0]])
        # precompute barycentric triangle
        tri = A
        facets.append((coef, tri))

    def eval_at(x, y):
        best = np.inf
        q = np.array([x, y])
        for coef, tri in facets:
            # barycentric of q in tri
            M = np.column_stack([tri[0] - tri[2], tri[1] - tri[2]])
            rhs = q - tri[2]
            try:
                lam = np.linalg.solve(M, rhs)
            except np.linalg.LinAlgError:
                continue
            lam3 = np.array([lam[0], lam[1], 1 - lam[0] - lam[1]])
            if lam3.min() >= -1e-8:
                e_plane = coef[0] * x + coef[1] * y + coef[2]
                if e_plane < best:
                    best = e_plane
        return best if np.isfinite(best) else np.nan

    return eval_at


def main():
    data_dir = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_DATA
    here = os.path.dirname(os.path.abspath(__file__))
    out_dir = sys.argv[2] if len(sys.argv) > 2 else os.path.join(here, "..", "results")
    os.makedirs(out_dir, exist_ok=True)
    np.random.seed(SEED)

    tr_df = pd.read_csv(os.path.join(data_dir, "CritExam__Ef_train.csv"))
    te_df = pd.read_csv(os.path.join(data_dir, "CritExam__Ef_test.csv"))
    te_ed_df = pd.read_csv(os.path.join(data_dir, "CritExam__Ed_test.csv"))

    X_tr = formula_features(tr_df["formula"])
    X_te = formula_features(te_df["formula"])
    reg = lgb.LGBMRegressor(n_estimators=300, learning_rate=0.05, num_leaves=63,
                            random_state=SEED, n_jobs=2, verbose=-1)
    reg.fit(X_tr, tr_df["target"].to_numpy())
    ef_pred = reg.predict(X_te)
    ef_test_mae = float(np.mean(np.abs(ef_pred - te_df["target"].to_numpy())))

    # collect systems (binary/ternary) present in test
    sys_map = defaultdict(lambda: {"formulas": [], "ef_true": [], "ef_pred": [], "ed_true": []})
    for i, f in enumerate(te_df["formula"]):
        els = frozenset(parse_formula(f).keys())
        if len(els) == 2 or len(els) == 3:
            sys_map[els]["formulas"].append(f)
            sys_map[els]["ef_true"].append(te_df["target"].iloc[i])
            sys_map[els]["ef_pred"].append(ef_pred[i])
            sys_map[els]["ed_true"].append(te_ed_df["target"].iloc[i])

    tr_sys = defaultdict(lambda: {"formulas": [], "ef_true": []})
    for i, f in enumerate(tr_df["formula"]):
        els = frozenset(parse_formula(f).keys())
        if len(els) == 2 or len(els) == 3:
            tr_sys[els]["formulas"].append(f)
            tr_sys[els]["ef_true"].append(tr_df["target"].iloc[i])

    # cap to largest systems (by test count)
    ordered = sorted(sys_map.items(), key=lambda kv: -len(kv[1]["formulas"]))[:MAX_SYSTEMS]

    all_true = []
    all_pred = []
    n_systems = 0
    n_compounds = 0
    per_system = {}
    for els, te_data in ordered:
        tr_data = tr_sys.get(els)
        if tr_data is None or len(tr_data["formulas"]) < len(els) + 2:
            continue
        el_list = sorted(els, key=lambda e: ELEM_IDX[e])
        # composition coords
        tr_cv = [composition_vector(f) for f in tr_data["formulas"]]
        if len(els) == 2:
            tr_x = np.array([[cv[el_list[0]]] for cv in tr_cv])
            e_tr = np.array(tr_data["ef_true"])
            pts = np.column_stack([tr_x[:, 0], e_tr])
            fn = lower_hull_binary(pts)
            for j, f in enumerate(te_data["formulas"]):
                cv = composition_vector(f)
                xq = cv[el_list[0]]
                hull_e = fn(xq)
                if np.isnan(hull_e):
                    continue
                all_pred.append(te_data["ef_pred"][j] - hull_e)
                all_true.append(te_data["ed_true"][j])
        else:  # ternary
            tr_xy = np.array([[cv[el_list[0]], cv[el_list[1]]] for cv in tr_cv])
            e_tr = np.array(tr_data["ef_true"])
            fn = ternary_lower_hull(tr_xy, e_tr)
            for j, f in enumerate(te_data["formulas"]):
                cv = composition_vector(f)
                hull_e = fn(cv[el_list[0]], cv[el_list[1]])
                if np.isnan(hull_e):
                    continue
                all_pred.append(te_data["ef_pred"][j] - hull_e)
                all_true.append(te_data["ed_true"][j])
        n_systems += 1
        per_system["-".join(el_list)] = len(te_data["formulas"])

    if len(all_pred) == 0:
        print("No systems evaluated")
        return

    y_pred = (np.array(all_pred) <= 0).astype(int)
    y_true = (np.array(all_true) <= 0).astype(int)
    acc = accuracy_score(y_true, y_pred)
    f1 = f1_score(y_true, y_pred)
    tn, fp, fn2, tp = confusion_matrix(y_true, y_pred).ravel()
    fpr = fp / (fp + tn) if (fp + tn) > 0 else float("nan")
    mae_dh = float(np.mean(np.abs(np.array(all_pred) - np.array(all_true))))
    n_compounds = len(all_pred)

    out = {
        "method": "ElFrac-LightGBM + train-set hull reconstruction (binary/ternary)",
        "n_systems": n_systems,
        "n_compounds": n_compounds,
        "ef_test_mae": round(ef_test_mae, 4),
        "dh_mae_vs_true": round(mae_dh, 4),
        "stability_acc": round(float(acc), 4),
        "stability_f1": round(float(f1), 4),
        "stability_fpr": round(float(fpr), 4),
        "tn": int(tn), "fp": int(fp), "fn": int(fn2), "tp": int(tp),
        "true_stability_rate": round(float(y_true.mean()), 4),
    }
    print(json.dumps(out, indent=2))
    with open(os.path.join(out_dir, "hull_check_metrics.json"), "w") as fp:
        json.dump(out, fp, indent=2)
    print("Wrote", os.path.join(out_dir, "hull_check_metrics.json"))


if __name__ == "__main__":
    main()
