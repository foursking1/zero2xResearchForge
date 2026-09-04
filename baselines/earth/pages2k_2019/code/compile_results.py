"""Compile per-claim JSON results into evidence_table.csv and metrics.json."""
from __future__ import annotations

import csv
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "results")


def load(name):
    with open(os.path.join(OUT, name)) as f:
        return json.load(f)


def main():
    c01 = load("c01_results.json")
    c02 = load("c02_results.json")
    c03 = load("c03_results.json")
    c04 = load("c04_results.json")

    # ---------------- evidence table ----------------
    rows = []  # (claim, metric, value, unit/definition)

    # C01
    for m, v in c01["reference_period_check"]["raw_data_1961_1990_ensemble_mean_C"].items():
        rows.append(["C01", f"raw_1961-1990_ensemble_mean_{m}", f"{v:.4f}", "degC, raw data (nonzero -> 1961-1990 reference not pre-applied)"])
    rows.append(["C01", "reference_period", "1961-1990", "CE, applied per member"])
    for p in ["1-1800", "1-1850"]:
        for m in c01["preindustrial_cooling_rate_C_per_century"][p]:
            v = c01["preindustrial_cooling_rate_C_per_century"][p][m]
            rows.append(["C01", f"preindustrial_cooling_{p}_{m}", f"{v:.4f}", "degC per century, OLS trend"])
        rows.append(["C01", f"preindustrial_cooling_{p}_median", f"{c01['preindustrial_cooling_rate_C_per_century']['median_'+p]:.4f}", "degC per century"])
    for m, v in c01["warmest_10yr_period"]["per_method_fraction_20th_century"].items():
        rows.append(["C01", f"warmest10yr_20c_fraction_{m}", f"{v:.4f}", "fraction of members, midpoint in 1901-2000"])
    rows.append(["C01", "warmest10yr_20c_fraction_overall", f"{c01['warmest_10yr_period']['overall_fraction_20th_century']:.4f}", "fraction of 3000 members"])
    for k, v in c01["coherence"]["raw_ensemble_mean_correlations"].items():
        rows.append(["C01", f"coherence_raw_{k}", f"{v:.4f}", "correlation of ensemble-mean reconstructions"])
    for k, v in c01["coherence"]["bandpassed_30_200_ensemble_mean_correlations"].items():
        rows.append(["C01", f"coherence_bandpassed_{k}", f"{v:.4f}", "correlation of 30-200yr filtered ensemble means"])
    rows.append(["C01", "methods_available", f"{len(c01['methods_available'])}/7", "CPS, PCR, PAI present; OIE, M08, BHM, DA absent"])
    rows.append(["C01", "methods_missing", "OIE;M08;BHM;DA", ""])

    # C02
    s = c02["between_method_spread_degC"]
    rows.append(["C02", "between_method_spread_bandpassed_median", f"{s['bandpassed_median']:.4f}", "degC, std of 3 method ensemble means across time"])
    rows.append(["C02", "between_method_spread_raw_median", f"{s['raw_median']:.4f}", "degC"])
    rows.append(["C02", "spread_ratio_bandpassed_to_raw", f"{s['ratio_median_bp_to_raw']:.4f}", "dimensionless"])
    for m, rng in c02["bandpassed_anomaly_range_degC"].items():
        rows.append(["C02", f"bandpassed_anomaly_range_{m}", f"[{rng[0]:.3f},{rng[1]:.3f}]", "degC, min/max of filtered ensemble mean"])
    rows.append(["C02", "overall_bandpassed_anomaly_range", f"[{c02['overall_bandpassed_range_degC'][0]:.3f},{c02['overall_bandpassed_range_degC'][1]:.3f}]", "degC"])
    for k, v in c02["cross_method_correlations_bandpassed"].items():
        rows.append(["C02", f"cross_method_corr_bandpassed_{k}", f"{v:.4f}", ""])
    rows.append(["C02", "median_cross_method_correlation", f"{c02['median_cross_method_correlation']:.4f}", ""])

    # C03
    for m in c03["methods_available"]:
        r = c03["per_member_pairs"][m]
        rows.append(["C03", f"variance_ratio_median_{m}", f"{r['variance_ratio_median']:.3f}", "median var(model)/var(member), 1000-2000 CE, 30-200yr"])
        rows.append(["C03", f"variance_ratio_median_{m}_paper", f"{r['paper_variance_ratio_median']}", "paper Fig.2 (citation)"])
        rows.append(["C03", f"correlation_median_{m}", f"{r['correlation_median']:.3f}", "median corr(model,member)"])
        rows.append(["C03", f"correlation_median_{m}_paper", f"{r['paper_correlation_median']}", "paper Fig.2 (citation)"])
        rows.append(["C03", f"fraction_corr_abs_gt_0.19_{m}", f"{r['fraction_pairs_abs_corr_gt_0.19']:.4f}", "naive 95% threshold"])
    rows.append(["C03", "variance_ratio_median_overall", f"{c03['per_member_pairs']['overall_variance_ratio_median']:.3f}", "median over 3 methods x 23 models x 1000 members"])
    rows.append(["C03", "variance_ratio_median_overall_paper", f"{c03['per_member_pairs']['paper_overall_variance_ratio_median']}", "paper (citation)"])
    rows.append(["C03", "correlation_median_overall", f"{c03['per_member_pairs']['overall_correlation_median']:.3f}", ""])
    rows.append(["C03", "n_model_runs_used", f"{c03['per_member_pairs'].get('n_model_runs_used', 23)}", ""])

    # C04
    rows.append(["C04", "n_residual_estimates", f"{c04['n_residual_estimates']}", "paper expects 7000"])
    rows.append(["C04", "n_control_estimates", f"{c04['n_control_estimates']}", "paper expects 43"])
    rows.append(["C04", "residual_variance_median", f"{c04['residual_variance_median']:.4f}", "authors' units"])
    rows.append(["C04", "control_variance_median", f"{c04['control_variance_median']:.4f}", "authors' units"])
    rows.append(["C04", "fraction_residual_within_control_range", f"{c04['fraction_residual_within_control_range']:.4f}", "paper expects 0.99"])
    rows.append(["C04", "median_ratio_resid_over_control", f"{c04['median_ratio_resid_over_control']:.3f}", ""])
    rows.append(["C04", "amplitude_ratio_resid_over_control", f"{c04['amplitude_ratio_resid_over_control']:.3f}", "sqrt variance ratio"])
    rows.append(["C04", "residual_variance_range", f"[{c04['residual_variance_range'][0]:.3f},{c04['residual_variance_range'][1]:.3f}]", "authors' units"])
    rows.append(["C04", "control_variance_range", f"[{c04['control_variance_range'][0]:.3f},{c04['control_variance_range'][1]:.3f}]", "authors' units"])
    rows.append(["C04", "KS_pvalue", f"{c04['ks_test']['pvalue']:.4f}", "two-sample KS test"])
    ind = c04["independent_control_variance_crosscheck"]
    rows.append(["C04", "independent_control_variance_median_degC2", f"{ind['median']:.5f}", "degC^2, this study, trimmed 30-200yr bandpass"])

    with open(os.path.join(OUT, "evidence_table.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["claim", "metric", "value", "definition"])
        w.writerows(rows)

    # ---------------- metrics.json ----------------
    metrics = {
        "task_id": "pages2k_2019",
        "claims": {
            "C01": {
                "judgment": "partially_supported",
                "methods_available": c01["methods_available"],
                "preindustrial_cooling_rate_C_per_century_median_1_1800": c01["preindustrial_cooling_rate_C_per_century"]["median_1-1800"],
                "warmest_10yr_fraction_20th_century": c01["warmest_10yr_period"]["overall_fraction_20th_century"],
                "coherence_raw_median": c01["coherence"]["median_raw_correlation"],
                "coherence_bandpassed_median": c01["coherence"]["median_bandpassed_correlation"],
                "raw_1961_1990_ensemble_mean_C": c01["reference_period_check"]["raw_data_1961_1990_ensemble_mean_C"],
            },
            "C02": {
                "judgment": "partially_supported",
                "between_method_spread_bandpassed_median_C": c02["between_method_spread_degC"]["bandpassed_median"],
                "between_method_spread_raw_median_C": c02["between_method_spread_degC"]["raw_median"],
                "spread_ratio_bandpassed_to_raw": c02["between_method_spread_degC"]["ratio_median_bp_to_raw"],
                "bandpassed_anomaly_range_C": c02["overall_bandpassed_range_degC"],
                "median_cross_method_correlation_bandpassed": c02["median_cross_method_correlation"],
            },
            "C03": {
                "judgment": "partially_supported",
                "variance_ratio_median": {m: c03["per_member_pairs"][m]["variance_ratio_median"] for m in c03["methods_available"]},
                "variance_ratio_median_overall": c03["per_member_pairs"]["overall_variance_ratio_median"],
                "variance_ratio_median_overall_paper": c03["per_member_pairs"]["paper_overall_variance_ratio_median"],
                "correlation_median": {m: c03["per_member_pairs"][m]["correlation_median"] for m in c03["methods_available"]},
                "correlation_median_overall": c03["per_member_pairs"]["overall_correlation_median"],
            },
            "C04": {
                "judgment": "supported",
                "n_residual_estimates": c04["n_residual_estimates"],
                "n_control_estimates": c04["n_control_estimates"],
                "fraction_residual_within_control_range": c04["fraction_residual_within_control_range"],
                "median_ratio_resid_over_control": c04["median_ratio_resid_over_control"],
                "residual_variance_median": c04["residual_variance_median"],
                "control_variance_median": c04["control_variance_median"],
            },
        },
    }

    with open(os.path.join(OUT, "metrics.json"), "w") as f:
        json.dump(metrics, f, indent=2)

    print("wrote evidence_table.csv and metrics.json")


if __name__ == "__main__":
    main()
