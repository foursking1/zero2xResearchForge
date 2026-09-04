"""
Data loading / splitting / preprocessing.

- Reads the frozen ``data/url.csv`` (11,430 x 64, 63 features + is_phishing).
- Stratified split 75% train(+validation) / 25% test (same proportion as the
  CAA paper: "75% of the dataset for training and validation and the
  remaining 25% for testing").
- Per-feature affine scaling of each feature column into its domain range
  [min_i, max_i] defined by the frozen ``data/url_features.csv`` boundaries:
      scaled_i = (raw_i - min_i) / (max_i - min_i) in [0, 1]
  This is the range-scaling used by the constrained-attacks framework the
  paper builds on (attacks operate in the scaled space; feasibility of the
  raw feature values is equivalent to scaled values living in [0,1]).
  The scaling parameters come from the frozen constraints file only -- the
  test split is never used to fit anything.
"""

from __future__ import annotations

import os

import numpy as np
import pandas as pd
import torch

from constraints import URLConstraintSet, FEATURES

_URL_CSV_DEFAULT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "url.csv"
)


def load_url(csv_path: str = None) -> pd.DataFrame:
    if csv_path is None:
        csv_path = _URL_CSV_DEFAULT
    df = pd.read_csv(csv_path)
    assert df.shape == (11430, 64), f"unexpected shape {df.shape}"
    assert abs(float(df["is_phishing"].mean()) - 0.5) < 0.01
    return df


def train_validation_test_split(df, seed: int = 42):
    from sklearn.model_selection import train_test_split

    X = df.iloc[:, :-1]
    y = df["is_phishing"].to_numpy()
    # paper split: 75% train(+val) / 25% test
    X_trv, X_te, y_trv, y_te = train_test_split(
        X, y, test_size=0.25, random_state=seed, stratify=y
    )
    x_tr, x_va, y_tr, y_va = train_test_split(
        X_trv, y_trv, test_size=0.2, random_state=seed, stratify=y_trv
    )
    return (x_tr, y_tr), (x_va, y_va), (X_te, y_te)


class Preprocessor:
    """Affine [0,1] range scaling from the frozen url_features.csv bounds."""

    def __init__(self, features_csv: str = None):
        self.cset = URLConstraintSet(features_csv)
        self.fmin = self.cset.d_min.numpy().copy()
        self.fmax = self.cset.d_max.numpy().copy()
        rng = self.fmax - self.fmin
        self.range = np.where(rng > 0, rng, 1.0)
        self.fixed = rng <= 0

    def fit(self, X_tr=None):
        return self  # scaling is data-independent (frozen bounds)

    def transform(self, X):
        X = np.asarray(X, dtype=np.float64)
        return (X - self.fmin) / self.range

    def inverse(self, Z):
        Z = np.asarray(Z, dtype=np.float64)
        return Z * self.range + self.fmin

    def to_torch(self):
        return (torch.tensor(self.fmin),
                torch.tensor(self.fmax),
                torch.tensor(self.range))


def accuracy(y_true, y_pred):
    return float((np.asarray(y_pred) == np.asarray(y_true)).mean())