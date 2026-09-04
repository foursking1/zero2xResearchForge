# -*- coding: utf-8 -*-
"""
DeepDISC JADES photo-z catalog verification.

Task: 2510.27032_deepdisc_jwst_photoz
Frozen catalog: F:/dataset/astro/2510.27032_deepdisc_jwst_photoz/jades_photoz_catalog.csv.gz

Claims tested (paper arXiv:2510.27032, Merz et al. 2026):
  A1: probabilistic photo-z catalog for all JADES DR2 GOODS-S photometric sources
      (~94,000 rows; point estimate = PDF mode + 68/95/99% CI).
  A2 (quality, NOT directly testable here): DeepDISC test N=298 scatter IQR=0.0311,
      outlier fraction eta=0.0503, bias=0.0035; vs EAZY (IQR=0.0403/eta=0.1242) and
      EAZY+HST (IQR=0.0198/eta=0.0705).
"""
import os
import json
import numpy as np
import pandas as pd

DATA = r"F:/dataset/astro/2510.27032_deepdisc_jwst_photoz"
df = pd.read_csv(os.path.join(DATA, "jades_photoz_catalog.csv.gz"), compression="gzip")

outdir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
os.makedirs(outdir, exist_ok=True)

n = len(df)
mode = df["z_phot_mode"].to_numpy()
l68, u68 = df["l68"].to_numpy(), df["u68"].to_numpy()
l95, u95 = df["l95"].to_numpy(), df["u95"].to_numpy()
l99, u99 = df["l99"].to_numpy(), df["u99"].to_numpy()
forced = df["forced"].to_numpy(dtype=bool)
spec_rep = df["spec_rep"].to_numpy()

# ----------------------------------------------------------------------------
# 1. Structure / scale
# ----------------------------------------------------------------------------
scale = {
    "rows": int(n),
    "columns": list(df.columns),
    "n_unique_ID": int(df["ID"].nunique()),
    "n_duplicate_ID": int(df["ID"].duplicated().sum()),
}

# ----------------------------------------------------------------------------
# 2. Self-consistency
# ----------------------------------------------------------------------------
self_cons = {}
# (a) mode inside 68% CI
self_cons["mode_in_68"] = float(np.mean((l68 <= mode) & (mode <= u68)))
# (b) monotonicity: l68>=l95>=l99  and  u68<=u95<=u99
self_cons["l_monotone"] = float(np.mean((l68 >= l95) & (l95 >= l99)))
self_cons["u_monotone"] = float(np.mean((u68 <= u95) & (u95 <= u99)))
self_cons["both_monotone"] = float(np.mean((l68 >= l95) & (l95 >= l99) & (u68 <= u95) & (u95 <= u99)))
# (c) pathological values
self_cons["n_z_negative"] = int((mode < 0).sum())
self_cons["n_l68_negative"] = int((l68 < 0).sum())
self_cons["n_ci_width_negative"] = int(((u68 - l68) < 0).sum()) + int(((u95 - l95) < 0).sum()) + int(((u99 - l99) < 0).sum())
self_cons["n_nan_any"] = int(df[["z_phot_mode", "l68", "u68", "l95", "u95", "l99", "u99"]].isna().sum().sum())
# width of CI
w68 = u68 - l68
w95 = u95 - l95
w99 = u99 - l99
self_cons["width68_mean"] = float(w68.mean())
self_cons["width95_mean"] = float(w95.mean())
self_cons["width99_mean"] = float(w99.mean())
# check CI containment: 68 inside 95 inside 99
self_cons["ci_nested"] = float(np.mean((l68 >= l95) & (u68 <= u95) & (l95 >= l99) & (u95 <= u99)))

# ----------------------------------------------------------------------------
# 3. Distribution and stratification
# ----------------------------------------------------------------------------
dist = {
    "z_mode_min": float(mode.min()),
    "z_mode_max": float(mode.max()),
    "z_mode_median": float(np.median(mode)),
    "z_mode_mean": float(np.mean(mode)),
    "z_mode_q1": float(np.percentile(mode, 25)),
    "z_mode_q3": float(np.percentile(mode, 75)),
    "frac_z_gt_6": float(np.mean(mode > 6)),
    "frac_z_gt_10": float(np.mean(mode > 10)),
    "frac_z_lt_0_1": float(np.mean(mode < 0.1)),
}
# histogram peaks (coarse)
hist, edges = np.histogram(mode, bins=100)
dist["hist_counts"] = [int(x) for x in hist]
dist["hist_edges"] = [float(x) for x in edges]

# CI width vs z bins
z_bins = [0, 0.5, 1, 1.5, 2, 3, 4, 6, 8, 12, 20]
labels = [f"{z_bins[i]}-{z_bins[i+1]}" for i in range(len(z_bins) - 1)]
df_t = df.copy()
df_t["zbin"] = pd.cut(mode, bins=z_bins, labels=labels, right=False)
strat = []
for lab in labels:
    sub = df_t[df_t["zbin"] == lab]
    if len(sub) == 0:
        continue
    strat.append({
        "zbin": lab, "n": int(len(sub)),
        "frac": float(len(sub) / n),
        "w68_mean": float((sub["u68"] - sub["l68"]).mean()),
        "w99_mean": float((sub["u99"] - sub["l99"]).mean()),
        "mode_median": float(sub["z_phot_mode"].median()),
    })

# forced stratification
forced_stats = {}
for flag in (False, True):
    sub = df_t[df_t["forced"] == flag]
    forced_stats[str(flag)] = {
        "n": int(len(sub)),
        "frac": float(len(sub) / n),
        "w68_mean": float((sub["u68"] - sub["l68"]).mean()),
        "w95_mean": float((sub["u95"] - sub["l95"]).mean()),
        "w99_mean": float((sub["u99"] - sub["l99"]).mean()),
        "mode_median": float(sub["z_phot_mode"].median()),
        "frac_z_gt_6": float(np.mean(sub["z_phot_mode"] > 6)),
    }

# spec_rep stats
sr_counts = df["spec_rep"].value_counts()
spec_rep_stats = {
    "n_unique": int(sr_counts.size),
    "top_values": [{"val": float(k), "count": int(v)} for k, v in sr_counts.head(8).items()],
    "max_value": float(df["spec_rep"].max()),
    "frac_zero": float(np.mean(spec_rep == 0)),
    "note": "spec_rep values are small-integer markers, not spectral redshifts. "
            "0 dominates (72.7%); 658.0 appears 2092x and is likely a group/representative index.",
}

# ----------------------------------------------------------------------------
# 4. Testability analysis (qualitative, but quantify what the catalog CAN/CANNOT do)
# ----------------------------------------------------------------------------
testability = {
    "directly_checkable_in_catalog": [
        "catalog row count (94,000)",
        "probabilistic structure (mode + 68/95/99 CI)",
        "CI self-consistency and monotonicity",
        "z_phot_mode distribution and forced/spec_rep stratification",
    ],
    "not_checkable_without_extra_data": [
        "bias / scatter IQR / outlier fraction eta (need spec-z test set, N=298/330)",
        "relative quality vs EAZY (need spec-z and matched filter set)",
        "image-based detection completeness (need NIRCam images + model weights)",
        "temperature/calibration of PDFs (need ensemble weights)",
    ],
    "required_extra_data": {
        "specz_test_set": "spectroscopic redshifts for the paper's test sample (N=298/330)",
        "nirCam_images": "JWST NIRCam images for JADES DR2 GOODS-S",
        "model_weights": "DeepDISC ensemble model weights / architecture",
        "eazy_outputs": "EAZY template-fit photo-zs on matched filter set",
    },
    "catalog_supports_claim_of_quality": False,
    "reason": "The catalog alone contains no spectral redshifts or model outputs; "
              "scatter/outlier/bias and 'comparable-or-better than EAZY' statements "
              "require an external spec-z sample and the EAZY comparison runs.",
}

# ----------------------------------------------------------------------------
# 5. Outputs
# ----------------------------------------------------------------------------
metrics = {
    "scale": scale,
    "self_consistency": self_cons,
    "distribution": dist,
    "strat_by_zbin": strat,
    "strat_by_forced": forced_stats,
    "spec_rep": spec_rep_stats,
    "testability": testability,
    "paper_anchor": {
        "paper_rows": 94000,
        "deepdisc_N": 298, "deepdisc_bias": 0.0035,
        "deepdisc_IQR": 0.0311, "deepdisc_eta": 0.0503,
        "eazy9_IQR": 0.0403, "eazy9_eta": 0.1242,
        "eazy_hst_IQR": 0.0198, "eazy_hst_eta": 0.0705,
    },
}

# evidence table
rows = []
rows.append({"check": "rows", "n": n, "stat": n, "pass_rate": 1.0 if n == 94000 else 0.0})
rows.append({"check": "mode_in_68", "n": n, "stat": self_cons["mode_in_68"], "pass_rate": self_cons["mode_in_68"]})
rows.append({"check": "l_monotone", "n": n, "stat": self_cons["l_monotone"], "pass_rate": self_cons["l_monotone"]})
rows.append({"check": "u_monotone", "n": n, "stat": self_cons["u_monotone"], "pass_rate": self_cons["u_monotone"]})
rows.append({"check": "ci_nested", "n": n, "stat": self_cons["ci_nested"], "pass_rate": self_cons["ci_nested"]})
rows.append({"check": "n_z_negative", "n": n, "stat": self_cons["n_z_negative"], "pass_rate": float(self_cons["n_z_negative"] == 0)})
rows.append({"check": "n_ci_width_negative", "n": n, "stat": self_cons["n_ci_width_negative"], "pass_rate": float(self_cons["n_ci_width_negative"] == 0)})
rows.append({"check": "n_nan_any", "n": n, "stat": self_cons["n_nan_any"], "pass_rate": float(self_cons["n_nan_any"] == 0)})
for s in strat:
    rows.append({"check": f"zbin_{s['zbin']}", "n": s["n"], "stat": s["w68_mean"], "pass_rate": float("nan")})
for flag, s in forced_stats.items():
    rows.append({"check": f"forced_{flag}_w68_mean", "n": s["n"], "stat": s["w68_mean"], "pass_rate": float("nan")})
    rows.append({"check": f"forced_{flag}_w99_mean", "n": s["n"], "stat": s["w99_mean"], "pass_rate": float("nan")})

ev = pd.DataFrame(rows)
ev.to_csv(os.path.join(outdir, "evidence_table.csv"), index=False)
with open(os.path.join(outdir, "metrics.json"), "w", encoding="utf-8") as f:
    json.dump(metrics, f, indent=2, default=float)

# ----------------------------------------------------------------------------
# 6. Figures
# ----------------------------------------------------------------------------
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
fig, axes = plt.subplots(1, 3, figsize=(15, 5))

ax = axes[0]
ax.hist(mode, bins=100, color="steelblue")
ax.axvline(np.median(mode), color="red", ls="--", label=f"median={np.median(mode):.2f}")
ax.set_xlabel("z_phot_mode")
ax.set_ylabel("N sources")
ax.set_title(f"photo-z mode distribution (N={n:,})")
ax.legend()

ax = axes[1]
# CI width vs z (hexbin)
ax.hexbin(mode, w99, gridsize=50, bins="log", cmap="viridis")
ax.set_xlabel("z_phot_mode")
ax.set_ylabel("99% CI width")
ax.set_title("99% CI width vs photo-z")

ax = axes[2]
# forced comparison of CI width
for flag, c in zip((False, True), ("steelblue", "darkred")):
    sub = df_t[df_t["forced"] == flag]
    ax.hist(sub["u68"] - sub["l68"], bins=60, alpha=0.5, color=c,
            label=f"forced={flag} (N={len(sub):,})")
ax.set_xlabel("68% CI width")
ax.set_ylabel("N sources")
ax.set_title("68% CI width by forced flag")
ax.legend()
fig.tight_layout()
fig.savefig(os.path.join(outdir, "figure.svg"))
fig.savefig(os.path.join(outdir, "figure.png"), dpi=150)

print(json.dumps(metrics, indent=2, default=float))
