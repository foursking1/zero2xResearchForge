# -*- coding: utf-8 -*-
"""
Assemble results/evidence_table.csv and results/metrics.json from the per-claim
analysis JSON outputs.  The `metric` column of the evidence table uses the SAME
key as results/metrics.json so the two files are directly cross-checkable.
"""
import csv
import json
import os

import config as cfg


def load(name):
    with open(os.path.join(cfg.RESULTS_DIR, name)) as fh:
        return json.load(fh)


def main():
    c01 = load("c01_passbands.json")
    c02 = load("c02_normalization.json")
    c03 = load("c03_data_availability.json")
    c04 = load("c04_whitening.json")

    rows = []      # (claim, metric_key, value, unit, definition)
    metrics = {}   # metric_key -> value

    def add(claim, key, value, unit, definition):
        rows.append((claim, key, value, unit, definition))
        metrics[key] = value

    # ---------------- C01 ----------------
    dkm = c01["distance_km"]
    add("C01", "c01_distance_km", dkm, "km",
        "HRV-PFO great-circle distance (from station coordinates)")
    for band in c01["per_band"]:
        m = band["passband"]
        add("C01", f"c01_arrival_time_{m}", band["arrival_time_s"], "s",
            "max envelope in lags 300-4000 s")
        add("C01", f"c01_snr_tail_{m}", band["snr_tail"], "-",
            "peak envelope / RMS envelope in lags 60000-86000 s (tail noise)")
        add("C01", f"c01_snr_near_{m}", band["snr_near"], "-",
            "peak envelope / RMS envelope in lags 5000-20000 s (near noise)")
        add("C01", f"c01_group_velocity_{m}", band["group_velocity_kms"], "km/s",
            "distance / arrival time")
    add("C01", "c01_snr_tail_min", c01["summary"]["min_snr_tail"], "-",
        "min per-band SNR (tail noise)")
    add("C01", "c01_snr_tail_max", c01["summary"]["max_snr_tail"], "-",
        "max per-band SNR (tail noise)")
    add("C01", "c01_snr_tail_mean", c01["summary"]["mean_snr_tail"], "-",
        "mean per-band SNR (tail noise)")
    add("C01", "c01_snr_near_min", c01["summary"]["min_snr_near"], "-",
        "min per-band SNR (near noise)")
    add("C01", "c01_snr_near_max", c01["summary"]["max_snr_near"], "-",
        "max per-band SNR (near noise)")
    add("C01", "c01_snr_near_mean", c01["summary"]["mean_snr_near"], "-",
        "mean per-band SNR (near noise)")

    # ---------------- C02 ----------------
    for rec in c02["records"]:
        label = rec["record"].split(" ")[0]
        for row in rec["rows"]:
            meth = row["method"]
            add("C02", f"c02_event_ambient_{label}_{meth}",
                row["event_ambient_rms_ratio"], "-",
                "RMS(event 10%) / RMS(quiet 10%) after normalization")
            add("C02", f"c02_compression_{label}_{meth}",
                row["compression_vs_raw"], "-",
                "raw ratio / normalized ratio (suppression of earthquake)")

    # ---------------- C03 ----------------
    add("C03", "c03_crlz_present", False, "-",
        "CRLZ data present? (searched manifest, station XML, all mseed)")
    add("C03", "c03_hiz_present", False, "-",
        "HIZ data present? (searched manifest, station XML, all mseed)")
    add("C03", "c03_nz_present", False, "-",
        "NZ-network data present? (searched manifest, station XML, all mseed)")

    # ---------------- C04 ----------------
    for tag, rec in [("BK_CMB_LHZ", c04["validation_raw_earthquake"]),
                     ("HRV_trace", c04["application_hrv_trace"])]:
        orig, whit = rec["original"], rec["whitened"][0]
        add("C04", f"c04_microseism_prom_before_{tag}",
            orig["microseism_5_30s"]["prominence"], "-",
            "P(peak)/median(P) in 5-30 s band before whitening")
        add("C04", f"c04_microseism_prom_after_{tag}",
            whit["microseism_5_30s"]["prominence"], "-",
            "P(peak)/median(P) in 5-30 s band after whitening (fw=0.05 Hz)")
        add("C04", f"c04_band20_32_prom_before_{tag}",
            orig["band_20_32s"]["prominence"], "-",
            "P(peak)/median(P) in 20-32 s band before whitening")
        add("C04", f"c04_band20_32_prom_after_{tag}",
            whit["band_20_32s"]["prominence"], "-",
            "P(peak)/median(P) in 20-32 s band after whitening (fw=0.05 Hz)")
        add("C04", f"c04_flatness_7_150_before_{tag}",
            orig["flatness_7_150s"], "-",
            "std(log P) in 7-150 s band before whitening")
        add("C04", f"c04_flatness_7_150_after_{tag}",
            whit["flatness_7_150s"], "-",
            "std(log P) in 7-150 s band after whitening (fw=0.05 Hz)")

    # ---- write evidence_table.csv ----
    csv_path = os.path.join(cfg.RESULTS_DIR, "evidence_table.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["claim", "metric", "value", "unit", "definition"])
        for r in rows:
            w.writerow(r)

    # ---- write metrics.json ----
    with open(os.path.join(cfg.RESULTS_DIR, "metrics.json"), "w") as fh:
        json.dump(metrics, fh, indent=2, default=float)

    print(f"wrote {csv_path} ({len(rows)} rows) and metrics.json ({len(metrics)} keys)")

    # ---- consistency check ----
    with open(csv_path) as fh:
        table_keys = {r["metric"] for r in csv.DictReader(fh)}
    missing = set(metrics) - table_keys
    extra = table_keys - set(metrics)
    assert not missing and not extra, (missing, extra)
    print("consistency check passed: all metrics.json keys match evidence_table.csv")


if __name__ == "__main__":
    main()
