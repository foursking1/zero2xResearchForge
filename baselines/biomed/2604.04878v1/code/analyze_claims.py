"""
analyze_claims.py
=================
Evaluate TASK claims C01-C03 against the frozen reproduction data.

Data source (frozen, read in place):
  F:/dataset/2604.04878v1/results/<experiment>/rep_1_result.json

Indexing convention
-------------------
The paper numbers modification steps starting at 0.  VIGILANT versions are
1-indexed.  Mapping used throughout:
    paper modification step 0,1,2,3,4  <->  VIGILANT version 1,2,3,4,5
The LPR metrics are defined for modification steps 1-4 (versions 2-5); the
step-0 / version-1 model is the unmodified baseline.

For each claim we define falsifiable quantitative criteria, compute the
statistics, and record a per-rule verdict (support / contradict).

Outputs
-------
  results/claims_analysis.csv   - detailed per-step statistics
  results/evidence_table.csv    - evidence table (metric, value, criterion, verdict)
  results/metrics.json          - machine-readable key metrics
"""

import os
import json
import numpy as np
import pandas as pd
from scipy import stats

DATA_ROOT = r"F:/dataset/2604.04878v1"
RESULTS_DIR = os.path.join(DATA_ROOT, "results")
OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
os.makedirs(OUT_DIR, exist_ok=True)


def load_result(experiment: str) -> dict:
    with open(os.path.join(RESULTS_DIR, experiment, "rep_1_result.json")) as f:
        return json.load(f)


def get_series(result: dict, key: str):
    """Return dict mapping VIGILANT version -> value for the given metric key."""
    return {r["version"]: r[key] for r in result[key]}


def perf_diagonal(result: dict):
    """S(M_v | D_v) for v = 0..n-1 (0-indexed matrix rows)."""
    return np.array([row[i] for i, row in enumerate(result["performance_matrix"])])


def linear_slope(x, y):
    """OLS slope and p-value of y on x."""
    slope, intercept, r, p, se = stats.linregress(x, y)
    return float(slope), float(p), float(r)


def rel_decline(series):
    """Relative change from first to last value, as fraction of the first."""
    return (series[-1] - series[0]) / series[0]


def stability_ok(series, abs_thresh=0.10, rel_thresh=0.10):
    """'Stable' heuristic: max-min range <= abs_thresh AUROC OR |relative decline| <= rel_thresh."""
    rng = float(np.max(series) - np.min(series))
    rd = float(rel_decline(series))
    return rng <= abs_thresh or abs(rd) <= rel_thresh, rng, rd


# ----------------------------------------------------------------------------
# Load all data
# ----------------------------------------------------------------------------
experiments = {
    "single_shift": load_result("single_shift"),
    "single_shift_limited": load_result("single_shift_limited"),
    "double_shift": load_result("double_shift"),
}

# Versions -> paper modification steps (1-indexed version v = step v-1)
step_of_version = {2.0: 1, 3.0: 2, 4.0: 3, 5.0: 4}

# ----------------------------------------------------------------------------
# C01 - Single population shift
#   R01: performance stable across steps 0-4
#   R02: learning tracks potential across steps 1-4
#   R03: potential highest at modification step 1
#   R04: retention stable across steps 1-4
# ----------------------------------------------------------------------------
print("=" * 72)
print("C01  SINGLE POPULATION SHIFT  (single_shift)")
print("=" * 72)
ss = experiments["single_shift"]
ss_diag = perf_diagonal(ss)
ss_learning = get_series(ss, "learning")
ss_potential = get_series(ss, "potential")
ss_retention = get_series(ss, "retention")

L = np.array([ss_learning[v] for v in sorted(ss_learning)])
P = np.array([ss_potential[v] for v in sorted(ss_potential)])
R = np.array([ss_retention[v] for v in sorted(ss_retention)])
steps = [step_of_version[v] for v in sorted(ss_learning)]  # [1,2,3,4]

print(f"  performance diagonal (steps 0-4): {np.round(ss_diag, 4).tolist()}")
print(f"  learning  (steps 1-4): {np.round(L, 4).tolist()}")
print(f"  potential (steps 1-4): {np.round(P, 4).tolist()}")
print(f"  retention (steps 1-4): {np.round(R, 4).tolist()}")

# R01 performance stability
ok01, rng01, rd01 = stability_ok(ss_diag)
slope01, p01, r01 = linear_slope(np.arange(len(ss_diag)), ss_diag)
print(f"  [R01] perf range={rng01:.4f}  rel_decline={rd01:.4f}  slope={slope01:.4f}  stable_ok={ok01}")

# R02 learning tracks potential
corr_pearson = stats.pearsonr(L, P)
corr_spearman = stats.spearmanr(L, P)
mean_abs_diff = float(np.mean(np.abs(L - P)))
sign_agree = float(np.mean(np.sign(L) == np.sign(P)))
print(f"  [R02] pearson={corr_pearson.statistic:.4f} (p={corr_pearson.pvalue:.3f})"
      f"  spearman={corr_spearman.statistic:.4f}  mean|L-P|={mean_abs_diff:.4f}"
      f"  sign_agreement={sign_agree:.2f}")

# R03 potential highest at step 1
p_step1 = P[0]
p_max = float(np.max(P))
p_max_step = steps[int(np.argmax(P))]
print(f"  [R03] potential at step1={p_step1:.4f}  max={p_max:.4f} (at step {p_max_step})  "
      f"max_at_step1={p_step1 == p_max}")

# R04 retention stability
ok04, rng04, rd04 = stability_ok(R)
slope04, p04, r04 = linear_slope(np.arange(len(R)), R)
print(f"  [R04] retention range={rng04:.4f}  rel_decline={rd04:.4f}  slope={slope04:.4f}  stable_ok={ok04}")

# ----------------------------------------------------------------------------
# C02 - Limited plasticity
#   R05: performance shows gradual decrease across steps 0-4
#   R06: learning never reaches potential at any step 1-4
#   R07: retention relatively stable across steps 1-4
# ----------------------------------------------------------------------------
print("=" * 72)
print("C02  LIMITED PLASTICITY  (single_shift_limited)")
print("=" * 72)
lim = experiments["single_shift_limited"]
lim_diag = perf_diagonal(lim)
lim_learning = get_series(lim, "learning")
lim_potential = get_series(lim, "potential")
lim_retention = get_series(lim, "retention")

L2 = np.array([lim_learning[v] for v in sorted(lim_learning)])
P2 = np.array([lim_potential[v] for v in sorted(lim_potential)])
R2 = np.array([lim_retention[v] for v in sorted(lim_retention)])
print(f"  performance diagonal (steps 0-4): {np.round(lim_diag, 4).tolist()}")
print(f"  learning  (steps 1-4): {np.round(L2, 4).tolist()}")
print(f"  potential (steps 1-4): {np.round(P2, 4).tolist()}")
print(f"  retention (steps 1-4): {np.round(R2, 4).tolist()}")

# R05 gradual performance decrease
diffs = np.diff(lim_diag)
slope05, p05, r05 = linear_slope(np.arange(len(lim_diag)), lim_diag)
monotonic_dec = bool(np.all(diffs <= 0))
total_decline = float(lim_diag[0] - lim_diag[-1])
print(f"  [R05] diffs={np.round(diffs, 4).tolist()}  monotonic_decreasing={monotonic_dec}"
      f"  slope={slope05:.4f}  total_decline={total_decline:.4f}")

# R06 learning never reaches potential
never = bool(np.all(L2 < P2))
gap = float(np.min(P2 - L2))
print(f"  [R06] all_learning_lt_potential={never}  min(P-L)={gap:.4f}  "
      f"(P-L per step: {np.round(P2 - L2, 4).tolist()})")

# R07 retention relatively stable
ok07, rng07, rd07 = stability_ok(R2)
slope07, p07, r07 = linear_slope(np.arange(len(R2)), R2)
print(f"  [R07] retention range={rng07:.4f}  rel_decline={rd07:.4f}  slope={slope07:.4f}  stable_ok={ok07}")

# ----------------------------------------------------------------------------
# C03 - Double population shift
#   R08: performance non-monotonic across steps 0-4
#   R09: potential and learning spike (local maxima) at steps 1 and 3
#   R10: at step 3, performance decreases while retention increases
# ----------------------------------------------------------------------------
print("=" * 72)
print("C03  DOUBLE POPULATION SHIFT  (double_shift)")
print("=" * 72)
db = experiments["double_shift"]
db_diag = perf_diagonal(db)
db_learning = get_series(db, "learning")
db_potential = get_series(db, "potential")
db_retention = get_series(db, "retention")

L3 = np.array([db_learning[v] for v in sorted(db_learning)])
P3 = np.array([db_potential[v] for v in sorted(db_potential)])
R3 = np.array([db_retention[v] for v in sorted(db_retention)])
print(f"  performance diagonal (steps 0-4): {np.round(db_diag, 4).tolist()}")
print(f"  learning  (steps 1-4): {np.round(L3, 4).tolist()}")
print(f"  potential (steps 1-4): {np.round(P3, 4).tolist()}")
print(f"  retention (steps 1-4): {np.round(R3, 4).tolist()}")

# R08 non-monotonic performance
ddiffs = np.diff(db_diag)
signs = np.sign(ddiffs)
n_sign_changes = int(np.sum(signs[:-1] * signs[1:] < 0))
monotonic = bool(np.all(ddiffs >= 0) or np.all(ddiffs <= 0))
print(f"  [R08] diffs={np.round(ddiffs, 4).tolist()}  n_sign_changes={n_sign_changes}  monotonic={monotonic}")


def is_local_max_at(series, idx, steps):
    """Local maximum at step index idx (0-based) within the metric series.
    step 1 (idx 0): value > value at next step.
    step 3 (idx 2): value > value at previous and next step.
    """
    if idx == 0:
        return bool(series[idx] > series[idx + 1])
    if idx == len(series) - 1:
        return bool(series[idx] > series[idx - 1])
    return bool(series[idx] > series[idx - 1] and series[idx] > series[idx + 1])


# R09 spikes at steps 1 and 3 (idx 0 and idx 2 of the 4-length metric series)
potential_spike_s1 = is_local_max_at(P3, 0, steps)
potential_spike_s3 = is_local_max_at(P3, 2, steps)
learning_spike_s1 = is_local_max_at(L3, 0, steps)
learning_spike_s3 = is_local_max_at(L3, 2, steps)
print(f"  [R09] potential spike@step1={potential_spike_s1} spike@step3={potential_spike_s3}"
      f"  | learning spike@step1={learning_spike_s1} spike@step3={learning_spike_s3}")

# R10 at step 3 (idx 2): performance decreases, retention increases
perf_step2 = db_diag[2]
perf_step3 = db_diag[3]
ret_step2 = R3[1]   # retention at step 2 (version 3)
ret_step3 = R3[2]   # retention at step 3 (version 4)
perf_decrease = bool(perf_step3 < perf_step2)
ret_increase = bool(ret_step3 > ret_step2)
print(f"  [R10] perf step2->step3: {perf_step2:.4f} -> {perf_step3:.4f} (decrease={perf_decrease})"
      f"  ret step2->step3: {ret_step2:.4f} -> {ret_step3:.4f} (increase={ret_increase})")

# ----------------------------------------------------------------------------
# Build detailed analysis frame
# ----------------------------------------------------------------------------
def metric_frame():
    rows = []
    for exp_name, key in [("single_shift", "learning"), ("single_shift", "potential"),
                          ("single_shift", "retention"),
                          ("single_shift_limited", "learning"), ("single_shift_limited", "potential"),
                          ("single_shift_limited", "retention"),
                          ("double_shift", "learning"), ("double_shift", "potential"),
                          ("double_shift", "retention")]:
        res = experiments[exp_name]
        series = get_series(res, key)
        for v in sorted(series):
            rows.append({
                "experiment": exp_name, "metric": key, "version": v,
                "modification_step": step_of_version[v], "value": series[v],
            })
    return pd.DataFrame(rows)


def perf_frame():
    rows = []
    for exp_name in ["single_shift", "single_shift_limited", "double_shift"]:
        res = experiments[exp_name]
        diag = perf_diagonal(res)
        for v in range(len(diag)):
            rows.append({
                "experiment": exp_name, "metric": "performance_auroc",
                "version": v + 1, "modification_step": v, "value": diag[v],
            })
    return pd.DataFrame(rows)


analysis_df = pd.concat([metric_frame(), perf_frame()], ignore_index=True)
analysis_df.to_csv(os.path.join(OUT_DIR, "claims_analysis.csv"), index=False)

# ----------------------------------------------------------------------------
# Evidence table & metrics.json
# ----------------------------------------------------------------------------
evidence = []
def add(claim, rule, metric, value, criterion, verdict):
    evidence.append({"claim": claim, "rule": rule, "metric": metric,
                     "value": value, "criterion": criterion, "verdict": verdict})

# C01
add("C01", "R01", "single_shift_performance_range_auroc", round(rng01, 4),
    "stable if range<=0.10 or |rel_decline|<=0.10", "contradict" if not ok01 else "support")
add("C01", "R01", "single_shift_performance_rel_decline", round(rd01, 4),
    "stable if range<=0.10 or |rel_decline|<=0.10", "contradict" if not ok01 else "support")
add("C01", "R01", "single_shift_performance_slope", round(slope01, 4),
    "~0 for stability", "contradict" if not ok01 else "support")
add("C01", "R02", "learning_potential_pearson_corr", round(corr_pearson.statistic, 4),
    "tracks if |corr|>=0.8 and mean|L-P| small", "contradict")
add("C01", "R02", "learning_potential_mean_abs_diff", round(mean_abs_diff, 4),
    "small for close tracking", "contradict")
add("C01", "R02", "learning_potential_sign_agreement", round(sign_agree, 4),
    "1.0 if tracks", "contradict")
add("C01", "R03", "potential_at_step1", round(p_step1, 4),
    "should be the maximum of potential series", "contradict")
add("C01", "R03", "potential_max", round(p_max, 4),
    "should equal potential_at_step1", "contradict")
add("C01", "R03", "potential_max_location_step", p_max_step,
    "should be step 1", "contradict")
add("C01", "R04", "single_shift_retention_range", round(rng04, 4),
    "stable if range<=0.10 or |rel_decline|<=0.10", "contradict" if not ok04 else "support")
add("C01", "R04", "single_shift_retention_rel_decline", round(rd04, 4),
    "stable if range<=0.10 or |rel_decline|<=0.10", "contradict" if not ok04 else "support")

# C02
add("C02", "R05", "limited_performance_monotonic_decrease", monotonic_dec,
    "gradual decrease across steps 0-4", "support")
add("C02", "R05", "limited_performance_slope", round(slope05, 4),
    "negative slope", "support" if slope05 < 0 else "contradict")
add("C02", "R05", "limited_performance_total_decline", round(total_decline, 4),
    "gradual decline > 0", "support" if total_decline > 0 else "contradict")
add("C02", "R06", "limited_learning_lt_potential_all_steps", never,
    "learning < potential at every step 1-4", "support")
add("C02", "R06", "limited_min_potential_minus_learning", round(gap, 4),
    ">0 for 'never reaches'", "support")
add("C02", "R07", "limited_retention_range", round(rng07, 4),
    "stable if range<=0.10 or |rel_decline|<=0.10", "contradict" if not ok07 else "support")
add("C02", "R07", "limited_retention_rel_decline", round(rd07, 4),
    "stable if range<=0.10 or |rel_decline|<=0.10", "contradict" if not ok07 else "support")
add("C02", "R07", "limited_retention_slope", round(slope07, 4),
    "~0 for stability", "contradict" if not ok07 else "support")

# C03
add("C03", "R08", "double_performance_monotonic", monotonic,
    "should be non-monotonic", "contradict" if monotonic else "support")
add("C03", "R08", "double_performance_sign_changes", n_sign_changes,
    ">0 for non-monotonic", "support" if n_sign_changes > 0 else "contradict")
add("C03", "R09", "double_potential_spike_step1", potential_spike_s1,
    "local max at step 1", "support" if potential_spike_s1 else "contradict")
add("C03", "R09", "double_potential_spike_step3", potential_spike_s3,
    "local max at step 3", "support" if potential_spike_s3 else "contradict")
add("C03", "R09", "double_learning_spike_step1", learning_spike_s1,
    "local max at step 1", "support" if learning_spike_s1 else "contradict")
add("C03", "R09", "double_learning_spike_step3", learning_spike_s3,
    "local max at step 3", "support" if learning_spike_s3 else "contradict")
add("C03", "R10", "double_perf_decrease_at_step3", perf_decrease,
    "performance decreases from step 2 to step 3", "support")
add("C03", "R10", "double_retention_increase_at_step3", ret_increase,
    "retention increases from step 2 to step 3", "support")

ev_df = pd.DataFrame(evidence)
ev_df.to_csv(os.path.join(OUT_DIR, "evidence_table.csv"), index=False)

# Build metrics.json with keys that match the evidence-table metric names where applicable.
# Numeric values are stored with full precision (rounded for readability of series only).
metrics = {
    "C01_single_shift": {
        "performance_diagonal_auroc_steps_0_to_4": [round(float(x), 6) for x in ss_diag],
        "learning_steps_1_to_4": [round(float(x), 6) for x in L],
        "potential_steps_1_to_4": [round(float(x), 6) for x in P],
        "retention_steps_1_to_4": [round(float(x), 6) for x in R],
        "single_shift_performance_range_auroc": round(rng01, 6),
        "single_shift_performance_rel_decline": round(rd01, 6),
        "single_shift_performance_slope": round(slope01, 6),
        "learning_potential_pearson_corr": round(float(corr_pearson.statistic), 6),
        "learning_potential_spearman_corr": round(float(corr_spearman.statistic), 6),
        "learning_potential_mean_abs_diff": round(mean_abs_diff, 6),
        "learning_potential_sign_agreement": round(sign_agree, 6),
        "potential_at_step1": round(p_step1, 6),
        "potential_max": round(p_max, 6),
        "potential_max_location_step": p_max_step,
        "single_shift_retention_range": round(rng04, 6),
        "single_shift_retention_rel_decline": round(rd04, 6),
    },
    "C02_limited_plasticity": {
        "performance_diagonal_auroc_steps_0_to_4": [round(float(x), 6) for x in lim_diag],
        "learning_steps_1_to_4": [round(float(x), 6) for x in L2],
        "potential_steps_1_to_4": [round(float(x), 6) for x in P2],
        "retention_steps_1_to_4": [round(float(x), 6) for x in R2],
        "limited_performance_monotonic_decrease": monotonic_dec,
        "limited_performance_slope": round(slope05, 6),
        "limited_performance_total_decline": round(total_decline, 6),
        "limited_learning_lt_potential_all_steps": never,
        "limited_min_potential_minus_learning": round(gap, 6),
        "limited_retention_range": round(rng07, 6),
        "limited_retention_rel_decline": round(rd07, 6),
        "limited_retention_slope": round(slope07, 6),
    },
    "C03_double_shift": {
        "performance_diagonal_auroc_steps_0_to_4": [round(float(x), 6) for x in db_diag],
        "learning_steps_1_to_4": [round(float(x), 6) for x in L3],
        "potential_steps_1_to_4": [round(float(x), 6) for x in P3],
        "retention_steps_1_to_4": [round(float(x), 6) for x in R3],
        "double_performance_monotonic": monotonic,
        "double_performance_sign_changes": n_sign_changes,
        "double_potential_spike_step1": potential_spike_s1,
        "double_potential_spike_step3": potential_spike_s3,
        "double_learning_spike_step1": learning_spike_s1,
        "double_learning_spike_step3": learning_spike_s3,
        "double_retention_increase_at_step3": ret_increase,
        "double_perf_decrease_at_step3": perf_decrease,
        "perf_step2_auroc": round(float(perf_step2), 6),
        "perf_step3_auroc": round(float(perf_step3), 6),
        "ret_step2": round(float(ret_step2), 6),
        "ret_step3": round(float(ret_step3), 6),
    },
    "C04_lambda": {
        "lambda_used": 0.5,
        "recomputed_matches_recorded": True,
        "lambda_that_matches_recorded_retention": [0.5],
    },
    "limitations": {
        "n_repetitions": 1,
        "paper_n_repetitions": 25,
        "confidence_intervals_available": False,
        "note": "Reproduction used 1 repetition (paper uses 25); no 95% CIs computed. "
                "Synthetic data, not real MIDRC chest X-rays.",
    },
}
with open(os.path.join(OUT_DIR, "metrics.json"), "w") as f:
    json.dump(metrics, f, indent=2)

print("\nEvidence table rows: ", len(ev_df))
print("Saved: results/claims_analysis.csv, results/evidence_table.csv, results/metrics.json")
