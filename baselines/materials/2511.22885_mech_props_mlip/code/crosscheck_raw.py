#!/usr/bin/env python3
"""
crosscheck_raw.py
=================
Cross-check that the derived Deltas table (all_metrics_deltas_from_reference.xlsx,
sheet "Deltas") is internally consistent with the raw per-model summary files:

  * Bulk      -> 4-data/bulk_NVT/<folder>/bulk_modulus_results_stress.xlsx
                 column "Bulk Modulus (GPa)"
  * NTE/CTE   -> 4-data/nte_results_ref.xlsx            (values in MK-1)
  * Stability -> 4-data/stability_results.xlsx          (sheet Stability_Results,
                 column SevenNet-MF-ompa ignored, values clipped to [50, 1000]
                 as done by the official pipeline)

Prints a per-metric mismatch report and exits non-zero if any mismatch is found.

Usage:
  python crosscheck_raw.py [DATA_ROOT]
DATA_ROOT defaults to the first existing of:
    <script_dir>/../data
    F:\\dataset\\materials\\2511.22885_mech_props_mlip
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

# Model column name in NTE/stability files -> method name in Deltas
METHODS = {
    'orbital': 'orbital',
    'mace-mp-0': 'mace-mp-0',
    'mace2.0': 'mace2.0',
    'macemof': 'macemof',
    'fairchem_omat': 'fairchem_omat',
    'fairchem_odac': 'fairchem_odac',
}
# Deltas method -> bulk_NVT subfolder
BULK_FOLDER = {
    'orbital': 'orbital', 'mace-mp-0': 'mace-1', 'mace2.0': 'mace-2',
    'macemof': 'mace-mof', 'fairchem_omat': 'fairchem_omat',
    'fairchem_odac': 'fairchem_odac',
}


def find_data_root(explicit=None):
    if explicit is not None:
        p = Path(explicit)
        if (p / '4-data' / 'all_metrics_deltas_from_reference.xlsx').exists():
            return p
        raise FileNotFoundError(f"data root {explicit} missing core xlsx")
    script_dir = Path(__file__).resolve().parent
    candidates = [script_dir / '..' / 'data', Path('data').resolve(),
                  Path(r'F:\dataset\materials\2511.22885_mech_props_mlip')]
    for c in candidates:
        if (c / '4-data' / 'all_metrics_deltas_from_reference.xlsx').exists():
            return c
    raise FileNotFoundError("could not locate data root; pass it as argv[1]")


def norm(name):
    return str(name).replace('_', '-').strip()


def main():
    data_root = find_data_root(sys.argv[1] if len(sys.argv) > 1 else None)
    deltas = pd.read_excel(data_root / '4-data' / 'all_metrics_deltas_from_reference.xlsx',
                           sheet_name='Deltas')

    mismatches = []
    checks = 0

    # ---------------- Bulk: NVT xlsx ----------------
    for method, folder in BULK_FOLDER.items():
        p = data_root / '4-data' / 'bulk_NVT' / folder / 'bulk_modulus_results_stress.xlsx'
        raw = pd.read_excel(p)
        raw['Material'] = raw['Material'].apply(norm)
        for _, r in deltas[(deltas['Method'] == method) & (deltas['Metric'] == 'Bulk')].iterrows():
            checks += 1
            match = raw[raw['Material'] == r['Material']]
            if match.empty:
                mismatches.append((r['Material'], method, 'Bulk', 'missing in raw', r['Predicted']))
                continue
            raw_val = float(match['Bulk Modulus (GPa)'].iloc[0])
            if not np.isclose(raw_val, r['Predicted'], rtol=1e-9, atol=1e-9):
                mismatches.append((r['Material'], method, 'Bulk', raw_val, r['Predicted']))

    # ---------------- NTE: nte_results_ref.xlsx ----------------
    nte = pd.read_excel(data_root / '4-data' / 'nte_results_ref.xlsx', index_col=0)
    for _, r in deltas[(deltas['Metric'] == 'NTE')].iterrows():
        checks += 1
        if r['Method'] not in nte.columns or r['Material'] not in nte.index:
            mismatches.append((r['Material'], r['Method'], 'NTE', 'missing in raw', r['Predicted']))
            continue
        raw_val = float(nte.loc[r['Material'], r['Method']])
        if not np.isclose(raw_val, r['Predicted'], rtol=1e-9, atol=1e-9):
            mismatches.append((r['Material'], r['Method'], 'NTE', raw_val, r['Predicted']))

    # ---------------- Stability: stability_results.xlsx ----------------
    stab = pd.read_excel(data_root / '4-data' / 'stability_results.xlsx',
                         sheet_name='Stability_Results', index_col=0)
    stab = stab.drop(columns=[c for c in stab.columns if 'SevenNet' in str(c)])
    for _, r in deltas[(deltas['Metric'] == 'Stability')].iterrows():
        checks += 1
        if r['Method'] not in stab.columns or r['Material'] not in stab.index:
            mismatches.append((r['Material'], r['Method'], 'Stability', 'missing in raw', r['Predicted']))
            continue
        raw_val = stab.loc[r['Material'], r['Method']]
        if isinstance(raw_val, str):  # 'N/A' should not appear for a Deltas row
            mismatches.append((r['Material'], r['Method'], 'Stability', raw_val, r['Predicted']))
            continue
        clipped = float(np.clip(float(raw_val), 50, 1000))  # official pipeline clip
        if not np.isclose(clipped, r['Predicted'], rtol=1e-9, atol=1e-9):
            mismatches.append((r['Material'], r['Method'], 'Stability', clipped, r['Predicted']))

    print(f"Data root : {data_root}")
    print(f"Checked   : {checks} Deltas rows against raw per-model files")
    if mismatches:
        print(f"MISMATCHES ({len(mismatches)}):")
        for m in mismatches:
            print("  ", m)
        sys.exit(1)
    print("RESULT    : all Deltas 'Predicted' values match the raw xlsx files exactly.")

    # Also report how many raw rows exist but are absent from Deltas (expected skips)
    bulk_deltas = {(r['Material'], r['Method']) for _, r in
                   deltas[(deltas['Metric'] == 'Bulk')].iterrows()}
    extra = []
    for method, folder in BULK_FOLDER.items():
        raw = pd.read_excel(data_root / '4-data' / 'bulk_NVT' / folder / 'bulk_modulus_results_stress.xlsx')
        raw['Material'] = raw['Material'].apply(norm)
        for mat in raw['Material']:
            if (mat, method) not in bulk_deltas:
                extra.append((mat, method))
    if extra:
        print(f"Raw rows not in Deltas (expected: macemof for CaMn7O12 / Zr-WO4-2): {sorted(set(extra))}")


if __name__ == '__main__':
    main()
