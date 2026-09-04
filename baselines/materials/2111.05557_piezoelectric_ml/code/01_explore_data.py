"""01_explore_data.py
Data statistics & distribution analysis of the frozen piezoelectric dataset.
Outputs: results/data_stats.csv, evidence/figures/*.png
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from common import (load_labels, load_mp, parse_formula, FROZEN_DATA_DIR,
                    RESULTS_DIR, FIGURES_DIR, N_EXPECTED_LABEL_ROWS,
                    N_EXPECTED_MP_ROWS, ELEM, SEED)

plt.rcParams.update({"font.size": 11})

df = load_labels()
mp = load_mp()

print("=" * 70)
print("Data package:", FROZEN_DATA_DIR)
print(f"Piezoelectric_renewed.csv rows (incl. header): {len(df)+1}  -> label rows: {len(df)}")
print(f"MP_allcompounds_synthesis_totalenergy.csv rows: {len(mp)}")
print("=" * 70)

y = df[df.columns[1]].astype(float).values
print("\n-- Piezoelectric_Modulus (C/m^2) distribution --")
print(pd.Series(y).describe().to_string())
print(f"fraction <= 2 C/m^2 : {(y <= 2).mean():.4f}")
print(f"fraction <= 1 C/m^2 : {(y <= 1).mean():.4f}")
print(f"fraction <= 5 C/m^2 : {(y <= 5).mean():.4f}")
print(f"n zeros (non-piezoelectric): {(y == 0).sum()}")
print(f"n negative: {(y < 0).sum()}")

print("\n-- Crystal symmetry distribution --")
sym = df["Crystal_Symmetry"].value_counts()
print(sym.to_string())

# composition parseability
parsed = df["Materials"].map(parse_formula)
n_parseable = parsed.notna().sum()
print(f"\n-- composition parsing --")
print(f"parseable formulas: {n_parseable}/{len(df)}")
bad = df.loc[parsed.isna(), "Materials"].tolist()
print(f"unparseable formulas: {bad}")

# elemental coverage of the property table
els_used = set()
for c in parsed.dropna():
    els_used.update(c.keys())
unknown = sorted(e for e in els_used if e not in ELEM)
print(f"distinct elements in train set: {len(els_used)}, unknown to table: {unknown}")

# save stats
stats = {
    "n_label_rows": int(len(df)),
    "n_mp_rows": int(len(mp)),
    "label_min": float(y.min()),
    "label_max": float(y.max()),
    "label_mean": float(y.mean()),
    "label_median": float(np.median(y)),
    "label_std": float(y.std()),
    "frac_le_2_Cm2": float((y <= 2).mean()),
    "frac_le_1_Cm2": float((y <= 1).mean()),
    "n_zero_labels": int((y == 0).sum()),
    "n_parseable_compositions": int(n_parseable),
    "n_unparseable": int(len(df) - n_parseable),
    "symmetry_counts": sym.to_dict(),
}
pd.DataFrame([stats]).T.to_csv(os.path.join(RESULTS_DIR, "data_stats.csv"),
                               header=["value"])

# figures
fig, axes = plt.subplots(1, 3, figsize=(15, 4.2))
axes[0].hist(y, bins=60, color="#4472C4", edgecolor="white")
axes[0].set_xlabel("Piezoelectric modulus (C/m$^2$)")
axes[0].set_ylabel("count")
axes[0].set_title("Full range")
axes[1].hist(y[y <= 2], bins=60, color="#4472C4", edgecolor="white")
axes[1].set_xlabel("Piezoelectric modulus (C/m$^2$)")
axes[1].set_title("0 - 2 C/m$^2$ (90.3% of data)")
axes[2].bar(sym.index, sym.values, color="#ED7D31")
axes[2].set_xlabel("Crystal symmetry")
axes[2].set_ylabel("count")
axes[2].tick_params(axis="x", rotation=45)
axes[2].set_title("Crystal symmetry distribution")
fig.tight_layout()
fig.savefig(os.path.join(FIGURES_DIR, "data_distribution.png"), dpi=150)
print("\nsaved: results/data_stats.csv, evidence/figures/data_distribution.png")
print("done.")
