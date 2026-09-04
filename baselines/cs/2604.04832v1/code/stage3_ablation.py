"""Stage 3 (C03): sensor ablation audit + FDR-MCC correlation.

Computes:
  A) distributional-shift FDR (paper's Fig.5 method, signal-level ablation),
  B) delta pairwise FDR (feature-level ablation) + per-class criticality,
  C) FDR vs MCC correlation across the 8 sensors for each pair (and overall).

Writes:
  results/stage3_ablation_results.json
  results/mlp_ablation_correlation.json
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

import common
from common import (CLASS_NAMES, SENSOR_LABEL_0BASED, SENSOR_LABEL_1BASED,
                    extract_sample_features)
from ablation import (distributional_shift_ablation, delta_fdr_ablation)
from mlp_oracle import group_kfold_mlp
from separability import PAIR_DEFS, fdr_per_feature

OUT_DIR = Path(__file__).resolve().parents[1] / "results"


def sensor_rank_report(class_criticality: dict) -> dict:
    """0-based sensor -> paper 1-based label mapping in the ranking table."""
    out = {}
    for cname, crit in class_criticality.items():
        out[cname] = {
            "top_3": [f"sensor_{s}" for s in crit["top_3"]],
            "bottom_3": [f"sensor_{s}" for s in crit["bottom_3"]],
            "ranking": crit["ranking"],
        }
    return out


def main() -> dict:
    X, Y, pids = common.load_processed()
    F, _, _ = common.load_features()

    # --- A) distributional-shift ablation (paper's method, signal level) ---
    print("[stage3] signal-level distributional-shift ablation ...")
    shift = distributional_shift_ablation(X, Y)

    # --- B) delta pairwise FDR ablation (feature level) --------------------
    print("[stage3] feature-level delta-FDR ablation ...")
    delta = delta_fdr_ablation(F, Y)

    # --- C) FDR-MCC correlation across the 8 sensors per pair -------------
    print("[stage3] MLP on ablated features (8 sensors) for correlation ...")
    corr = ablation_mcc_correlation(F, Y, pids)

    # 1-based label maps for the report
    map0 = {f"sensor_{i}": SENSOR_LABEL_1BASED[i] for i in range(8)}

    summary = {
        "distributional_shift_ablation": {
            "per_class_f1_shift": shift["per_class"],
            "normalized_f1_per_class": shift["normalized_f1"],
            "criticality": shift["criticality"],
        },
        "delta_fdr_ablation": {
            "baseline_fdr_max": delta["baseline_fdr_max"],
            "baseline_fdr_mean": delta["baseline_fdr_mean"],
            "delta_fdr_max": delta["delta_fdr_max"],
            "delta_fdr_normalized": delta["delta_fdr_normalized"],
            "sensor_criticality_per_pair": delta["sensor_criticality"],
            "class_criticality": delta["class_criticality"],
            "class_criticality_mean": delta["class_criticality_mean"],
        },
        "sensor_0based_to_paper_label": {k: v for k, v in map0.items()},
        "correlation": corr,
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUT_DIR / "stage3_ablation_results.json", "w") as fh:
        json.dump(summary, fh, indent=2, default=float)
    with open(OUT_DIR / "mlp_ablation_correlation.json", "w") as fh:
        json.dump(corr, fh, indent=2, default=float)

    # concise console report
    print("\n--- Metric A: distributional-shift F1 criticality (top/bottom) ---")
    for cname, crit in shift["criticality"].items():
        top = [map0[s] for s in crit["top_3"]]
        bot = [map0[s] for s in crit["bottom_3"]]
        print(f"  {cname:8s}: top3={top}  bottom3={bot}")
    print("\n--- Metric B: delta-FDR class criticality (top/bottom) ---")
    for cname, crit in delta["class_criticality"].items():
        top = [map0[s] for s in crit["top_3"]]
        bot = [map0[s] for s in crit["bottom_3"]]
        print(f"  {cname:8s}: top3={top}  bottom3={bot}")
    print("\n--- FDR-MCC correlation (per pair) ---")
    for pair, v in corr["per_pair"].items():
        print(f"  {pair:20s}: r={v['pearson_r']:.3f} p={v['p_value']:.4f}")
    return summary


def ablation_mcc_correlation(F, Y, pids):
    """Pearson correlation between delta_FDR and delta_MCC across sensors."""
    from scipy import stats
    from common import NUM_SENSORS

    base = group_kfold_mlp(F, Y, pids, hidden_layers=(32, 16), random_state=42)
    base_mcc = base["overall_pairwise_mcc"]

    # delta_FDR_mean uses the more spread-out mean-aggregated FDR
    mean_fdr = {}
    for pair, la, lb in PAIR_DEFS:
        fa, fb = F[Y == la], F[Y == lb]
        mean_fdr[pair] = float(np.mean(fdr_per_feature(fa, fb)))

    per_pair = {}
    all_delta_fdr, all_delta_mcc = [], []
    per_sensor = {}

    for s in range(NUM_SENSORS):
        Fa = np.copy(F)
        start = s * 9
        Fa[:, start:start + 9] = 0.0
        ablated = group_kfold_mlp(Fa, Y, pids, hidden_layers=(32, 16), random_state=42)
        key = f"sensor_{s}"
        per_sensor[key] = {}
        for pair, la, lb in PAIR_DEFS:
            fa, fb = Fa[Y == la], Fa[Y == lb]
            d_fdr_mean = mean_fdr[pair] - float(np.mean(fdr_per_feature(fa, fb)))
            d_mcc = base_mcc[pair] - ablated["overall_pairwise_mcc"][pair]
            per_sensor[key][pair] = {
                "delta_fdr_mean": d_fdr_mean,
                "delta_mcc": d_mcc,
                "ablated_mcc": ablated["overall_pairwise_mcc"][pair],
            }
            all_delta_fdr.append(d_fdr_mean)
            all_delta_mcc.append(d_mcc)

    for pair, _, _ in PAIR_DEFS:
        x = np.array([per_sensor[f"sensor_{s}"][pair]["delta_fdr_mean"]
                      for s in range(NUM_SENSORS)])
        y = np.array([per_sensor[f"sensor_{s}"][pair]["delta_mcc"]
                      for s in range(NUM_SENSORS)])
        if np.std(x) > 1e-10 and np.std(y) > 1e-10:
            r, p = stats.pearsonr(x, y)
        else:
            r, p = 0.0, 1.0
        per_pair[pair] = {"pearson_r": float(r), "p_value": float(p), "n": int(len(x))}

    x = np.array(all_delta_fdr)
    y = np.array(all_delta_mcc)
    if np.std(x) > 1e-10 and np.std(y) > 1e-10:
        r_all, p_all = stats.pearsonr(x, y)
    else:
        r_all, p_all = 0.0, 1.0

    return {
        "per_sensor": per_sensor,
        "per_pair": per_pair,
        "overall_24_points": {"pearson_r": float(r_all), "p_value": float(p_all),
                              "n": int(len(x))},
        "baseline_mcc": base_mcc,
        "method_note": "delta_FDR uses mean-aggregated FDR; delta_MCC = baseline MCC - ablated MCC "
                       "(GroupKFold, arch=(32,16)).",
    }


if __name__ == "__main__":
    main()
