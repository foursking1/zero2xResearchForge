"""Central configuration for the exoplanet mass-imputation reproduction.

Everything here describes how the frozen NASA Exoplanet Archive snapshot
(data/pscomppars_2026-08-13.csv) is turned into the three datasets studied
by Lalande, Tasker & Doya (2024; arXiv:2410.06922):

  Dataset 1  "complete"   : planets with all six properties observed.
                            (paper used a 2018 snapshot w/ 550 planets;
                             this 2026 snapshot contains more of them --
                             a data fact, not an error.)
  Dataset 2  "full"       : all planets, six properties, missing values kept.
  Dataset 3  "extended"   : all planets, eight properties (adds eccentricity
                            and stellar metallicity).

The paper log-transforms five variables (radius, mass, period, equilibrium
temperature, stellar mass) and uses them as such; eccentricity, metallicity
and number-of-planets are used as-is.  All conventions follow the paper text.
"""
import math
from pathlib import Path

import pandas as pd

# --------------------------------------------------------------------------
# Paths
# --------------------------------------------------------------------------
CODE_DIR = Path(__file__).resolve().parent
AGENT_DIR = CODE_DIR.parent
TASK_DIR = AGENT_DIR.parent
DATA_CSV = TASK_DIR / "data" / "pscomppars_2026-08-13.csv"
RESULTS_DIR = AGENT_DIR / "results"
EVIDENCE_DIR = AGENT_DIR / "evidence"

# --------------------------------------------------------------------------
# Dataset definitions (as in the paper)
# --------------------------------------------------------------------------
SIX_COLS = ["pl_rade", "pl_masse", "pl_orbper", "pl_eqt", "st_mass", "sy_pnum"]
EIGHT_COLS = ["pl_rade", "pl_masse", "pl_orbper", "pl_orbeccen",
              "pl_eqt", "st_mass", "st_met", "sy_pnum"]
LOG_COLS = ["pl_rade", "pl_masse", "pl_orbper", "pl_eqt", "st_mass"]  # log10

# Feature names inside the matrices (fixed order used everywhere)
F6 = ["log_rade", "log_masse", "log_orbper", "log_eqt", "log_stmass", "nplanets"]
F8 = ["log_rade", "log_masse", "log_orbper", "ecc", "log_eqt",
      "log_stmass", "feh", "nplanets"]

# Map an archive column to the feature-matrix name (or None to keep col name)
_COL2FEAT = {"pl_rade": "log_rade", "pl_masse": "log_masse",
             "pl_orbper": "log_orbper", "pl_eqt": "log_eqt",
             "st_mass": "log_stmass", "pl_orbeccen": "ecc",
             "st_met": "feh", "sy_pnum": "nplanets"}


def make_features(df, eight=False):
    """Return the (n, p) transformed feature matrix with NaN for missing.

    log10 is applied to the five logged properties, other properties are kept
    as-is.  Only strictly-positive values are logged (others become NaN).
    """
    cols = EIGHT_COLS if eight else SIX_COLS
    data = {}
    for c in cols:
        name = _COL2FEAT[c]
        vals = df[c].astype(float)
        if c in LOG_COLS:
            pos = vals[vals > 0]
            lv = pd.Series(index=vals.index, dtype="float64")
            lv.loc[pos.index] = pos.apply(math.log10)
            data[name] = lv
        else:
            data[name] = vals
    return pd.DataFrame(data)

# --------------------------------------------------------------------------
# Protocol / hyper-parameters (all stated in the paper)
# --------------------------------------------------------------------------
SEED = 42                # random seed for the reproducible 150-test split
N_TEST = 150             # number of test planets (paper: TLG2020's 150)
K_KNN = 15               # kNN-Imputer k (paper: k = 15)
N_TREES = 20             # MissForest trees (paper: Ntrees = 20)
MICE_MAX_ITER = 10
MF_MAX_ITER = 10
GAIN_STEPS = 2500        # GAIN training iterations (paper: Niter = 2500)
GAIN_HINT = 0.9
GAIN_ALPHA = 100.0
KNKDE_NCAP = 20          # kNN x KDE neighbor cap (paper: Ncap = 20)
# kNN x KDE "temperature" multiplier used in the softmax distance weights
# w_i = softmax(-d_i / (s * tau)) where s = dispersion of the neighbour
# distances.  The paper fixes the softmax temperature tau = 50^-1 on its own
# distance scale; in our standardized feature space that literal value would
# collapse the weights onto the single nearest neighbour, contradicting the
# paper's own description of kNN x KDE averaging over the capped neighbours
# (giving rise to the mass "plateaus").  We therefore keep the temperature as
# a tunable *tightness parameter* acting on the local distance dispersion and
# fix it (not optimize it) to tau = 2, i.e. a mild distance taper over the
# capped 20-neighbourhood -- see report.md for the derivation and the
# robustness comparison (uniform vs arithmetic vs geometric).
KNKDE_TAU = 2.0