"""02_build_features.py
Build the feature matrices (basic Magpie-like vs enhanced) for the labeled set.
Saves .npz cache + column info for reuse by 03/04/05.
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import pandas as pd

from common import (load_labels, load_mp, parse_formula, build_feature_frame,
                    RESULTS_DIR, FROZEN_DATA_DIR, ELEM, SYMMETRY_CLASSES)

df = load_labels()
mp = load_mp()

# ---- parse compositions --------------------------------------------------
comps = df["Materials"].map(parse_formula)
keep = comps.notna().to_numpy()
n_drop = int((~keep).sum())
print(f"drop unparseable materials: {n_drop} -> {df.loc[~keep, 'Materials'].tolist()}")

sub = df.loc[keep].reset_index(drop=True)
comps = comps.loc[keep].tolist()

# ---- align MP-derived properties on mp_id (same order as sub) ------------
mp_sub = mp.set_index("material_id").loc[sub["mp_id"]].reset_index(drop=True)
print("MP properties aligned on mp_id:", mp_sub.shape)

# ---- build features --------------------------------------------------------
Xb, Xe = build_feature_frame(comps, symmetries=sub["Crystal_Symmetry"].tolist(),
                             mp_sub=mp_sub)

# add a few extra 'enhanced' composition-derived descriptors
pol = []
for comp in comps:
    els, fr = zip(*sorted(comp.items()))
    ens = np.array([ELEM[e][4] for e in els])
    w = np.array(fr, dtype=float)
    pol.append(float(np.average(np.abs(ens[:, None] - ens[None, :]),
                                weights=w[:, None] * w[None, :])))
Xe["EN_pair_polarity"] = pol

# intermediate level: basic + structure descriptors (symmetry + polarity),
# i.e. enriched features WITHOUT the MP energy/magnetic/electronic block.
sym_cols = [c for c in Xe.columns if c.startswith("sym_")]
Xm = pd.concat([Xb, Xe[sym_cols + ["EN_pair_polarity"]]], axis=1)

y = sub["Piezoelectric_Modulus"].to_numpy(dtype=float)
mp_id = sub["mp_id"].to_numpy()
formula = sub["Materials"].to_numpy()
sym = sub["Crystal_Symmetry"].to_numpy()

print(f"\nfeature shapes: basic {Xb.shape}, mid {Xm.shape}, enhanced {Xe.shape}, labels {len(y)}")

np.savez(os.path.join(RESULTS_DIR, "features.npz"),
         Xb=Xb.to_numpy(dtype=np.float64),
         Xm=Xm.to_numpy(dtype=np.float64),
         Xe=Xe.to_numpy(dtype=np.float64),
         y=y, mp_id=mp_id, formula=formula, sym=sym,
         drop_indices=np.where(~keep)[0])
pd.DataFrame({"column": Xb.columns}).to_csv(
    os.path.join(RESULTS_DIR, "columns_basic.csv"), index=False)
pd.DataFrame({"column": Xm.columns}).to_csv(
    os.path.join(RESULTS_DIR, "columns_mid.csv"), index=False)
pd.DataFrame({"column": Xe.columns}).to_csv(
    os.path.join(RESULTS_DIR, "columns_enhanced.csv"), index=False)
pd.DataFrame({"column": Xe.columns[~Xe.columns.isin(Xb.columns)]}).to_csv(
    os.path.join(RESULTS_DIR, "columns_enhanced_only.csv"), index=False)

print("saved results/features.npz + column listings")
