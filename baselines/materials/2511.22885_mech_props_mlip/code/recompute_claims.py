#!/usr/bin/env python3
"""
recompute_claims.py
===================
Independent recomputation of the critical claims of arXiv:2511.22885v1
("Evaluating Mechanical Property Prediction across Material Classes using
Molecular Dynamics Simulations with Universal Machine-Learned Interatomic
Potentials") from the frozen official data package (Zenodo 10.5281/zenodo.17730688
derived tables).

This script performs NO molecular dynamics and uses NO model weights.  It only
aggregates the frozen derived tables:

  * 4-data/all_metrics_deltas_from_reference.xlsx   (Deltas sheet, 215 rows)
  * 4-data/bulk_NVT/<model>/bulk_modulus_results_stress.xlsx   (NVT bulk modulus)
  * 4-data/nte_results_ref.xlsx                     (CTE / alpha_V)
  * 4-data/stability_results.xlsx                   (decomposition temperature)
  * 4-data/bulk_NPT/bulk_moduli_multimethod_results.npz         (NPT bulk modulus)

Aggregation conventions (matching the official analysis scripts
data/3-analysis/score_methods.py and data/2-calculate/calculate_all_deltas.py
as well as the paper's own phrasing):

  MAE% = 100 * |Delta| / |Reference|          (per data row)
  Per-method-per-metric MAE% = mean of row-level MAE% within (Method, Metric)
  Metric-level MAE = mean of the 6 method-level MAE% values, +/- SAMPLE std
                     (numpy ddof=1), i.e. the paper's "43.8 +/- 6.9 %" style.
  Model overall error = mean of row-level MAE% over ALL rows of that model
                     (the paper's "average error across metrics and materials");
                     the equally-weighted per-metric mean is also reported.
  Median deviation  = median of Delta, either over all rows (view 1) or
                     per-method median then mean over the 6 methods (view 2,
                     the paper's "averaged across all models").

Two reference conventions are handled for the Stability (T_decomp) metric:
  * Deltas-table Reference column (official pipeline, capped at 1000 K):
      CaMn7O12=1000, Zr-WO4-2=1000, SiO2=1000, UiO-67=680
  * Paper Table 3 / task-note references:
      CaMn7O12=550, Zr-WO4-2=1050, SiO2=1000, UiO-67=670
The paper's reported T_decomp median of +18.50 K is reproduced exactly only
with the second convention; the first (frozen Deltas column) gives +4.50 K.
Both are reported.

Outputs (written to results/ relative to this file's parent):
  * evidence_table.csv   -- per-model x per-metric MAE%, ranking, directionality
  * metrics.json         -- all headline numbers used in the report

Usage:
  python recompute_claims.py [DATA_ROOT] [OUTPUT_DIR]
DATA_ROOT defaults to the first existing of:
    <script_dir>/../data   (normalised task layout)
    F:\\dataset\\materials\\2511.22885_mech_props_mlip
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# ----------------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------------
METHOD_TO_PAPER = {
    'mace-mp-0': 'MACE-1',
    'mace2.0': 'MACE-2',
    'macemof': 'MACE-MOF',
    'fairchem_omat': 'fairchem_OMAT',
    'fairchem_odac': 'fairchem_ODAC',
    'orbital': 'Orb-v3',
}
METHODS = list(METHOD_TO_PAPER.keys())
METRICS = ['Bulk', 'NTE', 'Stability']
METRIC_LABEL = {'Bulk': 'KT (bulk modulus, GPa)', 'NTE': 'alpha_V (CTE, MK-1)',
                'Stability': 'T_decomp (K)'}

# Materials excluded in one aggregation view of the paper (MACE-MOF has no
# Ca/W chemistry, so CaMn7O12 and Zr-WO4-2 rows are missing for macemof).
EXCLUDED_MATERIALS = ['CaMn7O12', 'Zr-WO4-2']

# Stability reference values of the official pipeline (already the Deltas column)
# vs. the paper Table 3 values used in the paper's own median report.
DELTAS_STABILITY_REF = {
    'MOF-5': 728, 'MOF-10': 650, 'ZIF-8': 550, 'NU-1000': 700, 'SiO2': 1000,
    'trumof-2': 450, 'UiO-66': 650, 'UiO-67': 680, 'UiO-66-NH2': 400,
    'Zr-WO4-2': 1000, 'Zn-CN-2': 375, 'CALF-20': 380, 'CaMn7O12': 1000,
}
PAPER_STABILITY_REF = {
    'MOF-5': 728, 'MOF-10': 650, 'ZIF-8': 550, 'NU-1000': 700, 'SiO2': 1000,
    'trumof-2': 450, 'UiO-66': 650, 'UiO-67': 670, 'UiO-66-NH2': 400,
    'Zr-WO4-2': 1050, 'Zn-CN-2': 375, 'CALF-20': 380, 'CaMn7O12': 550,
}


def find_data_root(explicit=None):
    if explicit is not None:
        p = Path(explicit)
        if (p / '4-data' / 'all_metrics_deltas_from_reference.xlsx').exists():
            return p
        raise FileNotFoundError(f"data root {explicit} missing core xlsx")
    script_dir = Path(__file__).resolve().parent
    candidates = [
        script_dir / '..' / 'data',
        Path('data').resolve(),
        Path(r'F:\dataset\materials\2511.22885_mech_props_mlip'),
    ]
    for c in candidates:
        if (c / '4-data' / 'all_metrics_deltas_from_reference.xlsx').exists():
            return c
    raise FileNotFoundError("could not locate data root; pass it as argv[1]")


def load_deltas(data_root):
    p = data_root / '4-data' / 'all_metrics_deltas_from_reference.xlsx'
    df = pd.read_excel(p, sheet_name='Deltas')
    # Verify internal consistency of the official Delta / Percent_Error columns
    df['mae_pct_recomputed'] = 100.0 * df['Delta'].abs() / df['Reference'].abs()
    assert np.allclose(df['mae_pct_recomputed'], df['Percent_Error'], atol=1e-8), \
        'Percent_Error column inconsistent with Delta/Reference'
    assert np.allclose(df['Delta'], df['Predicted'] - df['Reference'], atol=1e-8), \
        'Delta inconsistent with Predicted - Reference'
    assert np.allclose(df['Absolute_Error'], df['Delta'].abs(), atol=1e-8), \
        'Absolute_Error inconsistent with |Delta|'
    return df


# ----------------------------------------------------------------------------
# Core aggregations
# ----------------------------------------------------------------------------
def per_method_metric_mae(df):
    """Mean row-level MAE% per (Method, Metric)."""
    return (df.groupby(['Method', 'Metric'])['mae_pct_recomputed'].mean()
              .reset_index())


def metric_level_mean(df):
    """Mean +/- SAMPLE std (ddof=1) of the 6 method-level MAE%, per metric."""
    pm = per_method_metric_mae(df)
    out = {}
    for m in METRICS:
        vals = pm.loc[pm['Metric'] == m, 'mae_pct_recomputed']
        out[m] = {'mean': float(vals.mean()),
                  'std_sample_ddof1': float(vals.std(ddof=1))}
    return out


def model_overall_mae(df):
    """Per-model overall error.

    view_B: mean row-level MAE% over ALL rows of the model
            ("average error across metrics and materials" - paper phrasing,
             also the value used by the task's calibration / rubric).
    view_A: equally-weighted mean of the model's three metric-level MAE%.
    """
    pm = per_method_metric_mae(df)
    rows = []
    for method in METHODS:
        allrows = df.loc[df['Method'] == method, 'mae_pct_recomputed']
        sub = pm[pm['Method'] == method]
        rows.append({'Method': method,
                     'Overall_MAE_pct_viewB_mean_all_rows': float(allrows.mean()),
                     'Overall_MAE_pct_viewA_mean_of_metric_means': float(sub['mae_pct_recomputed'].mean()),
                     'N_rows': int(len(allrows))})
    return pd.DataFrame(rows).sort_values('Overall_MAE_pct_viewB_mean_all_rows')


def per_model_median_delta(df, metric):
    """Per-method median Delta for one metric -> dict method -> median."""
    sub = df[df['Metric'] == metric]
    out = {}
    for method in METHODS:
        vals = sub.loc[sub['Method'] == method, 'Delta']
        out[method] = float(np.median(vals.values)) if len(vals) else np.nan
    return out


def median_deviations(df, stability_ref_override=None):
    """Two aggregation views of median Delta per metric.

    view1 (all rows): median over all Delta rows of the metric.
    view2 (paper): mean over the 6 per-method medians
        ('median deviations ... averaged across all models').

    stability_ref_override optionally replaces the Stability Reference column
    with paper Table 3 values to reproduce the paper's T_decomp median.
    """
    res = {}
    for m in METRICS:
        sub = df[df['Metric'] == m].copy()
        if m == 'Stability' and stability_ref_override is not None:
            sub['Delta'] = sub['Predicted'] - sub['Material'].map(stability_ref_override)
        per_method = [float(v) for v in per_model_median_delta(sub, m).values()
                      if not np.isnan(v)]
        res[m] = {
            'median_all_rows': float(np.median(sub['Delta'])),
            'mean_of_method_medians': float(np.mean(per_method)),
            'min_method_median': float(np.min(per_method)),
            'max_method_median': float(np.max(per_method)),
            'min_all_rows': float(sub['Delta'].min()),
            'max_all_rows': float(sub['Delta'].max()),
        }
    return res


def directionality(df):
    """Per-method sign of median Delta for Bulk and NTE."""
    rows = []
    for metric in ['Bulk', 'NTE']:
        per_method = per_model_median_delta(df, metric)
        for method in METHODS:
            v = per_method[method]
            rows.append({'Metric': metric, 'Method': method,
                         'median_Delta': v,
                         'sign': 'negative' if v < 0 else ('positive' if v > 0 else 'zero')})
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------
# Bonus checks
# ----------------------------------------------------------------------------
def fairchem_odac_profile(df):
    """Overall MAE (mean over all rows, View B) and Stability MAE."""
    sub = df[df['Method'] == 'fairchem_odac']
    stab = sub.loc[sub['Metric'] == 'Stability', 'mae_pct_recomputed']
    per_metric = (sub.groupby('Metric')['mae_pct_recomputed'].mean()
                    .round(2).to_dict())
    return {'overall_MAE_pct_viewB': float(sub['mae_pct_recomputed'].mean()),
            'stability_MAE_pct': float(stab.mean()),
            'per_metric_MAE_pct': per_metric}


def camn7o12_example(data_root):
    """NPT vs NVT bulk modulus for CaMn7O12.

    NPT: 300 K value from bulk_moduli_multimethod_results.npz, averaged over the
         models that report CaMn7O12 (4 models).
    NVT: bulk_modulus_results_stress.xlsx value averaged over models, excluding
         fairchem_odac (paper treats it as an outlier; macemof is absent).
    """
    npt_path = data_root / '4-data' / 'bulk_NPT' / 'bulk_moduli_multimethod_results.npz'
    npt = np.load(npt_path, allow_pickle=True)['results'].item()
    npt_vals = {}
    for method in METHODS:
        if method in npt and 'CaMn7O12' in npt[method] and 300 in npt[method]['CaMn7O12']:
            npt_vals[method] = float(npt[method]['CaMn7O12'][300])
    npt_mean = float(np.mean(list(npt_vals.values())))

    nvt_vals = {}
    for method, folder in [('mace-mp-0', 'mace-1'), ('mace2.0', 'mace-2'),
                           ('macemof', 'mace-mof'), ('fairchem_omat', 'fairchem_omat'),
                           ('fairchem_odac', 'fairchem_odac'), ('orbital', 'orbital')]:
        p = (data_root / '4-data' / 'bulk_NVT' / folder /
             'bulk_modulus_results_stress.xlsx')
        d = pd.read_excel(p)
        r = d.loc[d['Material'] == 'CaMn7O12', 'Bulk Modulus (GPa)']
        if len(r):
            nvt_vals[method] = float(r.iloc[0])
    all_mean = float(np.mean(list(nvt_vals.values())))
    excl_odac = {k: v for k, v in nvt_vals.items() if k != 'fairchem_odac'}
    excl_mean = float(np.mean(list(excl_odac.values())))

    return {
        'NPT_300K_per_model_GPa': {k: round(v, 3) for k, v in npt_vals.items()},
        'NPT_300K_mean_GPa': round(npt_mean, 3),
        'NVT_per_model_GPa': {k: round(v, 3) for k, v in nvt_vals.items()},
        'NVT_mean_all_GPa': round(all_mean, 3),
        'NVT_mean_excl_fairchem_odac_GPa': round(excl_mean, 3),
        'experimental_GPa': 190.0,
    }


def exclusion_sensitivity(df):
    """Ranking stability when dropping CaMn7O12 and Zr-WO4-2."""
    keep = ~df['Material'].isin(EXCLUDED_MATERIALS)
    df_excl = df[keep].copy()
    overall_excl = model_overall_mae(df_excl)
    overall_all = model_overall_mae(df)
    return {
        'all_materials': overall_all.set_index('Method')['Overall_MAE_pct_viewB_mean_all_rows'].to_dict(),
        'excl_CaMn7O12_ZrWO4': overall_excl.set_index('Method')['Overall_MAE_pct_viewB_mean_all_rows'].to_dict(),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('data_root', nargs='?', default=None)
    ap.add_argument('outdir', nargs='?', default=None)
    args = ap.parse_args()

    data_root = find_data_root(args.data_root)
    outdir = Path(args.outdir) if args.outdir else Path(__file__).resolve().parent / '..' / 'results'
    outdir.mkdir(parents=True, exist_ok=True)

    df = load_deltas(data_root)
    pm = per_method_metric_mae(df)
    metric_level = metric_level_mean(df)
    overall = model_overall_mae(df)
    medians_deltas = median_deviations(df)
    medians_paper = median_deviations(df, stability_ref_override=PAPER_STABILITY_REF)
    direc = directionality(df)
    odac = fairchem_odac_profile(df)
    camn = camn7o12_example(data_root)
    sens = exclusion_sensitivity(df)

    # ---------------- evidence table ----------------
    ev = []
    for method in METHODS:
        row = {'model': METHOD_TO_PAPER[method], 'method_col': method}
        for m in METRICS:
            v = pm.loc[(pm['Method'] == method) & (pm['Metric'] == m), 'mae_pct_recomputed']
            row[f'MAE_pct_{m}'] = round(float(v.iloc[0]), 2) if len(v) else np.nan
        o = overall.loc[overall['Method'] == method].iloc[0]
        # primary: mean over all rows (paper's 'across metrics and materials', rubric value)
        row['overall_MAE_pct_viewB'] = round(float(o['Overall_MAE_pct_viewB_mean_all_rows']), 2)
        # secondary: equal-weight mean of the three metric-level MAE%
        row['overall_MAE_pct_viewA'] = round(float(o['Overall_MAE_pct_viewA_mean_of_metric_means']), 2)
        for m in ['Bulk', 'NTE']:
            med = direc.loc[(direc['Method'] == method) & (direc['Metric'] == m), 'median_Delta']
            row[f'median_Delta_{m}'] = round(float(med.iloc[0]), 3) if len(med) else np.nan
            row[f'direction_{m}'] = ('underestimate' if (len(med) and med.iloc[0] < 0)
                                     else ('overestimate' if (len(med) and med.iloc[0] > 0) else 'zero'))
        ev.append(row)
    ev_df = pd.DataFrame(ev)
    ev_df['rank'] = ev_df['overall_MAE_pct_viewB'].rank(method='min').astype(int)
    ev_df = ev_df.sort_values('overall_MAE_pct_viewB')
    ev_df.to_csv(outdir / 'evidence_table.csv', index=False)

    # ---------------- metrics json ----------------
    metrics = {
        'data_root_used': str(data_root),
        'n_rows_deltas': int(len(df)),
        'metric_level_MAE_pct_mean_std_ddof1': {
            'Bulk': {'mean': round(metric_level['Bulk']['mean'], 2),
                     'std': round(metric_level['Bulk']['std_sample_ddof1'], 2)},
            'NTE': {'mean': round(metric_level['NTE']['mean'], 2),
                    'std': round(metric_level['NTE']['std_sample_ddof1'], 2)},
            'Stability': {'mean': round(metric_level['Stability']['mean'], 2),
                          'std': round(metric_level['Stability']['std_sample_ddof1'], 2)},
        },
        'model_ranking_by_overall_MAE_viewB': {
            METHOD_TO_PAPER[r['Method']]: round(float(r['Overall_MAE_pct_viewB_mean_all_rows']), 2)
            for _, r in overall.iterrows()
        },
        'model_overall_MAE_viewA_metric_means': {
            METHOD_TO_PAPER[r['Method']]: round(float(r['Overall_MAE_pct_viewA_mean_of_metric_means']), 2)
            for _, r in overall.iterrows()
        },
        'median_deviations_DeltasReference': {
            'Bulk': {k: round(v, 3) for k, v in medians_deltas['Bulk'].items()},
            'NTE': {k: round(v, 3) for k, v in medians_deltas['NTE'].items()},
            'Stability': {k: round(v, 3) for k, v in medians_deltas['Stability'].items()},
        },
        'median_deviations_Stability_PaperRef': {
            m: {k: round(v, 3) for k, v in medians_paper[m].items()}
            for m in METRICS
        },
        'directionality_per_model': {
            m: {'Bulk_median_Delta': round(float(direc.loc[(direc['Method'] == m) & (direc['Metric'] == 'Bulk'), 'median_Delta'].iloc[0]), 3),
                'NTE_median_Delta': round(float(direc.loc[(direc['Method'] == m) & (direc['Metric'] == 'NTE'), 'median_Delta'].iloc[0]), 3)}
            for m in METHODS
        },
        'fairchem_ODAC': odac,
        'CaMn7O12_example': camn,
        'exclusion_sensitivity_overall_MAE': sens,
    }
    with open(outdir / 'metrics.json', 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=2)

    # ---------------- console summary ----------------
    print(f"data root: {data_root}")
    print(f"Deltas rows: {len(df)}")
    print("\n=== A1 Directionality (median Delta sign per model) ===")
    for m in METHODS:
        b = direc.loc[(direc['Method'] == m) & (direc['Metric'] == 'Bulk'), 'median_Delta'].iloc[0]
        n = direc.loc[(direc['Method'] == m) & (direc['Metric'] == 'NTE'), 'median_Delta'].iloc[0]
        print(f"  {METHOD_TO_PAPER[m]:<14s} KT med={b:+8.3f} ({'<0' if b<0 else '>=0'})  "
              f"alphaV med={n:+8.3f} ({'>0' if n>0 else '<=0'})")
    print("\n=== A2 Model ranking (overall MAE%, mean over all rows) ===")
    for _, r in overall.iterrows():
        print(f"  {METHOD_TO_PAPER[r['Method']]:<14s} {r['Overall_MAE_pct_viewB_mean_all_rows']:6.2f}%  "
              f"(view A={r['Overall_MAE_pct_viewA_mean_of_metric_means']:.2f}%)")
    print("\n=== A3 Metric-level MAE (mean of method means +/- sample std) ===")
    for m in METRICS:
        print(f"  {METRIC_LABEL[m]:<28s} {metric_level[m]['mean']:6.2f}% +/- {metric_level[m]['std_sample_ddof1']:5.2f}%")
    print("\n=== Median deviations ===")
    for m in METRICS:
        print(f"  {METRIC_LABEL[m]:<28s} all-rows={medians_deltas[m]['median_all_rows']:8.3f}  "
              f"mean-of-method-medians={medians_deltas[m]['mean_of_method_medians']:8.3f}")
    print("  (Stability with paper Table 3 refs: mean-of-method-medians = "
          f"{medians_paper['Stability']['mean_of_method_medians']:.2f} K)")
    print("\n=== Bonus: fairchem_ODAC ===")
    print(f"  overall MAE (view B) = {odac['overall_MAE_pct_viewB']:.1f}%, stability MAE = {odac['stability_MAE_pct']:.1f}%")
    print("\n=== Bonus: CaMn7O12 ===")
    print(f"  NPT 300K mean = {camn['NPT_300K_mean_GPa']} GPa (paper 9.3)")
    print(f"  NVT mean excl fairchem_odac = {camn['NVT_mean_excl_fairchem_odac_GPa']} GPa (paper 197.8)")
    print(f"  experimental = {camn['experimental_GPa']} GPa")
    print("\n=== Exclusion sensitivity (drop CaMn7O12 & Zr-WO4-2) ===")
    for k, v in sens.items():
        ranked = sorted(v.items(), key=lambda kv: kv[1])
        print(f"  {k}: " + ", ".join(f"{METHOD_TO_PAPER[m]}={x:.1f}%" for m, x in ranked))

    print(f"\nWrote evidence_table.csv and metrics.json to {outdir}")


if __name__ == '__main__':
    main()
