#!/usr/bin/env python3
"""
03_evidence_summary.py
======================
Aggregate every metric produced by the analysis scripts into:
  results/evidence_table.csv   (指标名 | 数值 | 口径)
  results/metrics.json         (machine-readable, same keys)

It also prints the final claim verdicts:
  C01: "LVI scores per LFA range from 2 to 2.5; LFA 41 scores 2.5 (BNAM) /
       2 (CM2.6); none experience net loss"
  C02: "BNAM and CM2.6 bottom temperature projections show similar spatial
       patterns but different magnitudes"
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parents[1] / "results"


def read_csv(name: str) -> pd.DataFrame:
    return pd.read_csv(OUT / name)


def main() -> None:
    pct = read_csv("pct_change_per_lfa_cm26_recomputed.csv")
    pct["LFA"] = pct["LFA"].astype(str)
    lvi = read_csv("lvi_per_lfa_recomputed.csv")
    lvi["LFA"] = lvi["LFA"].astype(str)
    cm26 = read_csv("cm26_temp_change_stats.csv").iloc[0]
    sub = read_csv("cm26_temp_change_subregions.csv")
    bnam = read_csv("bnam_present_temp_stats.csv").iloc[0]
    comp = read_csv("cm26_vs_bnam_present_comparison.csv").iloc[0]

    # ------------------------------------------------------------------ #
    # Build evidence rows: (metric, value, definition)
    # ------------------------------------------------------------------ #
    ev = []

    def add(metric, value, definition):
        ev.append({"指标名": metric, "数值": value, "口径": definition})

    # ---- C01: LVI recomputation (CM2.6) ----
    offshore = lvi[lvi["LFA"].isin(["33", "34", "35", "36", "38", "41"])]
    lvi_vals = offshore.set_index("LFA")["LVI"]
    add("lvi_range_paper_lfas_cm26",
        f"{float(lvi_vals.min()):.1f}-{float(lvi_vals.max()):.1f}",
        "Range of recomputed LVI across paper Fig-6 LFAs (33,34,35,36,38,41), CM2.6 scenario")
    for lfa in ["33", "34", "35", "36", "38", "41"]:
        v = lvi_vals[lfa]
        add(f"lvi_lfa{lfa}_cm26_recomputed", f"{v:.1f}" if pd.notna(v) else "NaN",
            f"Recomputed LVI for LFA {lfa}, CM2.6 scenario (Table 2 lookup)")
    add("lvi_lfa41_cm26_paper", "2",
        "Paper-reported LVI for LFA 41 under CM2.6 (paper p.11, Fig 6)")
    add("lvi_lfa41_bnam_paper", "2.5",
        "Paper-reported LVI for LFA 41 under BNAM (paper p.11, Fig 6)")
    add("lvi_lfa41_bnam_verifiable", "False",
        "BNAM future (2055 RCP8.5) field absent from frozen data; BNAM exposure/LVI not computable")
    add("none_net_loss_median_supported", str(bool((pct["median_pct_change"] >= 0).all())),
        "All 8 paper LFAs have median percent change in suitable habitat >= 0 (CM2.6)")
    add("lfa35_median_pct_change_cm26", f"{pct.loc[pct.LFA=='35','median_pct_change'].iloc[0]:.3f}",
        "LFA 35 median percent change (paper says gain 'only marginally outweighs the loss')")
    add("lfa35_mean_pct_change_cm26", f"{pct.loc[pct.LFA=='35','mean_pct_change'].iloc[0]:.3f}",
        "LFA 35 mean percent change (recomputed)")

    # ---- C02: temperature projections ----
    add("cm26_bottom_temp_change_mean", f"{cm26['mean']:.4f}",
        "CM2.6 bottom-temp change (one_percent-control), arithmetic mean over valid ocean cells (degC)")
    add("cm26_bottom_temp_change_area_weighted_mean", f"{cm26['area_weighted_mean']:.4f}",
        "Area-weighted (cos-lat) mean of CM2.6 bottom-temp change (degC)")
    add("cm26_bottom_temp_change_median", f"{cm26['median']:.4f}",
        "Median CM2.6 bottom-temp change (degC)")
    add("cm26_bottom_temp_change_max", f"{cm26['max']:.4f}",
        "Maximum CM2.6 bottom-temp change (degC)")
    add("cm26_bottom_temp_change_min", f"{cm26['min']:.4f}",
        "Minimum CM2.6 bottom-temp change (degC)")
    add("cm26_frac_cells_warming", f"{cm26['frac_warming_gt_0']:.4f}",
        "Fraction of valid CM2.6 ocean cells with positive bottom-temp change")
    add("cm26_frac_cells_gt_2C", f"{cm26['frac_gt_2C']:.4f}",
        "Fraction of valid CM2.6 ocean cells with bottom-temp change > 2 degC")
    add("cm26_max_warming_location",
        f"lon={cm26['max_change_lon']:.2f}, lat={cm26['max_change_lat']:.2f}",
        "Lat/lon of the maximum CM2.6 bottom-temp change cell")
    for _, r in sub.iterrows():
        add(f"cm26_subregion_mean_{r['subregion'].split(' ')[0]}", f"{r['mean_change']:.3f}",
            f"Mean CM2.6 bottom-temp change in {r['subregion']} (degC)")

    add("bnam_future_projection_available", "False",
        "BNAM 2055 RCP8.5 monthly bottom-temperature field is NOT in the frozen data (P03/P17 reports)")
    add("bnam_present_annual_mean_in_cm26_domain", f"{bnam['annual_mean_in_cm26_domain']:.4f}",
        "BNAM present-day (1990-2015) annual-mean bottom temp in CM2.6 domain (degC)")
    add("bnam_summer_jas_mean", f"{bnam['summer_mean_JAS_in_cm26_domain']:.4f}",
        "BNAM present-day summer (JAS) mean bottom temp in CM2.6 domain (degC)")
    add("bnam_winter_jfm_mean", f"{bnam['winter_mean_JFM_in_cm26_domain']:.4f}",
        "BNAM present-day winter (JFM) mean bottom temp in CM2.6 domain (degC)")
    add("present_day_spatial_corr_cm26_vs_bnam", f"{comp['spatial_corr_present']:.4f}",
        "Spatial correlation of present-day bottom temp (CM2.6 control vs BNAM climatology, overlap cells)")
    add("present_day_bias_bnam_minus_cm26", f"{comp['mean_bias_BNAM_minus_CM26_control']:.4f}",
        "Mean present-day bias BNAM - CM2.6 control (degC)")
    add("c02_direct_projection_comparison_possible", "False",
        "BNAM projection change field absent; direct BNAM-vs-CM2.6 projection comparison not computable")

    evdf = pd.DataFrame(ev)
    evdf.to_csv(OUT / "evidence_table.csv", index=False, encoding="utf-8-sig")

    # ------------------------------------------------------------------ #
    # Machine-readable metrics.json (keys identical to evidence table)
    # ------------------------------------------------------------------ #
    metrics = {r["指标名"]: r["数值"] for _, r in evdf.iterrows()}
    metrics["_verdicts"] = {
        "C01": {
            "verdict": "partially_supported",
            "summary": (
                "'None experience net loss' is supported (all CM2.6 LFAs have median % change >= 0). "
                "The reported LVI values (range 2-2.5; LFAs 33/38 score 2; LFA 41 = 2 under CM2.6) are "
                "NOT reproduced: recomputed CM2.6 LVI = 2.0-3.5, with LFA 33=2.5, 38=2.5, 41=3.5. "
                "The BNAM-specific value (LFA 41 = 2.5) is unverifiable because the BNAM 2055 RCP8.5 "
                "field is absent from the frozen data."
            ),
            "mismatched_lfas_cm26": ["33", "38", "41"],
            "matched_lfas_cm26": ["34", "35", "36"],
        },
        "C02": {
            "verdict": "inconclusive",
            "summary": (
                "The direct BNAM-vs-CM2.6 projection comparison cannot be made: the frozen data contain "
                "the CM2.6 bottom-temperature change field and the BNAM present-day climatology, but NOT "
                "the BNAM 2055 RCP8.5 projection. CM2.6 change is fully characterised (mean 1.52 C, "
                "100% of cells warming, max 6.81 C, largest changes on Gulf of Maine/Georges Bank/Scotian "
                "Shelf). The paper-cited 'CM2.6 larger than BNAM' magnitude contrast cannot be verified."
            ),
        },
    }
    with open(OUT / "metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)

    print("Wrote", OUT / "evidence_table.csv", "and", OUT / "metrics.json")
    print("\n=== Final claim verdicts ===")
    for claim, info in metrics["_verdicts"].items():
        print(f"\n{claim}: {info['verdict'].upper()}")
        print(f"  {info['summary']}")


if __name__ == "__main__":
    main()
