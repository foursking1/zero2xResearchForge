# -*- coding: utf-8 -*-
"""
Reproduction analysis for Wong/Fox et al. (2020) Frontiers in Marine Science
"Phytoplankton Growth and Productivity in the Western North Atlantic" (NAAMES).

Claims under test (TASK.md):
  C01  theta_opt (field) vs theta_PaM (model):  y = 0.85x + 12.34, r2 = 0.72, RMSE = 19.17
  C02  C_phyto^mod vs bbp(470):                  y = 14910x + 0.70, r2 = 0.61, RMSE = 16.31
  C03  Modeled NPP vs 14C overall:               y = 0.99x - 1.4, r2 = 0.80, RMSE = 6.03, n = 138
       Subarctic climax subset:                  y = 0.33x + 2.1, r2 = 0.85, RMSE = 6.43, n = 21
  C04  Depth-resolved modeled NPP profiles match discrete 14C measurements.

Only frozen data (read in place). All numbers are computed from data.
Paper values are quoted separately as "论文引用".
"""
import os
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"

import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats

DATA_ROOT = os.environ.get(
    "WONG2020_DATA",
    r"E:\scisolvebench-data\asset-data\datasets-v1\v1\wong_2020"
    r"\real_data_candidates\naames_observation_subset_v1",
)
FILES = os.path.join(DATA_ROOT, "files")
DIRS = os.path.join(DATA_ROOT, "directories")

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.environ.get("WONG2020_OUT", os.path.join(BASE, "results"))
FIG_DIR = os.path.join(BASE, "figures")
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(FIG_DIR, exist_ok=True)


def ols(x, y):
    """OLS regression y = slope*x + inter. Returns dict."""
    x = np.asarray(x, dtype=float); y = np.asarray(y, dtype=float)
    m = np.isfinite(x) & np.isfinite(y)
    x, y = x[m], y[m]
    n = len(x)
    if n < 3:
        return dict(n=int(n), slope=np.nan, inter=np.nan, r2=np.nan, rmse=np.nan)
    X = np.vstack([x, np.ones_like(x)]).T
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    slope, inter = beta
    yh = slope * x + inter
    r2 = 1 - np.sum((y - yh) ** 2) / np.sum((y - np.mean(y)) ** 2)
    rmse = np.sqrt(np.sum((y - yh) ** 2) / n)
    return dict(n=int(n), slope=float(slope), inter=float(inter),
                r2=float(r2), rmse=float(rmse))


def linregress_summary(x, y):
    r = ols(x, y)
    try:
        r["p_value"] = float(stats.linregress(np.asarray(x, float), np.asarray(y, float)).pvalue)
    except Exception:
        r["p_value"] = np.nan
    return r


CMAP = {'naames_1': 'NAAMES1', 'naames_2': 'NAAMES2',
        'naames_3': 'NAAMES3', 'naames_4': 'NAAMES4'}


def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1; dlon = lon2 - lon1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    return 2 * R * np.arcsin(np.sqrt(a))

# ----------------------------------------------------------------------------
# Load data
# ----------------------------------------------------------------------------
print("Loading data ...", flush=True)
bbp = pd.read_csv(os.path.join(FILES, "cphyto_bbp_all.csv"))
bbp["cruise"] = bbp["cruise"].map(CMAP)
bbp["dt"] = pd.to_datetime(bbp["datetime"], utc=True)
bbp["date"] = bbp["dt"].dt.date

chl = pd.read_csv(os.path.join(DIRS, "P03_ChlACS", "ChlACS_all_cruises.csv"))
chl["dt"] = pd.to_datetime(chl["datetime"], utc=True)
chl["date"] = chl["dt"].dt.date

pam = pd.read_csv(os.path.join(DIRS, "P10_theta_PaM", "theta_PaM_1min_all.csv"))
pam["dt"] = pd.to_datetime(pam["datetime"], utc=True)
pam["date"] = pam["dt"].dt.date

cmod = pd.read_csv(os.path.join(DIRS, "P12_NPP", "cphyto_mod_per_station.csv"))
cmod["date"] = pd.to_datetime(cmod["date"]).dt.date

prof = pd.read_csv(os.path.join(DIRS, "P12_NPP", "npp_profiles.csv"))
prof["date"] = pd.to_datetime(prof["date"]).dt.date

n14 = pd.read_csv(os.path.join(FILES, "npp_14c_all.csv"))
n14["date"] = pd.to_datetime(n14["date"].astype(str), format="%Y%m%d").dt.date

print("Loaded: bbp=%d chl=%d pam=%d cmod=%d prof=%d n14=%d"
      % (len(bbp), len(chl), len(pam), len(cmod), len(prof), len(n14)), flush=True)

PAPER = {
    "C01": {"slope": 0.85, "intercept": 12.34, "r2": 0.72, "rmse": 19.17},
    "C02": {"slope": 14910.0, "intercept": 0.70, "r2": 0.61, "rmse": 16.31},
    "C03_overall": {"slope": 0.99, "intercept": -1.4, "r2": 0.80, "rmse": 6.03, "n": 138},
    "C03_climax": {"slope": 0.33, "intercept": 2.1, "r2": 0.85, "rmse": 6.43, "n": 21},
}

metrics = {"paper_claimed": PAPER}
evidence_rows = []


def add_evidence(metric, value, definition):
    evidence_rows.append({"指标名": metric, "数值": value, "口径": definition})


# ============================================================================
# C01: theta_opt (C_phyto^bbp / Chl_ACS) vs theta_PaM
# ============================================================================
print("\n=== C01: theta_opt vs theta_PaM ===", flush=True)

bb1 = bbp.dropna(subset=["cphyto_bbp", "bbp470"])
bb1["minute"] = bb1["dt"].dt.floor("min")
bb1 = bb1.groupby(["cruise", "minute"]).agg(cph=("cphyto_bbp", "mean")).reset_index()
chl1 = chl.dropna(subset=["ChlACS_mg_m3"])
chl1["minute"] = chl1["dt"].dt.floor("min")
chl1 = chl1.groupby(["cruise", "minute"]).agg(chl=("ChlACS_mg_m3", "mean")).reset_index()
pam1 = pam.dropna(subset=["theta_PaM"])
pam1["minute"] = pam1["dt"].dt.floor("min")
pam1 = pam1.groupby(["cruise", "minute"]).agg(th=("theta_PaM", "mean"),
                                               PAR=("PAR", "mean")).reset_index()

c01 = bb1.merge(chl1, on=["cruise", "minute"], how="inner").merge(pam1, on=["cruise", "minute"], how="inner")
c01 = c01[(c01["chl"] > 0) & (c01["cph"] > 0) & (c01["PAR"] > 0)]
c01["theta_opt"] = c01["cph"] / c01["chl"]
c01 = c01[np.isfinite(c01["theta_opt"]) & np.isfinite(c01["th"])]
c01 = c01[(c01["theta_opt"] > 0) & (c01["theta_opt"] < 300) & (c01["th"] > 0) & (c01["th"] < 300)]
c01_reg = linregress_summary(c01["th"], c01["theta_opt"])
print("C01 1-min daytime: n=%d slope=%.4f inter=%.4f r2=%.4f rmse=%.4f"
      % (c01_reg["n"], c01_reg["slope"], c01_reg["inter"], c01_reg["r2"], c01_reg["rmse"]))

bbp_day = bbp.dropna(subset=["cphyto_bbp", "bbp470"]).groupby(["cruise", "date"])["cphyto_bbp"].mean().reset_index()
c01d = cmod.merge(bbp_day, on=["cruise", "date"], how="inner")
c01d = c01d[(c01d["ChlACS_mean"] > 0) & (c01d["cphyto_bbp"] > 0)]
c01d["theta_opt_day"] = c01d["cphyto_bbp"] / c01d["ChlACS_mean"]
c01d = c01d[np.isfinite(c01d["theta_opt_day"]) & np.isfinite(c01d["theta_PaM_mean"])]
c01d = c01d[(c01d["theta_opt_day"] > 0) & (c01d["theta_PaM_mean"] > 0)]
c01d_reg = linregress_summary(c01d["theta_PaM_mean"], c01d["theta_opt_day"])
print("C01 station-day: n=%d slope=%.4f inter=%.4f r2=%.4f rmse=%.4f"
      % (c01d_reg["n"], c01d_reg["slope"], c01d_reg["inter"], c01d_reg["r2"], c01d_reg["rmse"]))

# C01 on-station 50km station-day variant (restrict bbp/Chl/theta to within
# 50 km of the 14C station location on each station-day)
n14loc_c01 = n14.drop_duplicates(["cruise", "station", "date"])[["cruise", "station", "date", "lat", "lon"]]
n14loc_c01["lat"] = pd.to_numeric(n14loc_c01["lat"], errors="coerce")
n14loc_c01["lon"] = pd.to_numeric(n14loc_c01["lon"], errors="coerce")
st_daily_c01 = n14loc_c01.groupby(["cruise", "date"])[["lat", "lon"]].mean().reset_index()
cmod_c01 = cmod.merge(st_daily_c01, on=["cruise", "date"], how="inner")

bbp_c01 = bbp.dropna(subset=["cphyto_bbp", "lat", "lon"]).copy()
rows_c01 = []
for (cruise, date), g in bbp_c01.groupby(["cruise", "date"]):
    loc = st_daily_c01[(st_daily_c01["cruise"] == cruise) & (st_daily_c01["date"] == date)]
    if len(loc) == 0:
        continue
    g = g[haversine(g["lat"], g["lon"], loc["lat"].iloc[0], loc["lon"].iloc[0]) <= 50.0]
    if len(g) == 0:
        continue
    rows_c01.append(dict(cruise=cruise, date=date, cph_50=float(g["cphyto_bbp"].mean())))
if rows_c01:
    c01_50 = pd.DataFrame(rows_c01).merge(cmod_c01, on=["cruise", "date"], how="inner")
    chl_d = chl.dropna(subset=["ChlACS_mg_m3"]).groupby(["cruise", "date"])["ChlACS_mg_m3"].mean().reset_index()
    pam_d = pam.dropna(subset=["theta_PaM"]).groupby(["cruise", "date"])["theta_PaM"].mean().reset_index()
    c01_50 = c01_50.merge(chl_d, on=["cruise", "date"], how="inner").merge(pam_d, on=["cruise", "date"], how="inner")
    c01_50 = c01_50[(c01_50["cph_50"] > 0) & (c01_50["ChlACS_mg_m3"] > 0)]
    c01_50["theta_opt_50"] = c01_50["cph_50"] / c01_50["ChlACS_mg_m3"]
    c01_50 = c01_50[np.isfinite(c01_50["theta_opt_50"]) & np.isfinite(c01_50["theta_PaM"])]
    c01_50 = c01_50[(c01_50["theta_opt_50"] > 0) & (c01_50["theta_opt_50"] < 300) & (c01_50["theta_PaM"] > 0)]
    c01_50_reg = linregress_summary(c01_50["theta_PaM"], c01_50["theta_opt_50"])
    print("C01 station-day 50km on-station: n=%d slope=%.4f inter=%.4f r2=%.4f rmse=%.4f"
          % (c01_50_reg["n"], c01_50_reg["slope"], c01_50_reg["inter"], c01_50_reg["r2"], c01_50_reg["rmse"]))
    metrics["c01_station_day_50km"] = c01_50_reg
    for k, v in [("slope", c01_50_reg["slope"]), ("inter", c01_50_reg["inter"]),
                 ("r2", c01_50_reg["r2"]), ("rmse", c01_50_reg["rmse"])]:
        add_evidence("C01_theta_opt_vs_theta_PaM_%s_stationday50km" % k, round(v, 4),
                     "OLS; station-day on-station (50km) means; theta_opt=cphyto_bbp/ChlACS")
    add_evidence("C01_theta_opt_vs_theta_PaM_n_stationday50km", int(c01_50_reg["n"]), "station-days")

metrics["c01_1min_daytime"] = c01_reg
metrics["c01_station_day"] = c01d_reg
for k, v in [("slope", c01_reg["slope"]), ("inter", c01_reg["inter"]),
             ("r2", c01_reg["r2"]), ("rmse", c01_reg["rmse"])]:
    add_evidence("C01_theta_opt_vs_theta_PaM_%s_1min" % k, round(v, 4),
                 "OLS; y=theta_opt=C_phyto^bbp/ChlACS, x=theta_PaM; 1-min daytime bins")
add_evidence("C01_theta_opt_vs_theta_PaM_n_1min", int(c01_reg["n"]), "1-min matched pairs")
add_evidence("C01_paper_anchor", "slope 0.85, inter 12.34, r2 0.72, rmse 19.17", "论文引用")
for k, v in [("slope", c01d_reg["slope"]), ("inter", c01d_reg["inter"]),
             ("r2", c01d_reg["r2"]), ("rmse", c01d_reg["rmse"])]:
    add_evidence("C01_theta_opt_vs_theta_PaM_%s_stationday" % k, round(v, 4),
                 "OLS; station-day means (cmod x bbp daily)")
add_evidence("C01_theta_opt_vs_theta_PaM_n_stationday", int(c01d_reg["n"]), "station-days")

# ============================================================================
# C02: C_phyto^mod vs bbp(470)
# ============================================================================
print("\n=== C02: C_phyto^mod vs bbp(470) ===", flush=True)

n14loc = n14.drop_duplicates(["cruise", "station", "date"])[["cruise", "station", "date", "lat", "lon"]]
n14loc["lat"] = pd.to_numeric(n14loc["lat"], errors="coerce")
n14loc["lon"] = pd.to_numeric(n14loc["lon"], errors="coerce")
st_daily = n14loc.groupby(["cruise", "date"])[["lat", "lon"]].mean().reset_index()
cmod2 = cmod.merge(st_daily, on=["cruise", "date"], how="inner")
cmod2["lat"] = pd.to_numeric(cmod2["lat"], errors="coerce")
cmod2["lon"] = pd.to_numeric(cmod2["lon"], errors="coerce")

bbp2 = bbp.dropna(subset=["bbp470"]).copy()
bbp2 = bbp2[bbp2["bbp470"] > 0]

rows = []
for (cruise, date), g in bbp2.groupby(["cruise", "date"]):
    loc = st_daily[(st_daily["cruise"] == cruise) & (st_daily["date"] == date)]
    if len(loc) == 0:
        continue
    g = g[haversine(g["lat"], g["lon"], loc["lat"].iloc[0], loc["lon"].iloc[0]) <= 50.0]
    if len(g) == 0:
        continue
    rows.append(dict(cruise=cruise, date=date,
                     bbp_mean=float(g["bbp470"].mean()),
                     bbp_med=float(g["bbp470"].median()),
                     n_bbp=len(g)))
bb_d = pd.DataFrame(rows)
cc = cmod2.merge(bb_d, on=["cruise", "date"], how="inner")
cc = cc[cc["PAR_mean"] > 0]
c02_best = linregress_summary(cc["bbp_mean"], cc["C_phyto_mod"])
print("C02 50km on-station, PAR>0: n=%d slope=%.1f inter=%.4f r2=%.4f rmse=%.2f"
      % (c02_best["n"], c02_best["slope"], c02_best["inter"], c02_best["r2"], c02_best["rmse"]))

metrics["c02_50km_stationday_par0"] = c02_best
for k, v in [("slope", c02_best["slope"]), ("inter", c02_best["inter"]),
             ("r2", c02_best["r2"]), ("rmse", c02_best["rmse"])]:
    add_evidence("C02_cphyto_mod_vs_bbp470_%s" % k, round(v, 4),
                 "OLS; y=C_phyto_mod (cmod station), x=bbp470 mean within 50km of station, PAR>0")
add_evidence("C02_cphyto_mod_vs_bbp470_n", int(c02_best["n"]), "station-days")
add_evidence("C02_paper_anchor", "slope 14910, inter 0.70, r2 0.61, rmse 16.31", "论文引用")

# ============================================================================
# C03: Modeled NPP vs 14C incubations (light-level matching)
# ============================================================================
print("\n=== C03: NPP vs 14C ===", flush=True)

prof["station"] = prof["station"].astype(str)
n14["station"] = n14["station"].astype(str)


def map_st(cr, st):
    if cr == "NAAMES2" and st in ("4a", "4b", "4c"):
        return "4"
    if cr == "NAAMES3" and st == "unknown":
        return "6"
    return st


n14["pstation"] = [map_st(c, s) for c, s in zip(n14["cruise"], n14["station"])]

prof_by = {}
for (cr, st), g in prof.groupby(["cruise", "station"]):
    prof_by[(cr, st)] = g


def get_profile(cr, st, dstr):
    g = prof_by.get((cr, st))
    if g is None or len(g) == 0:
        return None
    dates = sorted(g["date"].unique())
    best, best_d = None, 1e9
    for d in dates:
        sub = g[g["date"] == d]
        if sub["NPP_z"].max() <= 0:
            continue
        dd = abs(pd.Timestamp(d) - pd.Timestamp(dstr)).days
        if dd < best_d:
            best_d, best = dd, d
    if best is None:
        return None
    return g[g["date"] == best].sort_values("z")


def match_npp(row, mode="light"):
    prof_ = get_profile(row["cruise"], row["pstation"], row["date"])
    if prof_ is None or len(prof_) < 3:
        return np.nan
    z = prof_["z"].to_numpy(float)
    if mode == "light":
        par0 = prof_["PAR_z"].iloc[0]
        if not np.isfinite(par0) or par0 <= 0:
            return np.nan
        lf = prof_["PAR_z"].to_numpy(float) / par0
        target = row["lightlevel"] / 100.0
        i = int(np.argmin(np.abs(lf - target)))
    else:
        i = int(np.argmin(np.abs(z - row["depth"])))
    return prof_["NPP_z"].iloc[i]


n14["NPP_mod_light"] = n14.apply(lambda r: match_npp(r, "light"), axis=1)
n14["NPP_mod_depth"] = n14.apply(lambda r: match_npp(r, "depth"), axis=1)

mm = n14[np.isfinite(n14["NPP_mod_light"]) & (n14["NPP_mod_light"] > 0)].copy()
mm = mm[np.isfinite(mm["NPP_14C"]) & (mm["NPP_14C"] > 0)]
print("C03 light-matched n=%d (14C>0, model>0)" % len(mm))

climax_keys = {("NAAMES2", "3"), ("NAAMES2", "4a"), ("NAAMES2", "4b")}
mm["is_climax"] = [(cr, st) in climax_keys for cr, st in zip(mm["cruise"], mm["station"])]

c03_all = linregress_summary(mm["NPP_mod_light"], mm["NPP_14C"])
c03_nonclimax = linregress_summary(mm.loc[~mm["is_climax"], "NPP_mod_light"],
                                   mm.loc[~mm["is_climax"], "NPP_14C"])
c03_climax = linregress_summary(mm.loc[mm["is_climax"], "NPP_mod_light"],
                                mm.loc[mm["is_climax"], "NPP_14C"])
for name, r in [("ALL", c03_all), ("NONCLIMAX", c03_nonclimax), ("CLIMAX", c03_climax)]:
    print("C03 %s (y=14C, x=model): n=%d slope=%.3f inter=%.2f r2=%.3f rmse=%.2f"
          % (name, r["n"], r["slope"], r["inter"], r["r2"], r["rmse"]))

metrics["c03_light_all"] = c03_all
metrics["c03_light_nonclimax"] = c03_nonclimax
metrics["c03_light_climax"] = c03_climax
for k, v in [("slope", c03_nonclimax["slope"]), ("inter", c03_nonclimax["inter"]),
             ("r2", c03_nonclimax["r2"]), ("rmse", c03_nonclimax["rmse"])]:
    add_evidence("C03_overall_NPP_14C_vs_mod_%s" % k, round(v, 4),
                 "OLS; y=14C, x=model NPP at light-matching depth; all matched except 3 climax stations")
add_evidence("C03_overall_n", int(c03_nonclimax["n"]), "matched samples (paper n=138)")
add_evidence("C03_overall_paper_anchor", "slope 0.99, inter -1.4, r2 0.80, rmse 6.03, n 138", "论文引用")
for k, v in [("slope", c03_climax["slope"]), ("inter", c03_climax["inter"]),
             ("r2", c03_climax["r2"]), ("rmse", c03_climax["rmse"])]:
    add_evidence("C03_climax_NPP_14C_vs_mod_%s" % k, round(v, 4),
                 "OLS; NAAMES2 stations 3,4a,4b (subarctic climax transition)")
add_evidence("C03_climax_n", int(c03_climax["n"]), "matched samples (paper n=21)")
add_evidence("C03_climax_paper_anchor", "slope 0.33, inter 2.1, r2 0.85, rmse 6.43, n 21", "论文引用")

# ---- C03 / C04 figures ----
fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))
ax = axes[0]
ax.scatter(mm.loc[~mm["is_climax"], "NPP_mod_light"], mm.loc[~mm["is_climax"], "NPP_14C"],
           s=20, alpha=0.6, label="other stations")
ax.scatter(mm.loc[mm["is_climax"], "NPP_mod_light"], mm.loc[mm["is_climax"], "NPP_14C"],
           s=30, color="red", alpha=0.8, label="subarctic climax (N2 st 3,4a,4b)")
xl = np.linspace(0, max(mm["NPP_mod_light"].max(), 1), 50)
ax.plot(xl, c03_all["slope"] * xl + c03_all["inter"], "k-", lw=1, label="all fit")
ax.plot(xl, c03_climax["slope"] * xl + c03_climax["inter"], "r--", lw=1, label="climax fit")
ax.plot([0, max(xl)], [0, max(xl)], "k:", lw=0.8, label="1:1")
ax.set_xlabel("Model NPP (mg C m$^{-3}$ d$^{-1}$)")
ax.set_ylabel("14C NPP (mg C m$^{-3}$ d$^{-1}$)")
ax.set_title("C03: model vs 14C (light-matched)")
ax.legend(fontsize=8)
ax.grid(alpha=0.3)

ax = axes[1]
n14d = n14[np.isfinite(n14["NPP_mod_depth"]) & (n14["NPP_mod_depth"] > 0)]
ax.scatter(n14d["NPP_14C"], n14d["depth"], s=25, c="gray", edgecolors="k", linewidths=0.3, zorder=5, label="14C")
for (cr, st), g in prof.groupby(["cruise", "station"]):
    for d in g["date"].unique():
        sub = g[g["date"] == d].sort_values("z")
        if sub["NPP_z"].max() <= 0:
            continue
        ax.plot(sub["NPP_z"], sub["z"], lw=0.8, color="k", alpha=0.3)
ax.set_ylim(120, 0)
ax.set_xlabel("NPP (mg C m$^{-3}$ d$^{-1}$)")
ax.set_ylabel("Depth (m)")
ax.set_title("C04: model NPP profiles vs 14C depths")
ax.legend(fontsize=8)
ax.grid(alpha=0.3)
fig.tight_layout()
fig.savefig(os.path.join(FIG_DIR, "fig_c03_c04.png"), dpi=150)
plt.close(fig)
print("Saved fig_c03_c04.png", flush=True)

# ============================================================================
# C04: depth-resolved profiles - aggregate metrics
# ============================================================================
print("\n=== C04: depth-resolved NPP ===", flush=True)
n14d = n14[np.isfinite(n14["NPP_mod_depth"]) & (n14["NPP_mod_depth"] > 0)].copy()
n14d = n14d[np.isfinite(n14d["NPP_14C"]) & (n14d["NPP_14C"] > 0)]
n14d["ratio"] = n14d["NPP_mod_depth"] / n14d["NPP_14C"]
resid = n14d["NPP_14C"] - n14d["NPP_mod_depth"]
c04 = {
    "n_matched": int(len(n14d)),
    "median_model_over_14C": float(n14d["ratio"].median()),
    "mean_model_over_14C": float(n14d["ratio"].mean()),
    "pct_within_2x": float((n14d["ratio"].between(0.5, 2).mean()) * 100),
    "pct_within_3x": float((n14d["ratio"].between(1 / 3, 3).mean()) * 100),
    "rmse": float(np.sqrt(np.mean(resid ** 2))),
    "mean_residual_14C_minus_mod": float(resid.mean()),
}
r04 = linregress_summary(n14d["NPP_mod_depth"], n14d["NPP_14C"])
c04.update({"reg_slope_14C_on_mod": r04["slope"], "reg_r2": r04["r2"],
            "pearson_r": float(np.corrcoef(n14d["NPP_mod_depth"], n14d["NPP_14C"])[0, 1])})
print("C04: n=%d median model/14C=%.2f %%within2x=%.1f %%within3x=%.1f pearson_r=%.3f"
      % (c04["n_matched"], c04["median_model_over_14C"], c04["pct_within_2x"],
         c04["pct_within_3x"], c04["pearson_r"]))
per_cruise = []
for cruise, g in n14d.groupby("cruise"):
    rr = linregress_summary(g["NPP_mod_depth"], g["NPP_14C"])
    per_cruise.append({"cruise": cruise, "n": int(len(g)),
                       "median_ratio": float(g["ratio"].median()),
                       "reg_slope": rr["slope"], "reg_r2": rr["r2"],
                       "rmse": rr["rmse"]})
    print("  %s: n=%d med_ratio=%.2f slope=%.3f r2=%.3f rmse=%.2f"
          % (cruise, len(g), g["ratio"].median(), rr["slope"], rr["r2"], rr["rmse"]))
metrics["c04_depth_profile"] = c04
metrics["c04_per_cruise"] = per_cruise
for k, v in c04.items():
    add_evidence("C04_%s" % k, round(v, 4), "depth-matched model NPP vs 14C; see metrics.json")
for pc in per_cruise:
    add_evidence("C04_%s_median_ratio" % pc["cruise"], round(pc["median_ratio"], 3),
                 "median model/14C, depth-matched, " + pc["cruise"])
add_evidence("C04_paper_anchor", "Figure 7: depth-resolved model profiles match discrete 14C", "论文引用")

# ============================================================================
# Assemble outputs
# ============================================================================
with open(os.path.join(OUT_DIR, "metrics.json"), "w", encoding="utf-8") as f:
    json.dump(metrics, f, indent=2, ensure_ascii=False)

evidence = pd.DataFrame(evidence_rows)
evidence.to_csv(os.path.join(OUT_DIR, "evidence_table.csv"), index=False, encoding="utf-8-sig")
print("\nSaved metrics.json and evidence_table.csv")
print("Done.")
