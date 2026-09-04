"""Label construction (SAScore threshold), corpus stats and graph featurization.

Deterministic pipeline. Labels are reproducible in two ways:
  a) recomputed from SMILES with RDKit's sascorer (preferred, verified identical),
  b) fallback to the frozen ``data/*_sascore.parquet`` files provided in the package
     when RDKit is unavailable.
Featurization and the physics-aware auxiliary targets (complexity, strain) require RDKit.
"""
import json
import logging
import os
import pickle
import sys
import time
import warnings

import numpy as np
import pandas as pd

from config import (CACHE_DIR, DATA_DIR, RESULT_DIR, SASCORE_EASY_BELOW,
                    SASCORE_HARD_ABOVE, ATOM_D, BOND_D, ELEMENTS, UNK_ELEM_IDX)

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
log = logging.getLogger("pipeline")

warnings.filterwarnings("ignore")

try:
    from rdkit import Chem
    from rdkit.Chem import GraphDescriptors
    from rdkit.Chem import AllChem
    from rdkit.Chem import rdMolDescriptors as _d  # noqa: F401
    from rdkit import RDLogger
    RDLogger.DisableLog("rdApp.*")
    RDKIT_OK = True
except Exception:  # pragma: no cover - offline fallback
    RDKIT_OK = False
    log.warning("RDKit not available - will use frozen sascore parquets and cached features")

if RDKIT_OK:
    _contrib = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(Chem.__file__))), "Contrib")
    if _contrib not in sys.path:
        sys.path.insert(0, _contrib)
    try:
        from SA_Score import sascorer as _sascorer
    except Exception:
        _sascorer = None
    _EIDX = {e: i for i, e in enumerate(ELEMENTS)}


def sascore_one(smi):
    if _sascorer is None:
        return np.nan
    m = Chem.MolFromSmiles(smi)
    if m is None:
        return np.nan
    return float(_sascorer.calculateScore(m))


def sascore_batch(smiles, chunks=10000, n_threads=1):
    """Compute sascore for a list of smiles with RDKit (or NaN on parse failure)."""
    out = np.full(len(smiles), np.nan)
    n = 0
    for i in range(0, len(smiles), chunks):
        block = smiles[i:i + chunks]
        for j, smi in enumerate(block):
            try:
                out[i + j] = sascore_one(smi)
            except Exception:
                out[i + j] = np.nan
        n += len(block)
        log.info("  sascore %d/%d" % (i + len(block), len(smiles)))
    return out


def load_raw():
    hiv = pd.read_csv(os.path.join(DATA_DIR, "HIV.csv"))
    tox = pd.read_csv(os.path.join(DATA_DIR, "tox21.csv.gz"))
    coc = pd.read_csv(os.path.join(DATA_DIR, "COCONUT_30k_seed42.csv"))
    return hiv, tox, coc


def frozen_sascore():
    """Merge sascore from the frozen parquet files (fallback path)."""
    hiv = pd.read_parquet(os.path.join(DATA_DIR, "HIV_sascore.parquet"))[["smiles", "sascore"]]
    tox = pd.read_parquet(os.path.join(DATA_DIR, "tox21_sascore.parquet"))[["smiles", "sascore"]]
    coc = pd.read_parquet(os.path.join(DATA_DIR, "COCONUT_sascore.parquet"))
    coc = coc.rename(columns={"canonical_smiles": "smiles"})[["smiles", "sascore"]]
    return {"HIV": hiv, "tox21": tox, "COCONUT": coc}


def attach_sascore(df, split, use_rdkit=None):
    if use_rdkit is None:
        use_rdkit = RDKIT_OK
    if use_rdkit:
        df = df.copy()
        df["sascore"] = sascore_batch(df["smiles"].tolist())
        df = df.dropna(subset=["sascore"])
        return df
    else:
        ref = frozen_sascore()[split]
        df = df.merge(ref, on="smiles", how="left")
        df = df.dropna(subset=["sascore"])
        return df


def build_corpus(use_rdkit_label):
    """Assemble labeled corpus via frozen sascore parquets (fallback, no RDKit)."""
    hiv, tox, coc = load_raw()
    ref = frozen_sascore()
    tr = pd.concat([hiv[["smiles"]], tox[["smiles"]]], ignore_index=True)
    tr["sascore"] = pd.concat([ref["HIV"]["sascore"], ref["tox21"]["sascore"]],
                              ignore_index=True).values
    te = pd.DataFrame({"smiles": coc["canonical_smiles"]})
    te = te.merge(ref["COCONUT"], on="smiles", how="left")
    tr = tr.dropna(subset=["sascore"])
    te = te.dropna(subset=["sascore"])
    return tr, te


def label_from_sascore(s):
    lab = pd.Series(index=s.index, dtype=float)
    lab[s < SASCORE_EASY_BELOW] = 1.0          # easy  -> positive class
    lab[s > SASCORE_HARD_ABOVE] = 0.0          # hard  -> negative class
    lab[((s >= SASCORE_EASY_BELOW) & (s <= SASCORE_HARD_ABOVE))] = np.nan  # middle band dropped
    return lab


def complexity(smi):
    m = Chem.MolFromSmiles(smi)
    if m is None:
        return np.nan
    try:
        return float(np.log1p(GraphDescriptors.BertzCT(m)))
    except Exception:
        return np.nan


def strain_uff(smi, cap=60.0):
    """Relaxation strain proxy: UFF energy drop from the 2D-geometry start.

    strain = max(0, E_UFF(2D initial) - E_UFF(after UFF relaxation)), capped.
    Deterministic given the SMILES (RDKit UFF). NaN when UFF params are missing.
    """
    m = Chem.MolFromSmiles(smi)
    if m is None:
        return np.nan
    try:
        if AllChem.UFFHasAllMoleculeParams(m) == 0:
            return np.nan
        from rdkit.Chem.rdForceFieldHelpers import UFFGetMoleculeForceField, UFFOptimizeMolecule
        AllChem.Compute2DCoords(m)
        ff = UFFGetMoleculeForceField(m)
        e0 = ff.CalcEnergy()
        UFFOptimizeMolecule(m, maxIters=400)
        e1 = ff.CalcEnergy()
        return float(min(max(0.0, e0 - e1), cap))
    except Exception:
        return np.nan


def atom_feat(a):
    el = _EIDX.get(a.GetSymbol(), UNK_ELEM_IDX)
    onehot = np.zeros(UNK_ELEM_IDX + 1)
    onehot[el] = 1.0
    return np.concatenate([onehot, [
        float(a.GetIsAromatic()),
        float(a.GetDegree()) / 4.0,
        float(min(a.GetFormalCharge() + 1, 2)),
        float(min(a.GetTotalNumHs(), 3)),
        float(a.IsInRing()),
        float(int(a.GetHybridization())) % 10.0,
    ]])


def bond_feat(b):
    t = b.GetBondTypeAsDouble()
    return [
        1.0 if t == 1.0 else 0.0, 1.0 if t == 2.0 else 0.0, 1.0 if t == 3.0 else 0.0,
        1.0 if b.GetIsAromatic() else 0.0, float(int(b.GetIsConjugated())),
    ]


def mode_bond(b):
    t = b.GetBondTypeAsDouble()
    if b.GetIsAromatic():
        return 3
    return {1.0: 0, 2.0: 1, 3.0: 2}.get(t, 4)


def onehot(labels, n):
    x = np.zeros((len(labels), n))
    x[np.arange(len(labels)), np.asarray(labels, dtype=int)] = 1.0
    return x


def featurize_mol(smi):
    """Return (X [n,D], edge_index [2,E], edge_attr [E,ED], n) or None."""
    m = Chem.MolFromSmiles(smi)
    if m is None or m.GetNumAtoms() == 0:
        return None
    X = atom_feats(m)
    si, di, ea = [], [], []
    for b in m.GetBonds():
        i, j = b.GetBeginAtomIdx(), b.GetEndAtomIdx()
        si += [i, j]
        di += [j, i]
        ea.append(bond_feat(b))
        ea.append(bond_feat(b))
    if not ea:
        return None
    return (X, (np.array(si, dtype=np.int64), np.array(di, dtype=np.int64)),
            np.array(ea, dtype=np.float32))


def atom_feats(m):
    return np.array([atom_feat(a) for a in m.GetAtoms()], dtype=np.float32)


def _chunk_list(lst, k):
    for i in range(0, len(lst), k):
        yield lst[i:i + k]


def compute_aux(smiles, kind):
    """kind in {'complexity','strain'}; returns np array with NaN."""
    out = np.full(len(smiles), np.nan)
    if not RDKIT_OK:
        return out
    fn = complexity if kind == "complexity" else strain_uff
    t0 = time.time()
    for i, smi in enumerate(smiles):
        try:
            out[i] = fn(smi)
        except Exception:
            out[i] = np.nan
        if (i + 1) % 5000 == 0:
            log.info("  %s %d/%d (%.0fs)" % (kind, i + 1, len(smiles), time.time() - t0))
    return out


def featurize_split(df):
    """Featurize a labeled frame into flat graph tensors. Returns dict of numpy arrays."""
    xs, es, eas, ys, ns, ss = [], [], [], [], [], []
    s0, d0 = [], []
    node_off, edge_off = 0, 0
    counts = []
    n_fail = 0
    for smi, lab in zip(df["smiles"].tolist(), df["label"].tolist()):
        r = featurize_mol(smi)
        if r is None:
            n_fail += 1
            continue
        X, (si, di), ea = r
        n = X.shape[0]
        xs.append(X)
        ys.append(lab)
        ss.append(smi)
        s0 += (si + node_off).tolist()
        d0 += (di + node_off).tolist()
        eas.append(ea)
        node_off += n
        edge_off += ea.shape[0]
        counts.append(n)
        ns.append(n)
    out = dict(
        smiles=np.asarray(ss, dtype=object),
        label=np.asarray(ys, dtype=np.float32),
        n_nodes=np.asarray(ns, dtype=np.int64),
        node_off=np.asarray([0] + list(np.cumsum(ns)), dtype=np.int64),
        X=np.concatenate(xs).astype(np.float32),
        edge_index=np.vstack([np.asarray(s0, dtype=np.int64), np.asarray(d0, dtype=np.int64)]),
        edge_attr=np.concatenate(eas).astype(np.float32),
        n_fail=n_fail,
    )
    return out


def add_aux_stats(df, aux_values):
    """Standardize aux targets using TRAIN statistics only."""
    tr_mask = df["split"] == "train"
    means, stds = {}, {}
    for k, v in aux_values.items():
        col = "aux_" + k
        df[col] = np.asarray(v, dtype=np.float64)
        m = tr_mask & ~np.isnan(df[col])
        mu = float(df.loc[m, col].mean())
        sd = float(df.loc[m, col].std())
        means[k], stds[k] = mu, sd
        df[col + "_z"] = (df[col] - mu) / sd
        df.loc[np.isnan(df[col]), col + "_z"] = np.nan
    return df, means, stds


def main(use_rdkit_label=None, force=False):
    cache = os.path.join(CACHE_DIR, "corpus_features.pkl")
    if not force and os.path.exists(cache):
        log.info("Loading cached features: %s" % cache)
        with open(cache, "rb") as f:
            return pickle.load(f)

    if use_rdkit_label is None:
        use_rdkit_label = RDKIT_OK

    # ---- labels (from raw SMILES via RDKit sascorer, or frozen parquet fallback)
    if use_rdkit_label:
        log.info("Computing SAScore with RDKit ...")
        hiv, tox, coc = load_raw()
        tr_smiles = pd.concat([hiv[["smiles"]], tox[["smiles"]]], ignore_index=True)
        te_smiles = coc[["canonical_smiles"]].rename(columns={"canonical_smiles": "smiles"})
        tr_s = sascore_batch(tr_smiles["smiles"].tolist())
        te_s = sascore_batch(te_smiles["smiles"].tolist())
        tr_smiles["sascore"], te_smiles["sascore"] = tr_s, te_s
        tr = tr_smiles.dropna(subset=["sascore"]).copy()
        te = te_smiles.dropna(subset=["sascore"]).copy()
    else:
        log.info("Using frozen sascore parquets")
        tr, te = build_corpus(use_rdkit_label=False)

    band_tr = int(((tr["sascore"] >= SASCORE_EASY_BELOW) & (tr["sascore"] <= SASCORE_HARD_ABOVE)).sum())
    band_te = int(((te["sascore"] >= SASCORE_EASY_BELOW) & (te["sascore"] <= SASCORE_HARD_ABOVE)).sum())

    tr["split"] = "train"
    te["split"] = "test"

    tr["label"] = label_from_sascore(tr["sascore"]).values
    te["label"] = label_from_sascore(te["sascore"]).values

    tr = tr.dropna(subset=["label"])
    te = te.dropna(subset=["label"])

    corpus = pd.concat([tr, te], ignore_index=True)
    corpus["smiles"] = corpus["smiles"].astype(str)

    log.info("labeled kept: train=%d test=%d" % (len(tr), len(te)))

    # ---- featurize (graph tensors)
    log.info("Featurizing graphs ...")
    gtr = featurize_split(tr)
    gte = featurize_split(te)
    log.info("train graphs n=%d (fail=%d), test graphs n=%d (fail=%d)" %
             (gtr["label"].size, gtr["n_fail"], gte["label"].size, gte["n_fail"]))

    # ---- auxiliary physics-aware targets (complexity / strain), train-only stats
    if RDKIT_OK:
        log.info("Computing aux targets (complexity) ...")
        comp_tr = compute_aux(tr["smiles"].tolist(), "complexity")
        log.info("Computing aux targets (strain) ...")
        strain_tr = compute_aux(tr["smiles"].tolist(), "strain")
        tr = tr.copy(); te = te.copy()
        tr["complexity"], tr["strain"] = comp_tr, strain_tr
        te["complexity"] = np.full(len(te), np.nan)
        te["strain"] = np.full(len(te), np.nan)
        aux_stats = {
            "complexity": dict(mean=float(np.nanmean(comp_tr)), std=float(np.nanstd(comp_tr)),
                               nan=int(np.isnan(comp_tr).sum()), n=int(len(comp_tr))),
            "strain": dict(mean=float(np.nanmean(strain_tr)), std=float(np.nanstd(strain_tr)),
                           nan=int(np.isnan(strain_tr).sum()), n=int(len(strain_tr))),
        }
        tr["comp_z"] = (tr["complexity"] - aux_stats["complexity"]["mean"]) / aux_stats["complexity"]["std"]
        tr["strain_z"] = (tr["strain"] - aux_stats["strain"]["mean"]) / aux_stats["strain"]["std"]
        te["comp_z"] = np.nan
        te["strain_z"] = np.nan
    else:
        aux_stats = None
        tr["comp_z"] = tr["strain_z"] = np.full(len(tr), np.nan)
        te["comp_z"] = te["strain_z"] = np.full(len(te), np.nan)

    tr["comp_z"] = np.where(np.isnan(tr["comp_z"]), 0.0, tr["comp_z"])
    te["comp_z"] = te["comp_z"].astype(float)
    tr["strain_z"] = np.where(np.isnan(tr["strain_z"]), 0.0, tr["strain_z"])
    te["strain_z"] = te["strain_z"].astype(float)

    # save
    artifact = dict(
        tr_frame=tr[["smiles", "label", "sascore", "comp_z", "strain_z"]],
        te_frame=te[["smiles", "label", "sascore", "comp_z", "strain_z"]],
        gtr=gtr, gte=gte, aux_stats=aux_stats,
        band_counts=dict(dropped_train=band_tr, dropped_test=band_te,
                         total_raw_train=int(tr.shape[0] + band_tr),
                         total_raw_test=int(te.shape[0] + band_te)),
    )
    with open(cache, "wb") as f:
        pickle.dump(artifact, f)
    log.info("saved %s" % cache)
    return artifact


def corpus_stats(artifact):
    tr = artifact["tr_frame"]
    te = artifact["te_frame"]
    teasy = int((tr["label"] == 1).sum()) + int((te["label"] == 1).sum())
    thard = int((tr["label"] == 0).sum()) + int((te["label"] == 0).sum())
    bc = artifact.get("band_counts", {})
    return dict(
        corpus=True,
        train_kept=int(len(tr)),
        train_easy=int((tr["label"] == 1).sum()),
        train_hard=int((tr["label"] == 0).sum()),
        test_kept=int(len(te)),
        test_easy=int((te["label"] == 1).sum()),
        test_hard=int((te["label"] == 0).sum()),
        band_dropped_train=bc.get("dropped_train", -1),
        band_dropped_test=bc.get("dropped_test", -1),
        total_kept=int(len(tr) + len(te)),
        total_easy=teasy,
        total_hard=thard,
        corpus_easy_frac=round(teasy / max(teasy + thard, 1), 4),
        corpus_hard_frac=round(thard / max(teasy + thard, 1), 4),
        train_easy_frac=round((tr["label"] == 1).sum() / len(tr), 4),
        train_hard_frac=round((tr["label"] == 0).sum() / len(tr), 4),
        sascore_band=dict(easy="sascore<4", hard="sascore>5", dropped="4<=sascore<=5"),
    )


if __name__ == "__main__":
    art = main()
    stats = corpus_stats(art)
    if stats.get("band_dropped_train", -1) == -1:
        # old cache without band counts: derive them from the frozen parquets
        hiv = pd.read_parquet(os.path.join(DATA_DIR, "HIV_sascore.parquet"))
        tox = pd.read_parquet(os.path.join(DATA_DIR, "tox21_sascore.parquet"))
        coc = pd.read_parquet(os.path.join(DATA_DIR, "COCONUT_sascore.parquet"))
        s_tr = pd.concat([hiv["sascore"], tox["sascore"]], ignore_index=True)
        stats["band_dropped_train"] = int(((s_tr >= SASCORE_EASY_BELOW) & (s_tr <= SASCORE_HARD_ABOVE)).sum())
        stats["band_dropped_test"] = int(((coc["sascore"] >= SASCORE_EASY_BELOW) & (coc["sascore"] <= SASCORE_HARD_ABOVE)).sum())
        stats["total_raw_train"] = int(len(s_tr))
        stats["total_raw_test"] = int(len(coc))
    with open(os.path.join(RESULT_DIR, "label_stats.json"), "w") as f:
        json.dump(stats, f, indent=2)
    log.info(json.dumps(stats, indent=2))