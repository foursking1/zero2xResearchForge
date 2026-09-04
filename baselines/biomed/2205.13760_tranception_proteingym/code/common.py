"""Shared helpers for the ProteinGym substitution-assay replication.

Conventions:
  - mutant strings follow ProteinGym format e.g. 'M1I' (single) or
    'K3R:V55A:Q94R' (multi). Positions are 1-indexed w.r.t. the `target_seq`
    stored in ProteinGym_reference_file_substitutions.csv.
  - DMS_score: higher = higher measured fitness (ProteinGym processed files
    are already re-oriented with raw_DMS_directionality).
"""
import os
import re

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # agent_solution/


def _find_data_dir():
    """Resolve the frozen ProteinGym data directory robustly."""
    cands = [
        os.environ.get("PROTEINGYM_DATA_DIR", ""),
        os.path.join(os.path.dirname(ROOT), "data"),          # <task>/data
        os.path.join(ROOT, "data"),
        "/mnt/f/dataset/biomed/2205.13760_tranception_proteingym",  # physical copy on this host
    ]
    for c in cands:
        if c and os.path.isfile(os.path.join(c, "ProteinGym_reference_file_substitutions.csv")):
            return c
    raise RuntimeError(
        "Cannot locate frozen data dir. Set env PROTEINGYM_DATA_DIR to the folder "
        "containing the assay CSVs and ProteinGym_reference_file_substitutions.csv."
    )


DATA = _find_data_dir()

ASSAYS = [
    "ADRB2_HUMAN_Jones_2020",
    "BLAT_ECOLX_Deng_2012",
    "BRCA1_HUMAN_Findlay_2018",
    "GAL4_YEAST_Kitzman_2015",
    "GFP_AEQVI_Sarkisyan_2016",
    "PTEN_HUMAN_Matreyek_2021",
]

AA20 = "ACDEFGHIKLMNPQRSTVWY"
AA_TO_IDX = {aa: i for i, aa in enumerate(AA20)}


def parse_mutant(m):
    """Return [(0-indexed_pos, wt_aa, mut_aa), ...] for a mutant string."""
    out = []
    for part in m.split(":"):
        g = re.fullmatch(r"([A-Z])(\d+)([A-Z])", part)
        if not g:
            raise ValueError(f"unparsable mutant {part!r} in {m!r}")
        wt, pos, mut = g.groups()
        out.append((int(pos) - 1, wt, mut))
    return out


def load_reference():
    return pd.read_csv(os.path.join(DATA, "ProteinGym_reference_file_substitutions.csv"))


def get_target_seq(ref, fid):
    return ref[ref["DMS_id"] == fid].iloc[0]["target_seq"]


def get_meta(ref, fid):
    r = ref[ref["DMS_id"] == fid].iloc[0]
    return {
        "uniprot_id": r["UniProt_ID"],
        "taxon": r["taxon"],
        "MSA_Neff": float(r["MSA_N_eff"]),
        "MSA_Neff_L_category": r["MSA_Neff_L_category"],
        "raw_DMS_directionality": int(r["raw_DMS_directionality"]),
    }


def load_assay(fid):
    """Return DataFrame with columns mutant, DMS_score, DMS_score_bin and a
    parsed `subs` list-of-lists of (pos0, wt, mut)."""
    df = pd.read_csv(os.path.join(DATA, f"{fid}.csv"))
    df["subs"] = df["mutant"].map(parse_mutant)
    return df


# Full BLOSUM62 log-odds substitution matrix, generated from the canonical
# published table (Henikoff & Henikoff 1992; NCBI BLAST reference).
_BLOSUM62_CANON = """
A  4 -1 -2 -2  0 -1 -1  0 -2 -1 -1 -1 -1 -2 -1  1  0 -3 -2  0
R -1  5  0 -2 -3  1  0 -2  0 -3 -2  2 -1 -3 -2 -1 -1 -3 -2 -3
N -2  0  6  1 -3  0  0  0  1 -3 -3  0 -2 -3 -2  1  0 -4 -2 -3
D -2 -2  1  6 -3  0  2 -1 -1 -3 -4 -1 -3 -3 -1  0 -1 -4 -3 -3
C  0 -3 -3 -3  9 -3 -4 -3 -3 -1 -1 -3 -1 -2 -3 -1 -1 -2 -2 -1
Q -1  1  0  0 -3  5  2 -2  0 -3 -2  1  0 -3 -1  0 -1 -2 -1 -2
E -1  0  0  2 -4  2  5 -2  0 -3 -3  1 -2 -3 -1  0 -1 -3 -2 -2
G  0 -2  0 -1 -3 -2 -2  6 -2 -4 -4 -2 -3 -3 -2  0 -2 -2 -3 -3
H -2  0  1 -1 -3  0  0 -2  8 -3 -3 -1 -2 -1 -2 -1 -2 -2  2 -3
I -1 -3 -3 -3 -1 -3 -3 -4 -3  4  2 -3  1  0 -3 -2 -1 -3 -1  3
L -1 -2 -3 -4 -1 -2 -3 -4 -3  2  4 -2  2  0 -3 -2 -1 -2 -1  1
K -1  2  0 -1 -3  1  1 -2 -1 -3 -2  5 -1 -3 -1  0 -1 -3 -2 -2
M -1 -1 -2 -3 -1  0 -2 -3 -2  1  2 -1  5  0 -2 -1 -1 -1 -1  1
F -2 -3 -3 -3 -2 -3 -3 -3 -1  0  0 -3  0  6 -4 -2 -2  1  3 -1
P -1 -2 -2 -1 -3 -1 -1 -2 -2 -3 -3 -1 -2 -4  7 -1 -1 -4 -3 -2
S  1 -1  1  0 -1  0  0  0 -1 -2 -2  0 -1 -2 -1  4  1 -3 -2 -2
T  0 -1  0 -1 -1 -1 -1 -2 -2 -1 -1 -1 -1 -2 -1  1  5 -2 -2  0
W -3 -3 -4 -4 -2 -2 -3 -2 -2 -3 -2 -3 -1  1 -4 -3 -2 11  2 -3
Y -2 -2 -2 -3 -2 -1 -2 -3  2 -1 -1 -2 -1  3 -3 -2 -2  2  7 -1
V  0 -3 -3 -3 -1 -2 -2 -3 -3  3  1 -2  1 -1 -2 -2  0 -3 -1  4
"""


def _build_blosum62():
    lines = [ln for ln in _BLOSUM62_CANON.strip().splitlines() if ln.strip()]
    aas = "ARNDCQEGHILKMFPSTWYV"
    rows = [ln.split() for ln in lines]
    mat = {}
    for row in rows:
        wt = row[0]
        for mut, val in zip(aas, row[1:]):
            mat[wt + mut] = int(val)
    return mat


BLOSUM62 = _build_blosum62()


def blosum62_score(wt, mut):
    """Raw BLOSUM62 log-odds for the substitution wt->mut (higher=more likely
    to be observed / conserved)."""
    return BLOSUM62[wt + mut]


def score_baseline_blosum62(subs):
    """Site-independent baseline: sum of BLOSUM62[wt_i, mut_i] over mutated
    positions. No training, no DMS data used."""
    return sum(blosum62_score(wt, mut) for _, wt, mut in subs)


def pc_alphas(y):
    """Pseudo-count 20-dim Dirichlet parameterization used for a
    frequency-style baseline."""
    import numpy as np
    a = np.full(20, 0.5)
    a[AA_TO_IDX[y]] += 1.0
    return a