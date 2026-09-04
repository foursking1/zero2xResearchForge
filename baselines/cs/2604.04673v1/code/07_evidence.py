"""
Assemble evidence_table.csv and metrics.json from all results.

Metrics keys are chosen to be stable and are mirrored 1:1 between the CSV
and the JSON. Each row: metric, value, unit, definition (caliber), source
(frozen_data | fresh_run | paper_citation).
"""
import csv, json
from pathlib import Path

import numpy as np

RES = Path(__file__).resolve().parent.parent / "results"
FROZEN = json.load(open(RES / "frozen_data_summary.json"))
HP = {}
if (RES / "highprecision_check.json").exists():
    HP = json.load(open(RES / "highprecision_check.json"))

rows = []  # (metric, value, unit, definition, source)


def add(metric, value, unit, definition, source):
    rows.append({
        "metric": metric,
        "value": value,
        "unit": unit,
        "definition": definition,
        "source": source,
    })


# ---------------- MLE risk (R01-R03) ----------------
for p in [5, 50, 100]:
    add(f"mle_risk_p{p}", float(p), "risk",
        f"MLE risk = p (minimax level), constant over ||theta||; frozen radial data confirms flat line at {p}",
        "theory+frozen")

# ---------------- BetaPrime max risk (R07-R09) ----------------
bp_frozen = {5: FROZEN["radial_p5"]["betaprime_risk_max"],
             50: FROZEN["radial_p50"]["betaprime_risk_max"],
             100: FROZEN["radial_p100"]["betaprime_risk_max"]}
for p in [5, 50, 100]:
    d = json.load(open(RES / f"radial_risk_p{p}_full.json"))
    bp_fresh = max(d["betaprime_risk"])
    add(f"betaprime_max_risk_p{p}", round(bp_frozen[p], 4), "risk",
        f"Max BetaPrime risk over sampled r; frozen data (r<=200/17/25) vs fresh (r=0..500)",
        "frozen_data")
    add(f"betaprime_max_risk_p{p}_fresh", round(bp_fresh, 4), "risk",
        "Max BetaPrime risk, fresh full-grid run r=0..500, N_mc=50k K_dir=10",
        "fresh_run")
    add(f"betaprime_exceeds_p_p{p}_fresh", bp_fresh > p, "bool",
        "BetaPrime max risk > minimax level p in fresh run", "fresh_run")

# ---------------- Fixed/dropout exceedance (C01-C03) ----------------
for p in [5, 50, 100]:
    d = json.load(open(RES / f"radial_risk_p{p}_full.json"))
    r = np.array(d["r_values"])
    fx = np.array(d["fixed_risk"])
    dp = np.array(d["dropout_risk"])
    bp = np.array(d["betaprime_risk"])
    add(f"fixed_max_risk_p{p}", round(fx.max(), 4), "risk",
        "Max fixed-scale BNN risk over r=0..500 (fresh)", "fresh_run")
    add(f"dropout_max_risk_p{p}", round(dp.max(), 4), "risk",
        "Max dropout BNN risk over r=0..500 (fresh)", "fresh_run")
    add(f"fixed_risk_at_r500_p{p}", round(fx[-1], 4), "risk",
        "Fixed-scale BNN risk at ||theta||=500 (fresh)", "fresh_run")
    add(f"dropout_risk_at_r500_p{p}", round(dp[-1], 4), "risk",
        "Dropout BNN risk at ||theta||=500 (fresh)", "fresh_run")
    add(f"fixed_exceeds_p_p{p}", bool(fx.max() > p), "bool",
        "Fixed-scale BNN max risk > p (fresh, r=0..500)", "fresh_run")
    add(f"dropout_exceeds_p_p{p}", bool(dp.max() > p), "bool",
        "Dropout BNN max risk > p (fresh, r=0..500)", "fresh_run")
    add(f"fixed_excess_over_p_p{p}", round(fx.max() - p, 4), "risk",
        "Max fixed-scale BNN excess over minimax level p", "fresh_run")
    add(f"dropout_excess_over_p_p{p}", round(dp.max() - p, 4), "risk",
        "Max dropout BNN excess over minimax level p", "fresh_run")
    # dropout between fixed and betaprime
    n = len(fx)
    between = sum(1 for i in range(n) if min(bp[i], fx[i]) <= dp[i] <= max(bp[i], fx[i]))
    add(f"dropout_between_pct_p{p}", round(between / n * 100, 1), "%",
        "Fraction of r where BetaPrime <= Dropout <= Fixed (fresh)", "fresh_run")

# frozen p=5 exceedance (C01)
add("fixed_exceeds_p_p5_frozen", True, "bool",
    "Frozen data: fixed_risk>5 for 172/201 r-points, first exceed at r=29, max 5.0315",
    "frozen_data")
add("fixed_max_risk_p5_frozen", round(FROZEN["radial_p5"]["fixed_risk_max"], 4), "risk",
    "Frozen data max fixed risk (r<=200)", "frozen_data")

# ---------------- High precision large-r checks ----------------
for p in [50, 100]:
    key = f"p{p}"
    if key in HP:
        for r_str, vals in HP[key].items():
            for est, v in vals.items():
                add(f"hp_p{p}_r{r_str}_{est}", round(v, 4), "risk",
                    f"High-precision risk (N_mc=200k, K_dir=30) at ||theta||={r_str}",
                    "fresh_run")

# ---------------- Shrinkage M_v sensitivity ----------------
if "shrinkage_mv_sensitivity_p5" in HP:
    for m_v, d in HP["shrinkage_mv_sensitivity_p5"].items():
        add(f"shrinkage_a_fixed_p5_s{int(d['s'][-1])}_mv{m_v}",
            round(d["a_fixed"][-1], 4), "a(s)",
            f"Fixed-scale shrinkage a(s) at s={d['s'][-1]:g} with M_v={m_v}",
            "fresh_run")

# ---------------- BetaPrime closed form ----------------
bpv = json.load(open(RES / "betaprime_shrinkage_verify.json"))
for p in [5, 50, 100]:
    add(f"betaprime_a0_p{p}", bpv[str(p)]["a0"], "a(s)",
        f"BetaPrime shrinkage a(0); expected 1/(p-1)={1/(p-1):.6f}",
        "fresh_run")
    add(f"betaprime_a_inf_p{p}", bpv[str(p)]["a_at_s"]["1e+06"], "a(s)",
        "BetaPrime shrinkage a(s) at s=1e6 (asymptote ~1)", "fresh_run")
    add(f"betaprime_monotone_p{p}", bpv[str(p)]["monotone_increasing"], "bool",
        "BetaPrime a(s) monotone increasing", "fresh_run")
    add(f"betaprime_bounded_p{p}", bpv[str(p)]["bounded_in_0_1"], "bool",
        "BetaPrime a(s) in (0,1)", "fresh_run")

# ---------------- Sparsity p=5 (C04) ----------------
sp = FROZEN["sparsity_p5_v2"]
add("betaprime_max_risk_sparsity_p5", round(sp["betaprime_max"], 4), "risk",
    "Max BetaPrime risk, sparsity experiment p=5, r in [0,2.5*sqrt(5)] (frozen v2)",
    "frozen_data")
for k, key in [(1, "hs_k1"), (2, "hs_k2"), (5, "hs_k5")]:
    if f"{key}_max" in sp:
        add(f"hs_k{k}_max_risk_p5_frozen", round(sp[f"{key}_max"], 4), "risk",
            f"Max Horseshoe risk at sparsity k={k}, p=5 (frozen v2, r<=5.59)", "frozen_data")
    if f"{key}_below_betaprime_pct" in sp:
        add(f"hs_k{k}_below_betaprime_pct_p5_frozen",
            round(sp[f"{key}_below_betaprime_pct"], 1), "%",
            f"Fraction of r where Horseshoe k={k} risk < BetaPrime risk (frozen v2)",
            "frozen_data")
spz = FROZEN["sparsity_p5_zz"]
add("hs_k5_max_risk_p5_frozen_zz", round(spz["hs_k5_max"], 4), "risk",
    "Max Horseshoe k=5 risk, p=5 (frozen zz run, r up to 20)", "frozen_data")

# fresh p=5 sparsity
try:
    spf = json.load(open(RES / "sparsity_p5_fresh.json"))
    for k, arr in spf["horseshoe_risk"].items():
        add(f"hs_k{k}_max_risk_p5_fresh", round(max(arr), 4), "risk",
            "Max Horseshoe risk, fresh run (reduced MC: 20 draws x 10 dirs, 1 chain)",
            "fresh_run")
except FileNotFoundError:
    pass

# fresh p=50/100 sparsity (dense k=p vs sparse k=1).
# Prefer the multi-chain _fresh.json run when available (3 chains, default config),
# else fall back to the reduced-MC 1-chain _dense1c.json run.
for p in [50, 100]:
    pfile = RES / f"sparsity_p{p}_fresh.json"
    mc_note = "fresh run (3 chains, default config)"
    if not pfile.exists():
        pfile = RES / f"sparsity_p{p}_dense1c.json"
        mc_note = "fresh reduced-MC run (10 draws x 5 dirs, 1 chain)"
    if not pfile.exists():
        continue
    dp = json.load(open(pfile))
    for k, arr in dp["horseshoe_risk"].items():
        add(f"hs_k{k}_max_risk_p{p}_fresh", round(max(arr), 4), "risk",
            f"Max Horseshoe risk p={p} k={k}, {mc_note}", "fresh_run")
    if str(p) in dp["horseshoe_risk"] and "1" in dp["horseshoe_risk"]:
        add(f"hs_dense_vs_sparse_ratio_p{p}",
            round(max(dp["horseshoe_risk"][str(p)]) / max(dp["horseshoe_risk"]["1"]), 2),
            "ratio", f"Ratio max risk dense(k=p) / sparse(k=1) at p={p}", "fresh_run")

# ---------------- SE check (r=500, multi-seed) ----------------
if (RES / "se_check.json").exists():
    se = json.load(open(RES / "se_check.json"))
    for p in ["5", "50", "100"]:
        for est in ["fixed", "dropout", "betaprime"]:
            d = se[p][est]
            add(f"se_p{p}_r500_{est}_mean", round(d["mean"], 4), "risk",
                f"Mean risk at r=500 over {d['n_seeds']} seeds (N_mc=50k, K_dir=10)",
                "fresh_run")
            add(f"se_p{p}_r500_{est}_se", round(d["se"], 4), "risk",
                "Empirical SE of risk estimate at r=500 across independent seeds",
                "fresh_run")
            add(f"se_p{p}_r500_{est}_excess_z", round((d["mean"] - int(p)) / d["se"], 2),
                "se_units",
                "Excess over minimax p in units of empirical SE at r=500", "fresh_run")

# ---------------- paper citation numbers ----------------
add("paper_hs_dense_risk_p5", 7.5, "risk",
    "Paper Section 5.2: Horseshoe risk at k=p=5 (dense) ~= 7.5", "paper_citation")
add("paper_hs_dense_risk_p50", 66.0, "risk",
    "Paper Section 5.2: Horseshoe risk at k=p=50 (dense) ~= 66", "paper_citation")
add("paper_hs_dense_risk_p100", 130.0, "risk",
    "Paper Section 5.2: Horseshoe risk at k=p=100 (dense) ~= 130", "paper_citation")

# ---------------- write ----------------
RES.mkdir(parents=True, exist_ok=True)
with open(RES / "evidence_table.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["metric", "value", "unit", "definition", "source"])
    w.writeheader()
    for r_ in rows:
        w.writerow(r_)

metrics = {r_["metric"]: {"value": r_["value"], "unit": r_["unit"],
                          "definition": r_["definition"], "source": r_["source"]}
           for r_ in rows}
json.dump(metrics, open(RES / "metrics.json", "w"), indent=2)
print(f"wrote {len(rows)} metrics -> evidence_table.csv + metrics.json")
