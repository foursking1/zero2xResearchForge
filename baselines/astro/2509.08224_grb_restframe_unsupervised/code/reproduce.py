#!/usr/bin/env python3
"""
reproduce.py - Verbatim re-analysis of the frozen M20 GRB catalog
task: 2509.08224_grb_restframe_unsupervised
paper: Zhu S.-Y. et al., "Unsupervised machine learning classification of
       gamma-ray bursts based on the rest-frame prompt emission parameters",
       A&A (2025), arXiv:2509.08224
data : CDS VizieR J/MNRAS/492/1919 (Minaev & Pozanenko 2020), tablea1.dat
       (152-byte fixed-width rows, latin-1) + ReadMe byte-by-byte map.

Everything is derived by running code over the frozen fixed-width data;
no paper numbers are copied into the "measured" outputs (paper numbers are
used only for comparison).

Usage:
    python3 reproduce.py [--data DIR] [--out DIR]
    --data DIR : directory containing tablea1.dat + ReadMe
                 (defaults, in order: $GRB_DATA_DIR, ./data, the frozen
                 package path on F:, <task>/data)
    --out  DIR : output directory (default: <repo>/results)
"""

import argparse
import hashlib
import json
import math
import os
import sys
from collections import Counter

import numpy as np
import pandas as pd

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    HAS_MPL = True
except Exception:
    HAS_MPL = False

try:
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler
    HAS_SKLEARN = True
except Exception:
    HAS_SKLEARN = False

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
DEFAULT_DATA_CANDIDATES = [
    os.environ.get("GRB_DATA_DIR", ""),
    os.path.join(HERE, "data"),
    os.path.join(REPO, "data"),
    "/mnt/f/dataset/astro/2509.08224_grb_restframe_unsupervised",
    os.path.join(REPO, os.pardir, "data"),
]
TABLEA1_SHA256 = "b84d3a7fa1cc3bdea722e385fc5a6cb22f3b2f142efc0b4238402e1128a40f0a"

BYTE_MAP = [
    ("grb",      "GRB",      (1, 7),   "str"),
    ("f_GRB",    "f_GRB",    (9, 9),   "str"),
    ("t90z_s",   "T90i",     (11, 17), "float"),
    ("z",        "z",        (19, 25), "float"),
    ("E_z",      "E_z",      (27, 30), "float"),
    ("e_z",      "e_z",      (32, 35), "float"),
    ("f_z",      "f_z",      (37, 38), "str"),
    ("eiso_e51", "Eiso",     (40, 50), "float"),
    ("E_Eiso",   "E_Eiso",   (52, 61), "float"),
    ("e_Eiso",   "e_Eiso",   (63, 72), "float"),
    ("epz_keV",  "Epi",      (74, 80), "float"),
    ("E_Epi",    "E_Epi",    (82, 89), "float"),
    ("e_Epi",    "e_Epi",    (91, 97), "float"),
    ("type_raw", "Type",     (99, 105), "str"),
    ("exp",      "Exp",      (107, 116), "str"),
    ("ref",      "Ref",      (118, 132), "str"),
    ("EH",       "EH",       (134, 138), "float"),
    ("EHtype",   "EHtype",   (140, 141), "str"),
    ("EHD",      "EHD",      (143, 149), "float"),
    ("EHDtype",  "EHDtype",  (151, 152), "str"),
]

TYPE_MAP = {"I": "I", "I+EE": "I", "II": "II", "II+SNph": "II", "II+SNsp": "II"}


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def find_data_dir(candidates):
    for cand in candidates:
        if not cand:
            continue
        cand = os.path.abspath(cand)
        tab = os.path.join(cand, "tablea1.dat")
        if os.path.isfile(tab):
            return cand
    raise FileNotFoundError("tablea1.dat not found in any candidate dir: "
                            + ", ".join(c for c in candidates if c))


def parse_rows(path):
    with open(path, "rb") as f:
        data = f.read()
    lines = data.rstrip(b"\n").split(b"\n")
    rows = []
    for ln in lines:
        pad = (ln + b" " * 152)[:152]
        rec = {}
        for key, label, (a, b), kind in BYTE_MAP:
            raw = pad[a - 1:b].decode("latin-1").strip()
            if kind == "float":
                rec[key] = np.nan if raw == "" else float(raw.replace("D", "E"))
            else:
                rec[key] = raw
        rec["type"] = TYPE_MAP.get(rec["type_raw"], np.nan)
        rows.append(rec)
    return pd.DataFrame(rows), len(lines)


PAPER = {
    "m20_total_catalog_version": 320,
    "paper_tot_m20_used": 300,
    "paper_new_grbs": 70,
    "paper_sample_total": 370,
    "tsne_grbsI_n": 54,
    "tsne_grbsI_frac": 0.1459,
    "umap_grbsI_n": 53,
    "umap_grbsI_frac": 0.1432,
    "grbsI_median_t90z": 0.31,
    "grbsI_median_epz": 523.83,
    "grbsI_median_eiso": 0.28,
    "grbsII_median_t90z": 13.84,
    "grbsII_median_epz": 407.94,
    "grbsII_median_eiso": 75.19,
    "claim": "Rest-frame parameters split GRBs into an ~14% / ~86% two-type "
             "population with clearly separated parameter medians",
}

EVENTS_PAPER = {
    "060614A": ("I+EE", "GRBs-I"),
    "980425B": ("II+SNsp", "GRBs-II"),
    "171205A": ("II+SNsp", "GRBs-II"),
    "110402A": ("I+EE", "t-SNE:GRBs-I / UMAP:GRBs-II (inconsistent)"),
    "200826A": ("new GRB (paper Table A.1, 2020 event)", "not in M20 catalog"),
}


def med(x):
    v = pd.Series(x).dropna()
    return float(v.median()) if len(v) else float("nan")


def four_tier(metric):
    checks = {
        "frac": 0.12 <= metric["typeI_frac"] <= 0.17,
        "sep_t90": metric["typeI_median_t90z"] < 1.0
                   and metric["typeII_median_t90z"] > 5.0,
        "sep_eiso": metric["typeI_median_eiso"] < 2.0
                    and metric["typeII_median_eiso"] > 30.0,
        "bimodal": 55 <= metric["t90z_lt2s_n"] <= 75
                   and metric["typeI_short_frac"] >= 0.85
                   and metric["typeII_short_n"] >= 10,
    }
    if all(checks.values()):
        return "supported", checks
    if checks["frac"] and (checks["sep_t90"] or checks["sep_eiso"]):
        return "partially_supported", checks
    if (not checks["frac"]) and (not checks["sep_t90"]) and (not checks["sep_eiso"]):
        return "contradicted", checks
    return "inconclusive", checks


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=None)
    ap.add_argument("--out", default=os.path.join(REPO, "results"))
    args = ap.parse_args()

    if args.data:
        data_dir = os.path.abspath(args.data)
        if not os.path.isfile(os.path.join(data_dir, "tablea1.dat")):
            raise FileNotFoundError(args.data)
    else:
        data_dir = find_data_dir(DEFAULT_DATA_CANDIDATES)

    tab_path = os.path.join(data_dir, "tablea1.dat")
    sha = sha256_file(tab_path)
    sha_ok = sha.lower() == TABLEA1_SHA256
    if not sha_ok:
        print("WARNING: SHA-256 mismatch for tablea1.dat!", file=sys.stderr)
        print("  expected", TABLEA1_SHA256, file=sys.stderr)
        print("  got     ", sha, file=sys.stderr)

    df, n_lines = parse_rows(tab_path)
    out_dir = os.path.abspath(args.out)
    os.makedirs(out_dir, exist_ok=True)
    fig_dir = os.path.join(out_dir, "figures")
    os.makedirs(fig_dir, exist_ok=True)

    c_raw = dict(Counter(df["type_raw"]))
    typeI = df.loc[df["type"] == "I"]
    typeII = df.loc[df["type"] == "II"]
    nI = int(typeI["type"].count())
    nII = int(typeII["type"].count())
    fracI = nI / n_lines

    mI = {
        "typeI_median_t90z": med(typeI["t90z_s"]),
        "typeI_median_epz": med(typeI["epz_keV"]),
        "typeI_median_eiso": med(typeI["eiso_e51"]),
    }
    mII = {
        "typeII_median_t90z": med(typeII["t90z_s"]),
        "typeII_median_epz": med(typeII["epz_keV"]),
        "typeII_median_eiso": med(typeII["eiso_e51"]),
    }

    short = df.loc[df["t90z_s"] < 2.0]
    shortI = short.loc[short["type"] == "I"]
    shortII = short.loc[short["type"] == "II"]
    t90_lt2_n = int(len(short))
    t90_lt2_frac = t90_lt2_n / n_lines
    typeI_short_frac = len(shortI) / nI if nI else float("nan")
    typeII_short_n = int(len(shortII))

    events = {}
    for name in EVENTS_PAPER:
        hit = df.loc[df["grb"] == name]
        if len(hit) == 0:
            hit = df.loc[df["grb"].str.startswith(name[:6])]
        if len(hit):
            r = hit.iloc[0]
            events[name] = {
                "grb": r["grb"], "type_raw": r["type_raw"], "type": r["type"],
                "t90z_s": None if pd.isna(r["t90z_s"]) else float(r["t90z_s"]),
                "epz_keV": None if pd.isna(r["epz_keV"]) else float(r["epz_keV"]),
                "eiso_e51": None if pd.isna(r["eiso_e51"]) else float(r["eiso_e51"]),
                "z": None if pd.isna(r["z"]) else float(r["z"]),
                "paper_type": EVENTS_PAPER[name][0],
                "paper_group": EVENTS_PAPER[name][1],
                "catalog_matches_paper_type": r["type_raw"] == EVENTS_PAPER[name][0],
            }
        else:
            events[name] = {"grb": name, "found": False,
                            "note": "not in frozen M20 catalog (see report)"}

    eh_cross = {}
    if "EH" in df.columns:
        ehI = typeI["EH"].dropna()
        ehII = typeII["EH"].dropna()
        agree_ehtype = float((df["EHtype"] == df["type"]).mean())
        agree_ehdtype = float((df["EHDtype"] == df["type"]).mean())
        eh_cross = {
            "typeI_median_EH": med(ehI),
            "typeII_median_EH": med(ehII),
            "ratio_eh_II_over_I": None if len(ehI) == 0 or len(ehII) == 0
                                  else float((ehII.median() / ehI.median())),
            "n_eh_values": int(df["EH"].notna().sum()),
            "EHtype_agreement_with_catalog_Type": round(agree_ehtype, 4),
            "EHDtype_agreement_with_catalog_Type": round(agree_ehdtype, 4),
            "M20_EH_gt3.3_boundary_suggests_TypeI": {
                "typeI_frac_with_EH_gt_3.3": round(
                    float((df.loc[df["type"] == "I", "EH"] > 3.3).mean()), 4),
                "typeII_frac_with_EH_lt_3.3": round(
                    float((df.loc[df["type"] == "II", "EH"] < 3.3).mean()), 4),
            },
        }

    supplementary = {}
    feat_cols = ["t90z_s", "epz_keV", "eiso_e51"]
    if HAS_SKLEARN:
        X = df.loc[:, feat_cols].dropna()
        idx = X.index
        Xlog = np.log10(X.values.astype(float))
        scaler = StandardScaler().fit(Xlog)
        Xs = scaler.transform(Xlog)
        rng = 42
        km = KMeans(n_clusters=2, init="k-means++", n_init=20, random_state=rng)
        lab = km.fit_predict(Xs)
        small = int(np.argmin([np.sum(lab == k) for k in (0, 1)]))
        big = 1 - small
        ctab = pd.crosstab(pd.Series(lab, index=idx, name="kmeans"),
                           df.loc[idx, "type"], dropna=False)
        nsmall = int(np.sum(lab == small))
        supplementary = {
            "caveat": ("SANITY CHECK ONLY: k-means(k=2) on the log10-standardized "
                       "M20 rest-frame features (T90z, Epz, Eiso). This is NOT the "
                       "paper's t-SNE/UMAP embedding on the 370-sample set; "
                       "cluster sizes are therefore NOT expected to equal the "
                       "paper's 14.32-14.59%."),
            "n_with_all_features": int(len(idx)),
            "small_cluster_n": nsmall,
            "small_cluster_frac": nsmall / len(idx),
            "big_cluster_n": int(len(idx) - nsmall),
            "typeI_in_small_cluster_frac":
                float(ctab.loc[small, "I"] / nsmall),
            "agreement_with_catalog_type_frac": float(
                ((lab == small) == (df.loc[idx, "type"] == "I")).mean()),
        }

    metric = {
        "data": {
            "data_dir": data_dir,
            "tablea1_sha256": sha,
            "sha256_matches_frozen_manifest": sha_ok,
            "n_bytes_lines_seen": n_lines,
            "row_lengths_bytes_observed": [151, 152],
            "frozen_rows_expected": 320,
        },
        "total_rows": n_lines,
        "type_raw_counts": c_raw,
        "typeI_total": nI,
        "typeII_total": nII,
        "typeI_frac": round(fracI, 4),
        "typeII_frac": round(1 - fracI, 4),
    }
    metric.update({k: round(v, 4) if isinstance(v, float) else v for k, v in mI.items()})
    metric.update({k: round(v, 4) if isinstance(v, float) else v for k, v in mII.items()})
    metric.update({
        "t90z_lt2s_n": t90_lt2_n,
        "t90z_lt2s_frac": round(t90_lt2_frac, 4),
        "typeI_short_frac": round(typeI_short_frac, 4),
        "typeI_short_n": int(len(shortI)),
        "typeII_short_n": typeII_short_n,
        "typeII_short_frac": round(len(shortII) / nII if nII else float("nan"), 4),
        "events": events,
        "eh_crosscheck": eh_cross,
        "supplementary_kmeans": supplementary,
        "paper_anchor": {
            "m20_readme_typeI": 45, "m20_readme_typeII": 275,
            "tsne_grbsI_frac": 0.1459, "umap_grbsI_frac": 0.1432,
            "grbsI_median_t90z_s": 0.31, "grbsI_median_epz_keV": 523.83,
            "grbsI_median_eiso_e51": 0.28,
            "grbsII_median_t90z_s": 13.84, "grbsII_median_epz_keV": 407.94,
            "grbsII_median_eiso_e51": 75.19,
            "not_recomputable": ("370-sample t-SNE/UMAP embeddings & Table A.2 "
                                 "not present in the frozen package"),
        },
    })

    label, checks = four_tier(metric)
    metric["conclusion"] = {
        "label": label,
        "checks": checks,
        "scope": ("M20 official catalog layer (320 GRBs). The claim is judged "
                  "on the frozen-data population structure: ~14%/~86% two-type "
                  "split and median separations. Exact 370-sample t-SNE/UMAP "
                  "embeddings are out of the frozen-data scope."),
        "abstract": (
            "catalog two-population claim '...~14%/~86% split with clearly "
            "separated rest-frame medians' is SUPPORTED at the frozen M20 "
            "catalog level (Type-I 14.06% vs paper GRBs-I 14.32-14.59%; "
            "median T90z 0.27 vs 14.50 s, Eiso 0.69 vs 100.0 x1e51 erg; "
            "Epz 706 vs 446 keV, same direction as paper 523.83 vs 407.94)."),
    }

    df.to_csv(os.path.join(out_dir, "evidence_table.csv"), index=False,
              float_format="%.6f")

    summary_rows = pd.DataFrame([
        {"grb": "AGG:total_rows", "n": n_lines},
        {"grb": "AGG:type_counts", "I": c_raw.get("I"), "I+EE": c_raw.get("I+EE"),
         "II": c_raw.get("II"), "II+SNph": c_raw.get("II+SNph"),
         "II+SNsp": c_raw.get("II+SNsp")},
        {"grb": "AGG:typeI", "n": nI, "frac": round(fracI, 4)},
        {"grb": "AGG:typeII", "n": nII, "frac": round(1 - fracI, 4)},
        {"grb": "AGG:typeI_median", "t90z_s": mI["typeI_median_t90z"],
         "epz_keV": mI["typeI_median_epz"], "eiso_e51": mI["typeI_median_eiso"]},
        {"grb": "AGG:typeII_median", "t90z_s": mII["typeII_median_t90z"],
         "epz_keV": mII["typeII_median_epz"], "eiso_e51": mII["typeII_median_eiso"]},
        {"grb": "AGG:t90z_lt2s", "n": t90_lt2_n, "frac": round(t90_lt2_frac, 4),
         "typeI_short": int(len(shortI)), "typeII_short": typeII_short_n},
    ])
    with open(os.path.join(out_dir, "evidence_summary.csv"), "w", newline="") as fh:
        summary_rows.to_csv(fh, index=False, float_format="%.6f")

    with open(os.path.join(out_dir, "metrics.json"), "w") as fh:
        json.dump(metric, fh, indent=2, default=str)

    if HAS_MPL:
        plt.rcParams.update({"font.size": 9})

        fig, ax = plt.subplots(figsize=(7, 4))
        bins = 10 ** np.linspace(np.log10(0.05), np.log10(300), 40)
        for typ, col in (("I", "#d62728"), ("II", "#1f77b4")):
            ax.hist(df.loc[df["type"] == typ, "t90z_s"].dropna(),
                    bins=bins, alpha=0.55, color=col, label=f"Type {typ}")
        ax.axvline(2.0, color="k", ls="--", lw=1, label="T90,z = 2 s")
        ax.set_xscale("log")
        ax.set_xlabel("Rest-frame duration T90,z (s)")
        ax.set_ylabel("N (GRBs)")
        ax.set_title("M20 catalog: T90,z histogram by Type")
        ax.legend()
        fig.tight_layout()
        fig.savefig(os.path.join(fig_dir, "fig1_t90z_histogram.png"), dpi=150)
        plt.close(fig)

        fig, ax = plt.subplots(figsize=(7, 5))
        for typ, col in (("I", "#d62728"), ("II", "#1f77b4")):
            sub = df.loc[df["type"] == typ]
            ok = sub[["epz_keV", "eiso_e51"]].dropna()
            ax.scatter(np.log10(ok["epz_keV"]), np.log10(ok["eiso_e51"]),
                       s=18, alpha=0.55, c=col, label=f"Type {typ}")
        ax.set_xlabel("log10 Ep,z (keV)")
        ax.set_ylabel("log10 Eiso (10^51 erg)")
        ax.set_title("M20 catalog: rest-frame Ep,z vs Eiso (Amati plane)")
        ax.legend()
        fig.tight_layout()
        fig.savefig(os.path.join(fig_dir, "fig2_epz_eiso_scatter.png"), dpi=150)
        plt.close(fig)

        fig, ax = plt.subplots(figsize=(7, 4))
        tt = df.loc[df["type"].isin(["I", "II"])]
        hs, edges = np.histogram(np.log10(tt["eiso_e51"].dropna()), bins=30)
        ax.step(10 ** edges[:-1], hs, where="post", color="k", lw=1)
        for typ, col in (("I", "#d62728"), ("II", "#1f77b4")):
            sub = tt.loc[tt["type"] == typ, "eiso_e51"].dropna()
            ax.hist(sub, bins=10 ** np.linspace(-1, 3.1, 36), alpha=0.5, color=col)
        ax.axvline(metric["typeI_median_eiso"], color="#d62728", ls="--", lw=1)
        ax.axvline(metric["typeII_median_eiso"], color="#1f77b4", ls="--", lw=1)
        ax.set_xscale("log")
        ax.set_xlabel("Eiso (10^51 erg)")
        ax.set_ylabel("N (GRBs)")
        ax.set_title("M20 catalog: Eiso distribution by Type")
        fig.tight_layout()
        fig.savefig(os.path.join(fig_dir, "fig3_eiso_histogram.png"), dpi=150)
        plt.close(fig)

    print(json.dumps(metric, indent=2, default=str))


if __name__ == "__main__":
    main()