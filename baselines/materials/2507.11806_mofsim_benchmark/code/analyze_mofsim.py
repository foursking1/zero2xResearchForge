#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MOFSimBench (arXiv:2507.11806) — independent re-derivation of DFT bulk-modulus
reference values from the frozen official repository data.

Claims checked (L1 critical claim):
  C1 : 3rd-order Birch-Murnaghan fit of the four prototype MOFs reproduces
       SI Table S.1 "DFT" row (MOF-5=16.06, IRMOF-10=9.4, UiO-66=37.5,
       HKUST-1=23.58 GPa) and the CSV B0_GPa column.
  C2 : The EOS table contains exactly 100 structures and a robust BM fit of all
       100 reproduces the B0_GPa column (>=95/100 within 0.5 GPa).
  C3 : (a) the 4 opt_*_primitive.cif correspond to the 4 prototype structures;
       (b) heat-capacity DFT reference table coverage and cv_300K_JperKperg
       distribution vs the paper's "231" statement.

Fitting protocol
  * 3rd-order Birch-Murnaghan EOS (Eulerian finite strain form):
      E(V) = E0 + (9/16) V0 B0 [ (eta-1)^3 B1 + (eta-1)^2 (6 - 4 eta) ],
      eta = (V0/V)^(2/3),  units: hartree / Angstrom^3.
  * B1 free. Energies centred by subtracting E.min() before fitting so that
    huge absolute energies (~1e5 hartree for very large supercells) do not
    dominate the numerical scale (E0 is re-fit relative to the centre).
  * V0 initialised at the volume of the minimum-energy point.
  * Multi-start over B0 (0.5 .. 200 GPa) x B1 (2,3,4,5,6) with scipy
    least_squares; the minimum-cost solution is selected, subject to a loose
    physical bound |B1| <= 15 (fits whose B1 is far outside the physically
    expected range 3-6 are degenerate solutions of near-flat energy curves).
    If no solution has |B1| <= 15 the global minimum-cost fit is kept.
  * The pure minimum-cost (B1 unconstrained) value is recorded as a
    sensitivity column.

Frozen-data rules: reads ONLY files under data/; verifies checksums first;
never modifies any frozen file.
"""

import hashlib
import json
import math
import os
import sys
from collections import Counter

import numpy as np
import pandas as pd
from scipy.optimize import least_squares

# ----------------------------------------------------------------------------
# Constants & paths
# ----------------------------------------------------------------------------
HARTREE_PER_A3_TO_GPA = 4359.7447222071   # 1 hartree/A^3 = 4359.7447222071 GPa
B1_PHYS_MAX = 15.0                          # physical bound on B1 for selection

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))          # task root
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(os.path.dirname(HERE), "results")

EOS_CSV = os.path.join(DATA, "bulk_modulus_eos_dft_reference.csv")
HEAT_CSV = os.path.join(DATA, "heat_capacity_cv_300k_dft_reference.csv")
SI_CSV = os.path.join(DATA, "SI_Table_S1_bulk_modulus_GPa.csv")
CKSUM = os.path.join(DATA, "checksums.sha256")
CIF_FILES = {
    "MOF-5":    os.path.join(DATA, "opt_MOF-5_primitive.cif"),
    "IRMOF-10": os.path.join(DATA, "opt_IRMOF-10_primitive.cif"),
    "UiO-66":   os.path.join(DATA, "opt_UiO-66_primitive.cif"),
    "HKUST-1":  os.path.join(DATA, "opt_HKUST-1_primitive.cif"),
}

PROTOTYPES = ["MOF-5", "IRMOF-10", "UiO-66", "HKUST-1"]

# Table S.1 "DFT" row (paper value), read from the frozen SI CSV.
PAPER_DFT_B0 = {"MOF-5": 16.06, "IRMOF-10": 9.4, "UiO-66": 37.5, "HKUST-1": 23.58}

# ----------------------------------------------------------------------------
# Checksum verification (frozen-file integrity)
# ----------------------------------------------------------------------------
def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_checksums():
    """Verify every file listed in data/checksums.sha256. Returns list of failures."""
    failures = []
    with open(CKSUM, "r", encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split(None, 1)
            if len(parts) != 2:
                failures.append(("PARSE", line))
                continue
            expect, name = parts
            name = name.strip()
            path = os.path.join(DATA, name)
            if not os.path.exists(path):
                failures.append((name, "missing"))
                continue
            actual = sha256(path)
            if actual != expect:
                failures.append((name, f"sha256 mismatch: {actual}"))
    return failures


# ----------------------------------------------------------------------------
# 3rd-order Birch-Murnaghan EOS
# ----------------------------------------------------------------------------
def bm3_eos(V, E0, V0, B0, B1):
    """3rd-order Birch-Murnaghan EOS (Eulerian finite-strain form).

    E(V) = E0 + (9/16) V0 B0 [ (eta-1)^3 B1 + (eta-1)^2 (6 - 4 eta) ]
    with eta = (V0/V)^(2/3).  Units: E in hartree, V in A^3, B0 in hartree/A^3.
    """
    eta = np.power(V0 / V, 2.0 / 3.0)
    return E0 + (9.0 * V0 * B0 / 16.0) * ((eta - 1.0) ** 3 * B1 + (eta - 1.0) ** 2 * (6.0 - 4.0 * eta))


def fit_bm_eos(V, E, B1_phys_max=B1_PHYS_MAX):
    """Robust 3rd-order BM fit; returns dict with fitted parameters.

    Strategy (see module docstring): energies centred; V0 init at the
    minimum-energy volume; multi-start least_squares; select the
    minimum-cost solution subject to |B1| <= B1_phys_max (fall back to the
    global minimum-cost solution if none satisfies the bound).  Also returns
    the unconstrained minimum-cost solution for sensitivity.
    """
    V = np.asarray(V, dtype=float)
    E = np.asarray(E, dtype=float)
    i0 = int(np.argmin(E))
    V0_guess = float(V[i0])
    E_shift = float(E.min())
    Ec = E - E_shift

    def make_resid(Vc):
        def resid(p):
            E0c, V0, B0g, B1 = p
            B0 = B0g / HARTREE_PER_A3_TO_GPA
            return bm3_eos(Vc, E0c, V0, B0, B1) - Ec
        return resid

    solutions = []          # (cost, params) for all starts
    # Explicit per-parameter scale for the optimiser: the residual itself is in
    # hartree, so E0c is scaled by the energy range, V0 by its own size, B0 by
    # ~50 GPa and B1 is O(1).  For near-flat E(V) curves this scale choice is
    # what lets the low-B0 starts land in the physically-reasonable B1~4 basin
    # instead of a degenerate B1~-50 basin.
    x_scale = [max(1.0, float(Ec.max())), V0_guess, 50.0, 1.0]
    for b0g in (0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 50.0, 100.0, 200.0):
        for b1g in (2.0, 3.0, 4.0, 5.0, 6.0):
            p0 = np.array([0.0, V0_guess, b0g, b1g], dtype=float)
            try:
                res = least_squares(make_resid(V), p0, x_scale=x_scale,
                                    max_nfev=50000)
                x = res.x
                if x[1] <= 0.0 or x[2] <= 0.0 or not np.all(np.isfinite(x)):
                    continue
                solutions.append((res.cost, x))
            except Exception:
                continue

    if not solutions:
        raise RuntimeError(f"BM fit failed for V={V}, E={E}")

    solutions.sort(key=lambda s: s[0])
    gmin = solutions[0]                       # unconstrained minimum-cost fit
    phys = [s for s in solutions if abs(s[1][3]) <= B1_phys_max]
    sel = phys[0] if phys else gmin           # constrained selection

    def unpack(item):
        cost, (E0c, V0, B0g, B1) = item
        return {
            "B0_GPa": B0g,
            "V0": V0,
            "E0": E0c + E_shift,
            "B1": B1,
            "cost": cost,
        }

    out = unpack(sel)
    out["gmin_B0_GPa"] = unpack(gmin)["B0_GPa"]
    out["gmin_B1"] = unpack(gmin)["B1"]
    out["V0_in_sample"] = bool(V.min() - 1e-6 <= sel[1][1] <= V.max() + 1e-6)
    return out


# ----------------------------------------------------------------------------
# Parse frozen CSV helpers
# ----------------------------------------------------------------------------
def _parse_list(s):
    """Parse a Python-list-style string like '[1.0, 2.0]'."""
    s = s.strip()
    if s.startswith("[") and s.endswith("]"):
        inner = s[1:-1].replace(",", " ")
        return np.array([float(x) for x in inner.split() if x.strip()])
    return np.array([float(x) for x in s.split(",")])


def load_eos_table():
    df = pd.read_csv(EOS_CSV, index_col=0)
    df["V_list"] = df["volumes_A3"].apply(_parse_list)
    df["E_list"] = df["energies_au"].apply(_parse_list)
    df["strain_list"] = df["strains"].apply(_parse_list)
    df["E_range_Ha"] = df["E_list"].apply(lambda e: float(e.max() - e.min()))
    df["E_abs_Ha"] = df["E_list"].apply(lambda e: float(np.abs(e).max()))
    return df


# ----------------------------------------------------------------------------
# C1 + C2 : EOS fitting of the whole table
# ----------------------------------------------------------------------------
def fit_all(df):
    records = []
    for idx, row in df.iterrows():
        fit = fit_bm_eos(row["V_list"], row["E_list"])
        csv_b0 = float(row["B0_GPa"])
        rec = {
            "row": idx,
            "structure": row["structure"],
            "cif_name": row["cif_name"],
            "csv_B0_GPa": csv_b0,
            "fit_B0_GPa": fit["B0_GPa"],
            "fit_V0_A3": fit["V0"],
            "fit_E0_hartree": fit["E0"],
            "fit_B1": fit["B1"],
            "fit_cost": fit["cost"],
            "gmin_B0_GPa": fit["gmin_B0_GPa"],
            "gmin_B1": fit["gmin_B1"],
            "n_points": len(row["V_list"]),
            "V0_in_sample": fit["V0_in_sample"],
            "abs_dev_GPa": abs(fit["B0_GPa"] - csv_b0),
            "E_range_Ha": row["E_range_Ha"],
            "E_abs_Ha": row["E_abs_Ha"],
        }
        records.append(rec)
    return pd.DataFrame(records)


def classify_deviation(rec, csv_b0):
    """Human-readable reason for large |fit-CSV| deviations."""
    dev = rec["abs_dev_GPa"]
    if dev <= 0.5:
        return "ok"
    reasons = []
    if rec["E_abs_Ha"] > 5.0e4:
        reasons.append("giant supercell (|E|>5e4 Ha): CSV B0 inconsistent with "
                       "stored (V,E) curvature -> unstable fit (paper Methods)")
    if rec["E_range_Ha"] < 1.0e-3:
        reasons.append("near-flat E(V) (range<1e-3 Ha): B1-free fit "
                       "ill-conditioned, multiple local minima")
    if abs(rec["gmin_B1"]) > 15:
        reasons.append(f"global-minimum-cost fit has unphysical B1="
                       f"{rec['gmin_B1']:.1f}")
    if not reasons:
        reasons.append("ill-conditioned EOS fit")
    return "; ".join(reasons)


# ----------------------------------------------------------------------------
# C3a : CIF parsing (cell volume + atom counts + elements)
# ----------------------------------------------------------------------------
def parse_cif(path):
    """Parse a P1 CIF. Returns (volume A^3, n_atoms, element Counter)."""
    a = b = c = alpha = beta = gamma = None
    n_atoms = 0
    elements = Counter()
    in_loop = False
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            low = line.lower()
            if low.startswith("_cell_length_a"):
                a = float(line.split()[-1])
            elif low.startswith("_cell_length_b"):
                b = float(line.split()[-1])
            elif low.startswith("_cell_length_c"):
                c = float(line.split()[-1])
            elif low.startswith("_cell_angle_alpha"):
                alpha = float(line.split()[-1])
            elif low.startswith("_cell_angle_beta"):
                beta = float(line.split()[-1])
            elif low.startswith("_cell_angle_gamma"):
                gamma = float(line.split()[-1])
            elif low.startswith("_atom_site_") and "fract_x" in low:
                in_loop = True
            elif in_loop and line and not line.startswith("_") and line != "loop_":
                parts = line.split()
                if len(parts) >= 8:
                    n_atoms += 1
                    elements[parts[7]] += 1
    if a is None:
        raise ValueError(f"no cell in {path}")
    ca, cb, cg = (math.cos(math.radians(x)) for x in (alpha, beta, gamma))
    vol = a * b * c * math.sqrt(1 - ca*ca - cb*cb - cg*cg + 2*ca*cb*cg)
    return vol, n_atoms, dict(elements)


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------
def main():
    os.makedirs(OUT, exist_ok=True)
    print("=" * 78)
    print("MOFSimBench (arXiv:2507.11806) DFT reference re-derivation")
    print("=" * 78)

    # ---- 0. checksum verification ----------------------------------------
    print("\n[0] Verifying frozen-data checksums ...")
    failures = verify_checksums()
    if failures:
        print("CHECKSUM FAILURES (aborting):", failures)
        sys.exit(1)
    print("All files listed in data/checksums.sha256 verified OK.")

    # ---- load tables ------------------------------------------------------
    eos = load_eos_table()
    si = pd.read_csv(SI_CSV)
    print(f"[data] bulk_modulus_eos_dft_reference.csv rows = {len(eos)}")
    print(f"[data] SI_Table_S1 rows = {len(si)}, columns = {list(si.columns)}")

    # =======================================================================
    # C1 : prototype MOFs
    # =======================================================================
    print("\n" + "=" * 78)
    print("C1 — 3rd-order BM fit of the 4 prototype MOFs")
    print("=" * 78)
    c1_rows = []
    proto_fit = {}
    for name in PROTOTYPES:
        row = eos[eos["structure"] == name].iloc[0]
        fit = fit_bm_eos(row["V_list"], row["E_list"])
        proto_fit[name] = fit
        paper = PAPER_DFT_B0[name]
        dev_paper = fit["B0_GPa"] - paper
        dev_csv = fit["B0_GPa"] - float(row["B0_GPa"])
        ok_paper = abs(dev_paper) <= 0.5
        ok_csv = abs(dev_csv) <= 0.05
        c1_rows.append({
            "structure": name,
            "paper_B0_GPa": paper,
            "csv_B0_GPa": float(row["B0_GPa"]),
            "fit_B0_GPa": fit["B0_GPa"],
            "fit_V0_A3": fit["V0"],
            "fit_E0_hartree": fit["E0"],
            "fit_B1": fit["B1"],
            "dev_vs_paper_GPa": dev_paper,
            "dev_vs_csv_GPa": dev_csv,
            "within_0.5_GPa_of_paper": bool(ok_paper),
            "within_0.05_GPa_of_csv": bool(ok_csv),
            "n_points": len(row["V_list"]),
        })
        print(f"  {name:9s} paper={paper:8.2f}  csv={float(row['B0_GPa']):.4f}  "
              f"fit={fit['B0_GPa']:.4f}  dev_paper={dev_paper:+.4f}  "
              f"dev_csv={dev_csv:+.4f}  V0={fit['V0']:.2f}  B1={fit['B1']:.3f}")
    c1_df = pd.DataFrame(c1_rows)
    c1_df.to_csv(os.path.join(OUT, "evidence_table_prototypes.csv"), index=False,
                 float_format="%.6f")

    # =======================================================================
    # C2 : all 100 structures
    # =======================================================================
    print("\n" + "=" * 78)
    print("C2 — BM fit of all rows in the EOS table")
    print("=" * 78)
    fit_df = fit_all(eos)
    fit_df["reason"] = fit_df.apply(lambda r: classify_deviation(r, r["csv_B0_GPa"]),
                                    axis=1)
    fit_df.to_csv(os.path.join(OUT, "all100_fit_results.csv"), index=False,
                  float_format="%.6f")

    n_rows = len(eos)
    n_unique = eos["structure"].nunique()
    n_uniq_cif = eos["cif_name"].nunique()
    print(f"  rows = {n_rows}   unique structure names = {n_unique}   "
          f"unique cif_name = {n_uniq_cif}")

    devs = fit_df["abs_dev_GPa"]
    n_le_0_5 = int((devs <= 0.5).sum())
    n_le_0_1 = int((devs <= 0.1).sum())
    print(f"  |fit-CSV| B0 deviation: median={devs.median():.4f} GPa, "
          f"mean={devs.mean():.4f}, max={devs.max():.4f} GPa")
    print(f"  structures with |dev| <= 0.5 GPa : {n_le_0_5}/100 ({n_le_0_5/100:.1%})")
    print(f"  structures with |dev| <= 0.1 GPa : {n_le_0_1}/100 ({n_le_0_1/100:.1%})")

    # sensitivity: pure minimum-cost (B1 unconstrained) selection
    devs_gmin = np.abs(fit_df["gmin_B0_GPa"] - fit_df["csv_B0_GPa"])
    n_le_0_5_gmin = int((devs_gmin <= 0.5).sum())
    n_le_0_1_gmin = int((devs_gmin <= 0.1).sum())
    print(f"  [sensitivity, B1 unconstrained] |dev|<=0.5 : {n_le_0_5_gmin}/100, "
          f"<=0.1 : {n_le_0_1_gmin}/100")

    big = fit_df[fit_df["abs_dev_GPa"] > 0.5].sort_values("abs_dev_GPa",
                                                          ascending=False)
    print(f"  structures with |dev| > 0.5 GPa ({len(big)}):")
    for _, r in big.iterrows():
        flag = "" if r["V0_in_sample"] else "  [V0 OUTSIDE sampled V range]"
        print(f"    {r['structure']:42s} csv={r['csv_B0_GPa']:9.4f} "
              f"fit={r['fit_B0_GPa']:9.4f} dev={r['abs_dev_GPa']:8.4f}"
              f"  B1={r['fit_B1']:7.2f}{flag}")
        print(f"        reason: {r['reason']}")
    big.to_csv(os.path.join(OUT, "large_deviation_structures.csv"), index=False,
               float_format="%.6f")

    summary = {
        "n_rows": n_rows,
        "n_unique_structure": n_unique,
        "n_unique_cif_name": n_uniq_cif,
        "dev_GPa_median": float(devs.median()),
        "dev_GPa_mean": float(devs.mean()),
        "dev_GPa_max": float(devs.max()),
        "n_within_0.5_GPa": n_le_0_5,
        "frac_within_0.5_GPa": n_le_0_5 / n_rows,
        "n_within_0.1_GPa": n_le_0_1,
        "frac_within_0.1_GPa": n_le_0_1 / n_rows,
        "n_within_0.5_GPa_gmin_unconstrained": n_le_0_5_gmin,
        "n_within_0.1_GPa_gmin_unconstrained": n_le_0_1_gmin,
        "n_dev_gt_0.5_GPa": len(big),
        "large_dev_structures": big["structure"].tolist(),
        "n_fit_V0_outside_sample": int((~fit_df["V0_in_sample"]).sum()),
    }

    # =======================================================================
    # C3a : CIF correspondence
    # =======================================================================
    print("\n" + "=" * 78)
    print("C3a — prototype CIFs vs EOS-table structure names")
    print("=" * 78)
    cif_rows = []
    for name in PROTOTYPES:
        path = CIF_FILES[name]
        vol, n_atoms, elements = parse_cif(path)
        row = eos[eos["structure"] == name].iloc[0]
        v_strain1 = float(row["V_list"][row["strain_list"] == 1.0][0])
        v0_fit = proto_fit[name]["V0"]
        rel_diff = (vol - v_strain1) / v_strain1 * 100.0
        cif_rows.append({
            "structure": name,
            "cif_file": os.path.basename(path),
            "csv_cif_name": row["cif_name"],
            "cif_cell_volume_A3": vol,
            "csv_V_at_strain1_A3": v_strain1,
            "rel_diff_pct": rel_diff,
            "fit_V0_A3": v0_fit,
            "cif_n_atoms": n_atoms,
            "cif_elements": elements,
            "name_matches": name == os.path.basename(path).replace(
                "opt_", "").replace("_primitive", "").replace(".cif", ""),
        })
        print(f"  {name:9s} cif={os.path.basename(path):30s} "
              f"csv_cif_name={row['cif_name']:38s}")
        print(f"           V_cif={vol:10.3f}  V(strain=1)={v_strain1:10.3f}  "
              f"rel_diff={rel_diff:+.4f}%  n_atoms={n_atoms}  "
              f"elements={dict(elements)}")
    cif_df = pd.DataFrame(cif_rows)
    cif_df.to_csv(os.path.join(OUT, "cif_correspondence.csv"), index=False,
                  float_format="%.6f")

    # =======================================================================
    # C3b : heat-capacity table
    # =======================================================================
    print("\n" + "=" * 78)
    print("C3b — heat-capacity DFT reference table")
    print("=" * 78)
    cv = pd.read_csv(HEAT_CSV)
    n_cv = len(cv)
    n_cv_unique = cv["cif_name"].nunique()
    cv_col = cv["cv_300K_JperKperg"]
    cv_stats = {
        "n_rows": n_cv,
        "n_unique_cif_name": n_cv_unique,
        "cv_300K_JperKperg_median": float(cv_col.median()),
        "cv_300K_JperKperg_min": float(cv_col.min()),
        "cv_300K_JperKperg_max": float(cv_col.max()),
        "cv_300K_JperKperg_mean": float(cv_col.mean()),
        "cv_300K_JperKperg_q25": float(cv_col.quantile(0.25)),
        "cv_300K_JperKperg_q75": float(cv_col.quantile(0.75)),
        "paper_claimed_231": 231,
        "row_diff_vs_paper": n_cv - 231,
    }
    print(f"  heat-capacity table rows = {n_cv}   unique frameworks = {n_cv_unique}")
    print(f"  cv_300K_JperKperg : median={cv_col.median():.4f}  "
          f"IQR=[{cv_col.quantile(0.25):.4f}, {cv_col.quantile(0.75):.4f}]  "
          f"min={cv_col.min():.4f}  max={cv_col.max():.4f}")
    print(f"  paper (Figure 7) states DFT references comprise 231 "
          f"MOFs/COFs/zeolites; frozen table has {n_cv} rows "
          f"(difference {n_cv - 231:+d}).")
    with open(os.path.join(OUT, "heat_capacity_stats.json"), "w",
              encoding="utf-8") as f:
        json.dump(cv_stats, f, indent=2, ensure_ascii=False)
    cv.describe().to_csv(os.path.join(OUT, "heat_capacity_summary.csv"))

    # =======================================================================
    # Metrics JSON
    # =======================================================================
    metrics = {
        "task": "2507.11806_mofsim_benchmark",
        "data_source": "https://github.com/AI4ChemS/mofsim-bench (MIT license); "
                       "paper arXiv:2507.11806",
        "data_frozen_sha256_verified": (not failures),
        "eos_form": "3rd-order Birch-Murnaghan, B1 free, V0 init = volume at "
                    "minimum energy, energies centred; multi-start least_squares "
                    "(B0 in 0.5..200 GPa x B1 in 2..6); selection = "
                    f"minimum cost subject to |B1|<={B1_PHYS_MAX:.0f} (fall back "
                    "to global min-cost); pure min-cost recorded as sensitivity",
        "unit_conversion": "1 hartree/A^3 = 4359.7447222071 GPa",
        "C1_prototype_fit": c1_rows,
        "C2_all100": summary,
        "C3a_cif_correspondence": cif_rows,
        "C3b_heat_capacity": cv_stats,
        "not_recomputed": [
            "Figure 6 uMLIP MAE values (e.g. MACE-MP-MOF0=3.14 GPa) and "
            "Table S.1 UFF row (14.5/7.6/28.7/42.4 GPa) require uMLIP/UFF "
            "simulation outputs that are not part of the frozen data.",
        ],
    }
    with open(os.path.join(OUT, "metrics.json"), "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)

    print("\n[outputs]")
    for fn in ["evidence_table_prototypes.csv", "all100_fit_results.csv",
               "large_deviation_structures.csv", "cif_correspondence.csv",
               "heat_capacity_stats.json", "heat_capacity_summary.csv",
               "metrics.json"]:
        print("   ", os.path.join(OUT, fn))
    print("\nDone.")


if __name__ == "__main__":
    main()
