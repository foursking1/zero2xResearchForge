# -*- coding: utf-8 -*-
"""
ExoNet TESS candidate vetting -- KOI discrimination & TESS migration reproduction.

Task: 2604.15560_exonet
All metrics recomputed from the frozen data under /mnt/d/project/paper-bench/tasks/astro/2604.15560_exonet/data/.

Claims tested (paper arXiv:2604.15560, Islam 2026):
  A1: KOI binary discriminator test AUC = 0.9549, accuracy = 86.3%  (paper used
      multimodal light-curve + stellar params; frozen data are catalog features only).
  A2: Migration to 4,720 unseen TESS PC candidates -> 1,754 >=70% high-confidence,
      1,098 >=85%, 52 HZ (200-400 K), 6 rocky (<1.6 R_Earth) HZ.
  A3: Temperature scaling T*=1.573 (not directly testable without logits/weights).

This script independently computes all reported numbers.
"""
import os
import json
import numpy as np
import pandas as pd

from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score, accuracy_score, confusion_matrix, roc_curve
from sklearn.calibration import calibration_curve

DATA = r"/mnt/d/project/paper-bench/tasks/astro/2604.15560_exonet/data"
RNG = 42
rng = np.random.default_rng(RNG)

# ----------------------------------------------------------------------------
# 1. Load data
# ----------------------------------------------------------------------------
koi = pd.read_csv(os.path.join(DATA, "koi_cumulative.csv"))
tess = pd.read_csv(os.path.join(DATA, "tess_toi_pc.csv"))
exo = pd.read_csv(os.path.join(DATA, "exonet_candidates.csv"))

# ----------------------------------------------------------------------------
# 2. Published catalogue count verification (B-dimension check)
# ----------------------------------------------------------------------------
pub_counts = {
    "rows": int(len(exo)),
    "n_ge_70": int((exo["planet_prob"] >= 0.70).sum()),
    "n_ge_85": int((exo["planet_prob"] >= 0.85).sum()),
    "n_hz": int(((exo["eq_temp_K"] >= 200) & (exo["eq_temp_K"] <= 400)).sum()),
    "n_rocky_hz": int(((exo["eq_temp_K"] >= 200) & (exo["eq_temp_K"] <= 400)
                       & (exo["radius_earth"] < 1.6)).sum()),
    "n_very_high_conf": int((exo["confidence"] == "Very High").sum()),
    "n_high_conf": int((exo["confidence"] == "High").sum()),
}

# Cross-verify published radius_earth / host_teff_K against TESS table values
merge_pub = exo.merge(tess, on="toi", how="left")
pm = merge_pub.dropna(subset=["pl_rade", "radius_earth"])
pm_teff = merge_pub.dropna(subset=["st_teff", "host_teff_K"])
cross = {
    "n_matched_toi": int(merge_pub["tid"].notna().sum()),
    "n_total_toi": int(len(exo)),
    "rade_median_abs_diff": float((pm["pl_rade"] - pm["radius_earth"]).abs().median()),
    "rade_pct_within_20pct": float(((pm["pl_rade"] - pm["radius_earth"]).abs() / pm["pl_rade"] < 0.2).mean()),
    "teff_median_abs_diff": float((pm_teff["st_teff"] - pm_teff["host_teff_K"]).abs().median()),
}

# ----------------------------------------------------------------------------
# 3. KOI population (binary labels)
# ----------------------------------------------------------------------------
koi_bin = koi[koi["koi_disposition"].isin(["CONFIRMED", "FALSE POSITIVE"])].copy()
koi_bin["label"] = (koi_bin["koi_disposition"] == "CONFIRMED").astype(int)
# dedupe by kepoi_name (already unique in this snapshot, kept for fidelity)
koi_bin = koi_bin.drop_duplicates(subset="kepoi_name").reset_index(drop=True)

FEATURES = ["koi_period", "koi_depth", "koi_duration", "koi_ror", "koi_srad",
            "koi_teq", "koi_steff", "koi_slogg", "koi_smet", "koi_kepmag"]

# ----------------------------------------------------------------------------
# 4. KOI discriminator (catalog features only)
# ----------------------------------------------------------------------------
def train_eval_model(X, y, test_frac=0.2, n_cv=5):
    """Train RandomForest on stratified train/test split + report CV AUC."""
    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=test_frac, stratify=y, random_state=RNG)
    # median impute on train, fill test with train medians
    medians = X_tr.median()
    X_tr_f = X_tr.fillna(medians)
    X_te_f = X_te.fillna(medians)

    clf = RandomForestClassifier(n_estimators=400, max_depth=None,
                                 min_samples_leaf=1, n_jobs=4, random_state=RNG)
    clf.fit(X_tr_f, y_tr)
    proba_te = clf.predict_proba(X_te_f)[:, 1]
    pred_te = clf.predict(X_te_f)

    auc_te = roc_auc_score(y_te, proba_te)
    acc_te = accuracy_score(y_te, pred_te)
    cm = confusion_matrix(y_te, pred_te)

    # stratified CV AUC (on full data) for robustness
    skf = StratifiedKFold(n_splits=n_cv, shuffle=True, random_state=RNG)
    X_f = X.fillna(X.median())
    cv_aucs, cv_accs = [], []
    for tr, va in skf.split(X_f, y):
        m = RandomForestClassifier(n_estimators=200, n_jobs=4, random_state=RNG)
        m.fit(X_f.iloc[tr], y.iloc[tr])
        p = m.predict_proba(X_f.iloc[va])[:, 1]
        cv_aucs.append(roc_auc_score(y.iloc[va], p))
        cv_accs.append(accuracy_score(y.iloc[va], (p >= 0.5).astype(int)))
    return {
        "n_train": int(len(X_tr)), "n_test": int(len(X_te)),
        "auc_test": float(auc_te), "acc_test": float(acc_te),
        "confusion_matrix": cm.tolist(),
        "auc_cv_mean": float(np.mean(cv_aucs)), "auc_cv_std": float(np.std(cv_aucs)),
        "acc_cv_mean": float(np.mean(cv_accs)),
        "model": clf,
        "X_test": X_te_f, "y_test": y_te, "proba_test": proba_te,
        "medians": medians,
    }

X = koi_bin[FEATURES]
y = koi_bin["label"]
res_full = train_eval_model(X, y)

# ----------------------------------------------------------------------------
# 5. Common-feature model (migration; uses feature subset available in TESS)
# ----------------------------------------------------------------------------
# Build planet radius in Earth radii for KOI: Rp = ror * srad * (1 Rsun in Re)
RSUN_RE = 109.076  # solar radius in Earth radii
koi_bin["planet_radius_earth"] = koi_bin["koi_ror"] * koi_bin["koi_srad"] * RSUN_RE

COMMON = ["period_days", "radius_earth", "host_teff_K", "host_logg", "mag"]
koi_common = pd.DataFrame({
    "period_days": koi_bin["koi_period"],
    "radius_earth": koi_bin["planet_radius_earth"],
    "host_teff_K": koi_bin["koi_steff"],
    "host_logg": koi_bin["koi_slogg"],
    "mag": koi_bin["koi_kepmag"],
})
tess_common = pd.DataFrame({
    "period_days": tess["pl_orbper"],
    "radius_earth": tess["pl_rade"],
    "host_teff_K": tess["st_teff"],
    "host_logg": tess["st_logg"],
    "mag": tess["st_tmag"],
})

# drop rows missing essential labels for train
keep_tr = koi_bin["label"].notna()
Xc = koi_common[keep_tr]
yc = koi_bin["label"][keep_tr]

res_common = train_eval_model(Xc, yc)

# --- Star-level (by kepid) CV to quantify multiplicity leakage --------------
# Planets around the same host share stellar features; ensure no star spans
# train and test folds.
kepids = koi_bin["kepid"].values
skf_star = StratifiedKFold(n_splits=5, shuffle=True, random_state=RNG)
Xc_f = Xc.fillna(Xc.median())
star_cv_aucs = []
for tr_idx, va_idx in skf_star.split(Xc_f, yc):
    tr_k = kepids[tr_idx]
    va_k = kepids[va_idx]
    # drop train rows whose kepid appears in the validation set
    overlap = np.isin(tr_k, va_k)
    tr_clean = tr_idx[~overlap]
    if len(tr_clean) < 500 or len(np.unique(va_k)) == 1:
        continue
    m = RandomForestClassifier(n_estimators=200, n_jobs=4, random_state=RNG)
    m.fit(Xc_f.iloc[tr_clean], yc.iloc[tr_clean])
    p = m.predict_proba(Xc_f.iloc[va_idx])[:, 1]
    star_cv_aucs.append(roc_auc_score(yc.iloc[va_idx], p))

star_leakage_check = {
    "star_grouped_cv_auc_mean": float(np.mean(star_cv_aucs)) if star_cv_aucs else None,
    "star_grouped_cv_auc_std": float(np.std(star_cv_aucs)) if star_cv_aucs else None,
    "n_folds": int(len(star_cv_aucs)),
    "note": "Random 80/20 split (as in paper) shares host stars across folds; "
            "star-grouped CV removes that leakage and gives a lower-bound AUC.",
}

# Fit on full common-feature data for migration
med_c = Xc.median()
clf_c = RandomForestClassifier(n_estimators=400, n_jobs=4, random_state=RNG)
clf_c.fit(Xc.fillna(med_c), yc)

# --- Platt (sigmoid) calibration on KOI holdout -----------------------------
from sklearn.linear_model import LogisticRegression
platt = LogisticRegression()
platt.fit(res_common["proba_test"].reshape(-1, 1), res_common["y_test"])
cal_proba_test = platt.predict_proba(res_common["proba_test"].reshape(-1, 1))[:, 1]
cal_auc = roc_auc_score(res_common["y_test"], cal_proba_test)

tess_X = tess_common.fillna(med_c)
tess_proba = clf_c.predict_proba(tess_X)[:, 1]
tess_proba_cal = platt.predict_proba(tess_proba.reshape(-1, 1))[:, 1]

# Migration counts
n_tess = len(tess)
tess_n_ge_70 = int((tess_proba >= 0.70).sum())
tess_n_ge_85 = int((tess_proba >= 0.85).sum())
tess_n_ge_70_cal = int((tess_proba_cal >= 0.70).sum())
tess_n_ge_85_cal = int((tess_proba_cal >= 0.85).sum())

# --- HZ / rocky subdivision of our own high-confidence set -----------------
# Approximate equilibrium temperature for TESS PCs.
# a[AU] = (P_days/365.25)^(2/3) * Mstar^(1/3);  rough main-seq Mstar(Teff).
# Teq = Teff * sqrt(Rstar / (2 a)); Rstar and a in SAME unit -> use Rsun.
RSUN_PER_AU = 215.032  # solar radii per AU
def eq_temp(row):
    if pd.isna(row["period_days"]) or pd.isna(row["host_teff_K"]):
        return np.nan
    P = row["period_days"]
    Teff = row["host_teff_K"]
    # rough main-sequence mass (solar masses), power law calibrated at 1 Msun/5772K
    M = (Teff / 5772.0) ** 3.0
    a_au = (P / 365.25) ** (2.0 / 3.0) * M ** (1.0 / 3.0)  # AU
    a_rsun = a_au * RSUN_PER_AU
    # stellar radius in Rsun from logg: R/Rsun = 10^((4.44 - logg + log10 M)/2)
    if pd.isna(row["host_logg"]):
        R = M ** 0.8  # rough
    else:
        R = 10.0 ** ((4.44 - row["host_logg"] + np.log10(max(M, 1e-3))) / 2.0)
    return Teff * np.sqrt(R / (2.0 * a_rsun))

tess_eval = tess_common.copy()
tess_eval["toi"] = tess["toi"].values
tess_eval["Teq_proxy"] = tess_eval.apply(eq_temp, axis=1)

sel70 = tess_proba >= 0.70
sel85 = tess_proba >= 0.85
sel70_cal = tess_proba_cal >= 0.70
hz_mask = (tess_eval["Teq_proxy"] >= 200) & (tess_eval["Teq_proxy"] <= 400)
rocky_mask = tess_eval["radius_earth"] < 1.6

migration = {
    "n_tess_pc": int(n_tess),
    "n_ge_70": tess_n_ge_70,
    "n_ge_85": tess_n_ge_85,
    "n_ge_70_cal": tess_n_ge_70_cal,
    "n_ge_85_cal": tess_n_ge_85_cal,
    "n_hz": int((sel70 & hz_mask).sum()),
    "n_rocky_hz": int((sel70 & hz_mask & rocky_mask).sum()),
    "n_hz_ge85": int((sel85 & hz_mask).sum()),
    "n_rocky_hz_ge85": int((sel85 & hz_mask & rocky_mask).sum()),
    "n_hz_cal": int((sel70_cal & hz_mask).sum()),
    "n_rocky_hz_cal": int((sel70_cal & hz_mask & rocky_mask).sum()),
    "n_with_teq_proxy": int(tess_eval["Teq_proxy"].notna().sum()),
    "n_with_radius": int(tess_eval["radius_earth"].notna().sum()),
}

# For matched candidates, also compare our Teq proxy against published eq_temp_K
mp = tess_eval.assign(proba=tess_proba).merge(
    exo[["toi", "eq_temp_K", "radius_earth"]], on="toi", how="left")
mp_sub = mp.dropna(subset=["Teq_proxy", "eq_temp_K"])
teq_comp = {
    "n_matched_teq": int(len(mp_sub)),
    "teq_proxy_median_abs_diff": float((mp_sub["Teq_proxy"] - mp_sub["eq_temp_K"]).abs().median()),
    "teq_proxy_pct_within_100K": float(((mp_sub["Teq_proxy"] - mp_sub["eq_temp_K"]).abs() < 100).mean()),
}

# ----------------------------------------------------------------------------
# 6. Calibration proxy (on KOI held-out; paper T*=1.573 not directly testable)
# ----------------------------------------------------------------------------
prob_true, prob_pred = calibration_curve(res_common["y_test"],
                                         res_common["proba_test"],
                                         n_bins=10, strategy="quantile")
calib = {
    "n_bins": int(len(prob_true)),
    "prob_pred": [float(x) for x in prob_pred],
    "prob_true": [float(x) for x in prob_true],
    "ece": float(np.mean(np.abs(prob_true - prob_pred))),
    "note": "T*=1.573 not directly testable without logits/weights; "
            "reliability curve on KOI held-out is a proxy only.",
}

# ----------------------------------------------------------------------------
# 7. Collate
# ----------------------------------------------------------------------------
metrics = {
    "koi_population": {
        "rows": int(len(koi)),
        "n_confirmed": int((koi["koi_disposition"] == "CONFIRMED").sum()),
        "n_fp": int((koi["koi_disposition"] == "FALSE POSITIVE").sum()),
        "n_candidate": int((koi["koi_disposition"] == "CANDIDATE").sum()),
        "n_binary_after_drop_dedupe": int(len(koi_bin)),
        "n_dup_kepoi_name": int(koi["kepoi_name"].duplicated().sum()),
    },
    "tess_population": {"rows": int(len(tess))},
    "published_catalog": pub_counts,
    "published_cross_check": cross,
    "discriminator_full_features": {
        "features": FEATURES,
        "auc_test": res_full["auc_test"],
        "acc_test": res_full["acc_test"],
        "n_train": res_full["n_train"],
        "n_test": res_full["n_test"],
        "confusion_matrix": res_full["confusion_matrix"],
        "auc_cv_mean": res_full["auc_cv_mean"],
        "auc_cv_std": res_full["auc_cv_std"],
        "acc_cv_mean": res_full["acc_cv_mean"],
    },
    "discriminator_common_features": {
        "features": COMMON,
        "auc_test": res_common["auc_test"],
        "acc_test": res_common["acc_test"],
        "n_train": res_common["n_train"],
        "n_test": res_common["n_test"],
        "confusion_matrix": res_common["confusion_matrix"],
        "auc_cv_mean": res_common["auc_cv_mean"],
        "auc_cv_std": res_common["auc_cv_std"],
        "acc_cv_mean": res_common["acc_cv_mean"],
        "auc_after_platt": float(cal_auc),
    },
    "star_leakage_check": star_leakage_check,
    "migration": migration,
    "teq_proxy_comparison": teq_comp,
    "calibration_proxy": calib,
    "paper_anchor": {
        "paper_test_auc": 0.9549,
        "paper_accuracy": 0.863,
        "paper_migration_n_ge70": 1754,
        "paper_migration_n_ge85": 1098,
        "paper_hz": 52,
        "paper_rocky_hz": 6,
        "paper_T_star": 1.573,
        "paper_n_tess": 4720,
        "paper_n_koi": 7585,
    },
}

# evidence table: per-row-ish summary (model level + catalog level)
rows = []
rows.append({"dataset": "koi_cumulative", "n": len(koi), "pos": 2747, "neg": 4839,
             "metric": "population", "value": len(koi)})
rows.append({"dataset": "koi_binary", "n": len(koi_bin), "pos": int(y.sum()),
             "neg": int((1 - y).sum()), "metric": "population_binary", "value": len(koi_bin)})
for tag, r in [("full_features", res_full), ("common_features", res_common)]:
    rows.append({"dataset": f"koi_{tag}", "n": r["n_train"] + r["n_test"],
                 "pos": "NA", "neg": "NA", "metric": "auc_test", "value": r["auc_test"]})
    rows.append({"dataset": f"koi_{tag}", "n": r["n_train"] + r["n_test"],
                 "pos": "NA", "neg": "NA", "metric": "acc_test", "value": r["acc_test"]})
    rows.append({"dataset": f"koi_{tag}", "n": r["n_train"] + r["n_test"],
                 "pos": "NA", "neg": "NA", "metric": "auc_cv", "value": r["auc_cv_mean"]})
rows.append({"dataset": "tess_toi_pc", "n": len(tess), "pos": "NA", "neg": "NA",
             "metric": "migration_ge70", "value": migration["n_ge_70"]})
rows.append({"dataset": "tess_toi_pc", "n": len(tess), "pos": "NA", "neg": "NA",
             "metric": "migration_ge85", "value": migration["n_ge_85"]})
rows.append({"dataset": "tess_toi_pc", "n": len(tess), "pos": "NA", "neg": "NA",
             "metric": "migration_ge70_cal", "value": migration["n_ge_70_cal"]})
rows.append({"dataset": "tess_toi_pc", "n": len(tess), "pos": "NA", "neg": "NA",
             "metric": "migration_ge85_cal", "value": migration["n_ge_85_cal"]})
rows.append({"dataset": "exonet_candidates", "n": len(exo), "pos": "NA", "neg": "NA",
             "metric": "pub_ge70", "value": pub_counts["n_ge_70"]})
rows.append({"dataset": "exonet_candidates", "n": len(exo), "pos": "NA", "neg": "NA",
             "metric": "pub_ge85", "value": pub_counts["n_ge_85"]})
rows.append({"dataset": "exonet_candidates", "n": len(exo), "pos": "NA", "neg": "NA",
             "metric": "pub_hz", "value": pub_counts["n_hz"]})
rows.append({"dataset": "exonet_candidates", "n": len(exo), "pos": "NA", "neg": "NA",
             "metric": "pub_rocky_hz", "value": pub_counts["n_rocky_hz"]})
rows.append({"dataset": "exonet_candidates", "n": len(exo), "pos": "NA", "neg": "NA",
             "metric": "pub_very_high_conf", "value": pub_counts["n_very_high_conf"]})

evidence = pd.DataFrame(rows)

outdir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
os.makedirs(outdir, exist_ok=True)
evidence.to_csv(os.path.join(outdir, "evidence_table.csv"), index=False)
with open(os.path.join(outdir, "metrics.json"), "w", encoding="utf-8") as f:
    json.dump(metrics, f, indent=2, default=float)

# ----------------------------------------------------------------------------
# 8. Figures: ROC + migration probability distribution
# ----------------------------------------------------------------------------
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# ROC for common-feature discriminator (used for migration)
fpr, tpr, _ = roc_curve(res_common["y_test"], res_common["proba_test"])
axes[0].plot(fpr, tpr, lw=2, label=f"KOI common-feature RF (AUC={res_common['auc_test']:.4f})")
axes[0].plot([0, 1], [0, 1], "--", color="gray", label="Chance")
axes[0].set_xlabel("False positive rate")
axes[0].set_ylabel("True positive rate")
axes[0].set_title("KOI discriminator ROC (catalog features)")
axes[0].legend(loc="lower right")

# Migration: probability distribution of our classifier on TESS PCs
axes[1].hist(tess_proba, bins=50, color="steelblue", alpha=0.8)
axes[1].axvline(0.70, color="red", ls="--", label="0.70 threshold")
axes[1].axvline(0.85, color="darkred", ls="--", label="0.85 threshold")
axes[1].set_xlabel("Our classifier probability on TESS PC candidates")
axes[1].set_ylabel("Count")
axes[1].set_title(f"Migration: TESS PC (n={len(tess)}) probability distribution")
axes[1].legend()
fig.tight_layout()
fig.savefig(os.path.join(outdir, "figure.svg"))
fig.savefig(os.path.join(outdir, "figure.png"), dpi=150)

# ROC data for calibration figure (reliability)
fig2, ax2 = plt.subplots(figsize=(5, 5))
ax2.plot(prob_pred, prob_true, "o-", label="Reliability curve")
ax2.plot([0, 1], [0, 1], "--", color="gray", label="Perfect calibration")
ax2.set_xlabel("Mean predicted probability")
ax2.set_ylabel("Observed frequency")
ax2.set_title(f"Calibration proxy (KOI held-out, ECE={calib['ece']:.4f})")
ax2.legend()
fig2.tight_layout()
fig2.savefig(os.path.join(outdir, "figure_calibration.svg"))

print(json.dumps(metrics, indent=2, default=float))
