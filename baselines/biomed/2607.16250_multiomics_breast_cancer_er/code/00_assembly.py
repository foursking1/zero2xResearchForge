#!/usr/bin/env python3
"""00_assembly.py — Assemble frozen TCGA-BRCA multi-omic data into an ER-status dataset.

Data sources (frozen, cBioPortal datahub brca_tcga_pan_can_atlas_2018):
  data_mrna_seq_v2_rsem.txt   RNA-seq RSEM,  gene x sample
  data_cna.txt                GISTIC2.0 copy number, gene x sample (-2..2)
  data_rppa.txt               RPPA protein expression, protein x sample
  data_clinical_patient.txt   clinical patients (PAM50-like SUBTYPE)

Rules (documented, reproducible):
  1. Sample -> patient: TCGA barcode, first 12 characters (TCGA-XX-XXXX).
  2. Cohort = patients present in RNA & CNA & RPPA & clinical.
  3. ER status derived from PAM50-like SUBTYPE (no IHC ER field is shipped in
     the frozen clinical file):
        ER+ = BRCA_LumA | BRCA_LumB
        ER- = BRCA_Basal | BRCA_Her2
     BRCA_Normal and patients with missing subtype are excluded (normal-like
     tissue is not a tumor subtype and has ambiguous ER status).
  4. RPPA missing values are NOT imputed here; imputation is done fold-internally
     in the CV pipeline to avoid leakage.
  5. Output: results/assembled.npz (X_rna, X_cna, X_rppa, gene names, sample ids)
     and results/assembly_meta.csv.

Usage:  python 00_assembly.py --data-dir PATH_TO_FROZEN_DATA --out-dir results
"""
import argparse
import json
import os

import numpy as np
import pandas as pd


def load_omic(path, name_col):
    df = pd.read_csv(path, sep="\t")
    df = df.set_index(name_col)
    df = df.loc[:, ~df.columns.duplicated()]
    return df


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", required=True, help="frozen data dir")
    ap.add_argument("--out-dir", default="results")
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)

    rna = load_omic(os.path.join(args.data_dir, "data_mrna_seq_v2_rsem.txt"), "Hugo_Symbol")
    cna = load_omic(os.path.join(args.data_dir, "data_cna.txt"), "Hugo_Symbol")
    rppa = load_omic(os.path.join(args.data_dir, "data_rppa.txt"), "Composite.Element.REF")
    clin = pd.read_csv(os.path.join(args.data_dir, "data_clinical_patient.txt"),
                       sep="\t", comment="#")

    def patient_map(df):
        return {c[:12] for c in df.columns}

    patients = patient_map(rna) & patient_map(cna) & patient_map(rppa)
    patients = patients & set(clin.PATIENT_ID)
    patients = sorted(patients)
    print(f"[assembly] common patients (RNA&CNA&RPPA&clin): {len(patients)}")

    rna = rna[[c for c in rna.columns if c[:12] in set(patients)]]
    cna = cna[[c for c in cna.columns if c[:12] in set(patients)]]
    rppa = rppa[[c for c in rppa.columns if c[:12] in set(patients)]]
    rna.columns = [c[:12] for c in rna.columns]
    cna.columns = [c[:12] for c in cna.columns]
    rppa.columns = [c[:12] for c in rppa.columns]
    rna = rna[patients].T
    cna = cna[patients].T
    rppa = rppa[patients].T

    clin = clin.set_index("PATIENT_ID").loc[patients]
    subtype = clin["SUBTYPE"]

    er_map = {"BRCA_LumA": 1, "BRCA_LumB": 1, "BRCA_Basal": 0, "BRCA_Her2": 0}
    y = subtype.map(er_map)
    keep = y.notna()
    print(f"[assembly] exclude Normal-like/missing-subtype: {int((~keep).sum())}")

    rna = rna[keep]; cna = cna[keep]; rppa = rppa[keep]
    y = y[keep].astype(int).to_numpy()
    patients = [p for p, k in zip(patients, keep) if k]

    n_pos = int(y.sum()); n_neg = int(len(y) - y.sum())
    print(f"[assembly] final cohort: {len(y)} patients, ER+ {n_pos} ({n_pos/len(y):.1%}), "
          f"ER- {n_neg} ({n_neg/len(y):.1%})")

    # numeric coercion (RNA/CNA are clean; ensure float)
    X_rna = rna.to_numpy(dtype=np.float64)
    X_cna = cna.to_numpy(dtype=np.float64)
    X_rppa = rppa.to_numpy(dtype=np.float64)

    np.savez_compressed(
        os.path.join(args.out_dir, "assembled.npz"),
        X_rna=X_rna, X_cna=X_cna, X_rppa=X_rppa,
        rna_genes=rna.columns.to_numpy(),
        cna_genes=cna.columns.to_numpy(),
        rppa_proteins=rppa.columns.to_numpy(),
        patients=np.array(patients),
        y=y,
    )
    meta = pd.DataFrame({
        "patient_id": patients,
        "subtype": subtype[keep].to_numpy(),
        "er_status": y,
    })
    meta.to_csv(os.path.join(args.out_dir, "assembly_meta.csv"), index=False)

    summary = {
        "n_samples": int(len(y)),
        "n_er_positive": n_pos,
        "n_er_negative": n_neg,
        "er_positive_fraction": float(n_pos / len(y)),
        "er_negative_fraction": float(n_neg / len(y)),
        "n_rna_features": int(rna.shape[1]),
        "n_cna_features": int(cna.shape[1]),
        "n_rppa_features": int(rppa.shape[1]),
        "excluded_normal_like_or_missing_subtype": int((~keep).sum()),
        "er_mapping": {"ER+": "BRCA_LumA,BRCA_LumB", "ER-": "BRCA_Basal,BRCA_Her2"},
        "barcode_rule": "first 12 chars (TCGA-XX-XXXX)",
        "cohort_rule": "patients present in RNA&CNA&RPPA&clinical with defined ER subtype",
    }
    with open(os.path.join(args.out_dir, "assembly_summary.json"), "w") as f:
        json.dump(summary, f, indent=2, default=str)
    print("[assembly] saved assembled.npz, assembly_meta.csv, assembly_summary.json")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
