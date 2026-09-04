"""Load the frozen PAGES2k 2019 data from its original in-place location.

All paths point to the frozen data bundles; no large files are copied.

Primary bundle (manifest location):
  E:\\scisolvebench-data\\asset-data\\datasets-v1\\v1\\pages2k_2019\\
    real_data_candidates\\reconstruction_model_subset_v1\\files

Reconstruction ensemble text files (authors' published 7 x 1000-member
ensembles, not included in the curated subset bundle; identical to the
figshare/NOAA release) are read in place from:
  E:\\scisolvebench-data\\raw\\pages2k_2019\\work_dir\\data\\reconstructions\\recons
"""
import os
import numpy as np
import pandas as pd
import pyreadr

DATA_ROOT = r"E:\scisolvebench-data\asset-data\datasets-v1\v1\pages2k_2019\real_data_candidates\reconstruction_model_subset_v1\files"
RECONS_ROOT = r"E:\scisolvebench-data\raw\pages2k_2019\work_dir\data\reconstructions\recons"

METHODS = ["CPS", "PCR", "M08", "PAI", "OIE", "BHM", "DA"]
REF_START, REF_END = 1961, 1990  # anomaly reference period


def load_recon_ensembles():
    """Return dict method -> (years, data) with data (2000, 1000).

    The published .txt files carry a header row and are *not* centred on
    1961-1990; we apply the authors' anomalisation (subtract the mean of the
    ensemble median over 1961-1990 from every member, Figs_gmst.R lines 39-45).
    """
    out = {}
    for m in METHODS:
        path = os.path.join(RECONS_ROOT, m + ".txt")
        df = pd.read_csv(path, sep="\t")
        years = df["Year_CE"].values.astype(int)
        data = df.iloc[:, 1:].values.astype(float)
        em = np.nanmedian(data, axis=1)
        ref = np.nanmean(em[(years >= REF_START) & (years <= REF_END)])
        data = data - ref
        out[m] = (years, data)
    return out


def load_full_ensemble():
    """Return anomalized full ensemble (2000, 7000) and method labels.

    Column order matches Figs_gmst.R experiment.names: CPS, PCR, M08, PAI,
    OIE, BHM, DA.
    """
    recons = load_recon_ensembles()
    blocks = [recons[m][1] for m in METHODS]
    fe = np.concatenate(blocks, axis=1)
    labels = np.repeat(np.array(METHODS), 1000)
    years = recons["CPS"][0]
    return years, fe, labels


def load_medians():
    """Return anomalized ensemble median per method (2000, 7)."""
    recons = load_recon_ensembles()
    return recons["CPS"][0], np.column_stack([recons[m][1] for m in METHODS])


def load_models_fullforced():
    """CMIP5/CESM-LME past1000 GMST (Apr-Mar), shape (1155, 23), years 851-2005.

    Values are absolute GMST (Kelvin); anomalised here to 1961-1990.
    """
    r = pyreadr.read_r(os.path.join(DATA_ROOT, "Models_fullforced_Past1000_GMST_AprMAr.RData"))
    m = r["models.ama.fullforced"]
    years = np.arange(851, 851 + m.shape[0])
    v = m.values.astype(float)
    # anomalise: subtract per-column 1961-1990 mean
    sel = (years >= REF_START) & (years <= REF_END)
    ref = np.nanmean(v[sel], axis=0)
    v = v - ref
    return years, v, list(m.columns)


def load_models_control():
    """CMIP5 piControl GMST (Apr-Mar), shape (1198, 29), rows have model-specific
    start/end (NAs elsewhere). Absolute Kelvin values."""
    r = pyreadr.read_r(os.path.join(DATA_ROOT, "Models_ctrl_GMST_AprMar.RData"))
    c = r["ctl.ama"]
    return c.values.astype(float), list(c.columns)


def load_instrumental():
    """Cowtan & Way HadCRUT4 kriged Apr-Mar GMST anomaly, (year, value)."""
    path = os.path.join(DATA_ROOT, "had4_krig_ama_v2_0_0.txt")
    if not os.path.exists(path):
        path = r"E:\scisolvebench-data\raw\pages2k_2019\work_dir\data\authors_figshare\input\had4_krig_ama_v2_0_0.txt"
    arr = np.loadtxt(path)
    return arr[:, 0].astype(int), arr[:, 1]


def load_danda():
    """D&A residual ensemble objects from DandA_CESM_ens_30-200_1318.RData."""
    r = pyreadr.read_r(os.path.join(DATA_ROOT, "DandA_CESM_ens_30-200_1318.RData"))
    da_all = r["da.cesm.all.ens.14.30.200"].values.astype(float)      # (1001, 7000)
    da_volc = r["da.cesm.volc.ens.14.30.200"].values.astype(float)    # (3003, 7000)
    resid = r["da.cesm.all.ens.14.30.200.resid"].values.astype(float).ravel()  # (7000,)
    ctl_var = r["models.ctl.var.30.200"].values.astype(float).ravel()          # (42,)
    return da_all, da_volc, resid, ctl_var


def load_ar_noise():
    """AR-noise proxy reconstructions for PCR/CPS/PAI (2000, 3000)."""
    r = pyreadr.read_r(os.path.join(DATA_ROOT, "recons.PCP.ARnoise.RData"))
    return r["noise.full.ensemble"].values.astype(float)
