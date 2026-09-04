"""
verify_lpr_metrics.py
=====================
Verify C04: LPR metrics are computed using paper Equations 1-3 with lambda = 0.5.

Data source (frozen, read in place):
  F:/dataset/2604.04878v1/results/<experiment>/rep_1_result.json
  F:/dataset/2604.04878v1/VIGILANT/src  (reference VIGILANT package source)

Procedure:
  1. Load the 5x5 AUROC performance matrix for each of the three experiments.
  2. Recompute learning / potential / retention from the matrix using the VIGILANT
     package functions (learning, potential, retention) and compare with the values
     recorded in rep_1_result.json (assert near-exact match).
  3. Retention-lambda sensitivity: recompute retention for lambda in {0.0, 0.25, 0.5,
     0.75, 1.0} and confirm that only lambda=0.5 reproduces the recorded values.
  4. Run the VIGILANT toy-example test cases (tests/*.json) to confirm the package
     implements Equations 1-3 as claimed.

Outputs:
  - console report
  - results/lpr_verification.csv
  - results/retention_lambda_sensitivity.csv
"""

import os
import json
import sys
import glob
import math
import pandas as pd
import numpy as np

# ----------------------------------------------------------------------------
# Paths
# ----------------------------------------------------------------------------
DATA_ROOT = r"F:/dataset/2604.04878v1"
VIGILANT_SRC = os.path.join(DATA_ROOT, "VIGILANT", "src")
RESULTS_DIR = os.path.join(DATA_ROOT, "results")
OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
os.makedirs(OUT_DIR, exist_ok=True)

sys.path.insert(0, VIGILANT_SRC)
import vigilant  # noqa: E402

EXPERIMENTS = ["single_shift", "single_shift_limited", "double_shift"]


def build_performance_dataframe(matrix: np.ndarray, n_steps: int) -> pd.DataFrame:
    """Convert N x N performance matrix to the DataFrame format expected by VIGILANT.

    VIGILANT uses 1-indexed model/dataset versions.
    """
    rows = []
    for model_v in range(n_steps):
        for dataset_v in range(n_steps):
            rows.append({
                "model": model_v + 1,
                "dataset": dataset_v + 1,
                "performance": float(matrix[model_v, dataset_v]),
            })
    return pd.DataFrame(rows)


def load_result(experiment: str) -> dict:
    path = os.path.join(RESULTS_DIR, experiment, "rep_1_result.json")
    with open(path) as f:
        return json.load(f)


def verify_metrics_for_experiment(experiment: str, tol: float = 1e-8) -> dict:
    """Recompute LPR metrics from the stored performance matrix and compare to
    the values recorded in rep_1_result.json."""
    result = load_result(experiment)
    matrix = np.array(result["performance_matrix"])
    n_steps = matrix.shape[0]

    df = build_performance_dataframe(matrix, n_steps)

    # Recompute with the VIGILANT package (reference implementation)
    learning_df = vigilant.learning(df)
    potential_df = vigilant.potential(df)
    # NOTE: the reproduction code explicitly calls retention(df, decay=0.5)
    retention_df = vigilant.retention(df, decay=0.5)

    # Recorded values
    rec_learning = {r["version"]: r["learning"] for r in result["learning"]}
    rec_potential = {r["version"]: r["potential"] for r in result["potential"]}
    rec_retention = {r["version"]: r["retention"] for r in result["retention"]}

    checks = []
    max_err_learning = 0.0
    max_err_potential = 0.0
    max_err_retention = 0.0
    for _, row in learning_df.iterrows():
        v = row["version"]
        err = abs(row["learning"] - rec_learning[v])
        max_err_learning = max(max_err_learning, err)
        checks.append({
            "experiment": experiment, "version": v, "metric": "learning",
            "recomputed": row["learning"], "recorded": rec_learning[v], "abs_error": err,
        })
    for _, row in potential_df.iterrows():
        v = row["version"]
        err = abs(row["potential"] - rec_potential[v])
        max_err_potential = max(max_err_potential, err)
        checks.append({
            "experiment": experiment, "version": v, "metric": "potential",
            "recomputed": row["potential"], "recorded": rec_potential[v], "abs_error": err,
        })
    for _, row in retention_df.iterrows():
        v = row["version"]
        err = abs(row["retention"] - rec_retention[v])
        max_err_retention = max(max_err_retention, err)
        checks.append({
            "experiment": experiment, "version": v, "metric": "retention",
            "recomputed": row["retention"], "recorded": rec_retention[v], "abs_error": err,
        })

    ok = (max_err_learning <= tol) and (max_err_potential <= tol) and (max_err_retention <= tol)
    return {
        "experiment": experiment,
        "n_steps": n_steps,
        "max_err_learning": max_err_learning,
        "max_err_potential": max_err_potential,
        "max_err_retention": max_err_retention,
        "matches": ok,
        "checks": checks,
    }


def retention_lambda_sensitivity(experiment: str) -> pd.DataFrame:
    """Recompute retention with several decay values and record which lambda
    reproduces the recorded retention values."""
    result = load_result(experiment)
    matrix = np.array(result["performance_matrix"])
    df = build_performance_dataframe(matrix, matrix.shape[0])
    rec_retention = {r["version"]: r["retention"] for r in result["retention"]}

    rows = []
    for lam in [0.0, 0.25, 0.5, 0.75, 1.0]:
        ret_df = vigilant.retention(df, decay=lam)
        max_err = 0.0
        for _, row in ret_df.iterrows():
            v = row["version"]
            max_err = max(max_err, abs(row["retention"] - rec_retention[v]))
        rows.append({
            "experiment": experiment, "lambda": lam, "max_abs_error_vs_recorded": max_err,
            "matches_recorded": max_err < 1e-8,
        })
    return pd.DataFrame(rows)


def run_toy_examples() -> pd.DataFrame:
    """Run VIGILANT toy-example test cases from the package tests directory."""
    tests_dir = os.path.join(os.path.dirname(VIGILANT_SRC), "tests")
    rows = []
    n_pass = 0
    n_total = 0
    for path in sorted(glob.glob(os.path.join(tests_dir, "*.json"))):
        with open(path) as f:
            data = json.load(f)
        cases = data if isinstance(data, list) else [data]
        for case in cases:
            inp = pd.DataFrame(case["input"])
            exp = case["output"]
            for func_name in ["learning", "potential", "retention"]:
                func = vigilant.__dict__[func_name]
                out = func(inp).to_dict(orient="records")
                for item in out:
                    n_total += 1
                    expected = [x for x in exp if x["version"] == item["version"]]
                    if len(expected) != 1:
                        rows.append({"test_file": os.path.basename(path), "function": func_name,
                                     "version": item["version"], "expected": None,
                                     "actual": item[func_name], "pass": False})
                        continue
                    expected = expected[0]
                    for key in item:
                        ok = math.isclose(item[key], expected[key], rel_tol=0, abs_tol=1e-4)
                        n_pass += 1 if ok else 0
                        rows.append({"test_file": os.path.basename(path), "function": func_name,
                                     "version": item["version"], "key": key,
                                     "expected": expected[key], "actual": item[key], "pass": ok})
    return pd.DataFrame(rows), n_pass, n_total


if __name__ == "__main__":
    print("=" * 70)
    print("C04 VERIFICATION: Equations 1-3 with lambda = 0.5")
    print("=" * 70)

    # ---- 1. Recompute from stored performance matrices ---------------------
    all_checks = []
    summary_rows = []
    for exp in EXPERIMENTS:
        res = verify_metrics_for_experiment(exp)
        print(f"\n[{exp}]  matches recorded values: {res['matches']}")
        print(f"    max |recomputed - recorded| :  learning={res['max_err_learning']:.3e}"
              f"  potential={res['max_err_potential']:.3e}  retention={res['max_err_retention']:.3e}")
        all_checks.extend(res["checks"])
        summary_rows.append(res)

    checks_df = pd.DataFrame(all_checks)
    checks_df.to_csv(os.path.join(OUT_DIR, "lpr_verification.csv"), index=False)

    # ---- 2. Retention lambda sensitivity -----------------------------------
    print("\nRetention decay (lambda) sensitivity vs recorded values:")
    sens_dfs = []
    for exp in EXPERIMENTS:
        s = retention_lambda_sensitivity(exp)
        sens_dfs.append(s)
        for _, row in s.iterrows():
            marker = "  <== matches recorded" if row["matches_recorded"] else ""
            print(f"    {exp:20s} lambda={row['lambda']:.2f}  max_abs_err={row['max_abs_error_vs_recorded']:.3e}{marker}")
    sens_df = pd.concat(sens_dfs, ignore_index=True)
    sens_df.to_csv(os.path.join(OUT_DIR, "retention_lambda_sensitivity.csv"), index=False)

    # ---- 3. Toy example validation -----------------------------------------
    toy_df, n_pass, n_total = run_toy_examples()
    print(f"\nVIGILANT toy-example checks: {n_pass}/{n_total} value checks passed")
    toy_df.to_csv(os.path.join(OUT_DIR, "toy_example_validation.csv"), index=False)

    # ---- Overall C04 verdict -----------------------------------------------
    all_match = all(r["matches"] for r in summary_rows)
    lam_matches = all(
        sens_df[(sens_df["experiment"] == exp) & (sens_df["lambda"] == 0.5)]["matches_recorded"].all()
        for exp in EXPERIMENTS
    )
    lambda_is_half = sens_df[sens_df["matches_recorded"]]["lambda"].drop_duplicates().tolist()
    print("\n" + "=" * 70)
    print(f"Recomputed metrics match recorded values (all experiments): {all_match}")
    print(f"lambda=0.5 reproduces recorded retention (all experiments): {lam_matches}")
    print(f"lambda value(s) that reproduce recorded retention: {lambda_is_half}")
    print(f"Toy-example value checks passed: {n_pass}/{n_total}")
    print("=" * 70)
