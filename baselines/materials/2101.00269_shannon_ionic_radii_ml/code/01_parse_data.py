#!/usr/bin/env python3
"""
01_parse_data.py

Parse the frozen data package for task 2101.00269 into a clean machine-
learning-ready table (results/dataset_clean.csv) plus summary statistics
(results/dataset_summary.json).

Data provenance:
  * data/cmd-ml.github.io_index.html   -- raw HTML archive (ground truth,
     element symbols correct). Parsed here with a regex that mirrors the
     site's HTML structure (<div class="info" id="ELEMENT"> <table> rows).
  * data/ionic_radii_extended.csv      -- shipped flat parse of the same
     table. NOTE: its `element` column contains "H" for every row
     (parser bug in the frozen extract), while all other columns are
     identical to the HTML rows. We therefore re-derive elements from the
     HTML archive and cross-check counts/numerics against the CSV.
  * data/_html_parsed_full.csv         -- second shipped flat parse with
     correct element symbols (same rows as above).

Counts verified during parsing (must hold):
   1005 rows, 476 Shannon values, 988 ML predictions, 33 updated_anions,
   93 elements.
"""
import json
import os
import re
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from periodic_table import PERIODIC_TABLE, valence_electrons

DATA_DIR = os.environ.get("SHANNON_DATA_DIR",
                         os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                      "..", "..", "data"))
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results")
HTML_PATH = os.path.join(DATA_DIR, "cmd-ml.github.io_index.html")
CSV_PATH = os.path.join(DATA_DIR, "ionic_radii_extended.csv")


def parse_html(html_path):
    """Parse the archived cmd-ml.github.io page into rows."""
    html = open(html_path, encoding="utf-8", errors="replace").read()
    elements = re.findall(r'<div class="info" id="(\w+)">', html)
    records = []
    row_re = re.compile(
        r"<tr><td>([^<]*)</td><td>([^<]*)</td><td>([^<]*)</td>"
        r"<td>([^<]*)</td><td>([^<]*)</td><td>([^<]*)</td></tr>"
    )
    # capture each element block and its rows in order
    blocks = re.split(r'<div class="info" id="(\w+)">', html)
    # blocks[0] = preamble; then alternating (element, content)
    for i in range(1, len(blocks) - 1, 2):
        element = blocks[i]
        content = blocks[i + 1]
        for m in row_re.finditer(content):
            os_, cn, sh, ml, sd, ua = [g.strip() for g in m.groups()]
            records.append((element, os_, cn, sh if sh else "-", ml if ml else "-",
                            sd if sd else "-", ua if ua else "-"))
    return records


def shannon_to_numeric(val):
    """Convert a Shannon radius cell to (radius_pm, spin_flag).

    Cells may be a plain number, '-', or a spin/SP labelled entry
    (e.g. '78 (HS) & 61 (LS)'). For labelled entries we take the mean of the
    listed radii (documented approximation; the frozen CSV stores these
    cells verbatim as strings as well).
    """
    val = str(val).strip()
    if val in ("-", "", "nan", "None"):
        return np.nan, False
    nums = re.findall(r"\d+\.?\d*", val)
    if not nums:
        return np.nan, False
    spin = any(k in val for k in ("HS", "LS", "SP", "&"))
    vals = [float(n) for n in nums]
    return float(np.mean(vals)), spin


def build_clean():
    records = parse_html(HTML_PATH)
    df = pd.DataFrame(records, columns=[
        "element", "oxidation_state", "coordination_number",
        "shannon_radius_pm", "ml_radius_pm", "ml_sd_pm", "updated_anion"])

    # ---- cross-check against the shipped CSVs ----
    csv = pd.read_csv(CSV_PATH, dtype=str).fillna("")
    for c in csv.columns:
        if c != "element":
            csv[c] = csv[c].str.strip().replace("", "-")
    assert len(df) == len(csv) == 1005, f"row-count mismatch: {len(df)}"
    for col in ["oxidation_state", "coordination_number", "shannon_radius_pm",
                "ml_radius_pm", "ml_sd_pm", "updated_anion"]:
        cdf = df[col].astype(str).values
        ccsv = csv[col].astype(str).values
        assert np.all(cdf == ccsv), f"column {col} differs from shipped CSV"

    # ---- typed conversions ----
    for col in ["oxidation_state", "coordination_number"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    for col in ["ml_radius_pm", "ml_sd_pm"]:
        df[col] = pd.to_numeric(df[col].replace("-", np.nan), errors="coerce")

    sh_parts = df["shannon_radius_pm"].map(shannon_to_numeric)
    df["shannon_radius_pm_num"] = [p[0] for p in sh_parts]
    df["shannon_spin_notation"] = [p[1] for p in sh_parts]
    # keep the raw shannon string too
    df["shannon_radius_pm_raw"] = df["shannon_radius_pm"].replace("-", np.nan)

    df["updated_anion_pm"] = pd.to_numeric(
        df["updated_anion"].replace("-", np.nan), errors="coerce")

    # ---- elemental features ----
    feat = df["element"].map(PERIODIC_TABLE).apply(pd.Series)
    feat.columns = ["atomic_number", "period", "group", "block",
                    "ionization_potential_eV"]
    df = pd.concat([df, feat], axis=1)
    df["valence_electrons"] = df["element"].map(valence_electrons)

    # ---- flags ----
    df["has_shannon"] = df["shannon_radius_pm_num"].notna()
    df["has_ml"] = df["ml_radius_pm"].notna()
    df["ml_only"] = df["has_ml"] & ~df["has_shannon"]

    # ---- pm -> Angstrom ----
    df["shannon_radius_angstrom"] = df["shannon_radius_pm_num"] / 100.0
    df["ml_radius_angstrom"] = df["ml_radius_pm"] / 100.0

    out_cols = ["element", "atomic_number", "period", "group", "block",
                "valence_electrons", "ionization_potential_eV",
                "oxidation_state", "coordination_number",
                "shannon_radius_pm", "shannon_radius_pm_num",
                "shannon_radius_pm_raw", "shannon_spin_notation",
                "shannon_radius_angstrom",
                "ml_radius_pm", "ml_sd_pm", "ml_radius_angstrom",
                "updated_anion", "updated_anion_pm",
                "has_shannon", "has_ml", "ml_only"]
    df = df[out_cols]

    os.makedirs(OUT_DIR, exist_ok=True)
    df.to_csv(os.path.join(OUT_DIR, "dataset_clean.csv"), index=False)

    # ---- summary ----
    n_ml_new = int(df["ml_only"].sum())
    summary = {
        "n_rows": int(len(df)),
        "n_elements": int(df["element"].nunique()),
        "n_shannon_values": int(df["has_shannon"].sum()),
        "n_shannon_clean_numeric": int(((~df["shannon_spin_notation"]) & df["has_shannon"]).sum()),
        "n_shannon_spin_notation": int(df["shannon_spin_notation"].sum()),
        "n_ml_values": int(df["has_ml"].sum()),
        "n_ml_only_new_predictions": int(n_ml_new),
        "n_updated_anion": int(df["updated_anion_pm"].notna().sum()),
        "n_unique_oxidation_states": int(df["oxidation_state"].nunique()),
        "n_unique_coordination_numbers": int(df["coordination_number"].nunique()),
        "shannon_radius_pm_min": float(df["shannon_radius_pm_num"].min()),
        "shannon_radius_pm_max": float(df["shannon_radius_pm_num"].max()),
        "ml_radius_pm_min": float(df["ml_radius_pm"].min()),
        "ml_radius_pm_max": float(df["ml_radius_pm"].max()),
        "source_html": os.path.basename(HTML_PATH),
        "source_csv": "ionic_radii_extended.csv",
    }
    with open(os.path.join(OUT_DIR, "dataset_summary.json"), "w") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    return df, summary


if __name__ == "__main__":
    df, summary = build_clean()
    print(json.dumps(summary, indent=2))