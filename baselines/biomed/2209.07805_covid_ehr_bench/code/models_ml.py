"""ML baselines (RandomForest / LightGBM / clinical-style logistic regression)
for the TJH early-mortality prediction task.

All fits use only the frozen training cohort. The frozen test set is scored
exactly once, after training, and never participates in fitting.
"""
from __future__ import annotations

import os
import pickle
import time

import lightgbm as lgb
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from common import SHARED_FEATURES
from preprocess import AggregateBuilder

RANDOM_STATE = 42
N_JOBS = 4  # bounded; n_jobs=-1 can hang thread pools on this host


class MLModels:
    """Container: holds fitted ML models and returns test probability vectors."""

    def __init__(self):
        self.rf = None
        self.lgbm = None
        self.clinical_lr = None
        self.lr_use_idx = None        # column indices (scaled raw) for the 3 lasts
        self.scaler = None
        self.feat_cols = None
        self.mask_cols = None

    def fit(self, train_df):
        builder = AggregateBuilder(feats=SHARED_FEATURES, window_hours=72.0)
        Xtr, ytr, _, _, _, self.scaler, self.mask_cols, self.feat_cols = builder.build(
            train_df, train_df.iloc[:0])
        raw_idx = [self.feat_cols.index(c) for c in self.feat_cols
                   if not c.endswith("__missing")]
        self.raw_idx = raw_idx
        Xtr_scaled = np.concatenate([
            self.scaler.transform(Xtr[:, raw_idx]),
            Xtr[:, [self.feat_cols.index(c) for c in self.mask_cols]],
        ], axis=1)

        self.rf = RandomForestClassifier(
            n_estimators=600, max_depth=None, min_samples_leaf=1,
            max_features="sqrt", random_state=RANDOM_STATE, n_jobs=N_JOBS)
        self.rf.fit(Xtr, ytr)

        self.lgbm = lgb.LGBMClassifier(
            n_estimators=800, learning_rate=0.03, num_leaves=15,
            min_child_samples=4, subsample=0.8, colsample_bytree=0.8,
            random_state=RANDOM_STATE, verbose=-1, n_jobs=N_JOBS)
        self.lgbm.fit(Xtr, ytr)

        # clinical-style baseline: plain logistic on the 3 last-observed labs
        last_cols = [f"{f}_last" for f in SHARED_FEATURES]
        lr_col_idx = [self.feat_cols.index(c) for c in last_cols]
        self.lr_pick_idx = [raw_idx.index(i) for i in lr_col_idx]   # in scaled-raw frame
        self.clinical_lr = LogisticRegression(C=1.0, max_iter=2000,
                                              random_state=RANDOM_STATE)
        self.clinical_lr.fit(Xtr_scaled[:, self.lr_pick_idx], ytr)
        self._fit = True
        return self

    def predict_proba(self, Xte, yte=None):
        """Return dict name -> test probability array. Xte built like builder."""
        raw_idx = self.raw_idx
        Xte_scaled = np.concatenate([
            self.scaler.transform(Xte[:, raw_idx]),
            Xte[:, [self.feat_cols.index(c) for c in self.mask_cols]],
        ], axis=1)
        return {
            "rf": self.rf.predict_proba(Xte)[:, 1],
            "lightgbm": self.lgbm.predict_proba(Xte)[:, 1],
            "clinical_logistic": self.clinical_lr.predict_proba(
                Xte_scaled[:, self.lr_pick_idx])[:, 1],
        }

    def save(self, path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as fh:
            pickle.dump(self, fh)


def build_all_rep(train_df, test_df):
    """Convenience: build aggregate representation for both splits.

    Returns Xtr, ytr, Xte, yte, pid_te, and the (train-fitted) scaler/cols.
    """
    builder = AggregateBuilder(feats=SHARED_FEATURES, window_hours=72.0)
    Xtr, ytr, Xte, yte, pid_te, scaler, mask_cols, feat_cols = builder.build(
        train_df, test_df)
    return Xtr, ytr, Xte, yte, pid_te, scaler, mask_cols, feat_cols


if __name__ == "__main__":
    from sklearn.metrics import roc_auc_score
    from common import load_raw
    train, test = load_raw()
    m = MLModels().fit(train)
    Xtr, ytr, Xte, yte, pid_te, *_ = build_all_rep(train, test)
    probas = m.predict_proba(Xte)
    for k, p in probas.items():
        print(k, "AUROC=%.4f" % roc_auc_score(yte, p))