#!/usr/bin/env python3
"""
Extended cross-checks for the LoTSS-Deep DR1 classification catalogues.

Reads the 11-column master tables AND the extended tables, and produces a set of
independent, reproducible consistency checks:

  1. Master vs extended table row-by-row agreement of Overall_class.
  2. Overall_class reconstructed from AGN_final x RadioAGN_final (=== master overall).
  3. Per-field reliable-classification rate and class fractions (incl. ELAIS-N1 > 70% SFG).
  4. Morphological cross-check: share of sources with Extended_radio == 1
     (clear >80 kpc extended radio emission) within each class.  Radio-loud AGN
     (LERG/HERG) are expected to be far more frequently extended than SFG/RQAGN.
  5. Redshift statistics where available (z_best) per class.

Everything is computed from the frozen FITS files directly (no hard-coded numbers).

Usage:
    python crosscheck_lotss_deep.py <data_dir> <out_dir>
"""

import json
import os
import sys

import numpy as np
import pandas as pd

FIELDS = {"en1": "ELAIS-N1", "lockman": "Lockman Hole", "bootes": "Boötes"}
CLASS_ORDER = ["SFG", "RQAGN", "LERG", "HERG", "Unc"]


def load_master(data_dir, key):
    from astropy.io import fits as pyfits
    with pyfits.open(os.path.join(data_dir, f"{key}_classifications_dr1.fits")) as h:
        d = h[1].data
    return pd.DataFrame({
        "Source_Name": np.asarray(d["Source_Name"]).astype(str),
        "Overall_class": np.asarray(d["Overall_class"]).astype(str),
        "S_150MHz": np.asarray(d["S_150MHz"], float),
        "AGN_final": np.asarray(d["AGN_final"], int),
        "RadioAGN_final": np.asarray(d["RadioAGN_final"], int),
        "Radio_excess": np.asarray(d["Radio_excess"], float),
        "z_best": np.asarray(d["z_best"], float),
    })


def load_extended(data_dir, key):
    from astropy.io import fits as pyfits
    with pyfits.open(os.path.join(data_dir, f"{key}_classifications_extended_dr1.fits")) as h:
        d = h[1].data
    cols = ["Source_Name", "Overall_class", "Extended_radio",
            "Donley", "Lacy", "Stern", "Messias", "Xray", "Opt_spec",
            "AGNfrac_AF", "AGNfrac_CG_S"]
    out = {}
    for c in cols:
        if c in d.columns.names:
            out[c] = np.asarray(d[c])
    return pd.DataFrame(out)


def derive_from_flags(df):
    a = df["AGN_final"].values
    r = df["RadioAGN_final"].values
    derived = np.full(len(df), "", dtype=object)
    m = (a == -1) | (r == -1)
    derived[m] = "Unc"
    m = ~m
    derived[m & (a == 0) & (r == 0)] = "SFG"
    derived[m & (a == 1) & (r == 0)] = "RQAGN"
    derived[m & (a == 0) & (r == 1)] = "LERG"
    derived[m & (a == 1) & (r == 1)] = "HERG"
    return pd.Series(derived, index=df.index)


def sfg_vs_agn_cut(S):
    """
    Simple physical cross-check that does NOT reuse Overall_class:
    radio-excess (Radio_excess > +0.5 dex, matching the paper's radio-AGN
    definition) & not radiative (AGN_final==0)  ->  radio-selected AGN;
    otherwise (AGN_final==0 & Radio_excess <= +0.5) -> SFG-like.
    Compares the count against Overall_class SFG in the unambiguously
    radiative-free subset (AGN_final == 0), the population the paper puts in SFG.
    """
    a = S["AGN_final"].values
    re = S["Radio_excess"].values
    sel = (a == 0) & np.isfinite(re)
    rex = re > 0.5
    n_rad = int((sel & rex).sum())
    n_norad = int((sel & ~rex).sum())
    n_sfg_label = int((S["Overall_class"] == "SFG").sum())
    return {"n_AGN_final0": int(sel.sum()), "n_radio_excess_gt0p5": n_rad,
            "n_radio_excess_le0p5": n_norad, "n_Overall_class_SFG": n_sfg_label}


def main():
    ap_ = __import__("argparse").ArgumentParser()
    ap_.add_argument("data_dir")
    ap_.add_argument("out_dir")
    a = ap_.parse_args()
    data_dir, out_dir = a.data_dir, a.out_dir
    os.makedirs(out_dir, exist_ok=True)

    report = {"task_id": "2305.05782_lotss_deep_source_class",
              "per_field": {}, "summary": {}}
    rows, rows_morph, rows_fld = [], [], []

    for key, name in FIELDS.items():
        m = load_master(data_dir, key)
        e = load_extended(data_dir, key)

        # 1) master vs extended Overall_class agreement
        merged = m[["Source_Name", "Overall_class"]].merge(
            e[["Source_Name", "Overall_class"]], on="Source_Name",
            suffixes=("_master", "_ext"), how="inner")
        agree = int((merged["Overall_class_master"] == merged["Overall_class_ext"]).sum())
        n_join = len(merged)

        # 2) reconstructed class agreement
        recon = derive_from_flags(m)
        recon_ok = int((recon == m["Overall_class"]).sum())

        # 3) per-field reliability / fractions
        vc = m["Overall_class"].value_counts()
        n_tot = len(m)
        frac = {c: vc.get(c, 0) / n_tot for c in CLASS_ORDER}
        reliable = 1 - vc.get("Unc", 0) / n_tot

        # 4) morphology: Extended_radio==1 share by class
        ext = e.set_index("Source_Name")["Extended_radio"].reindex(m["Source_Name"]).values
        m = m.assign(Extended_radio=ext)
        for c in CLASS_ORDER:
            mask = m["Overall_class"] == c
            n_c = int(mask.sum())
            n_ext = int((mask & (ext == 1)).sum()) if n_c else 0
            rows_morph.append({"field": key, "class": c, "n": n_c,
                               "n_extended_radio_1": n_ext,
                               "frac_extended": n_ext / n_c if n_c else np.nan})
        # 5) simple radio-excess cross-check
        cc = sfg_vs_agn_cut(m)

        # 6) z median per class
        zmed = {}
        for c in CLASS_ORDER:
            mask = m["Overall_class"] == c
            zf = m.loc[mask, "z_best"]
            zf = zf[(zf > 0) & np.isfinite(zf)]
            zmed[c] = float(np.median(zf)) if len(zf) else None

        report["per_field"][key] = {
            "name": name, "n": n_tot,
            "master_vs_extended_agree": agree, "master_vs_extended_join": n_join,
            "reconstructed_class_agree": recon_ok, "reconstructed_class_total": n_tot,
            "reliable_classification_rate": round(reliable, 4),
            "class_fractions": {c: round(f, 4) for c, f in frac.items()},
            "class_counts": {c: int(vc.get(c, 0)) for c in CLASS_ORDER},
            "sfg_radio_excess_crosscheck": cc,
            "median_z_per_class": zmed,
        }
        rows_fld.append({"field": key, **{f"n_{c}": int(vc.get(c, 0)) for c in CLASS_ORDER},
                         "n_total": n_tot, "reliable_rate": round(reliable, 4)})
        for r in rows_morph:
            if r["field"] == key:
                rows.append(r)

    # summary over all fields
    all_m = pd.concat([load_master(data_dir, k) for k in FIELDS], ignore_index=True)
    vc_tot = all_m["Overall_class"].value_counts()
    n_tot = len(all_m)
    report["summary"] = {
        "n_total": n_tot,
        "class_counts": {c: int(vc_tot.get(c, 0)) for c in CLASS_ORDER},
        "class_fractions": {c: round(vc_tot.get(c, 0) / n_tot, 4) for c in CLASS_ORDER},
        "reliable_classification_rate": round(1 - vc_tot.get("Unc", 0) / n_tot, 4),
    }

    pd.DataFrame(rows_fld).to_csv(os.path.join(out_dir, "results", "per_field_summary.csv"),
                                  index=False)
    pd.DataFrame(rows).to_csv(os.path.join(out_dir, "results", "morphology_by_class.csv"),
                              index=False)
    with open(os.path.join(out_dir, "results", "crosscheck_metrics.json"), "w") as f:
        json.dump(report, f, indent=2, default=str)

    print(json.dumps(report, indent=2, default=str))
    return report


if __name__ == "__main__":
    main()