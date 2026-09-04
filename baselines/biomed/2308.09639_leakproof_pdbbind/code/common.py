"""Shared utilities for the LP-PDBBind leak-proof verification.

Column mapping for the frozen data files (official THGLab/LP-PDBBind repo
naming; the TASK.md names are synonyms):

  LP_PDBBind.csv
    'Unnamed: 0'  -> PDB complex ID   (TASK.md: 'PDB ID')
    'smiles'      -> ligand SMILES    (TASK.md: 'Ligand ID' source)
    'seq'         -> protein sequence (TASK.md: 'UniProt ID' source)
    'new_split'   -> time-based split (TASK.md: 'Time-based split')
    'value'       -> pKd/pKi (PKI)    (TASK.md: 'PKI')
    'CL2'         -> CL2 complex-type flag (TASK.md: 'CL2 complex type')
    'covalent'    -> covalent flag
    'date'        -> PDB deposit date (used by the time split)

  BDB2020+.csv
    'pdbid','value','smiles','seq','accurate','pKa'
"""
import os
import re
import hashlib
import json

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(ROOT, "data")
LP_CSV = os.path.join(DATA_DIR, "LP_PDBBind.csv")
BDB_CSV = os.path.join(DATA_DIR, "BDB2020+.csv")

SEED = 0
TRAIN_N, VAL_N, TEST_N = 11513, 2422, 4860          # paper Table 1 / §3.3
TEST_CL2_NONCOV_N = 2171                            # paper Table 1 (CL2 non-covalent test)

EXPECTED_SHA = {
    "LP_PDBBind.csv": "7bb4e54e66c0c58ab74263edb8c2a2d677c2474cfc4ae4dec1eb31a231b10f8a",
    "BDB2020+.csv": "9c1aa1e8e32852a267bf2bfa1955bd88347aae3474e2da54e9011bac73e8fe7a",
}


def sha256(path, chunk=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def verify_checksums():
    """Verify data integrity against the frozen SHA-256 hashes (TASK.md)."""
    report = {}
    for fn, expected in EXPECTED_SHA.items():
        path = os.path.join(DATA_DIR, fn)
        actual = sha256(path)
        report[fn] = (actual == expected, actual[:12])
    return report


def load_lp_data():
    """Load LP_PDBBind.csv, keep only rows with a time split; map columns."""
    df = pd.read_csv(LP_CSV)
    df = df.rename(columns={
        "Unnamed: 0": "pdb_id",
        "new_split": "split",
        "value": "pki",
    })
    df = df[df["split"].notna()].copy()            # 648 rows without split are dropped
    df["split"] = df["split"].astype(str)
    df["pki"] = pd.to_numeric(df["pki"], errors="coerce")
    df["smiles"] = df["smiles"].astype(object)     # keep NaN as NaN
    df["seq"] = df["seq"].astype(str)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    return df.reset_index(drop=True)


def load_bdb_data():
    """Load BDB2020+ (115 external complexes)."""
    df = pd.read_csv(BDB_CSV)
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df["pka"] = pd.to_numeric(df["pKa"], errors="coerce")
    df["seq"] = df["seq"].astype(str)
    df["smiles"] = df["smiles"].astype(object)
    return df


def select_cl1_noncov(df):
    """Rows satisfying CL1 & non-covalent (paper's training protocol)."""
    return df[(df["CL1"].astype(str) == "True")
              & (df["covalent"].astype(str) == "False")].copy()


# ----------------------------------------------------------------------------
# Ligand identity (canonical SMILES via RDKit) and target identity (sequence)
# ----------------------------------------------------------------------------
def canonical_smiles(smi):
    """Return canonical SMILES or None if unparseable / missing."""
    if smi is None or (isinstance(smi, float) and np.isnan(smi)):
        return None
    s = str(smi).strip()
    if not s or s.lower() == "nan":
        return None
    from rdkit import Chem
    try:
        mol = Chem.MolFromSmiles(s)
        return Chem.MolToSmiles(mol) if mol is not None else None
    except Exception:
        return None


def add_ligand_ids(df, col="smiles"):
    """Add '_lig' (canonical SMILES for intra-split identity) column."""
    df = df.copy()
    df["_lig"] = df[col].map(canonical_smiles)
    return df


def add_random_split(df, seed=SEED):
    """Re-assign rows to train/val/test with the SAME sizes as the time split
    but at random (fixed seed). Draws directly with a generator so the result
    is fully reproducible."""
    rng = np.random.RandomState(seed)
    idx = rng.permutation(len(df))
    split = np.empty(len(df), dtype=object)
    split[idx[:TRAIN_N]] = "train"
    split[idx[TRAIN_N:TRAIN_N + VAL_N]] = "val"
    split[idx[TRAIN_N + VAL_N:]] = "test"
    out = df.copy()
    out["split"] = split
    return out


# ----------------------------------------------------------------------------
# Ligand Morgan fingerprints (ECFP4) and protein dipeptide-composition features
# ----------------------------------------------------------------------------
def morgan_fingerprint(smi, radius=2, nbits=2048):
    """Morgan (ECFP4-like) fingerprint over canonical SMILES; None-safe."""
    if smi is None:
        return None
    from rdkit import Chem
    from rdkit.Chem import AllChem
    try:
        mol = Chem.MolFromSmiles(smi)
        if mol is None:
            return None
        return AllChem.GetMorganFingerprintAsBitVect(mol, radius, nBits=nbits)
    except Exception:
        return None


AMINO_ACIDS = "ACDEFGHIKLMNPQRSTVWY"
AA_INDEX = {a: i for i, a in enumerate(AMINO_ACIDS)}


def dipeptide_composition(seq, normalize=True):
    """400-dim dipeptide composition vector for a protein sequence."""
    seq = str(seq).upper()
    seq = re.sub(r"[^ACDEFGHIKLMNPQRSTVWY]", "", seq)
    vec = np.zeros(400, dtype=np.float64)
    if len(seq) < 2:
        return vec
    for i in range(len(seq) - 1):
        a, b = seq[i], seq[i + 1]
        if a in AA_INDEX and b in AA_INDEX:
            vec[AA_INDEX[a] * 20 + AA_INDEX[b]] += 1.0
    vec = vec / (len(seq) - 1)
    return vec


def rf_features(df):
    """Concatenate ligand Morgan ECFP4 (2048) + protein dipeptide comp (400)."""
    X = []
    ok = np.ones(len(df), dtype=bool)
    for i, (smi, seq) in enumerate(zip(df["smiles"], df["seq"])):
        c = canonical_smiles(smi)
        fp = morgan_fingerprint(c)
        if fp is None:
            ok[i] = False
            X.append(None)
            continue
        d = dipeptide_composition(seq)
        X.append(np.r_[np.asarray(fp, dtype=np.float64), d])
    X = np.vstack([x if x is not None else np.zeros(2048 + 400) for x in X])
    return X, ok


# ----------------------------------------------------------------------------
# Metrics
# ----------------------------------------------------------------------------
def rmse(y_true, y_pred):
    yt = np.asarray(y_true, dtype=float)
    yp = np.asarray(y_pred, dtype=float)
    return float(np.sqrt(np.mean((yt - yp) ** 2)))


def pearson_r(y_true, y_pred):
    yt = np.asarray(y_true, dtype=float)
    yp = np.asarray(y_pred, dtype=float)
    if yt.std() == 0 or yp.std() == 0:
        return float("nan")
    return float(np.corrcoef(yt, yp)[0, 1])


def save_json(obj, path):
    with open(path, "w") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)