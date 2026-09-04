"""Assemble the final evidence table (evidence_table.csv) and machine-readable
metrics (metrics.json) from the verification outputs.

Inputs (produced by verify_static.py / verify_flow.py):
  results/metrics_static.json
  results/metrics_flow.json
Outputs:
  results/evidence_table.csv
  results/metrics.json
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "results"


def load(name: str) -> dict:
    with open(OUT / name, "r", encoding="utf-8") as fh:
        return json.load(fh)


def main() -> None:
    static = load("metrics_static.json")
    flow = load("metrics_flow.json")

    rows = []

    # ── C01 rows ────────────────────────────────────────────────────────
    claim_costs = static["claim_values"]  # {"1":23.745, "2":19.916, "inf":19.323}
    for pkey in ["1", "2", "inf"]:
        plan = static["plans"][pkey]
        tc = static["tolerance_check"][pkey]
        rows.append({
            "claim_id": "C01",
            "metric": f"static_ot_cost_p{pkey}",
            "value": tc["frozen"],
            "claim_value": claim_costs[pkey],
            "rel_diff_pct": round(tc["rel_diff"] * 100, 4),
            "criterion": "cost of the frozen optimal spectral-OT coupling (frozen static_couplings.npz)",
            "reopt_cost": plan.get("reopt_cost"),
            "plan_feasible": plan["feasibility"]["max_row_err"] < 1e-3 and plan["feasibility"]["max_col_err"] < 1e-3,
        })
    # plan-difference rows
    for pair, d in static["plan_differences"].items():
        rows.append({
            "claim_id": "C01",
            "metric": f"plan_difference_{pair}",
            "value": d["l1_diff"],
            "claim_value": None,
            "rel_diff_pct": None,
            "criterion": "L1 distance between two frozen optimal couplings",
            "reopt_cost": None,
            "plan_feasible": None,
        })
    # displacement top-singular-share rows (C01 figure-adjacent)
    for pkey, s in static["displacement_svd"].items():
        rows.append({
            "claim_id": "C01",
            "metric": f"displacement_top_singular_share_p{pkey}",
            "value": s["top_singular_share"],
            "claim_value": None,
            "rel_diff_pct": None,
            "criterion": "s1/(s1+s2) of the displacement matrix Y[perm]-X (paper Fig.1 analogue)",
            "reopt_cost": None,
            "plan_feasible": None,
        })

    # ── C02 rows ────────────────────────────────────────────────────────
    claim_loss = flow["claim_values"]  # {"1":0.0018, "2":0.0016, "inf":0.0011}
    for pkey in ["1", "2", "inf"]:
        fl = flow["final_losses"][pkey]
        tc = flow["tolerance_check"][pkey]
        rows.append({
            "claim_id": "C02",
            "metric": f"mmd_final_loss_p{pkey}",
            "value": fl["recomputed"],
            "claim_value": claim_loss[pkey],
            "rel_diff_pct": round(tc["rel_diff"] * 100, 4),
            "criterion": "final MMD^2 loss after 6000 explicit-Euler steps (recomputed on frozen clouds)",
            "reopt_cost": None,
            "plan_feasible": None,
        })
        tm = flow["trajectory_metrics"][pkey]
        rows.append({
            "claim_id": "C02",
            "metric": f"trajectory_top_singular_share_p{pkey}",
            "value": tm["top_share"],
            "claim_value": None,
            "rel_diff_pct": None,
            "criterion": "s1/(s1+s2) of aggregate displacement X_final - X_0 (global-coordination proxy)",
            "reopt_cost": None,
            "plan_feasible": None,
        })
        rows.append({
            "claim_id": "C02",
            "metric": f"trajectory_mean_abs_cos_p{pkey}",
            "value": tm["mean_abs_cos_top_dir"],
            "claim_value": None,
            "rel_diff_pct": None,
            "criterion": "mean |cos angle| of per-particle displacement vs top singular direction",
            "reopt_cost": None,
            "plan_feasible": None,
        })
        rows.append({
            "claim_id": "C02",
            "metric": f"trajectory_s1_over_s2_p{pkey}",
            "value": tm["cond_s1_over_s2"],
            "claim_value": None,
            "rel_diff_pct": None,
            "criterion": "conditioning of aggregate displacement matrix",
            "reopt_cost": None,
            "plan_feasible": None,
        })
        rows.append({
            "claim_id": "C02",
            "metric": f"loss_reproduced_frozen_max_abs_diff_p{pkey}",
            "value": fl["max_abs_loss_diff_vs_frozen"],
            "claim_value": None,
            "rel_diff_pct": None,
            "criterion": "max |recomputed_loss - frozen_loss| over 6000 steps",
            "reopt_cost": None,
            "plan_feasible": None,
        })
        # velocity-field anisotropy (primary quantitative proxy for the
        # 'globally coordinated vs local' claim, evaluated at 4 steps)
        for step in ["0", "999", "2999", "5999"]:
            rows.append({
                "claim_id": "C02",
                "metric": f"velocity_grad_top_share_p{pkey}_step{step}",
                "value": flow["velocity_metrics"][pkey][step]["grad_top_share"],
                "claim_value": None,
                "rel_diff_pct": None,
                "criterion": "s1/(s1+s2) of the MMD gradient matrix at the given step (higher = more globally coordinated force field)",
                "reopt_cost": None,
                "plan_feasible": None,
            })

    # ── write CSV ───────────────────────────────────────────────────────
    fieldnames = ["claim_id", "metric", "value", "claim_value", "rel_diff_pct", "criterion", "reopt_cost", "plan_feasible"]
    with open(OUT / "evidence_table.csv", "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)
    print(f"Wrote {OUT / 'evidence_table.csv'} ({len(rows)} rows)")

    # ── metrics.json (key metrics, keys consistent with evidence table) ─
    metrics = {
        "C01_static_ot_costs": {p: static["plans"][p]["frozen_cost"] for p in ["1", "2", "inf"]},
        "C01_static_ot_claim": dict(static["claim_values"]),
        "C01_reopt_costs": {p: static["plans"][p].get("reopt_cost") for p in ["1", "2", "inf"]},
        "C02_mmd_final_losses": {p: flow["final_losses"][p]["recomputed"] for p in ["1", "2", "inf"]},
        "C02_mmd_final_loss_claim": dict(flow["claim_values"]),
        "C02_trajectory_top_singular_share": {p: flow["trajectory_metrics"][p]["top_share"] for p in ["1", "2", "inf"]},
        "C02_trajectory_s1_over_s2": {p: flow["trajectory_metrics"][p]["cond_s1_over_s2"] for p in ["1", "2", "inf"]},
        "C02_trajectory_mean_abs_cos": {p: flow["trajectory_metrics"][p]["mean_abs_cos_top_dir"] for p in ["1", "2", "inf"]},
        "C02_loss_reproduced_max_abs_diff": {p: flow["final_losses"][p]["max_abs_loss_diff_vs_frozen"] for p in ["1", "2", "inf"]},
        "C02_velocity_grad_top_share": {p: {k: v["grad_top_share"] for k, v in flow["velocity_metrics"][p].items()} for p in ["1", "2", "inf"]},
    }
    with open(OUT / "metrics.json", "w", encoding="utf-8") as fh:
        json.dump(metrics, fh, indent=2)
    print(f"Wrote {OUT / 'metrics.json'}")


if __name__ == "__main__":
    main()
