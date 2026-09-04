"""Baselines against which the five algorithms are compared.

1. mBM-class baseline -- a complete-data, multi-attribute regression fit on
   the complete-properties training subset only (the original mBM of TLG2020
   is a modified Boltzmann Machine that also requires a complete dataset to
   train on; it is not shipped in the frozen reproduction pack).  We use a
   deterministic least-squares / ridge model that, like the mBM, cannot
   exploit the incomplete archive but can use all six observed properties of
   the training planets.

2. PS-CP (Chen & Kipping 2017) -- the mass-radius relationship shipped in
   the NASA Exoplanet Archive's Planetary Systems Composite Parameters table
   (used by the paper as a reference estimator for the full-archive test).
"""
import numpy as np
from sklearn.linear_model import Ridge


# ----------------------------------------------------------------------
# 1) mBM-class baseline: complete-data regression model
# ----------------------------------------------------------------------
class MassRadiusBaseline:
    """Complete-data regression estimate of log10(M) from observed features.

    Trained on the (standardized) feature matrix of the *training* rows and
    used to predict the concealed masses of the test rows.  The model is a
    ridge regression including quadratic cross-terms of the (low-dimensional)
    log-features -- a moderately flexible, deterministic, fully reproducible
    stand-in for the complete-data mBM used in TLG2020 (which likewise cannot
    draw on incomplete observations).
    """

    def __init__(self, X_train, y_train, alpha=1.0):
        from sklearn.preprocessing import PolynomialFeatures
        pf = PolynomialFeatures(degree=2, include_bias=False)
        self.pf = pf.fit(X_train)
        self.reg = Ridge(alpha=alpha)
        self.reg.fit(pf.transform(X_train), y_train)

    def predict(self, X):
        return self.reg.predict(self.pf.transform(np.asarray(X)))


# ----------------------------------------------------------------------
# 2) Chen & Kipping (2017) median mass-radius relation (PS-CP)
# ----------------------------------------------------------------------
# Point-estimate parameter table from Chen & Kipping (2017) ApJ 834, 17,
# Table 3 (the published median relations, no intrinsic scatter).
_CK17 = [
    # (lo_R, hi_R, C0, C1)  with M = C0 * R^C1  (M in M_e, R in R_e)
    (0.0, 1.23, 0.9718, 3.584),
    (1.23, 14.31, 1.436, 1.698),
    (14.31, np.inf, 0.569, 0.881),
]


def chen_kipping_mass(radius_re):
    """Return predicted mass (M_e) for a radius (R_e) via the CK17 relation."""
    R = np.asarray(radius_re, dtype=float)
    M = np.full_like(R, np.nan)
    for lo, hi, c0, c1 in _CK17:
        m = (R >= lo) & (R < hi)
        M[m] = c0 * R[m] ** c1
    return M