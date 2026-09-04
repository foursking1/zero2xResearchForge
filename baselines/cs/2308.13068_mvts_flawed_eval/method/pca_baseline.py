"""Simple unsupervised baselines --- no training beyond fitting linear statistics.

Primary simple baseline:
  * PCA reconstruction error  (z-score -> PCA -> reconstruct -> MSE residual)

Secondary simple baseline:
  * Squared Mahalanobis distance to the training centroid.

The paper we re-discover (arXiv:2308.13068) reports PCA (with z-score
preprocessing + a light score-smoothing post-processing) beating elaborate
deep-learning detectors on point-wise F1 for SWaT and PSM.
"""
from __future__ import annotations

import numpy as np
from sklearn.decomposition import PCA

from scripts.common import zscore_fit, zscore_transform, smooth_ma


class PCAReconstructionBaseline:
    """Reconstruction-error scorer using PCA fit on the training segment.

    score_std controls how channel residuals are combined:
      'cholstd' : divide each channel's squared error by its in-sample (train)
                  reconstruction RMSE -> per-channel standardized error
                  (default; principled channel equalization fit on train only).
      'uniform' : plain mean squared reconstruction error.
    """

    def __init__(self, variance: float = 0.95, smooth: int = 5, seed: int = 0,
                 score_std: str = "cholstd"):
        self.variance = variance
        self.smooth = smooth
        self.seed = seed
        self.score_std = score_std
        self.mean_ = None
        self.std_ = None
        self.pca_: PCA = None
        self.n_components_ = None
        self.channel_residual_scale_ = None

    def fit(self, train: np.ndarray):
        rng = np.random.default_rng(self.seed)
        self.mean_, self.std_ = zscore_fit(train)
        X = zscore_transform(train, self.mean_, self.std_)
        self.pca_ = PCA(n_components=self.variance, svd_solver="full", random_state=self.seed)
        self.pca_.fit(X)
        self.n_components_ = int(self.pca_.n_components_)
        if self.score_std == "cholstd":
            R = X - self.pca_.inverse_transform(self.pca_.transform(X))
            s = np.sqrt(np.mean(R ** 2, axis=0))
            s[s == 0] = 1.0
            self.channel_residual_scale_ = s
        return self

    def score(self, x: np.ndarray, smooth: int | None = None):
        xz = zscore_transform(x, self.mean_, self.std_)
        xh = self.pca_.inverse_transform(self.pca_.transform(xz))
        R = xz - xh
        if self.score_std == "cholstd":
            mse = np.mean((R / self.channel_residual_scale_) ** 2, axis=1)
        else:
            mse = np.mean(R ** 2, axis=1)
        w = self.smooth if smooth is None else smooth
        if w and w > 1:
            mse = smooth_ma(mse, w)
        return mse


class MahalanobisBaseline:
    """Squared Mahalanobis distance to the (z-scored) training centroid."""

    def __init__(self, smooth: int = 5):
        self.smooth = smooth
        self.mean_ = None
        self.std_ = None
        self.cov_inv_ = None
        self.centroid_ = None

    def fit(self, train: np.ndarray):
        self.mean_, self.std_ = zscore_fit(train)
        X = zscore_transform(train, self.mean_, self.std_)
        self.centroid_ = X.mean(axis=0)
        Xc = X - self.centroid_
        cov = np.cov(Xc.T) + 1e-6 * np.eye(X.shape[1])
        self.cov_inv_ = np.linalg.inv(cov)
        return self

    def score(self, x: np.ndarray, smooth: int | None = None):
        xz = zscore_transform(x, self.mean_, self.std_) - self.centroid_
        d2 = np.einsum("ij,jk,ik->i", xz, self.cov_inv_, xz)
        w = self.smooth if smooth is None else smooth
        if w and w > 1:
            d2 = smooth_ma(d2, w)
        return d2