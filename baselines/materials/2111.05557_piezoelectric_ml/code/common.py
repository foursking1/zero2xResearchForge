"""Shared utilities for the 2111.05557 (piezoelectric ML) replication.

Contents:
  * FROZEN_DATA_DIR: location of the frozen data package (overridable by env).
  * Elemental property table (Magpie-style) + composition parser + feature builders.
  * Fixed 5-fold CV splits and evaluation metrics.
"""
import os
import re
import numpy as np
import pandas as pd

FROZEN_DATA_DIR = os.environ.get(
    "PIEZO_DATA_DIR",
    "/mnt/f/dataset/materials/2111.05557_piezoelectric_ml",
)
SOLUTION_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_DIR = os.path.join(SOLUTION_DIR, "results")
EVIDENCE_DIR = os.path.join(SOLUTION_DIR, "evidence")
FIGURES_DIR = os.path.join(EVIDENCE_DIR, "figures")
for d in (RESULTS_DIR, EVIDENCE_DIR, FIGURES_DIR):
    os.makedirs(d, exist_ok=True)

SEED = 42

LABEL_COL = "Piezoelectric_Modulus"
N_EXPECTED_LABEL_ROWS = 1705
N_EXPECTED_MP_ROWS = 138613

# ---------------------------------------------------------------------------
# Elemental property table (Magpie-style reference values).
# Each entry: (Z, period, group, weight, EN_Pauling, IE1_eV, EA_eV,
#              covalent_radius_pm, density_gcm3, melting_K, valence_el, therm_cond)
# Values are standard reference data (WebElements / periodic table handbooks);
# for lanthanides/actinides group is set to 3 (common convention).
# ---------------------------------------------------------------------------
ELEM = {
    "H":  (1, 1, 1, 1.008, 2.20, 13.598, 0.754, 31, 0.00009, 14.0, 1, 0.18),
    "He": (2, 1, 18, 4.003, 0.00, 24.587, 0.000, 31, 0.00018, 4.2, 2, 0.15),
    "Li": (3, 2, 1, 6.941, 0.98, 5.392, 0.618, 128, 0.53, 453.6, 1, 84.7),
    "Be": (4, 2, 2, 9.012, 1.57, 9.323, 0.000, 112, 1.85, 1560.0, 2, 200.0),
    "B":  (5, 2, 13, 10.81, 2.04, 8.298, 0.280, 84, 2.34, 2349.0, 3, 27.0),
    "C":  (6, 2, 14, 12.011, 2.55, 11.260, 1.263, 77, 2.27, 3823.0, 4, 129.0),
    "N":  (7, 2, 15, 14.007, 3.04, 14.534, 0.000, 75, 0.00125, 63.2, 5, 0.026),
    "O":  (8, 2, 16, 15.999, 3.44, 13.618, 1.461, 73, 0.00143, 54.4, 2, 0.027),
    "F":  (9, 2, 17, 18.998, 3.98, 17.423, 3.401, 71, 1.70, 53.5, 1, 0.028),
    "Ne": (10, 2, 18, 20.180, 0.00, 21.565, 0.000, 38, 0.00090, 24.6, 8, 0.049),
    "Na": (11, 3, 1, 22.990, 0.93, 5.139, 0.548, 166, 0.97, 371.0, 1, 141.0),
    "Mg": (12, 3, 2, 24.305, 1.31, 7.646, 0.000, 141, 1.74, 923.0, 2, 156.0),
    "Al": (13, 3, 13, 26.982, 1.61, 5.986, 0.433, 121, 2.70, 933.5, 3, 237.0),
    "Si": (14, 3, 14, 28.086, 1.90, 8.152, 1.385, 111, 2.33, 1687.0, 4, 148.0),
    "P":  (15, 3, 15, 30.974, 2.19, 10.487, 0.746, 110, 1.82, 317.3, 5, 0.24),
    "S":  (16, 3, 16, 32.066, 2.58, 10.360, 2.077, 102, 2.07, 388.4, 6, 0.205),
    "Cl": (17, 3, 17, 35.453, 3.16, 12.968, 3.613, 99, 3.21, 172.0, 1, 0.009),
    "Ar": (18, 3, 18, 39.948, 0.00, 15.760, 0.000, 71, 0.00178, 83.8, 8, 0.018),
    "K":  (19, 4, 1, 39.098, 0.82, 4.341, 0.502, 243, 0.86, 336.5, 1, 102.5),
    "Ca": (20, 4, 2, 40.078, 1.00, 6.113, 0.025, 176, 1.55, 1115.0, 2, 201.0),
    "Sc": (21, 4, 3, 44.956, 1.36, 6.561, 0.188, 144, 2.99, 1814.0, 3, 15.8),
    "Ti": (22, 4, 4, 47.867, 1.54, 6.828, 0.079, 160, 4.51, 1941.0, 4, 21.9),
    "V":  (23, 4, 5, 50.942, 1.63, 6.746, 0.525, 153, 6.11, 2183.0, 5, 30.7),
    "Cr": (24, 4, 6, 51.996, 1.66, 6.767, 0.666, 139, 7.15, 2180.0, 6, 93.9),
    "Mn": (25, 4, 7, 54.938, 1.55, 7.434, 0.000, 139, 7.21, 1519.0, 7, 7.8),
    "Fe": (26, 4, 8, 55.845, 1.83, 7.902, 0.151, 132, 7.87, 1811.0, 3, 80.4),
    "Co": (27, 4, 9, 58.933, 1.88, 7.881, 0.662, 126, 8.90, 1768.0, 3, 100.0),
    "Ni": (28, 4, 10, 58.693, 1.91, 7.640, 1.157, 124, 8.90, 1728.0, 2, 90.7),
    "Cu": (29, 4, 11, 63.546, 1.90, 7.726, 1.236, 132, 8.96, 1357.8, 2, 401.0),
    "Zn": (30, 4, 12, 65.38, 1.65, 9.394, 0.000, 122, 7.14, 692.7, 2, 116.0),
    "Ga": (31, 4, 13, 69.723, 1.81, 5.999, 0.300, 122, 5.91, 302.9, 3, 40.6),
    "Ge": (32, 4, 14, 72.630, 2.01, 7.900, 1.233, 122, 5.32, 1211.4, 4, 59.9),
    "As": (33, 4, 15, 74.922, 2.18, 9.789, 0.810, 119, 5.73, 1090.0, 5, 50.0),
    "Se": (34, 4, 16, 78.971, 2.55, 9.752, 2.021, 116, 4.81, 494.0, 6, 0.52),
    "Br": (35, 4, 17, 79.904, 2.96, 11.814, 3.364, 114, 3.12, 266.0, 7, 1.0),
    "Kr": (36, 4, 18, 83.798, 0.00, 13.999, 0.000, 116, 0.00374, 115.8, 8, 0.009),
    "Rb": (37, 5, 1, 85.468, 0.82, 4.177, 0.486, 265, 1.53, 312.5, 1, 58.2),
    "Sr": (38, 5, 2, 87.62, 0.95, 5.695, 0.000, 219, 2.64, 1050.0, 2, 35.4),
    "Y":  (39, 5, 3, 88.906, 1.22, 6.217, 0.307, 180, 4.47, 1799.0, 3, 17.2),
    "Zr": (40, 5, 4, 91.224, 1.33, 6.634, 0.426, 175, 6.52, 2128.0, 4, 22.7),
    "Nb": (41, 5, 5, 92.906, 1.60, 6.759, 0.893, 164, 8.57, 2750.0, 5, 53.7),
    "Mo": (42, 5, 6, 95.95, 2.16, 7.092, 0.746, 154, 10.28, 2896.0, 6, 138.0),
    "Tc": (43, 5, 7, 98.000, 1.90, 7.280, 0.550, 183, 11.50, 2430.0, 7, 50.6),
    "Ru": (44, 5, 8, 101.07, 2.20, 7.361, 1.046, 146, 12.37, 2607.0, 8, 117.0),
    "Rh": (45, 5, 9, 102.906, 2.28, 7.459, 1.137, 142, 12.41, 2237.0, 5, 150.0),
    "Pd": (46, 5, 10, 106.42, 2.20, 8.337, 0.562, 139, 12.02, 1828.0, 4, 71.8),
    "Ag": (47, 5, 11, 107.868, 1.93, 7.576, 1.302, 145, 10.49, 1234.9, 1, 429.0),
    "Cd": (48, 5, 12, 112.411, 1.69, 8.994, 0.000, 144, 8.65, 594.3, 2, 96.6),
    "In": (49, 5, 13, 114.818, 1.78, 5.786, 0.300, 163, 7.31, 429.8, 3, 81.8),
    "Sn": (50, 5, 14, 118.710, 1.96, 7.344, 1.112, 141, 7.31, 505.1, 4, 66.6),
    "Sb": (51, 5, 15, 121.760, 2.05, 8.608, 1.047, 133, 6.69, 903.8, 5, 24.4),
    "Te": (52, 5, 16, 127.60, 2.10, 9.010, 1.971, 135, 6.24, 722.7, 6, 2.35),
    "I":  (53, 5, 17, 126.904, 2.66, 10.451, 3.059, 139, 4.93, 386.9, 7, 0.45),
    "Xe": (54, 5, 18, 131.293, 0.00, 12.130, 0.000, 140, 0.00590, 161.4, 8, 0.0057),
    "Cs": (55, 6, 1, 132.905, 0.79, 3.894, 0.472, 244, 1.87, 301.6, 1, 35.9),
    "Ba": (56, 6, 2, 137.327, 0.89, 5.212, 0.145, 222, 3.51, 1000.0, 2, 18.4),
    "La": (57, 6, 3, 138.905, 1.10, 5.577, 0.470, 207, 6.15, 1193.0, 3, 13.4),
    "Ce": (58, 6, 3, 140.116, 1.12, 5.539, 0.500, 204, 6.77, 1068.0, 4, 11.3),
    "Pr": (59, 6, 3, 140.908, 1.13, 5.473, 0.350, 203, 6.77, 1208.0, 3, 12.5),
    "Nd": (60, 6, 3, 144.242, 1.14, 5.525, 0.350, 201, 7.01, 1297.0, 3, 16.5),
    "Pm": (61, 6, 3, 145.000, 1.13, 5.582, 0.350, 199, 7.26, 1315.0, 3, 15.0),
    "Sm": (62, 6, 3, 150.36, 1.17, 5.644, 0.350, 198, 7.52, 1345.0, 3, 13.3),
    "Eu": (63, 6, 3, 151.964, 1.20, 5.670, 0.350, 198, 5.24, 1099.0, 3, 13.9),
    "Gd": (64, 6, 3, 157.25, 1.20, 6.150, 0.350, 196, 7.90, 1585.0, 3, 10.6),
    "Tb": (65, 6, 3, 158.925, 1.20, 5.864, 0.350, 194, 8.23, 1629.0, 4, 11.1),
    "Dy": (66, 6, 3, 162.500, 1.22, 5.939, 0.350, 192, 8.55, 1680.0, 3, 10.7),
    "Ho": (67, 6, 3, 164.930, 1.23, 6.022, 0.350, 187, 8.80, 1734.0, 3, 16.2),
    "Er": (68, 6, 3, 167.259, 1.24, 6.108, 0.350, 185, 9.07, 1802.0, 3, 14.5),
    "Tm": (69, 6, 3, 168.934, 1.25, 6.184, 0.350, 186, 9.32, 1818.0, 3, 16.9),
    "Yb": (70, 6, 3, 173.045, 1.10, 6.254, 0.350, 187, 6.90, 1097.0, 3, 38.5),
    "Lu": (71, 6, 3, 174.967, 1.27, 5.426, 0.350, 187, 9.84, 1925.0, 3, 16.4),
    "Hf": (72, 6, 4, 178.49, 1.30, 6.825, 0.350, 175, 13.31, 2506.0, 4, 23.0),
    "Ta": (73, 6, 5, 180.948, 1.50, 7.550, 0.322, 170, 16.69, 3290.0, 5, 57.5),
    "W":  (74, 6, 6, 183.84, 2.36, 7.864, 0.815, 162, 19.25, 3695.0, 6, 173.0),
    "Re": (75, 6, 7, 186.207, 1.90, 7.360, 0.150, 151, 21.02, 3459.0, 7, 48.0),
    "Os": (76, 6, 8, 190.23, 2.20, 8.438, 1.078, 144, 22.59, 3306.0, 8, 87.6),
    "Ir": (77, 6, 9, 192.217, 2.20, 8.967, 1.564, 141, 22.56, 2719.0, 4, 147.0),
    "Pt": (78, 6, 10, 195.084, 2.28, 8.959, 2.125, 139, 21.45, 2041.4, 2, 71.6),
    "Au": (79, 6, 11, 196.967, 2.54, 9.226, 2.309, 136, 19.32, 1337.3, 3, 318.0),
    "Hg": (80, 6, 12, 200.592, 2.00, 10.438, 0.000, 132, 13.53, 234.3, 2, 8.3),
    "Tl": (81, 6, 13, 204.383, 1.62, 6.108, 0.350, 170, 11.85, 577.0, 3, 46.1),
    "Pb": (82, 6, 14, 207.2, 2.33, 7.417, 0.364, 146, 11.34, 600.6, 4, 35.3),
    "Bi": (83, 6, 15, 208.980, 2.02, 7.289, 0.942, 151, 9.79, 544.7, 5, 7.97),
    "Po": (84, 6, 16, 209.000, 2.00, 8.417, 1.900, 135, 9.32, 527.0, 6, 20.0),
    "At": (85, 6, 17, 210.000, 2.20, 9.318, 2.800, 127, 7.00, 575.0, 7, 1.7),
    "Rn": (86, 6, 18, 222.000, 0.00, 10.749, 0.000, 145, 0.00973, 202.0, 8, 0.0036),
    "Fr": (87, 7, 1, 223.000, 0.70, 4.073, 0.000, 260, 1.87, 300.0, 1, 15.0),
    "Ra": (88, 7, 2, 226.000, 0.90, 5.279, 0.000, 221, 5.50, 973.0, 2, 18.6),
    "Ac": (89, 7, 3, 227.000, 1.10, 5.170, 0.000, 215, 10.07, 1323.0, 3, 12.0),
    "Th": (90, 7, 3, 232.038, 1.30, 6.308, 0.350, 206, 11.72, 2115.0, 4, 54.0),
    "Pa": (91, 7, 3, 231.036, 1.50, 5.890, 0.350, 200, 15.37, 1841.0, 5, 6.0),
    "U":  (92, 7, 3, 238.029, 1.38, 6.194, 0.350, 196, 19.05, 1405.0, 6, 27.6),
    "Np": (93, 7, 3, 237.000, 1.36, 6.266, 0.350, 190, 20.45, 917.0, 5, 6.3),
    "Pu": (94, 7, 3, 244.000, 1.28, 6.026, 0.350, 187, 19.86, 913.0, 4, 6.7),
}

# Feature property names (subset of Magpie-like elemental properties used).
PROPERTY_NAMES = [
    "Z", "period", "group", "weight", "EN", "IE1", "EA",
    "covalent_radius", "density", "melting_point", "valence_el", "thermal_cond",
]

SYMMETRY_CLASSES = [
    "cubic", "hexagonal", "monoclinic", "orthorhombic",
    "tetragonal", "triclinic", "trigonal",
]


def load_labels():
    path = os.path.join(FROZEN_DATA_DIR, "Piezoelectric_renewed.csv")
    df = pd.read_csv(path)
    assert len(df) == N_EXPECTED_LABEL_ROWS, f"expected {N_EXPECTED_LABEL_ROWS}, got {len(df)}"
    return df


def load_mp():
    path = os.path.join(FROZEN_DATA_DIR, "MP_allcompounds_synthesis_totalenergy.csv")
    df = pd.read_csv(path, low_memory=False)
    assert len(df) == N_EXPECTED_MP_ROWS, f"expected {N_EXPECTED_MP_ROWS}, got {len(df)}"
    return df


# ---------------------------------------------------------------------------
# Composition parsing
# ---------------------------------------------------------------------------
_TOKEN_RE = re.compile(r"[A-Z][a-z]?|\d+|\(|\)")


def parse_formula(formula):
    """Parse a chemical formula (with parentheses) into {element: count}."""
    formula = str(formula).strip()
    toks = _TOKEN_RE.findall(formula)
    rec = {"pos": 0}

    def number():
        s = ""
        while rec["pos"] < len(toks) and toks[rec["pos"]].isdigit():
            s += toks[rec["pos"]]
            rec["pos"] += 1
        return int(s) if s else 1

    def parse_group():
        counts = {}
        while rec["pos"] < len(toks):
            t = toks[rec["pos"]]
            if t == "(":
                rec["pos"] += 1
                sub = parse_group()
                mult = number()
                for el, c in sub.items():
                    counts[el] = counts.get(el, 0) + c * mult
            elif t == ")":
                rec["pos"] += 1
                return counts
            else:  # element symbol
                if len(t) == 2 and t not in ELEM and t[0] in ELEM:
                    t = t[0]
                if t not in ELEM:
                    return None
                rec["pos"] += 1
                n = number()
                counts[t] = counts.get(t, 0) + n
        return counts

    counts = parse_group()
    if counts is None or rec["pos"] != len(toks):
        return None
    return counts


def fraction_vector(composition):
    """Return (elements, fractions)."""
    total = sum(composition.values())
    els = sorted(composition.keys())
    fr = [composition[e] / total for e in els]
    return els, fr


# ---------------------------------------------------------------------------
# Feature builders
# ---------------------------------------------------------------------------
def elemental_property_stats(els, fractions):
    """Magpie-like weighted statistics of elemental properties over a composition."""
    props = np.array([ELEM[e][: len(PROPERTY_NAMES)] for e in els],
                     dtype=float).reshape(len(els), len(PROPERTY_NAMES))
    fr = np.array(fractions, dtype=float)
    out = {}
    for j, name in enumerate(PROPERTY_NAMES):
        v = props[:, j]
        wmean = np.average(v, weights=fr)
        wstd = np.sqrt(np.average((v - wmean) ** 2, weights=fr))
        mad = np.average(np.abs(v - wmean), weights=fr)
        out[f"{name}_wmean"] = wmean
        out[f"{name}_wstd"] = wstd
        out[f"{name}_min"] = v.min()
        out[f"{name}_max"] = v.max()
        out[f"{name}_range"] = v.max() - v.min()
        out[f"{name}_mad"] = mad
    return out


def composition_basic_features(composition):
    """Composition-only (Magpie-like) feature vector for one material."""
    els, fr = fraction_vector(composition)
    feats = {}
    for e in ELEM:
        feats[f"frac_{e}"] = 0.0
    for e, f in zip(els, fr):
        feats[f"frac_{e}"] = f
    feats.update(elemental_property_stats(els, fr))
    feats["n_elements"] = len(els)
    fr = np.asarray(fr, dtype=float)
    feats["comp_entropy"] = -float(np.sum(fr * np.log(fr)))
    return feats


def build_feature_frame(compositions, symmetries=None, mp_sub=None):
    """Build feature matrix.

    compositions : list of dict {element: count}
    symmetries   : list of crystal symmetry strings (used for 'enhanced' level)
    mp_sub       : DataFrame indexed by mp_id with extra MP-derived properties
    Returns (X_basic, X_enhanced, feature_info).
    """
    basic_rows, enhanced_rows = [], []
    for i, comp in enumerate(compositions):
        b = composition_basic_features(comp)
        e = dict(b)
        if symmetries is not None:
            for s in SYMMETRY_CLASSES:
                e[f"sym_{s}"] = 1.0 if s == symmetries[i] else 0.0
        if mp_sub is not None:
            row = mp_sub.iloc[i]
            mp_feats = {
                "mp_final_energy_per_atom": row["final_energy_per_atom"],
                "mp_formation_energy_per_atom": row["formation_energy_per_atom"],
                "mp_e_above_hull": row["e_above_hull"],
                "mp_band_gap": row["band_gap"],
                "mp_density": row["density"],
                "mp_volume": row["volume"],
                "mp_total_magnetization": row["total_magnetization"],
                "mp_spacegroup_number": row["spacegroup.number"],
                "mp_nelements": row["nelements"],
            }
            for k, v in mp_feats.items():
                e[k] = v if v == v else 0.0  # NaN -> 0
        basic_rows.append(b)
        enhanced_rows.append(e)

    Xb = pd.DataFrame(basic_rows)
    Xe = pd.DataFrame(enhanced_rows)
    return Xb, Xe


# ---------------------------------------------------------------------------
# Evaluation utilities
# ---------------------------------------------------------------------------
def mae_rmse_r2(y_true, y_pred):
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    mae = float(np.mean(np.abs(y_true - y_pred)))
    rmse = float(np.sqrt(np.mean((y_true - y_pred) ** 2)))
    ss_res = float(np.sum((y_true - y_pred) ** 2))
    ss_tot = float(np.sum((y_true - np.mean(y_true)) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")
    rho = float(np.corrcoef(y_true, y_pred)[0, 1]) if len(np.unique(y_pred)) > 1 else float("nan")
    return {"MAE": mae, "RMSE": rmse, "R2": r2, "Spearman": rho}


def fixed_folds(n, n_splits=5, seed=SEED):
    """Deterministic shuffled K-fold indices (same folds for every model)."""
    from sklearn.model_selection import KFold
    kf = KFold(n_splits=n_splits, shuffle=True, random_state=seed)
    return list(kf.split(np.arange(n)))


def run_cv(model_factory, X, y, folds):
    """Generic 5-fold CV. model_factory(tr_idx, va_idx) -> fitted model with .predict.
    Returns per-fold metrics + pooled OOF metrics."""
    oof = np.zeros(len(y))
    per_fold = []
    for fold, (tr, va) in enumerate(folds):
        m = model_factory(tr, va)
        pred = np.asarray(m.predict(X.iloc[va]), dtype=float)
        oof[va] = pred
        per_fold.append({"fold": fold, **mae_rmse_r2(y[va], pred)})
    pooled = mae_rmse_r2(y, oof)
    return per_fold, pooled, oof


def summarize_folds(per_fold):
    """Mean +/- std of per-fold metrics."""
    rows = pd.DataFrame(per_fold).set_index("fold")
    out = {}
    for c in ["MAE", "RMSE", "R2", "Spearman"]:
        out[c] = rows[c].mean()
        out[f"{c}_std"] = rows[c].std()
    return out


def fmt(x, nd=4):
    if isinstance(x, float) or hasattr(x, "item"):
        return f"{x:.{nd}f}"
    return str(x)
