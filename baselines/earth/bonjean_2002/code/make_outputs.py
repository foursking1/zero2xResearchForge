#!/usr/bin/env python3
"""Aggregate per-claim results into the required deliverables:
  results/evidence_table.csv   (指标名, 数值, 口径)
  results/metrics.json         (machine readable, same metric names)

All values are recomputed by the analysis scripts from the frozen data.
"""
import os
import json
import csv

OUT = os.path.join(os.path.dirname(__file__), "..", "results")
os.makedirs(OUT, exist_ok=True)


def load(name):
    with open(os.path.join(OUT, name)) as f:
        return json.load(f)


c01 = load("c01_H_sweep.json")
c02 = load("c02_momentum_balance.json")
c03 = load("c03_stdd.json")
c04 = load("c04_gcm.json")
tao = load("tao_validation.json")

# (metric, value, unit, definition/口径, claim, source)
rows = []

def add(metric, value, unit, note, claim, source):
    rows.append((metric, value, unit, note, claim, source))

# ---------------- C01 ----------------
z = c01
add("H_argmin_Mx_LP", z["H_argmin_Mx_LP"], "m",
    "H minimising ||Mx|| equatorial momentum residual (Eq.11a), Large&Pond tau, equator=mean rows -0.5/+0.5",
    "C01", "recomputed")
add("H_flat_1pct_dMx_LP", z["H_flat_1pct_dMx_LP"], "m",
    "smallest H for which |d||Mx||/dH| <= 1% of its max (practical lower bound)",
    "C01", "recomputed")
add("dMx_dH_at_H70_LP", z["dMx_dH_at_H70_LP"], "m^-1 s^-2",
    "derivative of ||Mx|| w.r.t. H evaluated at H=70 m (paper criterion: ~0)",
    "C01", "recomputed")
add("dMy_dH_at_H70_LP", z["dMy_dH_at_H70_LP"], "m^-1 s^-2",
    "derivative of ||My|| w.r.t. H evaluated at H=70 m",
    "C01", "recomputed")
add("Mx_at_H70_LP", z["Mx_at_H70_LP"], "m s^-2",
    "||Mx|| equatorial momentum residual at H=70 m (Large&Pond tau)",
    "C01", "recomputed")
add("My_at_H70_LP", z["My_at_H70_LP"], "m s^-2",
    "||My|| equatorial momentum residual at H=70 m",
    "C01", "recomputed")
add("Mx_rel_change_70_to_100_pct", z["Mx_rel_change_70_to_100_pct"], "%",
    "relative change of ||Mx|| between H=70 and H=100 (flatness)",
    "C01", "recomputed")
add("My_rel_change_70_to_100_pct", z["My_rel_change_70_to_100_pct"], "%",
    "relative change of ||My|| between H=70 and H=100",
    "C01", "recomputed")
add("ref_npz_H_argmin_Mx", 80, "m",
    "reference artifact momentum_balance_H_sweep.npz argmin of ||Mx||", "C01", "reference artifact")
add("ref_npz_dMx_dH_at_H70", -1.41e-10, "m^-1 s^-2",
    "reference artifact d||Mx||/dH at H=70", "C01", "reference artifact")
add("paper_H", 70, "m", "paper claim optimal depth scale", "C01", "paper citation")

# ---------------- C02 ----------------
add("c02_zonal_corr_P_W", c02["zonal"]["corr_P_W"], "dimensionless",
    "correlation along longitude between pressure-gradient term g*z_x and wind-stress term -tau_x/H at equator, H=70",
    "C02", "recomputed")
add("c02_zonal_ratio_rmsW_rmsP", c02["zonal"]["ratio_rmsW_rmsP"], "dimensionless",
    "RMS(|wind term|)/RMS(|pressure term|) at H=70 (1 => full magnitude compensation)",
    "C02", "recomputed")
add("c02_zonal_rmsM_rmsP", c02["zonal"]["ratio_rmsM_rmsP"], "dimensionless",
    "RMS(residual)/RMS(pressure term), pointwise (0 => perfect compensation)",
    "C02", "recomputed")
add("c02_zonal_mean_P", c02["zonal"]["mean_P"], "m s^-2",
    "basin-mean zonal pressure-gradient term g*z_x",
    "C02", "recomputed")
add("c02_zonal_mean_W", c02["zonal"]["mean_W"], "m s^-2",
    "basin-mean zonal wind-stress term -tau_x/H",
    "C02", "recomputed")
add("c02_zonal_mean_M", c02["zonal"]["mean_M"], "m s^-2",
    "basin-mean zonal residual",
    "C02", "recomputed")
add("c02_zonal_meanW_over_meanP", c02["zonal"]["ratio_meanW_absmeanP"], "dimensionless",
    "|mean wind term|/|mean pressure term| (basin-scale compensation ratio)",
    "C02", "recomputed")
add("c02_zonal_meanM_over_meanP", c02["zonal"]["ratio_absmeanM_absmeanP"], "dimensionless",
    "|mean residual|/|mean pressure term| (0 => perfect basin-scale balance)",
    "C02", "recomputed")
add("c02_merid_corr_P_W", c02["meridional"]["corr_P_W"], "dimensionless",
    "meridional correlation between pressure and wind terms at H=70",
    "C02", "recomputed")
add("c02_merid_ratio_rmsW_rmsP", c02["meridional"]["ratio_rmsW_rmsP"], "dimensionless",
    "meridional RMS(|wind|)/RMS(|pressure|)",
    "C02", "recomputed")

# ---------------- C03 ----------------
add("stdd_u", c03["stdd_u_cm_s"], "cm/s",
    "STDD between time-mean diagnostic velocity (0-30 m) and drifter mean u, full tropical Pacific on 0.5-deg grid",
    "C03", "recomputed")
add("stdd_v", c03["stdd_v_cm_s"], "cm/s",
    "STDD between time-mean diagnostic velocity and drifter mean v, full domain",
    "C03", "recomputed")
add("stdd_u_20S_20N", c03["stdd_u_20S_20N_cm_s"], "cm/s",
    "STDD u restricted to 20S-20N (matches reference npz 13.5)",
    "C03", "recomputed")
add("stdd_v_20S_20N", c03["stdd_v_20S_20N_cm_s"], "cm/s",
    "STDD v restricted to 20S-20N",
    "C03", "recomputed")
add("spatial_corr_u_mod_drifter", c03["spatial_corr_u"], "dimensionless",
    "spatial correlation of mean u fields (model vs drifter)",
    "C03", "recomputed")
add("spatial_corr_v_mod_drifter", c03["spatial_corr_v"], "dimensionless",
    "spatial correlation of mean v fields (model vs drifter)",
    "C03", "recomputed")
add("mean_bias_u", c03["mean_bias_u_cm_s"], "cm/s",
    "mean (u_model - u_drifter)",
    "C03", "recomputed")
add("mean_bias_v", c03["mean_bias_v_cm_s"], "cm/s",
    "mean (v_model - v_drifter)",
    "C03", "recomputed")
add("paper_stdd_u", 8.0, "cm/s", "paper claim STDD zonal", "C03", "paper citation")
add("paper_stdd_v", 3.0, "cm/s", "paper claim STDD meridional", "C03", "paper citation")
add("ref_npz_stdd_u", 13.46, "cm/s", "reference artifact mean_velocity_statistics.npz", "C03", "reference artifact")
add("ref_npz_stdd_v", 10.27, "cm/s", "reference artifact mean_velocity_statistics.npz", "C03", "reference artifact")

# ---------------- C04 ----------------
add("gcm_data_present", c04["gcm_velocity_field_present"], "boolean",
    "whether any GCM surface/velocity fields exist in frozen data", "C04", "data check")
add("gcm_conclusion", c04["conclusion"], "-",
    "verdict: claim not testable with frozen data", "C04", "data check")

# ---------------- Supplementary TAO ----------------
for site in ["165E", "170W", "140W", "110W"]:
    add(f"tao_u_corr_{site}", tao[f"u_corr_{site}"], "dimensionless",
        f"correlation model vs TAO zonal velocity at {site}",
        "C03-supp", "recomputed")
    add(f"tao_u_bias_{site}", tao[f"u_bias_{site}_m_s"], "m/s",
        f"mean bias (u_model - u_TAO) at {site}",
        "C03-supp", "recomputed")

# ---------- write CSV ----------
with open(os.path.join(OUT, "evidence_table.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["metric", "value", "unit", "口径_definition", "claim", "source"])
    for r in rows:
        w.writerow(r)

# ---------- write metrics.json ----------
metrics = {}
for metric, value, unit, note, claim, source in rows:
    metrics[metric] = {"value": value, "unit": unit, "definition": note, "claim": claim, "source": source}
with open(os.path.join(OUT, "metrics.json"), "w", encoding="utf-8") as f:
    json.dump(metrics, f, indent=2)

print(f"Wrote {len(rows)} metrics to evidence_table.csv and metrics.json")
