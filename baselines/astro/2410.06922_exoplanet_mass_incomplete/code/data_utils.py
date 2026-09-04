"""Load, clean and split the frozen NASA Exoplanet Archive snapshot.

Implements section 2 of Lalande et al. (2024):

* the default PSCompPars rows are used (limits / no-error observations are
  already excluded from the archive's default values);
* five properties are log10-transformed;
* three datasets are built:
    - complete : all planets with the six properties observed,
    - full     : every planet (missing values kept),
    - extended : every planet with eight properties.
Only strictly positive values are kept for the logged properties (a few
archive entries carry zero / non-physical values and are treated as missing).
The SHA256 of the frozen CSV is verified on load.
"""
import hashlib

import numpy as np
import pandas as pd

import config

EXPECTED_SHA = "5D776826CD6EFD79A16328C60FC473A8C7DD0D90CACE35F848E6B60461AEDBE7"


def load_frozen_csv():
    """Return the raw frozen snapshot after SHA-256 verification."""
    raw = config.DATA_CSV.read_bytes()
    h = hashlib.sha256(raw).hexdigest().upper()
    assert h == EXPECTED_SHA, f"SHA256 mismatch: {h}"
    df = pd.read_csv(config.DATA_CSV, low_memory=False)
    return df


def _to_float_mask(df, cols):
    """Convert archive columns to float and return per-column NaN masks."""
    out = df[cols].apply(pd.to_numeric, errors="coerce")
    return out


def build_datasets(df):
    """Build and return the three {name: pd.DataFrame} with feature matrices."""
    # Drop non-positive / NaN for the logged properties (treated as missing).
    frank = df.reset_index(drop=True)

    # ----- complete : six properties all observed ---------------------------
    cdf = frank.copy()
    for c in config.SIX_COLS:
        v = pd.to_numeric(cdf[c], errors="coerce")
        cdf[c] = v
        if c in config.LOG_COLS:
            cdf.loc[v <= 0, c] = np.nan
    six_ok = cdf[config.SIX_COLS].notna().all(axis=1)
    complete_meta = cdf[six_ok].reset_index(drop=True)
    complete_feat = config.make_features(complete_meta, eight=False)

    # ----- full : all planets, six properties -------------------------------
    full_meta = frank.copy()
    for c in config.SIX_COLS:
        v = pd.to_numeric(full_meta[c], errors="coerce")
        full_meta[c] = v
        if c in config.LOG_COLS:
            full_meta.loc[v <= 0, c] = np.nan
    full_feat = config.make_features(full_meta, eight=False)

    # ----- extended : all planets, eight properties ------------------------
    ext_meta = frank.copy()
    for c in config.EIGHT_COLS:
        v = pd.to_numeric(ext_meta[c], errors="coerce")
        ext_meta[c] = v
        if c in config.LOG_COLS:
            ext_meta.loc[v <= 0, c] = np.nan
    ext_feat = config.make_features(ext_meta, eight=True)

    return {
        "complete": {"meta": complete_meta, "feat": complete_feat},
        "full": {"meta": full_meta, "feat": full_feat},
        "extended": {"meta": ext_meta, "feat": ext_feat},
    }


def split_test(indices, n_test=config.N_TEST, seed=config.SEED):
    """Deterministic (seeded) choice of n_test test rows out of indices."""
    rng = np.random.default_rng(seed)
    idx = np.asarray(indices)
    perm = rng.permutation(len(idx))
    test = idx[perm[:n_test]]
    train = idx[perm[n_test:]]
    return test, train


def summary(df):
    """Quick table of missing rates used for reporting."""
    rows = {}
    for c in df.columns:
        if c in ("pl_name", "discoverymethod", "disc_year", "ra", "dec", "st_metratio"):
            continue
        n = df[c].isna().sum() if pd.api.types.is_float_dtype(df[c]) else 0
        n += int((df[c] == "").sum()) if df[c].dtype == object else 0
        rows[c] = n
    return rows


if __name__ == "__main__":
    df = load_frozen_csv()
    ds = build_datasets(df)
    print(f"planets={len(df)}  complete={len(ds['complete']['meta'])}")