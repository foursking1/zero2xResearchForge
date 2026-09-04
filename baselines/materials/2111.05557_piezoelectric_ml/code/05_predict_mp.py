"""05_predict_mp.py
Expansion prediction (paper anchor #7): apply the best trained model (SVR on
enhanced features) to Materials Project compounds and report the top-20
predicted high-piezoelectric candidates. Also lists the RF top-20 for contrast.
Outputs: results/mp_expansion_predictions.csv, results/mp_top20.csv
"""
import os
import sys
import json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.svm import SVR
from sklearn.preprocessing import StandardScaler

from common import (load_labels, load_mp, parse_formula, ELEM, PROPERTY_NAMES,
                    composition_basic_features, SYMMETRY_CLASSES, SEED,
                    RESULTS_DIR)

np.random.seed(SEED)

df = load_labels()
mp = load_mp()

# symmetry class from spacegroup number (international tables ranges)
def spacegroup_to_class(sg):
    if sg <= 2: return "triclinic"
    if sg <= 15: return "monoclinic"
    if sg <= 74: return "orthorhombic"
    if sg <= 142: return "tetragonal"
    if sg <= 167: return "trigonal"
    if sg <= 194: return "hexagonal"
    return "cubic"

# ---- parse MP compositions -------------------------------------------------
mp = mp.copy()
mp["_comp"] = mp["pretty_formula"].map(parse_formula)
mp = mp[mp["_comp"].notna()].copy()
mp = mp[mp["_comp"].apply(len) > 0].copy()          # drop empty parses (e.g. 'nan')
mp["_unknown"] = mp["_comp"].apply(
    lambda c: any(e not in ELEM for e in c.keys()))
mp = mp[~mp["_unknown"]].copy()
print("MP compounds with parseable, fully-known compositions:",
      len(mp))

# exclude the labeled (training) materials for the "discovery" prediction
train_ids = set(df["mp_id"])
mp = mp[~mp["material_id"].isin(train_ids)].copy()
print("after excluding the 1,705 labeled materials:", len(mp))

# deduplicate identical compositions (keep first) -> closer to a 'material' list
mp = mp.drop_duplicates(subset="pretty_formula").reset_index(drop=True)
print("after dedup by composition:", len(mp))

# ---- build enhanced features for MP set -----------------------------------
basic_rows = []
for comp in mp["_comp"]:
    basic_rows.append(composition_basic_features(comp))
Xb_mp = pd.DataFrame(basic_rows)

sym = mp["spacegroup.number"].map(spacegroup_to_class).fillna("unknown")
sym_feats = pd.DataFrame({
    f"sym_{s}": (sym == s).astype(float) for s in SYMMETRY_CLASSES
})
polarity = []
for comp in mp["_comp"]:
    els = sorted(comp.keys())
    ens = np.array([ELEM[e][4] for e in els])
    tot = sum(comp.values())
    w = np.array([comp[e] / tot for e in els], dtype=float)
    polarity.append(float(np.average(np.abs(ens[:, None] - ens[None, :]),
                                     weights=w[:, None] * w[None, :])))
mp_feats = pd.DataFrame({
    "mp_final_energy_per_atom": mp["final_energy_per_atom"],
    "mp_formation_energy_per_atom": mp["formation_energy_per_atom"],
    "mp_e_above_hull": mp["e_above_hull"],
    "mp_band_gap": mp["band_gap"],
    "mp_density": mp["density"],
    "mp_volume": mp["volume"],
    "mp_total_magnetization": mp["total_magnetization"],
    "mp_spacegroup_number": mp["spacegroup.number"],
    "mp_nelements": mp["nelements"],
}).fillna(0.0)

Xe_mp = pd.concat([Xb_mp, sym_feats, pd.DataFrame({"EN_pair_polarity": polarity}),
                   mp_feats], axis=1)
print("MP feature matrix:", Xe_mp.shape)

# ensure identical column set as training 'enhanced'
cols = pd.read_csv(os.path.join(RESULTS_DIR, "columns_enhanced.csv"))["column"]
missing = set(cols) - set(Xe_mp.columns)
extra = set(Xe_mp.columns) - set(cols)
if missing:
    print("WARNING missing columns:", sorted(missing))
Xe_mp = Xe_mp[list(cols)]
print("aligned to training columns:", Xe_mp.shape, "extra dropped:", len(extra))

# ---- train best model on ALL labeled data (enhanced features) --------------
d = np.load(os.path.join(RESULTS_DIR, "features.npz"), allow_pickle=True)
Xe_train = pd.DataFrame(d["Xe"], columns=cols)
y_train = d["y"]

sc = StandardScaler()
Xe_s = sc.fit_transform(Xe_train)

svr = SVR(C=10, gamma="scale", epsilon=0.1)
svr.fit(Xe_s, y_train)

rf = RandomForestRegressor(n_estimators=500, max_features="sqrt",
                           random_state=SEED, n_jobs=-1)
rf.fit(Xe_train, y_train)

pred_svr = svr.predict(sc.transform(Xe_mp))
pred_rf = rf.predict(Xe_mp)

out = pd.DataFrame({
    "material_id": mp["material_id"],
    "formula": mp["pretty_formula"],
    "spacegroup_number": mp["spacegroup.number"],
    "crystal_symmetry": sym,
    "band_gap": mp["band_gap"],
    "formation_energy_per_atom": mp["formation_energy_per_atom"],
    "e_above_hull": mp["e_above_hull"],
    "predicted_piezoelectric_modulus_SVR": pred_svr,
    "predicted_piezoelectric_modulus_RF": pred_rf,
})
out.to_csv(os.path.join(RESULTS_DIR, "mp_expansion_predictions.csv"), index=False)

top20 = out.sort_values("predicted_piezoelectric_modulus_SVR",
                        ascending=False).head(20).reset_index(drop=True)
top20.to_csv(os.path.join(RESULTS_DIR, "mp_top20.csv"), index=False)

print("\n===== TOP 20 predicted high-piezoelectric candidates (SVR-enhanced) =====")
print(top20[["rank" if "rank" in top20 else "formula"]].assign(
    rank=range(1, 21)).to_string(index=False)
      if False else
      pd.concat([top20, pd.Series(range(1, 21), name="rank")], axis=1)[
          ["rank", "formula", "material_id", "crystal_symmetry",
           "predicted_piezoelectric_modulus_SVR"]].to_string(index=False))
print("\ntop-20 predicted values (SVR):",
      np.round(top20["predicted_piezoelectric_modulus_SVR"].values, 3).tolist())

summary = {
    "n_mp_total": int(load_mp().shape[0]),
    "n_mp_parseable_known_elements": int(mp.shape[0]),
    "n_excluded_labeled": int(len(train_ids)),
    "n_predicted_materials": int(len(out)),
    "top20_count": int(len(top20)),
}
with open(os.path.join(RESULTS_DIR, "expansion_summary.json"), "w") as f:
    json.dump(summary, f, indent=2)
print("summary:", summary)
print("done.")
