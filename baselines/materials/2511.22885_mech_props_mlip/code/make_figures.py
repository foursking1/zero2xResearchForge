#!/usr/bin/env python3
"""
make_figures.py
===============
Generate two figures for the report from the frozen Deltas table:

  1. fig_delta_violins.png  -- Delta (predicted - reference) distributions
                               per model for Bulk, NTE and Stability with the
                               per-model median marked (mirrors the paper's
                               combined violin figure).
  2. fig_pred_vs_ref.png    -- predicted vs reference parity scatter per metric.

Usage:
  python make_figures.py [DATA_ROOT] [OUTPUT_DIR]
"""

import sys
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

METHODS = ['orbital', 'mace-mp-0', 'mace2.0', 'macemof', 'fairchem_omat', 'fairchem_odac']
PAPER_NAME = {'orbital': 'Orb-v3', 'mace-mp-0': 'MACE-1', 'mace2.0': 'MACE-2',
              'macemof': 'MACE-MOF', 'fairchem_omat': 'fairchem_OMAT',
              'fairchem_odac': 'fairchem_ODAC'}


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


def main():
    data_root = find_data_root(sys.argv[1] if len(sys.argv) > 1 else None)
    outdir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(__file__).resolve().parent / '..' / 'results'
    outdir.mkdir(parents=True, exist_ok=True)

    df = pd.read_excel(data_root / '4-data' / 'all_metrics_deltas_from_reference.xlsx',
                       sheet_name='Deltas')

    # ---------------- Figure 1: Delta violins ----------------
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.2), sharey=False)
    metrics_info = [('Bulk', r'$\Delta K_T$ / GPa'),
                    ('NTE', r'$\Delta \alpha_V$ / MK$^{-1}$'),
                    ('Stability', r'$\Delta T_{decomp}$ / K')]
    for ax, (metric, ylab) in zip(axes, metrics_info):
        data_by_method = []
        for method in METHODS:
            vals = df.loc[(df['Metric'] == metric) & (df['Method'] == method), 'Delta'].values
            data_by_method.append(vals)
        parts = ax.violinplot(data_by_method, positions=range(len(METHODS)),
                              showmeans=False, showmedians=True, widths=0.7)
        for pc in parts['bodies']:
            pc.set_facecolor('#9ecae1'); pc.set_edgecolor('black'); pc.set_alpha(0.6)
        parts['cmedians'].set_color('red'); parts['cmedians'].set_linewidth(2)
        # jittered points
        for i, method in enumerate(METHODS):
            vals = data_by_method[i]
            x = i + np.random.default_rng(42).uniform(-0.18, 0.18, len(vals))
            ax.scatter(x, vals, s=14, color='k', alpha=0.55, zorder=3)
        ax.axhline(0, color='tab:gray', ls='--', lw=1)
        ax.set_xticks(range(len(METHODS)))
        ax.set_xticklabels([PAPER_NAME[m] for m in METHODS], rotation=45, ha='right')
        ax.set_ylabel(ylab)
        ax.set_title(metric)
    fig.tight_layout()
    fig.savefig(outdir / 'fig_delta_violins.png', dpi=200)
    plt.close(fig)

    # ---------------- Figure 2: predicted vs reference parity ----------------
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.2))
    colors = plt.get_cmap('tab10').colors
    for ax, (metric, ylab) in zip(axes, metrics_info):
        sub = df[df['Metric'] == metric]
        for i, method in enumerate(METHODS):
            s = sub[sub['Method'] == method]
            ax.scatter(s['Reference'], s['Predicted'], s=20, alpha=0.7,
                       label=PAPER_NAME[method], color=colors[i])
        lo = min(sub['Reference'].min(), sub['Predicted'].min())
        hi = max(sub['Reference'].max(), sub['Predicted'].max())
        ax.plot([lo, hi], [lo, hi], 'k--', lw=1)
        ax.set_xlabel('Reference')
        ax.set_ylabel('Predicted')
        ax.set_title(metric)
        if metric == 'Stability':
            ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(outdir / 'fig_pred_vs_ref.png', dpi=200)
    plt.close(fig)
    print(f"figures written to {outdir}")


if __name__ == '__main__':
    main()
